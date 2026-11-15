"""CHECKPOINT E RETOMADA POR ETAPA (V2.4).

O piloto da lagartixa bloqueou duas vezes no preparo, e a retomada regenerou TUDO: pesquisa, acervo e roteiro (o
roteiro saiu diferente, com outros contratos sem dados). Aqui cada etapa cara fica gravada e pode ser reaproveitada:

  tema      (a pergunta e os termos do pedido)       ← roteiro.tema_livre
  pesquisa  (fatos, fontes, link, dossiê)           ← fontes.coletar
  acervo    (itens do acervo + os arquivos de imagem)  ← acervo.coletar
  roteiro   (o tema e o roteiro completo `v`, com o acervo final e os contratos já pré-validados)

`--retomar PASTA [--retomar-etapa roteiro|acervo|pesquisa|tema]` carrega as etapas até a escolhida e refaz só as
seguintes. O checkpoint de origem nunca é alterado: a execução nova grava o próprio checkpoint (as etapas carregadas
são copiadas para ele, com a procedência).

Auditoria: cada arquivo de etapa tem sha256 no manifesto e uma cópia intocada em `.original/`. Se alguém editar o
checkpoint à mão (ex.: corrigir um contrato), a retomada detecta, lista o que mudou (por cena e campo) e grava isso em
`v['_checkpoint']`, que vai para os relatórios. Imagens têm sha256 próprio: arquivo trocado também aparece.

Ativo só com MOTOR_VISUAL=v2 (ver main.py). Sem `ativar()`, `etapa()` só executa a função: nada muda.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import re
import os
import shutil
import subprocess
from pathlib import Path

VERSAO = 'checkpoint-v1'
ETAPAS = ('tema', 'pesquisa', 'acervo', 'roteiro')
CAMPOS_ARQUIVO = ('arq',)            # caminhos locais de imagem nos itens do acervo

ATUAL: 'Checkpoint | None' = None


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _commit() -> str:
    if os.getenv('GITHUB_SHA'):
        return os.environ['GITHUB_SHA']
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ''


# ───────────────────────── serialização (Path, bytes, tuplas) ─────────────────────────
def _codificar(x):
    if isinstance(x, Path):
        return str(x)
    if isinstance(x, (bytes, bytearray)):
        return {'__bytes__': base64.b64encode(bytes(x)).decode('ascii')}
    if isinstance(x, dict):
        return {str(k): _codificar(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [_codificar(v) for v in x]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return str(x)


def _decodificar(x):
    if isinstance(x, dict):
        if set(x) == {'__bytes__'}:
            return base64.b64decode(x['__bytes__'])
        return {k: _decodificar(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_decodificar(v) for v in x]
    return x


def _json(obj) -> bytes:
    return json.dumps(_codificar(obj), ensure_ascii=False, indent=1, sort_keys=False).encode('utf-8')


# ───────────────────────── diferenças (para a auditoria de edição à mão) ─────────────────────────
def diferencas(a, b, caminho: str = '', limite: int = 60) -> list[str]:
    out: list[str] = []

    def rec(x, y, p):
        if len(out) >= limite:
            return
        if isinstance(x, dict) and isinstance(y, dict):
            for k in list(dict.fromkeys(list(x) + list(y))):
                if k == 'mini':
                    continue
                if k not in y:
                    out.append(f'{p}.{k}: removido')
                elif k not in x:
                    out.append(f'{p}.{k}: adicionado = {json.dumps(y[k], ensure_ascii=False)[:120]}')
                else:
                    rec(x[k], y[k], f'{p}.{k}')
        elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
            for i, (u, w) in enumerate(zip(x, y)):
                rec(u, w, f'{p}[{i}]')
        elif x != y:
            out.append(f'{p}: {json.dumps(x, ensure_ascii=False)[:100]} → {json.dumps(y, ensure_ascii=False)[:100]}')

    rec(a, b, caminho or '$')
    return out


class Checkpoint:
    def __init__(self, pasta: Path, origem: Path | None = None, ate: str | None = None, pedido: str = '', parte: int = 1):
        self.pasta = Path(pasta)
        self.origem = Path(origem) if origem else None
        if ate and ate not in ETAPAS:
            raise ValueError(f'etapa de retomada desconhecida: {ate!r} (use {", ".join(ETAPAS)})')
        self.ate = (ate or ETAPAS[-1]) if self.origem else None
        self.registro = {'versao': VERSAO, 'origem': str(self.origem) if self.origem else None, 'retomar_ate': self.ate,
                         'carregadas': [], 'executadas': [], 'editado': {}, 'avisos': []}
        self.pasta.mkdir(parents=True, exist_ok=True)
        (self.pasta / 'arquivos').mkdir(exist_ok=True)
        (self.pasta / '.original').mkdir(exist_ok=True)
        self.man_origem = None
        if self.origem:
            arq = self.origem / 'manifesto.json'
            if not arq.exists():
                raise FileNotFoundError(f'checkpoint sem manifesto: {arq}')
            self.man_origem = json.loads(arq.read_text(encoding='utf-8'))
            pedido = pedido or self.man_origem.get('pedido', '')
            parte = parte or self.man_origem.get('parte', 1)
        self.manifesto = {'versao': VERSAO, 'pedido': pedido, 'parte': parte, 'commit': _commit(),
                          'criado': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                          'origem': ({'pasta': str(self.origem), 'commit': self.man_origem.get('commit'),
                                      'criado': self.man_origem.get('criado')} if self.man_origem else None),
                          'etapas': {}}
        self._gravar_manifesto()

    # ── manifesto ──
    def _gravar_manifesto(self):
        (self.pasta / 'manifesto.json').write_text(json.dumps(self.manifesto, ensure_ascii=False, indent=1), encoding='utf-8')

    def carregar_de_origem(self, nome: str) -> bool:
        return bool(self.origem and self.ate and ETAPAS.index(nome) <= ETAPAS.index(self.ate)
                    and nome in (self.man_origem or {}).get('etapas', {}))

    # ── arquivos de imagem ──
    def _guardar_arquivos(self, itens: list) -> dict:
        hashes = {}
        for x in itens or []:
            if not isinstance(x, dict):
                continue
            for campo in CAMPOS_ARQUIVO:
                p = x.get(campo)
                if not p or not Path(p).exists():
                    continue
                pasta_arq = (self.pasta / 'arquivos').resolve()
                destino = Path(p) if Path(p).resolve().parent == pasta_arq else pasta_arq / f"{x.get('id') or Path(p).stem}_{Path(p).name}"
                if Path(p).resolve() != destino.resolve():
                    if destino.exists() and destino.read_bytes() != Path(p).read_bytes():   # ids repetidos: nunca sobrescreve
                        destino = destino.with_name(f"{_sha(Path(p).read_bytes())[:8]}_{destino.name}")
                    shutil.copy2(p, destino)
                rel = str(destino.resolve().relative_to(self.pasta.resolve()))
                hashes[rel] = _sha(destino.read_bytes())
                x[campo] = rel
        return hashes

    def _restaurar_arquivos(self, itens: list, base: Path, hashes: dict, etapa: str):
        for x in itens or []:
            if not isinstance(x, dict):
                continue
            for campo in CAMPOS_ARQUIVO:
                rel = x.get(campo)
                if not rel or Path(str(rel)).is_absolute():
                    continue
                arq = base / rel
                if not arq.exists():
                    self.registro['avisos'].append(f'{etapa}: arquivo ausente {rel} (item {x.get("id")})')
                    x[campo] = None
                    continue
                if hashes.get(rel) and _sha(arq.read_bytes()) != hashes[rel]:
                    self.registro['editado'].setdefault(etapa, []).append(f'imagem trocada: {rel}')
                destino = self.pasta / rel
                if arq.resolve() != destino.resolve():
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(arq, destino)
                x[campo] = destino.resolve()

    @staticmethod
    def _itens(nome: str, obj):
        """Onde estão os itens com arquivo em cada etapa."""
        if nome == 'acervo':
            return obj
        if nome == 'roteiro':
            return (obj.get('v') or {}).get('acervo') or []
        return []

    # ── gravar / carregar ──
    def salvar(self, nome: str, obj, procedencia: str = 'executada'):
        import copy
        obj = copy.deepcopy(obj)
        hashes = self._guardar_arquivos(self._itens(nome, obj))
        dados = _json(obj)
        (self.pasta / f'{nome}.json').write_bytes(dados)
        (self.pasta / '.original' / f'{nome}.json').write_bytes(dados)
        self.manifesto['etapas'][nome] = {'arquivo': f'{nome}.json', 'sha256': _sha(dados), 'arquivos': hashes,
                                          'procedencia': procedencia,
                                          'gravado': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
        self._gravar_manifesto()

    def carregar(self, nome: str):
        info = self.man_origem['etapas'][nome]
        bruto = (self.origem / info['arquivo']).read_bytes()
        obj = _decodificar(json.loads(bruto.decode('utf-8')))
        if _sha(bruto) != info.get('sha256'):
            orig = self.origem / '.original' / info['arquivo']
            mudou = diferencas(json.loads(orig.read_text(encoding='utf-8')), json.loads(bruto.decode('utf-8'))) if orig.exists() \
                else ['arquivo diferente do gravado (sem cópia original para comparar)']
            self.registro['editado'][nome] = mudou or ['mudança só de formatação']
        self._restaurar_arquivos(self._itens(nome, obj), self.origem, info.get('arquivos') or {}, nome)
        if (self.origem / 'edicao_aplicada.json').exists() and nome == 'roteiro':     # quem editou, por quê, o quê
            self.registro['edicao'] = json.loads((self.origem / 'edicao_aplicada.json').read_text(encoding='utf-8'))
        self.registro['carregadas'].append(nome)
        # a execução nova também guarda a etapa (com procedência), para poder ser retomada de novo
        self.salvar(nome, obj, procedencia='carregada de ' + str(self.origem) + (' (EDITADA À MÃO)' if nome in self.registro['editado'] else ''))
        return obj

    def etapa(self, nome: str, fn):
        if self.carregar_de_origem(nome):
            print(f'  [checkpoint] {nome}: retomada de {self.origem}' + (' — EDITADA À MÃO' if nome in self.registro['editado'] else ''))
            return self.carregar(nome)
        obj = fn()
        self.salvar(nome, obj)
        self.registro['executadas'].append(nome)
        return obj


# ───────────────────────── API usada pelo main/roteiro ─────────────────────────
def ativar(pasta: Path, origem: Path | None = None, ate: str | None = None, pedido: str = '', parte: int = 1) -> Checkpoint:
    global ATUAL
    ATUAL = Checkpoint(pasta, origem, ate, pedido, parte)
    return ATUAL


def desativar():
    global ATUAL
    ATUAL = None


def etapa(nome: str, fn):
    """Sem checkpoint ativo: só executa `fn` (o comportamento de sempre)."""
    return ATUAL.etapa(nome, fn) if ATUAL else fn()


def manifesto_de(pasta: Path) -> dict:
    return json.loads((Path(pasta) / 'manifesto.json').read_text(encoding='utf-8'))


def registro() -> dict | None:
    return dict(ATUAL.registro) if ATUAL else None


# ───────────────────────── edição editorial auditada (V2.4) ─────────────────────────
def _caminho(d: dict, chave: str, valor=None, ler: bool = False):
    partes = chave.split('.')
    alvo = d
    for p in partes[:-1]:
        alvo = alvo.setdefault(p, {}) if not ler else (alvo.get(p) or {})
    return alvo.get(partes[-1]) if ler else alvo.__setitem__(partes[-1], valor)


def _limpo_fala(x) -> str:
    return re.sub(r'\s+', ' ', str(x or '').replace('*', '')).strip()


def editar(pasta: Path, edicao: dict) -> dict:
    """Aplica uma edição EDITORIAL localizada ao `roteiro.json` de um checkpoint (antes da retomada).
    Formato: {"motivo", "autor", "operacoes": [{"evento": "e2", "esperado_sha256": {"fala": sha}, "set": {"fala": ...,
    "acontecimento.sujeito": ...}} | {"campo": "resumo", "substituir_sha256": sha_do_trecho, "trecho_novo": ...,
    "trecho_antigo_de": "e2"} | {"campo": "suspense", "valor_de": "e13"}]}.
    Trava: o texto atual de cada campo com `esperado_sha256` precisa bater (edição feita sobre o roteiro certo).
    A cópia intocada continua em `.original/`; a retomada lista o diff campo a campo (Checkpoint.carregar), e a
    própria edição fica gravada em `edicao_aplicada.json` (vai para o relatório)."""
    pasta = Path(pasta)
    arq = pasta / 'roteiro.json'
    d = json.loads(arq.read_text(encoding='utf-8'))
    v = d['v']
    falas_antigas, aplicadas = {}, []
    for op in edicao.get('operacoes') or []:
        if op.get('evento'):
            idx = [k for k, c in enumerate(v['cenas']) if (c.get('acontecimento') or {}).get('id') == op['evento']]
            if not idx:
                raise ValueError(f"edição: acontecimento {op['evento']} não existe no checkpoint")
            for k in idx:
                c = v['cenas'][k]
                for campo, sha in (op.get('esperado_sha256') or {}).items():
                    atual = str(_caminho(c, campo, ler=True) or '')
                    if _sha(atual.encode('utf-8')) != sha:
                        raise ValueError(f"edição: {op['evento']}.{campo} não é o texto esperado (checkpoint errado?)")
                falas_antigas.setdefault(op['evento'], c.get('fala') or '')
                for campo, valor in (op.get('set') or {}).items():
                    _caminho(c, campo, valor)
                aplicadas.append(f"{op['evento']} (cena {k}): {', '.join(op.get('set') or {})}")
        elif op.get('substituir_eventos'):
            # V2.4: troca um TRECHO do roteiro (os planos de uma sequência de acontecimentos) por planos novos, com a
            # mesma trava: o texto atual das falas removidas precisa bater com `esperado_sha256` (falas unidas por \n)
            ids = list(op['substituir_eventos'])
            idx = [k for k, c in enumerate(v['cenas']) if (c.get('acontecimento') or {}).get('id') in ids]
            if not idx or idx != list(range(idx[0], idx[-1] + 1)):
                raise ValueError(f'edição: {ids} não formam um trecho contínuo do roteiro')
            antigas = '\n'.join(str(v['cenas'][k].get('fala') or '') for k in idx)
            if _sha(antigas.encode('utf-8')) != op.get('esperado_sha256'):
                raise ValueError(f'edição: as falas de {ids} não são as esperadas (checkpoint errado?)')
            novas = op.get('cenas') or []
            if not novas or any(not (c.get('fala') and isinstance(c.get('acontecimento'), dict) and c['acontecimento'].get('id')) for c in novas):
                raise ValueError('edição: plano novo sem fala ou sem acontecimento')
            for eid in ids:
                falas_antigas.setdefault(eid, ' '.join(str(c.get('fala') or '') for c in v['cenas'] if (c.get('acontecimento') or {}).get('id') == eid))
            v['cenas'][idx[0]:idx[-1] + 1] = [dict(c) for c in novas]
            aplicadas.append(f"{', '.join(ids)} (planos {idx[0]}–{idx[-1]}) → {len(novas)} plano(s): "
                             + ', '.join(dict.fromkeys(c['acontecimento']['id'] for c in novas)))
        elif op.get('acrescentar_fatos') or op.get('acrescentar_fontes'):
            # fatos novos entram COM a fonte no fim da linha (mesmo formato da pesquisa) e ficam rastreáveis
            for f in op.get('acrescentar_fatos') or []:
                if not re.search(r'\([^()]+\)\s*$', f):
                    raise ValueError(f'edição: fato sem fonte entre parênteses no fim: {f[:60]}')
                v['fatos'] = str(v.get('fatos') or '').rstrip('\n') + '\n- ' + f
            for fo in op.get('acrescentar_fontes') or []:
                if fo not in (v.get('fontes') or []):
                    v.setdefault('fontes', []).append(fo)
            aplicadas.append(f"fatos +{len(op.get('acrescentar_fatos') or [])} · fontes +{len(op.get('acrescentar_fontes') or [])}")
        elif op.get('campo') and op.get('regenerar'):
            # o resumo/suspense sai do roteiro FINAL (falas editadas), não de um texto antigo
            falas = []
            for c in v['cenas']:
                if c.get('tipo') == 'fechamento':
                    continue
                falas.append(_limpo_fala(c.get('fala_ideia') if c.get('sub') == 0 else c.get('fala') if not c.get('sub') else ''))
            v[op['campo']] = ' '.join(f for f in falas if f)
            aplicadas.append(f"{op['campo']}: regenerado das falas finais")
        elif op.get('campo'):
            campo = op['campo']
            if op.get('valor_de'):
                novo = next(c['fala'] for c in v['cenas'] if (c.get('acontecimento') or {}).get('id') == op['valor_de'])
                v[campo] = novo
            else:
                antigo = falas_antigas.get(op.get('trecho_antigo_de'), '')
                if not antigo or antigo not in str(v.get(campo) or ''):
                    raise ValueError(f'edição: trecho antigo não encontrado em {campo}')
                v[campo] = str(v[campo]).replace(antigo, op['trecho_novo'])
            aplicadas.append(f'{campo}: atualizado')
    arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    reg = {'motivo': edicao.get('motivo'), 'autor': edicao.get('autor'), 'aplicadas': aplicadas,
           'quando': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'operacoes': edicao.get('operacoes')}
    (pasta / 'edicao_aplicada.json').write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding='utf-8')
    return reg


if __name__ == '__main__':          # python -m src.v2.checkpoint editar <pasta> <edicao.json>
    import sys
    if len(sys.argv) == 4 and sys.argv[1] == 'editar':
        r = editar(Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text(encoding='utf-8')))
        print('[checkpoint] edição editorial aplicada: ' + '; '.join(r['aplicadas']))
    else:
        raise SystemExit('uso: python -m src.v2.checkpoint editar <pasta> <edicao.json>')
