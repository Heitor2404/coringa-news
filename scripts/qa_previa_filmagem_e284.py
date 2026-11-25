"""Prévia LOCAL (sem visão) das janelas escolhidas pela varredura temporal para necessidades de movimento.

Lê a saída do E247 (replay ou fluxo normal), refaz a exploração dos arquivos locais e grava uma folha por vídeo com
as janelas na ordem em que o motor as enviaria à visão: tempo, movimento residual do referente, câmera, evento.
Diagnóstico para inspeção; não aprova nada.
Uso: python -m scripts.qa_previa_filmagem_e284 <pasta_saida_e247> <pasta_previa>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import amostragem_documental as A


def candidatos_video(r):
    for row in r.get('cobertura', []):
        for rd in row.get('rodadas', []):
            for c in (rd.get('pesquisa') or {}).get('candidatos', []):
                if c.get('tipo') == 'video' and c.get('local_source') and Path(c['local_source']).is_file():
                    yield row.get('necessidade_id'), c


def main(entrada, saida):
    entrada, saida = Path(entrada), Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    r = json.loads((entrada / 'revisao.json').read_text())
    needs = {n['id']: n for n in r['case']['necessidades']}
    vistos = set(); resumo = []
    for nid, c in candidatos_video(r):
        if c['local_source'] in vistos or needs[nid].get('evidencia_visual') != 'movimento':
            continue
        vistos.add(c['local_source'])
        a = c.get('aquisicao') or {}
        m = {'expected_sha256': a.get('sha256') or '0' * 64, 'duration_s': a.get('duration_s'), 'local_source': c['local_source'],
             'width': a.get('width'), 'height': a.get('height'),
             'metadados_texto': '\n'.join(str(c.get(k) or '') for k in ('titulo', 'descricao', 'desc') if c.get(k)),
             'termos_necessidade': [needs[nid]['mostrar'], *needs[nid].get('consultas_en', [])]}
        e = A.explorar(m, E.frame)
        sel = A.selecionar(e, limite=6, priorizar_movimento=True)
        k = len(resumo)
        folha = Image.new('RGB', (3 * 320 + 20, max(1, len(sel)) * 210 + 40), (12, 16, 22))
        d = ImageDraw.Draw(folha)
        d.text((10, 8), f"{nid} | {str(c.get('titulo'))[:90]} | {e.get('varredura_local', {}).get('modo')} "
                        f"planos={len(e.get('varredura_local', {}).get('planos') or [])}", fill=(240, 240, 240))
        for i, w in enumerate(sel):
            for j, f in enumerate((0, .5, .9)):
                try:
                    im = E.frame(c['local_source'], w['inicio_s'] + w['duracao_s'] * f, width=320)
                    im.thumbnail((320, 180)); folha.paste(im, (10 + j * 320, 36 + i * 210))
                except Exception:
                    pass
            mv = w.get('movimento_local') or {}
            d.text((10, 36 + i * 210 + 182), f"#{i} t={w['inicio_s']:.1f}s ref={mv.get('referente')} cam={mv.get('camera')} "
                   f"ev={mv.get('evento')} acomp={mv.get('acompanhada')} deriva={mv.get('deriva')}", fill=(255, 210, 90))
        nome = f'previa-{k + 1}.jpg'
        folha.save(saida / nome, quality=86)
        resumo.append({'necessidade_id': nid, 'titulo': c.get('titulo'), 'fonte': c.get('fonte'), 'sha256': a.get('sha256'),
                       'duracao_s': a.get('duration_s'), 'folha': nome, 'varredura': e.get('varredura_local'),
                       'ordem_janelas_s': [w['inicio_s'] for w in sel],
                       'sinais': [w.get('movimento_local') and {k2: w['movimento_local'][k2] for k2 in
                                  ('referente', 'camera', 'evento', 'acompanhada', 'deriva', 'parado')} for w in sel],
                       'prova_semantica': False})
    (saida / 'previa.json').write_text(json.dumps({'videos': resumo, 'visao_chamadas': 0, 'publicar': False}, ensure_ascii=False, indent=1))
    print('PREVIA_E284', len(resumo), 'videos')


if __name__ == '__main__':
    main(*sys.argv[1:3])
