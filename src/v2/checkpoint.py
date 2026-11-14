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
