"""V2.4 — PRÉVIA VISUAL antes da narração (auditoria do MP4 43730252500, nota 2/10).

O preparo decide QUAL composição representa cada acontecimento crítico; esta etapa renderiza essa composição, com os
dados do contrato, no MESMO renderizador do vídeo (palco), ANTES de gastar voz e render. Por acontecimento crítico
representado por composição:

  · quadros no início / meio / fim da cena (1,0 s · 3,5 s · 6,6 s de uma cena de 7 s) → galeria auditável;
  · erros de JavaScript e avisos do renderizador (dado que a composição não entendeu) → bloqueio;
  · texto fora da área segura / sobreposto / cortado de forma persistente (palco.medir) → bloqueio;
  · área de conteúdo vazia (tela uniforme fora do título) → bloqueio;
  · início igual ao fim (nada muda na tela: o mecanismo não é mostrado) → bloqueio — só para composições que
    DEMONSTRAM (contrato.DEMONSTRATIVAS), que prometem mudança de estado.

Quando a composição não consegue representar o acontecimento, o resultado é uma LIMITAÇÃO explícita (bloqueio no
preparo, com o motivo e os quadros), nunca uma troca silenciosa por foto. Não usa IA nem serviço pago.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.v2 import contrato

DUR = 7.0
INSTANTES = (1.0, 3.5, 6.6)
AREA = (90, 520, 990, 1100)          # região do conteúdo (abaixo do título, acima da faixa de legenda)
DIFERENCA_MIN = 2.0                  # média absoluta (0–255) entre início e fim abaixo disso = nada mudou
VAZIO_STD = 5.0
OCUPACAO_MIN = 0.02                 # < 2% da área útil desenhada = objeto pequeno demais
FRACAO_MIN = 0.004                   # ≥ 0,4% da área mudou de fato (objeto pequeno em movimento conta)


def _medidas(arqs: list[Path]) -> dict:
    import numpy as np
    from PIL import Image
    g = [np.asarray(Image.open(a).convert('L').crop(AREA).resize((225, 145)), float) for a in arqs]
    frac = lambda a, b: round(float((abs(a - b) > 25).mean()), 4)
    return {'std': [round(float(x.std()), 2) for x in g],
            'dif_ini_fim': round(float(abs(g[0] - g[-1]).mean()), 2),
            'dif_ini_meio': round(float(abs(g[0] - g[1]).mean()), 2),
            # objeto pequeno que se move (planeta, seta) muda pouco a MÉDIA; a fração de pixels que mudou de verdade pega
            'frac_mudou': max(frac(g[0], g[1]), frac(g[0], g[-1]), frac(g[1], g[-1])),
            # quanto da área útil o desenho ocupa no fim (objeto minúsculo no meio da tela não explica nada)
            'ocupacao': round(float((abs(g[-1] - __import__('numpy').median(g[-1])) > 30).mean()), 4)}


def renderizar(comp: str, params: dict, pasta: Path, nome: str, fundo: dict | None = None) -> dict:
    """Renderiza uma composição sozinha e devolve quadros, problemas de geometria e erros do renderizador."""
    from src.v2 import fiscal_v2, palco
    pasta.mkdir(parents=True, exist_ok=True)
    d = {'duration': DUR, 'meta': {'titulo': 'prévia', 'marca': '@coringa.explica'},
         'scenes': [{'comp': comp, 'start': 0, 'end': DUR, 'params': params, 'fala': '', **({'fundo': fundo} if fundo else {})}], 'captions': []}
    quadros = []
    with palco.abrir(palco.preparar(d), pasta / f'_trab_{nome}') as pg:
        for t in INSTANTES:
            a = pasta / f'{nome}_{t:.1f}s.jpg'
            palco.capturar(pg, t, a, 82)
            quadros.append(a)
        geo = palco.medir(pg, DUR, .25)
        erros = list(pg.erros) + list(pg.evaluate('V2.avisos') or [])
    graves = [f"{g['tipo']}: {g['txt']}" for g in fiscal_v2._persistentes([g for g in geo if g.get('grave')])]
    return {'quadros': quadros, 'graves': graves, 'erros': [str(e)[:160] for e in erros], 'medidas': _medidas(quadros)}


def problemas(comp: str, r: dict) -> list[str]:
    p = []
    if r['erros']:
        p.append('renderizador: ' + '; '.join(r['erros'][:2]))
    if r['graves']:
        p.append('texto fora da área/sobreposto: ' + '; '.join(r['graves'][:3]))
    if max(r['medidas']['std']) < VAZIO_STD:
        p.append('área de conteúdo vazia nos três quadros')
    md = r['medidas']
    if contrato.demonstra(comp) and max(md['dif_ini_fim'], md.get('dif_ini_meio', 0)) < DIFERENCA_MIN and md.get('frac_mudou', 0) < FRACAO_MIN:
        p.append(f"início e fim iguais (diferença {md['dif_ini_fim']}, {md.get('frac_mudou', 0) * 100:.2f}% dos pixels): a mudança de estado não aparece")
    if contrato.demonstra(comp) and md.get('ocupacao', 1) < OCUPACAO_MIN:
        p.append(f"desenho ocupa só {md['ocupacao'] * 100:.1f}% da área útil: objetos pequenos demais para o vertical")
    if comp == 'mecanismo.estados':
        p += [f'esquema: {x}' for x in contrato.esquema_problemas((r.get('params') or {}).get('esquema'))]
    return p


def validar(v: dict, pasta: Path) -> dict:
    """Prévia de todos os acontecimentos CRÍTICOS que o preparo resolveu por composição. Devolve o relatório com os
    bloqueios (mesmo formato do preparo) e grava a galeria (folha.jpg) e o relatório (previa.json) em `pasta`."""
    rel = {'eventos': [], 'bloqueios': []}
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)       # sem composição crítica também grava o relatório (vazio)
    vistos = set()
    for i, c in enumerate(v.get('cenas') or []):
        ac = c.get('acontecimento') if isinstance(c.get('acontecimento'), dict) else None
        if not ac or not ac.get('id') or ac['id'] in vistos or not contrato.critico(ac):
            continue
        rep = ac.get('representacao') if isinstance(ac.get('representacao'), dict) else {}
        if rep.get('modo') != 'composicao' or not rep.get('comp'):
            continue
        vistos.add(ac['id'])
        params = dict(ac.get('dados') or {})
        params.setdefault('titulo', str(ac.get('mostrar') or ac.get('acao') or '')[:36])
        try:
            r = renderizar(rep['comp'], params, pasta, ac['id'])
        except Exception as e:                      # sem navegador/erro de render: a prévia não pode atestar → bloqueio
            r = {'quadros': [], 'graves': [], 'erros': [f'prévia não renderizou: {str(e)[:120]}'], 'medidas': {'std': [0], 'dif_ini_fim': 0, 'dif_ini_meio': 0, 'frac_mudou': 0}}
        r['params'] = params
        pr = problemas(rep['comp'], r)
        rel['eventos'].append({'evento': ac['id'], 'comp': rep['comp'], 'quadros': [Path(q).name for q in r['quadros']],
                               'medidas': r['medidas'], 'problemas': pr, 'ok': not pr})
        if pr:
            rel['bloqueios'].append({'evento': ac['id'], 'cenas': [i], 'tipo': ac['tipo'], 'mostrar': ac.get('mostrar'),
                                     'faltam': [f"prévia visual de {rep['comp']}: {x}" for x in pr]})
    _folha(pasta, rel['eventos'])
    (pasta / 'previa.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding='utf-8')
    return rel


def _folha(pasta: Path, eventos: list[dict]) -> Path | None:
    from PIL import Image, ImageDraw
    linhas = [e for e in eventos if e['quadros']]
    if not linhas:
        return None
    W, H = 360, 640
    f = Image.new('RGB', (W * 3, H * len(linhas)), (8, 12, 18))
    dr = ImageDraw.Draw(f)
    for y, e in enumerate(linhas):
        for x, q in enumerate(e['quadros']):
            f.paste(Image.open(pasta / q).resize((W, H)), (x * W, y * H))
        dr.text((8, y * H + 6), f"{e['evento']} {e['comp']} {'OK' if e['ok'] else 'BLOQUEIO'}", fill=(255, 220, 0) if e['ok'] else (255, 80, 60))
    arq = pasta / 'folha.jpg'
    f.save(arq, quality=80)
    return arq


def resumo(rel: dict) -> str:
    return f"prévia visual: {len(rel['eventos'])} composição(ões) crítica(s) · {len(rel['bloqueios'])} bloqueio(s)" + ''.join(
        f"\n  {e['evento']} {e['comp']}: {'ok' if e['ok'] else ' | '.join(e['problemas'])}" for e in rel['eventos'])
