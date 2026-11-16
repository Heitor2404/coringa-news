"""Memória recuperável do Coringa — separada em duas:

- ENGENHARIA (docs/memoria/erros.json): erros corrigidos, com ID permanente e o teste que detecta a regressão.
- EDITORIAL (docs/memoria/feedback.jsonl + docs/memoria/regras_editoriais.json): avaliação humana por timestamp e
  categoria, e regras derivadas dela, com estado proposto → testado → aprovado | reprovado | obsoleto.

Só regra APROVADA influencia a produção como boa prática (entra no prompt do diretor). Nada aqui treina modelo: é
memória versionada no Git, consultada por código, com prova (teste/feedback) de cada item.

CLI:
  python -m src.v3.memoria feedback <video> <mm:ss> <categoria> "texto" [--gravidade revisao] [--autor heitor] [--direcao direcao.json]
  python -m src.v3.memoria abertos [video]
  python -m src.v3.memoria regra-nova "texto da regra" --tags mecanismo,processo [--origem FB-…]
  python -m src.v3.memoria estado <REG-id> <proposto|testado|aprovado|reprovado|obsoleto> "evidência"
  python -m src.v3.memoria erros [tag]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA = RAIZ / 'docs' / 'memoria'
ERROS = PASTA / 'erros.json'
FEEDBACK = PASTA / 'feedback.jsonl'
REGRAS = PASTA / 'regras_editoriais.json'

CATEGORIAS = ('factual', 'enquadramento', 'movimento', 'anotacao', 'texto', 'ritmo', 'audio', 'transicao', 'midia', 'licenca', 'outro')
GRAVIDADES = ('bloqueio', 'revisao', 'estetica')
ESTADOS = ('proposto', 'testado', 'aprovado', 'reprovado', 'obsoleto')
TRANSICOES = {'proposto': {'testado', 'reprovado', 'obsoleto'}, 'testado': {'aprovado', 'reprovado', 'obsoleto'},
              'aprovado': {'obsoleto', 'reprovado'}, 'reprovado': {'proposto', 'obsoleto'}, 'obsoleto': set()}


# ---------------------------------------------------------------- engenharia
def erros() -> list[dict]:
    return json.loads(ERROS.read_text(encoding='utf-8'))['erros']


def erros_pertinentes(tags: set[str] | list[str]) -> list[dict]:
    """Erros com regra para o diretor e alguma tag em comum com os acontecimentos do vídeo (ou tag '*')."""
    tags = set(tags) | {'*'}
    return [e for e in erros() if e.get('regra_diretor') and e['estado'] in ('corrigido', 'parcial') and tags & set(e.get('tags') or [])]


def problemas_registro() -> list[str]:
    """Integridade da memória de engenharia: campos e testes que existem de verdade (nome da função no arquivo)."""
    obrig = ('id', 'titulo', 'data', 'versao', 'sintoma', 'causa_raiz', 'arquivos', 'correcao', 'testes', 'gravidade', 'estado', 'referencia')
    out, vistos = [], set()
    for e in erros():
        for c in obrig:
            if e.get(c) in (None, '') or (c == 'testes' and e.get('verificavel') and not e.get('testes')):
                out.append(f"{e.get('id')}: campo {c} vazio")
        if e['id'] in vistos:
            out.append(f"{e['id']}: ID repetido")
        vistos.add(e['id'])
        for t in e.get('testes') or []:
            arq, _, nome = t.partition('::')
            p = RAIZ / arq
            if not p.exists():
                out.append(f"{e['id']}: arquivo de teste ausente {arq}")
            elif not re.search(rf'^def {re.escape(nome)}\b', p.read_text(encoding='utf-8'), re.M):
                out.append(f"{e['id']}: teste {nome} não existe em {arq}")
    return out


# ---------------------------------------------------------------- editorial: feedback
def _commit() -> str:
    try:
        return subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, cwd=RAIZ).stdout.strip()
    except Exception:
        return ''


def _segundos(t) -> float:
    if isinstance(t, (int, float)):
        return float(t)
    p = [float(x) for x in str(t).replace(',', '.').split(':')]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0]


def feedbacks(video: str | None = None) -> list[dict]:
    if not FEEDBACK.exists():
        return []
    out = [json.loads(l) for l in FEEDBACK.read_text(encoding='utf-8').splitlines() if l.strip()]
    return [f for f in out if not video or f['video'] == video]


def registrar_feedback(video: str, t, categoria: str, texto: str, gravidade: str = 'revisao', autor: str = 'humano',
                       direcao: Path | None = None, caminho: Path | None = None) -> dict:
    if categoria not in CATEGORIAS:
        raise ValueError(f'categoria {categoria!r}: use uma de {CATEGORIAS}')
    if gravidade not in GRAVIDADES:
        raise ValueError(f'gravidade {gravidade!r}: use uma de {GRAVIDADES}')
    caminho = Path(caminho or FEEDBACK)
    seg = _segundos(t)
    plano = None
    if direcao and Path(direcao).exists():          # liga o timestamp ao plano do storyboard (e à receita usada)
        reg = json.loads(Path(direcao).read_text(encoding='utf-8'))
        lista = reg if isinstance(reg, list) else (reg.get('registro') or [])
        for i, r in enumerate(lista):
            a, b = (r.get('tempo') or [None, None])[:2]
            if a is not None and a <= seg < b:
                plano = {'indice': i, 'evento_id': r.get('evento_id'), 'composicao': r.get('composicao'), 'receita': r.get('receita')}
                break
    n = len(feedbacks()) if caminho == FEEDBACK else (len(caminho.read_text().splitlines()) if caminho.exists() else 0)
    f = {'id': f'FB-{n + 1:04d}', 'video': video, 'commit': _commit(), 't': round(seg, 2), 'categoria': categoria, 'gravidade': gravidade,
         'texto': texto.strip(), 'autor': autor, 'plano': plano, 'causa': None, 'correcao': None, 'regra': None, 'estado': 'aberto',
         'data': time.strftime('%Y-%m-%d %H:%M')}
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(f, ensure_ascii=False) + '\n')
    return f


# ---------------------------------------------------------------- editorial: regras com estado
def regras(caminho: Path | None = None) -> list[dict]:
    c = Path(caminho or REGRAS)
    return json.loads(c.read_text(encoding='utf-8'))['regras'] if c.exists() else []


def _gravar_regras(rs: list[dict], caminho: Path | None = None):
    Path(caminho or REGRAS).write_text(json.dumps({'versao': 1, 'regras': rs}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def nova_regra(texto: str, tags: list[str], origem: str = '', caminho: Path | None = None) -> dict:
    rs = regras(caminho)
    r = {'id': f'REG-{len(rs) + 1:03d}', 'texto': texto.strip(), 'tags': tags, 'estado': 'proposto', 'origem': origem,
         'historico': [{'estado': 'proposto', 'data': time.strftime('%Y-%m-%d'), 'evidencia': origem or 'criada'}]}
    _gravar_regras(rs + [r], caminho)
    return r


def mudar_estado(rid: str, estado: str, evidencia: str, caminho: Path | None = None) -> dict:
    """Muda o estado com evidência obrigatória e transição válida (aprovar exige ter sido testada)."""
    if estado not in ESTADOS:
        raise ValueError(f'estado {estado!r}')
    if not evidencia.strip():
        raise ValueError('mudança de estado sem evidência')
    rs = regras(caminho)
    r = next((x for x in rs if x['id'] == rid), None)
    if not r:
        raise KeyError(rid)
    if estado not in TRANSICOES[r['estado']]:
        raise ValueError(f"{rid}: {r['estado']} → {estado} não é permitido (aprovar exige 'testado' antes)")
    r['estado'] = estado
    r['historico'].append({'estado': estado, 'data': time.strftime('%Y-%m-%d'), 'evidencia': evidencia})
    _gravar_regras(rs, caminho)
    return r


def regras_para_producao(tags: set[str], caminho: Path | None = None) -> list[dict]:
    """O que a produção pode usar AUTOMATICAMENTE: só regras aprovadas e pertinentes."""
    tags = set(tags) | {'*'}
    return [r for r in regras(caminho) if r['estado'] == 'aprovado' and tags & set(r.get('tags') or ['*'])]


def _cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('feedback'); s.add_argument('video'); s.add_argument('t'); s.add_argument('categoria', choices=CATEGORIAS)
    s.add_argument('texto'); s.add_argument('--gravidade', default='revisao', choices=GRAVIDADES); s.add_argument('--autor', default='humano')
    s.add_argument('--direcao')
    s = sub.add_parser('abertos'); s.add_argument('video', nargs='?')
    s = sub.add_parser('regra-nova'); s.add_argument('texto'); s.add_argument('--tags', default='*'); s.add_argument('--origem', default='')
    s = sub.add_parser('estado'); s.add_argument('id'); s.add_argument('estado', choices=ESTADOS); s.add_argument('evidencia')
    s = sub.add_parser('erros'); s.add_argument('tag', nargs='?')
    sub.add_parser('conferir')
    a = ap.parse_args(argv)
    if a.cmd == 'feedback':
        print(json.dumps(registrar_feedback(a.video, a.t, a.categoria, a.texto, a.gravidade, a.autor, Path(a.direcao) if a.direcao else None), ensure_ascii=False))
    elif a.cmd == 'abertos':
        for f in feedbacks(a.video):
            if f['estado'] == 'aberto':
                print(f"{f['id']} {f['video']} {f['t']:>6.1f}s [{f['categoria']}/{f['gravidade']}] {f['texto'][:100]}")
    elif a.cmd == 'regra-nova':
        print(json.dumps(nova_regra(a.texto, a.tags.split(','), a.origem), ensure_ascii=False))
    elif a.cmd == 'estado':
        print(json.dumps(mudar_estado(a.id, a.estado, a.evidencia), ensure_ascii=False))
    elif a.cmd == 'erros':
        for e in (erros_pertinentes({a.tag}) if a.tag else erros()):
            print(f"{e['id']} [{e['estado']}/{e['gravidade']}] {e['titulo']} → {', '.join(e['testes'])}")
    elif a.cmd == 'conferir':
        p = problemas_registro()
        print('\n'.join(p) or 'memória de engenharia íntegra')
        sys.exit(1 if p else 0)


if __name__ == '__main__':
    _cli()
