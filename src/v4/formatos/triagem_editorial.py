"""Portão de PRÉ-PRODUÇÃO do ATLAS: contrato fala → prova, antes de TTS/render.

Não tenta adivinhar se a cena é bonita, nem usa métricas de câmera como qualidade.
Exige que o storyboard declare pergunta, referente, aprendizado e IDs de provas
que realmente existem no plano. Uma visão independente e aprovação humana ainda
são necessárias: este teste impede regressões óbvias, não certifica estética.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

VERBOS = {'LOCALIZAR', 'MOSTRAR', 'DEMONSTRAR', 'CONECTAR', 'COMPARAR', 'REVELAR'}
MIDIAS = {'atlas.provaVisual', 'dossie.documentCard', 'editorial.peopleCard'}
FISICOS = MIDIAS | {'registro.video'}
FLUXOS = {'editorial.flowConnections'}
COMPARACOES = {'editorial.comparison', 'editorial.hierarchy', 'editorial.timeline'}
NAO_PROVA = {'editorial.titleOrPayoff', 'editorial.cta', 'editorial.statCard'}


def avaliar(plano: dict, catalogo: dict | None = None) -> dict:
    """Checagem fail-closed do contrato novo. Não transforma texto declarado em prova."""
    erros: list[dict] = []

    def falha(codigo: str, beat: str, motivo: str):
        erros.append({'codigo': codigo, 'beat': beat, 'motivo': motivo})

    if plano.get('formato') != 'atlas':
        return {'pronto': True, 'bloqueios': [], 'nota': 'aplica-se somente a ATLAS'}
    fatos = {f.get('id'): f for f in (plano.get('narracao') or {}).get('fatos') or []}
    beats = plano.get('beats') or []
    if not beats:
        falha('E-PLANO-VAZIO', '-', 'não há storyboard')
    if catalogo is not None:
        biblioteca = {it.get('id'): it for it in catalogo.get('itens') or []}
    else:
        biblioteca = None
    clipes = plano.get('clipes') or []
    por_id = {c.get('id'): c for c in clipes if c.get('id')}
    mapa_declarado = bool((plano.get('destaques') or []) or (plano.get('rotulos') or [])
                          or (plano.get('rotas') or []))
    for beat in beats:
        bid = str(beat.get('id') or '?')
        direcao = beat.get('direcao_visual')
        if not isinstance(direcao, dict):
            falha('E-SEM-CONTRATO-VISUAL', bid,
                  'faltam pergunta visual, referente, aprendizado e provas verificáveis')
            continue
        verbo = str(direcao.get('verbo') or '').upper()
        if verbo not in VERBOS:
            falha('E-VERBO-VISUAL', bid, f'verbo inválido ou ausente: {verbo!r}')
        for campo in ('pergunta', 'referente', 'aprendizado'):
            if len(str(direcao.get(campo) or '').strip()) < 12:
                falha('E-DIRECAO-INCOMPLETA', bid, f'{campo} ausente ou sem especificidade')
        if not beat.get('fatos') or any(
            fid not in fatos or not fatos[fid].get('fontes') for fid in beat.get('fatos') or []
        ):
            falha('E-FATO-SEM-FONTE', bid, 'beat sem evidência factual rastreável')
        provas = direcao.get('provas')
        if not isinstance(provas, list) or not provas or not all(isinstance(x, str) and x.strip() for x in provas):
            falha('E-PROVA-NAO-DECLARADA', bid, 'IDs de evidências obrigatórios, não basta descrever "prova"')
            continue
        layers = beat.get('camadas') or []
        elementos = {L.get('id'): L for L in layers if L.get('id')}
        refs = {**por_id, **elementos}
        validas = []
        for eid in provas:
            if eid == 'mapa' and verbo == 'LOCALIZAR' and beat.get('roi') and (
                mapa_declarado or any(L.get('componente') == 'atlas.geoPin' for L in layers)
            ):
                validas.append('mapa')
                continue
            el = refs.get(eid)
            if el is None:
                falha('E-PROVA-INEXISTENTE', bid, f'{eid}: prova não existe no storyboard')
                continue
            comp = el.get('componente')
            if comp in NAO_PROVA:
                falha('E-TEXTO-NAO-E-PROVA', bid, f'{eid}: título/cartão não demonstra objeto nem acontecimento')
                continue
            if comp in FISICOS:
                asset = (el.get('p') or el.get('params') or {}).get('asset')
                if not asset:
                    falha('E-MIDIA-SEM-ASSET', bid, f'{eid}: mídia sem asset identificável')
                    continue
                if biblioteca is not None:
                    it = biblioteca.get(asset) or {}
                    if not (it.get('sha256_origem') and it.get('licenca')
                            and (it.get('prova') or {}).get('midia_corresponde') is True):
                        falha('E-MIDIA-NAO-COMPROVADA', bid, f'{asset}: sem prova de origem/licença/mídia')
                        continue
            validas.append(comp)
        if not validas:
            falha('E-SEM-PROVA-REAL', bid, 'nenhuma prova declarada foi verificada')
            continue
        if verbo == 'MOSTRAR' and not any(x in FISICOS for x in validas):
            falha('E-OBJETO-SEM-IMAGEM', bid, 'MOSTRAR objeto exige mídia real comprovada, não mapa/card')
        if verbo == 'DEMONSTRAR' and not any(x == 'registro.video' or x.startswith('mecanismo.') for x in validas):
            falha('E-ACAO-SEM-MECANISMO', bid, 'DEMONSTRAR ação exige registro de ação ou mecanismo, não etiqueta')
        if verbo == 'CONECTAR' and not any(x in FLUXOS for x in validas):
            falha('E-RELACAO-SEM-FLUXO', bid, 'dependência exige fluxo causal, não etiquetas de países')
        if verbo == 'COMPARAR' and not any(x in COMPARACOES for x in validas):
            falha('E-COMPARACAO-SEM-OBJETO', bid, 'comparação precisa de composição com objetos/dados contrapostos')
        if verbo == 'REVELAR' and all(x == 'mapa' for x in validas):
            falha('E-REVELACAO-DECORATIVA', bid, 'revelação precisa mostrar consequência, não fundo geográfico')
    return {'pronto': not erros, 'bloqueios': erros,
            'beats': len(beats), 'regra': 'contrato_semantico_antes_de_voz_v1',
            'revisao_multimodal': 'OBRIGATORIA_EM_ETAPA_SEPARADA'}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print('Uso: python -m src.v4.formatos.triagem_editorial <plano.json>', file=sys.stderr)
        return 2
    plano = json.loads(Path(argv[0]).read_text(encoding='utf-8'))
    bib = Path(__file__).resolve().parents[2] / 'biblioteca_comprovada.json'
    # Catálogo de formatos fica em src/v4/biblioteca_comprovada.json.
    bib = Path(__file__).resolve().parents[1] / 'biblioteca_comprovada.json'
    catalogo = json.loads(bib.read_text(encoding='utf-8')) if bib.exists() else None
    res = avaliar(plano, catalogo)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res['pronto'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
