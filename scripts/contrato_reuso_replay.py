"""Contrato congelado do replay privado sem IA (risco 3.3 da auditoria independente).

`reusos_analises >= 6` deixava passar a perda de 3 das 9 análises comprovadas. O contrato verifica, para a mesma coleção
congelada de checkpoints e as mesmas necessidades: o multiconjunto EXATO de revisões reaproveitadas (identidade, não só
quantidade), os estados e a revisão selecionada da cobertura, zero visão, zero HTTP/buscas de origem e a preservação
das respostas inválidas históricas no catálogo restaurado. Mudança legítima exige atualizar o contrato com justificativa.

Uso:
  python -m scripts.contrato_reuso_replay extrair <revisao.json> [biblioteca.sqlite3] > atual.json
  python -m scripts.contrato_reuso_replay conferir <revisao.json> <contrato.json> [biblioteca.sqlite3]
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path


def _ids_reutilizados_por_varredura(obj, out):
    """IDs presentes na saída (independe do campo reusos_ids; serve para saídas antigas)."""
    if isinstance(obj, dict):
        if obj.get('provedor') == 'reuso_privado' and isinstance(obj.get('revisao_id'), str):
            out.add(obj['revisao_id'])
        if obj.get('revisao_reutilizada') is True and isinstance((obj.get('revisao') or {}).get('revisao_id'), str):
            out.add(obj['revisao']['revisao_id'])
        for v in obj.values():
            _ids_reutilizados_por_varredura(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _ids_reutilizados_por_varredura(v, out)
    return out


def _invalidas(db):
    if not db or not Path(db).is_file():
        return None
    n = 0
    con = sqlite3.connect(db)
    try:
        for (conteudo,) in con.execute("SELECT conteudo FROM analises WHERE tipo LIKE 'documental:%'"):
            try:
                d = json.loads(conteudo)
            except ValueError:
                continue
            n += sum(1 for j in d.get('janelas', []) if isinstance(j, dict) and 'resposta_invalida' in j)
    except sqlite3.Error:
        return None
    finally:
        con.close()
    return n


def extrair(revisao, db=None):
    r = json.loads(Path(revisao).read_text(encoding='utf8'))
    cob = r.get('cobertura') or []
    consumo = (r.get('cobertura_documentario') or {}).get('consumo') or {}
    return {
        'reusos_analises': r.get('reusos_analises'),
        'reusos_ids': sorted(Counter(r.get('reusos_ids') or []).items()),
        'reusos_ids_unicos': sorted(_ids_reutilizados_por_varredura(r, set())),
        'estados': [x.get('estado') for x in cob],
        'selecionados': [x.get('selecionado') for x in cob],
        'visao_chamadas_logicas': r.get('visao_chamadas_logicas'),
        'telemetria_visao': len(r.get('telemetria_visao') or []),
        'http': consumo.get('http'), 'buscas': consumo.get('buscas'),
        'rede_aquisicao_http': (r.get('rede_aquisicao') or {}).get('http'),
        'respostas_invalidas_preservadas': _invalidas(db),
        'publish': r.get('publish'),
    }


def conferir(atual, contrato, modo='replay'):
    """Lista de violações (vazia = aprovado). No fluxo normal com visão zero buscas de METADADOS são legítimas;
    downloads de origem e visão continuam proibidos."""
    erros = []
    for campo in ('reusos_analises', 'reusos_ids', 'reusos_ids_unicos', 'estados', 'selecionados'):
        if json.dumps(atual.get(campo), sort_keys=True) != json.dumps(contrato.get(campo), sort_keys=True):
            erros.append(f'{campo}: esperado {contrato.get(campo)!r}, obtido {atual.get(campo)!r}')
    if atual.get('visao_chamadas_logicas') != 0 or atual.get('telemetria_visao') != 0:
        erros.append('visão nova no replay')
    for campo in (('http', 'buscas') if modo == 'replay' else ('http',)):
        if atual.get(campo) not in (0, None):
            erros.append(f'{campo} de origem no replay: {atual.get(campo)}')
    if atual.get('rede_aquisicao_http') not in (0, None):
        erros.append(f'downloads de origem: {atual.get("rede_aquisicao_http")}')
    if atual.get('publish') is not False:
        erros.append('publish deve ser False')
    minimo = contrato.get('respostas_invalidas_preservadas')
    if minimo is not None and (atual.get('respostas_invalidas_preservadas') or 0) < minimo:
        erros.append(f'respostas inválidas perdidas: {atual.get("respostas_invalidas_preservadas")} < {minimo}')
    return erros


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ['extrair'] and len(a) in (2, 3):
        print(json.dumps(extrair(a[1], a[2] if len(a) == 3 else None), ensure_ascii=False, indent=1))
        return 0
    modo = 'replay'
    if '--normal' in a:
        a.remove('--normal'); modo = 'normal'
    if a[:1] == ['conferir'] and len(a) in (3, 4):
        contrato = json.loads(Path(a[2]).read_text(encoding='utf8'))
        atual = extrair(a[1], a[3] if len(a) == 4 else None)
        erros = conferir(atual, contrato, modo)
        print(json.dumps({'estado': 'APROVADA' if not erros else 'REPROVADA', 'erros': erros,
                          'reusos': atual['reusos_analises']}, ensure_ascii=False))
        return 0 if not erros else 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
