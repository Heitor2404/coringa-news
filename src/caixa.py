"""LIVRO-CAIXA COM TRAVA (Plano Mestre §5). Protege dinheiro real; não é o antigo `orcamento_video` (que só monitora o
equivalente do Claude Code e "não bloqueia").

Três métricas separadas, nunca somadas entre si:
  cobrado_usd  — cobrança efetiva em dinheiro (provedor pago);
  credito_usd  — consumo equivalente de assinatura/créditos (ex.: Claude Code com OAuth: cobrança 0);
  cota         — unidades de cota gratuita (pedidos ao Gemini grátis, Groq...).

REGRA CENTRAL (P1b, 16/11): cobrança que não pode ser verificada conta como o PIOR CASO, nunca como zero.
  * provedor que cobra (faturamento 'pago' ou 'confirmar') só é chamado com: ratificação humana do teto
    (CAIXA_RATIFICADO), pior caso declarado > 0 e um MEDIDOR que lê a cobrança real da resposta. Sem medidor → negado
    antes de chamar (cobrança não verificável).
  * medidor que não consegue ler (None/erro), falha da chamada, ou `depois()` sem cobrança informada → registra o pior
    caso e trava novas chamadas pagas do vídeo (o medidor deixou de ser confiável).
  * reserva feita e nunca liquidada (execução morta no meio) → na próxima abertura vira gasto no pior caso.
  * provedor declarado grátis cujo medidor acusar cobrança > 0 → registra a cobrança e bloqueia o provedor.
  * provedor desconhecido → negado. Limites de tentativas pagas por etapa, chamadas totais e tempo → negado.

ARMAZÉM: 'local' (arquivo + trava de arquivo; só protege o mesmo computador) ou 'git' (ramo `caixa-livro` do próprio
repositório, cifrado; cada mudança é um commit empurrado SEM força: se outro runner empurrou antes, o push é recusado,
o livro é relido e a decisão refeita — compare-and-swap). No git, a exclusão entre runners é um ARRENDAMENTO gravado no
livro (quem abriu, até quando); outro runner não abre o mesmo vídeo enquanto o arrendamento valer. Fora de um caixa
aberto, `antes()` devolve None e nada muda.
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
import re
import socket
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

TETO_USD = float(os.getenv('CAIXA_TETO_USD') or 0.80)        # limite de segurança provisório (não habilita pagos)
ALERTA_USD = float(os.getenv('CAIXA_ALERTA_USD') or 0.60)
MAX_POR_ETAPA = int(os.getenv('CAIXA_MAX_POR_ETAPA') or 4)    # tentativas PAGAS por etapa
MAX_CHAMADAS = int(os.getenv('CAIXA_MAX_CHAMADAS') or 200)    # todas as chamadas (inclusive grátis)
MAX_SEGUNDOS = float(os.getenv('CAIXA_MAX_SEGUNDOS') or 5400)
ARRENDAMENTO_S = MAX_SEGUNDOS + 900

# Faturamento declarado de cada provedor usado hoje. 'assinatura' e 'cota' não geram cobrança em dinheiro pelo que está
# configurado (OAuth da assinatura; chaves do plano grátis). 'confirmar' = pode cobrar dependendo do plano da conta:
# tratado como pago. Qualquer provedor fora daqui é desconhecido → negado.
PROVEDORES = {
    'claude_code': {'faturamento': 'assinatura', 'nota': 'CLI com CLAUDE_CODE_OAUTH_TOKEN; ANTHROPIC_API_KEY removida do ambiente'},
    'gemini': {'faturamento': 'cota', 'nota': 'chaves do plano grátis (texto, visão e TTS); se a conta ganhar faturamento, mudar para pago'},
    'groq': {'faturamento': 'cota', 'nota': 'plano grátis'},
    'pollinations': {'faturamento': 'cota', 'nota': 'serviço grátis sem conta'},
    'gemini_imagem': {'faturamento': 'confirmar', 'nota': 'geração de imagem do Gemini: em geral fora do plano grátis'},
    'cloudflare': {'faturamento': 'confirmar', 'nota': 'Workers AI: alocação diária grátis; conta paga cobra além dela; a resposta não traz o custo'},
}
PAGOS = ('pago', 'confirmar')
_HUMANO = re.compile(r'^humano:[^:]+:\d{4}-\d{2}-\d{2}$')


class OperacaoNegada(RuntimeError):
    """A trava recusou a operação. A mensagem diz o motivo e o que precisa de autorização."""


class CaixaOcupado(RuntimeError):
    """Outra execução já está com o caixa deste vídeo aberto (ou o armazém não pôde ser usado com segurança)."""


class Conflito(RuntimeError):
    """O livro mudou no armazém remoto entre a leitura e a gravação."""


_ATUAL: dict = {}


def _provedores() -> dict:
    extra = os.getenv('CAIXA_PROVEDORES')            # ex.: '{"cloudflare": {"faturamento": "pago"}}'
    p = {k: dict(v) for k, v in PROVEDORES.items()}
    if extra:
        for k, v in json.loads(extra).items():
            p.setdefault(k, {}).update(v)
    return p


def faturamento(provedor: str) -> str:
    return (_provedores().get(provedor) or {}).get('faturamento', 'desconhecido')


def ratificado() -> bool:
    return bool(_HUMANO.match(os.getenv('CAIXA_RATIFICADO') or ''))


def _slug(video: str) -> str:
    return re.sub(r'[^a-z0-9_-]+', '-', video.lower())[:60] or 'video'


def _novo_livro(video: str) -> dict:
    return {'video': video, 'cobrado_usd': 0.0, 'credito_usd': 0.0, 'cota': {}, 'operacoes': [], 'negadas': [],
            'por_etapa': {}, 'chamadas': 0, 'segundos': 0.0, 'execucoes': 0, 'reservas': {}, 'travado': '',
            'provedores_bloqueados': {}, 'arrendamento': None}


# ---------------------------------------------------------------- armazéns
class ArmazemLocal:
    """Arquivo JSON + trava de arquivo. Protege só execuções no MESMO computador."""
    remoto = False

    def __init__(self, pasta: Path):
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)
        self._fd = None

    def _arq(self, video):
        return self.pasta / f'caixa_{_slug(video)}.json'

    def travar(self, video):
        fd = os.open(str(self._arq(video).with_suffix('.lock')), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise CaixaOcupado(f'outra execução está gastando o orçamento de "{video}"')
        self._fd = fd

    def soltar(self, video):
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None

    def ler(self, video):
        a = self._arq(video)
        return (json.loads(a.read_text(encoding='utf-8')) if a.exists() else None), None

    def gravar(self, video, livro, versao):
        a = self._arq(video)
        tmp = a.with_suffix('.tmp')
        tmp.write_text(json.dumps(livro, ensure_ascii=False, indent=1), encoding='utf-8')
        tmp.replace(a)
        return None


class ArmazemGit:
    """Livro num ramo do repositório (padrão `caixa-livro`), um arquivo cifrado por vídeo. Gravar = commit novo sobre a
    versão lida + push sem força; push recusado = Conflito (outro runner gravou antes). Não mexe na árvore de trabalho."""
    remoto = True

    def __init__(self, repo: Path, chave: str, remoto: str = 'origin', ramo: str = 'caixa-livro'):
        if not chave:
            raise CaixaOcupado('armazém git do caixa sem chave (CAIXA_CHAVE/CHECKPOINT_KEY): não abro sem cifrar')
        from cryptography.fernet import Fernet
        self.repo, self.remoto_nome, self.ramo = Path(repo), remoto, ramo
        self.f = Fernet(base64.urlsafe_b64encode(hashlib.sha256(('coringa-caixa-v1:' + chave).encode()).digest()))

    def _git(self, *a, inp=None, env=None):
        return subprocess.run(['git', '-C', str(self.repo), *a], input=inp, capture_output=True, text=True,
                              env={**os.environ, **(env or {})})

    def _caminho(self, video):
        return f'{_slug(video)}.json.enc'

    def travar(self, video):        # a exclusão entre runners é o arrendamento no próprio livro (ver abrir)
        pass

    def soltar(self, video):
        pass

    def ler(self, video):
        ls = self._git('ls-remote', '--heads', self.remoto_nome, self.ramo)
        if ls.returncode != 0:
            raise CaixaOcupado(f'não consegui ler o livro remoto: {ls.stderr.strip()[:200]}')
        if not ls.stdout.strip():
            return None, None                               # ramo ainda não existe
        f = self._git('fetch', '-q', self.remoto_nome, f'+refs/heads/{self.ramo}:refs/caixa/{self.ramo}')
        if f.returncode != 0:
            raise CaixaOcupado(f'não consegui ler o livro remoto: {f.stderr.strip()[:200]}')
        versao = self._git('rev-parse', f'refs/caixa/{self.ramo}').stdout.strip()
        r = self._git('show', f'{versao}:{self._caminho(video)}')
        if r.returncode != 0:
            return None, versao
        return json.loads(self.f.decrypt(r.stdout.strip().encode()).decode()), versao

    def gravar(self, video, livro, versao):
        blob = self._git('hash-object', '-w', '--stdin', inp=self.f.encrypt(json.dumps(livro, ensure_ascii=False).encode()).decode()).stdout.strip()
        with tempfile.TemporaryDirectory() as d:
            env = {'GIT_INDEX_FILE': str(Path(d) / 'idx')}
            if versao:
                self._git('read-tree', versao, env=env)
            self._git('update-index', '--add', '--cacheinfo', f'100644,{blob},{self._caminho(video)}', env=env)
            arvore = self._git('write-tree', env=env).stdout.strip()
        cenv = {'GIT_AUTHOR_NAME': 'coringa-caixa', 'GIT_AUTHOR_EMAIL': 'actions@users.noreply.github.com',
                'GIT_COMMITTER_NAME': 'coringa-caixa', 'GIT_COMMITTER_EMAIL': 'actions@users.noreply.github.com'}
        commit = self._git('commit-tree', arvore, *(['-p', versao] if versao else []), '-m', f'caixa: {_slug(video)}', env=cenv).stdout.strip()
        p = self._git('push', '-q', self.remoto_nome, f'{commit}:refs/heads/{self.ramo}')
        if p.returncode != 0:
            raise Conflito(p.stderr.strip()[:200])
        self._git('update-ref', f'refs/caixa/{self.ramo}', commit)
        return commit


def armazem_padrao(pasta: Path):
    """CAIXA_ARMAZEM=git usa o ramo remoto (Actions, entre runners); senão, arquivo local na pasta da execução."""
    if (os.getenv('CAIXA_ARMAZEM') or '').lower() == 'git':
        chave = os.getenv('CAIXA_CHAVE') or os.getenv('CHECKPOINT_KEY') or (
            hashlib.sha256(('coringa-checkpoint-v1:' + os.getenv('COFRE_TOKEN', '')).encode()).hexdigest() if os.getenv('COFRE_TOKEN') else '')
        return ArmazemGit(Path(os.getenv('CAIXA_REPO') or Path(__file__).resolve().parents[1]), chave,
                          ramo=os.getenv('CAIXA_RAMO') or 'caixa-livro')
    return ArmazemLocal(pasta)


# ---------------------------------------------------------------- abrir / fechar
def _transacao(muda):
    """Lê o livro do armazém, aplica `muda(livro)` e grava; em conflito (outro runner gravou), relê e refaz (até 8x).
    Se `muda` levantar, nada é gravado."""
    c = _ATUAL
    for _ in range(8):
        livro, versao = c['_armazem'].ler(c['video'])
        livro = livro or _novo_livro(c['video'])
        r = muda(livro)
        try:
            c['_armazem'].gravar(c['video'], livro, versao)
        except Conflito:
            time.sleep(.15)
            continue
        c['livro'] = livro
        return r
    raise CaixaOcupado('o livro do caixa mudou 8 vezes seguidas durante a gravação: paro por segurança')


def abrir(video: str, pasta: Path, teto: float | None = None, alerta: float | None = None, armazem=None) -> dict:
    """Abre (ou retoma) o caixa do vídeo: total já gasto em execuções anteriores, reservas abandonadas viram gasto no
    pior caso, arrendamento contra outra execução simultânea (git) ou trava de arquivo (local)."""
    arm = armazem or armazem_padrao(Path(pasta))
    arm.travar(video)
    _ATUAL.clear()
    _ATUAL.update(video=video, _armazem=arm, teto=TETO_USD if teto is None else teto, alerta=ALERTA_USD if alerta is None else alerta,
                  inicio=time.time(), ratificado=ratificado(), dono=f'{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}',
                  _pendentes_locais=[])

    def muda(lv):
        ar = lv.get('arrendamento')
        if ar and ar.get('dono') != _ATUAL['dono'] and ar.get('ate', 0) > time.time():
            raise CaixaOcupado(f"outra execução ({ar.get('dono')}) está com o caixa de \"{video}\"")
        for rid, rs in list(lv['reservas'].items()):          # execução anterior morreu com reserva aberta
            lv['cobrado_usd'] = round(lv['cobrado_usd'] + rs['pior_usd'], 6)
            lv['operacoes'].append({**rs, 'ok': False, 'cobrado_usd': rs['pior_usd'], 'verificado': False,
                                    'erro': 'reserva abandonada por execução anterior: contada no pior caso'})
            del lv['reservas'][rid]
        lv['arrendamento'] = {'dono': _ATUAL['dono'], 'ate': time.time() + ARRENDAMENTO_S}
        lv['execucoes'] += 1
    try:
        _transacao(muda)
    except Exception:
        arm.soltar(video)
        _ATUAL.clear()
        raise
    return _ATUAL['livro']


def fechar() -> dict | None:
    if not _ATUAL:
        return None
    c = _ATUAL
    seg = time.time() - c['inicio']
    pend = list(c['_pendentes_locais'])

    def muda(lv):
        for op in pend:                                       # operações sem cobrança acumuladas (gravadas de uma vez)
            _somar(lv, op)
            lv['chamadas'] += 1
        lv['segundos'] = round(lv['segundos'] + seg, 1)
        if (lv.get('arrendamento') or {}).get('dono') == c['dono']:
            lv['arrendamento'] = None
    try:
        _transacao(muda)
    finally:
        c['_armazem'].soltar(c['video'])
    out = dict(c['livro'])
    _ATUAL.clear()
    return out


@contextmanager
def video(rotulo: str, pasta: Path, **kw):
    abrir(rotulo, pasta, **kw)
    try:
        yield _ATUAL['livro']
    finally:
        fechar()


def aberto() -> bool:
    return bool(_ATUAL)


# ---------------------------------------------------------------- operações
def _somar(lv, op):
    lv['credito_usd'] = round(lv['credito_usd'] + op.get('credito_usd', 0.0), 6)
    if op.get('faturamento') == 'cota':
        lv['cota'][op['provedor']] = lv['cota'].get(op['provedor'], 0) + op.get('cota', 1)
    if op.get('cobrado_usd'):
        lv['cobrado_usd'] = round(lv['cobrado_usd'] + op['cobrado_usd'], 6)
    lv['operacoes'].append(dict(op))


def _negar(motivo: str, **info) -> None:
    neg = {'motivo': motivo, **info, 'quando': time.strftime('%Y-%m-%dT%H:%M:%S')}
    try:
        _transacao(lambda lv: lv['negadas'].append(neg))
    finally:
        raise OperacaoNegada(motivo)


def antes(provedor: str, etapa: str, pior_usd: float | None = None, futuros_usd: float = 0.0, medidor: bool = False) -> dict | None:
    """Preflight. Devolve um bilhete para `depois()` ou levanta OperacaoNegada. Sem caixa aberto: None (não interfere).
    `medidor=True` declara que quem chama lê a cobrança real da resposta (obrigatório para provedor que cobra)."""
    if not _ATUAL:
        return None
    c = _ATUAL
    fat = faturamento(provedor)
    info = {'provedor': provedor, 'etapa': etapa, 'faturamento': fat, 'pior_usd': pior_usd}
    lv = c['livro']
    decorrido = lv['segundos'] + time.time() - c['inicio']
    if decorrido > MAX_SEGUNDOS:
        _negar(f'tempo de execução esgotado ({decorrido:.0f}s > {MAX_SEGUNDOS:.0f}s)', **info)
    if lv['chamadas'] + len(c['_pendentes_locais']) >= MAX_CHAMADAS:
        _negar(f'limite de chamadas do vídeo atingido ({MAX_CHAMADAS})', **info)
    if fat == 'desconhecido':
        _negar(f'provedor "{provedor}" sem faturamento declarado: não chamo', **info)
    if provedor in lv['provedores_bloqueados']:
        _negar(f'"{provedor}" bloqueado: {lv["provedores_bloqueados"][provedor]}', **info)
    if fat not in PAGOS:
        return {**info, 'pago': False, 't0': time.time()}
    # ---- provedor que cobra: decisão contra o livro do ARMAZÉM (outro runner pode ter gastado)
    if not c['ratificado']:
        _negar(f'"{provedor}" pode cobrar e o teto não foi ratificado (CAIXA_RATIFICADO): peço autorização', **info)
    if not medidor:
        _negar(f'"{provedor}" ({etapa}): cobrança real não verificável (sem medidor da resposta): não chamo', **info)
    if not isinstance(pior_usd, (int, float)) or not pior_usd > 0:
        _negar(f'custo de "{provedor}" ({etapa}) sem pior caso positivo ({pior_usd!r}): não chamo', **info)
    rid = uuid.uuid4().hex[:10]

    def muda(lv):
        if lv.get('travado'):
            raise OperacaoNegada(f'pagos travados neste vídeo: {lv["travado"]}')
        if lv['por_etapa'].get(etapa, 0) >= MAX_POR_ETAPA:
            raise OperacaoNegada(f'limite de tentativas pagas da etapa "{etapa}" atingido ({MAX_POR_ETAPA})')
        reservado = sum(r['pior_usd'] for r in lv['reservas'].values())
        total = lv['cobrado_usd'] + reservado + pior_usd + futuros_usd
        if total > c['teto']:
            raise OperacaoNegada(f'cobrança prevista US$ {total:.2f} > teto US$ {c["teto"]:.2f}: preciso de autorização explícita')
        lv['reservas'][rid] = {'provedor': provedor, 'etapa': etapa, 'faturamento': fat, 'pior_usd': pior_usd,
                               'dono': c['dono'], 'quando': time.strftime('%Y-%m-%dT%H:%M:%S')}
        lv['por_etapa'][etapa] = lv['por_etapa'].get(etapa, 0) + 1
        lv['chamadas'] += 1
    try:
        _transacao(muda)
    except OperacaoNegada as e:
        _negar(str(e), **info)
    return {**info, 'pago': True, 'reserva': rid, 't0': time.time()}


def depois(bilhete: dict | None, ok: bool = True, cobrado_usd: float | None = None, credito_usd: float = 0.0, cota: int = 1,
           erro: str = '') -> None:
    """Registra a operação. Provedor que cobra: `cobrado_usd` ausente/inválido ou falha → PIOR CASO, e os pagos do vídeo
    ficam travados. Provedor declarado grátis com cobrança > 0 → registra e bloqueia o provedor."""
    if not bilhete or not _ATUAL:
        return
    c = _ATUAL
    op = {k: bilhete[k] for k in ('provedor', 'etapa', 'faturamento')} | {
        'ok': ok, 'credito_usd': credito_usd, 'cota': cota, 'segundos': round(time.time() - bilhete['t0'], 1), **({'erro': erro[:200]} if erro else {})}
    valido = isinstance(cobrado_usd, (int, float)) and not isinstance(cobrado_usd, bool) and cobrado_usd == cobrado_usd and cobrado_usd >= 0
    if bilhete['pago']:
        verificado = ok and valido
        op['cobrado_usd'] = float(cobrado_usd) if verificado else float(bilhete['pior_usd'])
        op['verificado'] = verificado

        def muda(lv):
            lv['reservas'].pop(bilhete['reserva'], None)
            _somar(lv, op)
            if not verificado:
                lv['travado'] = lv.get('travado') or (f"{bilhete['provedor']}/{bilhete['etapa']}: "
                                                      + ('falha da chamada' if not ok else 'cobrança não informada pelo medidor')
                                                      + ' — contada no pior caso')
            if lv['cobrado_usd'] >= c['alerta'] and not lv.get('alertou'):
                lv['alertou'] = True
                print(f"  [caixa] ALERTA: cobrança do vídeo em US$ {lv['cobrado_usd']:.2f} (alerta {c['alerta']:.2f}, teto {c['teto']:.2f})")
        _transacao(muda)
        return
    op['cobrado_usd'] = 0.0
    if valido and cobrado_usd > 0:                          # declarado grátis, mas cobrou: a declaração está errada
        op['cobrado_usd'] = float(cobrado_usd)

        def muda(lv):
            _somar(lv, op)
            lv['chamadas'] += 1
            lv['provedores_bloqueados'][bilhete['provedor']] = f'declarado {bilhete["faturamento"]}, mas cobrou US$ {cobrado_usd:.4f}'
        _transacao(muda)
        return
    c['_pendentes_locais'].append(op)                       # sem cobrança: grava no fechamento (sem um push por chamada)


def operar(provedor: str, etapa: str, fn, pior_usd: float | None = None, futuros_usd: float = 0.0, credito=None, medidor=None):
    """antes() → fn() → depois(), com a cobrança lida por `medidor(resposta) -> usd` quando o provedor cobra.
    Sem medidor, provedor que cobra é negado ANTES de chamar. Falha da chamada = pior caso. OperacaoNegada propaga."""
    b = antes(provedor, etapa, pior_usd, futuros_usd, medidor=medidor is not None)
    try:
        r = fn()
    except Exception as e:
        depois(b, ok=False, cobrado_usd=None, credito_usd=(credito() if credito else 0.0), erro=str(e))
        raise
    cob = None
    if medidor is not None and b is not None:
        try:
            cob = medidor(r)
        except Exception:
            cob = None
    depois(b, ok=True, cobrado_usd=cob, credito_usd=(credito() if credito else 0.0))
    return r


def resumo() -> dict:
    if not _ATUAL:
        return {}
    lv, c = _ATUAL['livro'], _ATUAL
    pend = c['_pendentes_locais']
    cota = dict(lv['cota'])
    for o in pend:
        if o['faturamento'] == 'cota':
            cota[o['provedor']] = cota.get(o['provedor'], 0) + o.get('cota', 1)
    return {'cobrado_usd': lv['cobrado_usd'], 'credito_usd': round(lv['credito_usd'] + sum(o.get('credito_usd', 0) for o in pend), 6),
            'cota': cota, 'chamadas': lv['chamadas'] + len(pend), 'negadas': len(lv['negadas']), 'reservas_abertas': len(lv['reservas']),
            'travado': lv.get('travado'), 'teto': c['teto'], 'alerta': c['alerta'], 'ratificado': c['ratificado'],
            'armazem': 'git' if c['_armazem'].remoto else 'local'}
