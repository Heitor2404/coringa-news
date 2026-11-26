"""Contratos visuais entre ATLAS e FILME: mesmos critérios, sem fingir que metadados são imagens.

Este módulo NÃO julga a qualidade estética automaticamente. Separa:
  1. prova declarada no plano;
  2. evidência efetivamente inspecionada (quadro + veredito);
  3. aprovação HUMANA, sempre externa.

O revisor de ATLAS e o novo revisor de FILME devem usar a mesma rubrica.
Nunca converter "pixels mudaram", labels ou hashes em "acontecimento demonstrado".
"""
from __future__ import annotations

from collections.abc import Mapping

VERBOS_COM_ACAO = frozenset(('DEMONSTRAR', 'CONECTAR', 'COMPARAR', 'REVELAR'))
VERBOS = frozenset(('LOCALIZAR', 'MOSTRAR', 'DEMONSTRAR', 'CONECTAR', 'COMPARAR', 'REVELAR'))
CRITERIOS_BASE = (
    'referente_visivel', 'aprendizado_demonstrado',
    'enquadramento_adequado', 'imagem_celular_legivel',
)


def criterios(verbo: str, mapa: bool = False) -> tuple[str, ...]:
    """Usa requisitos por intenção, NÃO por nome do tema ou compositor."""
    exigidos = list(CRITERIOS_BASE)
    if mapa:
        exigidos.append('mapa_informativo')
    if verbo in VERBOS_COM_ACAO:
        exigidos.append('acao_ou_relacao_visivel')
    return tuple(exigidos)


def julgar_inspecao(verbo: str, mapa: bool, resposta: object) -> list[str]:
    """Retorna falhas iguais nos dois motores; só aceita booleano True explícito."""
    if not isinstance(resposta, Mapping):
        return ['SEM-REVISAO: resposta de visão não é um objeto']
    problemas = [
        f'V-{campo}: modelo não confirmou'
        for campo in criterios(verbo, mapa)
        if resposta.get(campo) is not True
    ]
    if problemas:
        extras = resposta.get('problemas')
        if isinstance(extras, list):
            problemas += [str(p)[:250] for p in extras[:3]]
    return problemas


def extrair(plano: dict) -> list[dict]:
    """Converte storyboard de cada motor em compromissos verificáveis, sem inventar provas."""
    formato = plano.get('formato')
    contratos = []
    if formato == 'atlas':
        from src.v4.formatos import plano as p_atlas
        for b in plano.get('beats') or []:
            d = b.get('direcao_visual') or {}
            camadas = {c.get('id'): c for c in b.get('camadas') or [] if c.get('id')}
            clips = {c.get('id'): c for c in plano.get('clipes') or [] if c.get('id')}
            refs = {**clips, **camadas}
            declaradas = d.get('provas') if isinstance(d.get('provas'), list) else []
            suportes = [refs[e].get('componente') or 'registro.video'
                        for e in declaradas if isinstance(e, str) and e in refs]
            if 'mapa' in declaradas and b.get('roi') and d.get('verbo') == 'LOCALIZAR':
                suportes.append('mapa')
            contratos.append({
                'id': b.get('id'), 'formato': formato,
                'verbo': str(d.get('verbo') or '').upper(),
                'pergunta': d.get('pergunta') or '',
                'referente': d.get('referente') or '',
                'aprendizado': d.get('aprendizado') or '',
                'provas_declaradas': declaradas,
                'provas_resolvidas': len(suportes),
                'suportes': suportes,
                'acoes_programadas': [],
                'acoes_esperadas': d.get('etapas_esperadas') or [],
                'substituicao': d.get('substituicao'),
                'mapa': (p_atlas.COMP.get(b.get('composicao') or '', {}).get('palco')
                         == 'mapa'),
            })
    elif formato == 'filme_editorial':
        for s in plano.get('shots') or []:
            tipo = s.get('type')
            verbo = {'comparison': 'COMPARAR', 'mechanism': 'DEMONSTRAR',
                     'photo': 'MOSTRAR', 'video': 'MOSTRAR',
                     'atlas_map': 'LOCALIZAR','animation_clip':'DEMONSTRAR'}.get(tipo, '')
            evid = []
            if tipo == 'mechanism':
                if s.get('mechanism') and s.get('evidence') == 'explainer':
                    evid.append('mecanismo.ilustrativo')
            elif tipo == 'animation_clip':
                from . import politica_animacao as PA
                if plano.get('tipo')=='PROVA_VISUAL_PRIVADA' and plano.get('publicar') is False and PA.avaliar([s],privado=True)['permitido']:
                    evid.append('animation_clip:'+s['animation_proof']['sha256'])
            elif tipo == 'scene_graph':
                # E202: cena declarativa compilada a partir de fatos com fonte; prova = ids de fatos citados
                # pelo diretor e checados no compilador (não é prova de imagem nem de exatidão)
                fatos = (s.get('direcao_visual') or {}).get('provas') or []
                sg = s.get('scene_graph') or {}
                if s.get('evidence') == 'explainer' and fatos and sg.get('sources'):
                    evid += [f'cena_declarativa.fato:{f}' for f in fatos]
            else:
                for field in ('asset', 'assetB'):
                    if s.get(field) in (plano.get('media') or {}):
                        evid.append(s[field])
            acoes = [c.get('action') for c in s.get('cues') or [] if c.get('action')]
            contratos.append({
                'id': s.get('id'), 'formato': formato,
                'verbo': (s.get('direcao_visual') or {}).get('verbo', verbo),
                'pergunta': s.get('headline') or '',
                'referente': s.get('subject') or '',
                'aprendizado': s.get('headline') or '',
                'provas_declaradas': ([s.get('mechanism')] if tipo == 'mechanism'
                                     else list((s.get('direcao_visual') or {}).get('provas') or []) if tipo == 'scene_graph'
                                     else [s.get(k) for k in ('asset', 'assetB') if s.get(k)]),
                'provas_resolvidas': len(evid),
                'suportes': evid,
                'acoes_programadas': acoes,
                'acoes_esperadas': s.get('estados_esperados') or [],
                'substituicao': s.get('substituicao'),
                'mapa': tipo == 'atlas_map',
                'natureza_evidencia': s.get('evidence'),
            })
    else:
        raise ValueError(f'formato visual não suportado: {formato}')
    return contratos


def auditar(plano: dict, julgamentos: dict | None = None) -> dict:
    """Relatório de 3 camadas. Sem quadros + visão, nunca reportar resultado "aprovado"."""
    contratos = extrair(plano)
    julgamentos = julgamentos or {}
    falhas = []
    inspecionados = 0
    confirmados = 0
    for c in contratos:
        ident = c.get('id') or '?'
        if c['verbo'] not in VERBOS:
            falhas.append({'id': ident, 'codigo': 'U-SEM-INTENCAO', 'motivo': 'intenção visual ausente'})
        if not c['referente'] or not c['aprendizado']:
            falhas.append({'id': ident, 'codigo': 'U-SEM-REFERENTE', 'motivo': 'referente/aprendizado não definido'})
        if not c['provas_resolvidas']:
            falhas.append({'id': ident, 'codigo': 'U-SEM-PROVA', 'motivo': 'nenhum suporte declarado resolvido'})
        # Evento esperado tem de aparecer em ordem no PLANO; nenhuma ação
        # visual é confirmada até a revisão dos frames reais. Sem lista
        # esperada => cobertura NÃO MENSURADA (não criar meta retroativa).
        esperado = c['acoes_esperadas']
        observado = c['acoes_programadas']
        if esperado:
            valido = (isinstance(esperado, list) and all(isinstance(x, str) and x for x in esperado)
                      and len(set(esperado)) == len(esperado)
                      and observado == esperado)
            if not valido:
                falhas.append({'id': ident, 'codigo': 'U-COBERTURA-ACAO',
                               'motivo': 'ações programadas não cobrem, em ordem, as ações esperadas'})

        # Regras de fallback são uma camada do MESMO contrato, não exceções
        # por guerra/país/tema. Sem marcação explícita, NÃO supor evento de origem.
        subst = c.get('substituicao')
        if isinstance(subst, dict):
            from src.v4.formatos.qa_video_fontes import decidir_uso
            checagem = decidir_uso(
                acontecimento=str(subst.get('acontecimento') or ''),
                evento_da_midia=str(subst.get('evento_da_midia') or ''),
                uso=str(subst.get('uso') or ''),
                cena_especifica=subst.get('cena_especifica') is not False,
                rotulo=str(subst.get('rotulo') or ''),
                origem_verificada=subst.get('origem_verificada') is True,
                licenca_verificada=subst.get('licenca_verificada') is True,
                representacao=subst.get('representacao'),
            )
            if not checagem['permitido']:
                falhas.append({'id': ident, 'codigo': checagem['codigo'],
                               'motivo': 'substituição de mídia recusada pelo contrato comum'})
        if ident in julgamentos:
            inspecionados += 1
            erros_visao = julgar_inspecao(c['verbo'], c['mapa'], julgamentos[ident])
            if erros_visao:
                falhas += [{'id': ident, 'codigo': 'U-INSPECAO-VISUAL',
                            'motivo': e} for e in erros_visao]
            else:
                confirmados += 1
    total = len(contratos)
    acoes_com_criterio = sum(bool(c['acoes_esperadas']) for c in contratos)
    acoes_programadas = sum(bool(c['acoes_esperadas'])
                           and c['acoes_esperadas'] == c['acoes_programadas'] for c in contratos)
    estruturais = [f for f in falhas if f['codigo'] != 'U-INSPECAO-VISUAL']
    return {
        'total_compromissos': total,
        'provas_resolvidas_no_plano': sum(bool(c['provas_resolvidas']) for c in contratos),
        'acoes_com_expectativa_declarada': acoes_com_criterio,
        'acoes_programadas_em_ordem': acoes_programadas,
        'acoes_realmente_vistas': 'NAO_MENSURADO_SEM_FRAMES',
        'inspecoes_com_veredito': inspecionados,
        'inspecoes_sem_reprovacao': confirmados,
        'falhas': falhas,
        'estrutura_declarada_ok': bool(total) and not estruturais,
        'prova_visual': ('NAO_INSPECIONADA' if inspecionados == 0
                         else 'PARCIAL' if inspecionados < total
                         else 'INSPECIONADA_COM_FALHAS' if falhas
                         else 'INSPECIONADA_POR_MODELO_NAO_HOMOLOGADA'),
        'aprovacao_humana': 'PENDENTE',
        'nota': 'Declarações e visão automatizada NÃO são aprovação estética; verificar material real.',
    }
