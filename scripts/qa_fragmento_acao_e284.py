"""E284: prova privada curta da seleção de filmagem de ação (sem narração), somente se a cobertura real permitir."""
import json
import math
import sys
from pathlib import Path

from scripts.qa_documentario_curado_e218 import PUBLIC
from src.v4.formatos import filme_editorial as F, ponte_cobertura_filme as P


def main(root):
    root = Path(root)
    r = json.loads((root / 'revisao.json').read_text())
    if r.get('publish') is not False:
        raise SystemExit('E284-PRIVADO')
    chosen, gate = P.preparar_cobertura(r, r['case'], minimo_s=1.4)
    resumo = {'publicar': False, 'tipo': 'PROVA_CURTA_SELECAO_FILMAGEM_SEM_NARRACAO', 'visao': r['visao_chamadas_logicas'],
              'reusos': r['reusos_analises'], 'estados': [(x['necessidade_id'], x['estado']) for x in r['cobertura']], 'gate': gate}
    print('E284 COBERTURA', resumo['estados'], resumo['visao'])
    if not gate['pronto_para_tts']:
        (root / 'prova.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=1))
        raise SystemExit(1)
    ends = []; end = 0
    for ch in r['case']['chapters']:
        end += sum(math.floor(chosen[i]['cap'] * 30 + 1e-6) for i in ch['needs']); ends.append(end)
    plan = P.plano(r['case'], chosen, ends)
    F.preparar(plan, root / 'fragmento', PUBLIC, fragmento_misto=True)
    resumo['duracao_s'] = plan['duracao']
    resumo['janelas'] = {i: {'fonte_s': (x.get('window') or {}).get('source_in_seconds'), 'cap_s': x['cap'],
                             'sha256': ((x.get('candidate') or {}).get('aquisicao') or {}).get('sha256'),
                             'titulo': (x.get('candidate') or {}).get('titulo'), 'pagina': (x.get('candidate') or {}).get('pagina')}
                         for i, x in chosen.items()}
    (root / 'prova.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main(sys.argv[1])
