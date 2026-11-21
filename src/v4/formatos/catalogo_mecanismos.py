"""Catálogo executável de capacidades de mecanismos para FilmeEditorial.

A pauta nunca escolhe o renderer só por nome ou criatividade do prompt.
O storyboard declara ações FÍSICAS a mostrar. Só montar se existir
capacidade real para todas; se não, bloquear e exigir outra direção visual.
NÃO implica suporte universal para qualquer assunto.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacidade:
    id: str
    acoes: tuple[str, ...]
    fases: frozenset[str]
    media_real_obrigatoria: bool = False
    # Perfil temporal cadastrado no próprio renderer; nenhum tempo é
    # descoberto pelo nome do assunto. Para diretor automático, a duração
    # total continua sendo exigida dos eventos/voz, nunca inventada.
    duracao_referencia: float = 0.0
    tempos_referencia: tuple[float, ...] = ()
    rotulos: tuple[str, ...] = ()


CAPACIDADES: dict[str, Capacidade] = {
    'lock_cycle': Capacidade(
        'lock_cycle', ('enter', 'seal', 'valves', 'rise', 'equalize', 'open', 'exit'),
        frozenset({'entrada', 'mecanismo', 'saida'}), True,
        17.5, (0,2.6,4.6,6.1,12.2,14,15.6),
        ('O NAVIO ENTRA', 'PORTÃO FECHA', 'VÁLVULA ABRE',
         'NAVIO SOBE COM A ÁGUA', 'OS NÍVEIS SE IGUALAM',
         'PORTÃO DE SAÍDA ABRE', 'O NAVIO SAI')),
    'lock_cycle_standalone': Capacidade(
        'lock_cycle_standalone', ('enter', 'seal', 'valves', 'rise', 'equalize', 'open', 'exit'),
        frozenset({'entrada', 'mecanismo', 'saida'}), False,
        17.5, (0,2.6,4.6,6.1,12.2,14,15.6),
        ('O NAVIO ENTRA', 'PORTÃO FECHA', 'VÁLVULA ABRE',
         'NAVIO SOBE COM A ÁGUA', 'OS NÍVEIS SE IGUALAM',
         'PORTÃO DE SAÍDA ABRE', 'O NAVIO SAI')),
    'lock_explainer': Capacidade(
        'lock_explainer', ('closed', 'water_enter', 'rise', 'equalize', 'release'),
        frozenset({'mecanismo'}), False,
        10.3, (0,1.2,3.0,7.1,8.8),
        ('CÂMARA FECHADA', 'ÁGUA ENTRA', 'NAVIO SOBE',
         'NÍVEIS IGUAIS', 'PASSAGEM LIBERADA')),
    'optical_projection': Capacidade(
        'optical_projection', ('source', 'reticle', 'projection', 'wafer'),
        frozenset({'origem', 'transformacao', 'resultado'}), False,
        6.9, (0,1.1,2.65,4.65),
        ('FONTE DE LUZ EUV', 'MÁSCARA REFLEXIVA',
         'ESPELHOS PROJETAM PADRÃO', 'RESIST DO WAFER EXPOSTO')),
}
# Mecanismos anteriores permanecem em modo LEGADO, sem escolha automática:
# lock_causal e lock_filling não prometem um ciclo completo.


def decidir(cena: dict) -> tuple[str | None, list[dict]]:
    """Resolver renderer a partir de ações necessárias, não de título/assunto.

    A lista de ações do storyboard NÃO é evidência de que são visíveis;
    render e auditoria do MP4 continuam mandatórios.
    """
    if cena.get('type') != 'mechanism':
        return cena.get('mechanism'), []
    requisitos = cena.get('processo_visual')
    if requisitos is None:
        if cena.get('mechanism') == 'auto':
            return None, [{
                'codigo': 'F-CAPACIDADE-SEM-OBJETIVO',
                'motivo': 'modo automático exige processo_visual com ações/fases'
            }]
        return cena.get('mechanism'), []
    if not isinstance(requisitos, dict):
        return None, [{'codigo':'F-CAPACIDADE-CONTRATO', 'motivo':'processo_visual inválido'}]
    needed = requisitos.get('acoes_necessarias')
    phases = requisitos.get('fases_necessarias')
    if not isinstance(needed, list) or not needed or not all(
        isinstance(x,str) and x.strip() for x in needed
    ) or len(set(needed)) != len(needed) or not isinstance(phases,list) or not phases or not all(
        isinstance(x,str) and x.strip() for x in phases
    ) or len(set(phases)) != len(phases):
        return None, [{'codigo':'F-CAPACIDADE-CONTRATO',
                       'motivo':'ações/fases necessárias devem ser explícitas e únicas'}]
    cues = cena.get('cues') or []
    real = tuple(x.get('action') for x in cues if isinstance(x,dict))
    needed_t = tuple(needed)
    fases = frozenset(phases)
    requested = cena.get('mechanism')
    if requested == 'auto':
        # Auto seleciona somente implementação com ações COMPLETAS, na ordem.
        # Quando existe versão autônoma, nunca simular ponte com vídeo real.
        choices = [c for c in CAPACIDADES.values() if not c.media_real_obrigatoria
                   and c.acoes == real and fases.issubset(c.fases)
                   and set(needed_t).issubset(c.acoes)]
        if len(choices)!=1:
            return None, [{'codigo':'F-CAPACIDADE-INDISPONIVEL',
                           'motivo':'nenhum renderer executa todas as ações e fases pedidas'}]
        requested = choices[0].id
    cap = CAPACIDADES.get(requested)
    if not cap:
        return None, [{'codigo':'F-CAPACIDADE-INDISPONIVEL',
                       'motivo':'renderer não consta do catálogo de ações verificáveis'}]
    if not fases.issubset(cap.fases):
        return None, [{'codigo':'F-CAPACIDADE-INCOMPLETA',
                       'motivo':'esta animação não mostra todas as fases exigidas: '+
                       ', '.join(sorted(fases-cap.fases))}]
    if not set(needed_t).issubset(cap.acoes) or not set(needed_t).issubset(real):
        return None, [{'codigo':'F-CAPACIDADE-INCOMPLETA',
                       'motivo':'animação não executa todas as ações necessárias do roteiro'}]
    if real != cap.acoes:
        return None, [{'codigo':'F-CAPACIDADE-ORDEM',
                       'motivo':'ações do storyboard divergem da máquina de estados implementada'}]
    return requested, []


def relatorio(cenas: list[dict]) -> list[dict]:
    items = []
    for c in cenas:
        if c.get('type') != 'mechanism':
            continue
        renderer, problemas = decidir(c)
        items.append({'cena':c.get('id'), 'renderer':renderer,
                      'acoes_programadas':[x.get('action') for x in c.get('cues') or []],
                      'etapas_exigidas':(c.get('processo_visual') or {}).get('fases_necessarias',[]),
                      'status':'BLOQUEADO' if problemas else 'CONTRATO_ESTRUTURAL_OK',
                      'revisao_mp4':'PENDENTE'})
    return items
