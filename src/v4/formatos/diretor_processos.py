"""Ponte segura evento confirmado → storyboard executável do FilmeEditorial.

Entrada: acontecimentos estruturados pelo roteiro/diretor (fato_id, aprendizado,
ações necessárias, fases, duração da fala, identidade textual).
Saída: shot com mecanismo e cues PRONTOS; ninguém precisa escrever tempos,
rótulos de estágio ou nome de componente manualmente.

Não deduz acontecimentos de palavras livres, não cria geometria, não certifica
fontes nem aprova vídeo. Faltam capacidades? BLOQUEAR, não gerar slide falso.
"""
from __future__ import annotations

import math

from src.v4.formatos import catalogo_mecanismos


class FalhaDiretor(ValueError):
    def __init__(self, codigo: str, cena: str, motivo: str):
        super().__init__(f'{codigo} [{cena}]: {motivo}')
        self.codigo = codigo
        self.cena = cena
        self.motivo = motivo

    def bloqueio(self) -> dict:
        return {'codigo': self.codigo, 'cena': self.cena, 'motivo': self.motivo}


def _erro(codigo: str, cena: str, motivo: str):
    raise FalhaDiretor(codigo, cena, motivo)


def _texto(v: object, *, minimo: int = 1, maximo: int = 200) -> bool:
    return isinstance(v, str) and minimo <= len(v.strip()) <= maximo


def _acoes(v: object) -> tuple[str, ...]:
    if not isinstance(v, list) or not v or any(not _texto(x, maximo=45) for x in v):
        return ()
    if len(set(v)) != len(v):
        return ()
    return tuple(v)


def _selecionar(acoes: tuple[str,...], fases: tuple[str,...], eid: str):
    # Para uso autônomo, nunca seleciona a versão que exige clipe real como ponte.
    candidatas = [
        c for c in catalogo_mecanismos.CAPACIDADES.values()
        if not c.media_real_obrigatoria
        and c.acoes == acoes and set(fases).issubset(c.fases)
        and c.duracao_referencia > 0
        and len(c.tempos_referencia) == len(c.acoes) == len(c.rotulos)
    ]
    if len(candidatas) != 1:
        _erro('F-DIRETOR-SEM-CAPACIDADE', eid,
              'nenhum mecanismo comprovadamente implementado cobre todas as ações e fases; '
              'usar mídia real adequada ou cadastrar nova capacidade')
    return candidatas[0]


def expandir(plano: dict) -> dict:
    """Expande somente planos opt-in. Revalida depois no preflight existente."""
    if not isinstance(plano, dict):
        _erro('F-DIRETOR-CONTRATO', '-', 'plano inválido')
    if 'eventos_diretor' not in plano:
        return plano
    if plano.get('shots'):
        _erro('F-DIRETOR-AMBIGUO', '-', 'não misturar cenas manuais e eventos automáticos')
    eventos = plano.get('eventos_diretor')
    if not isinstance(eventos, list) or not eventos:
        _erro('F-DIRETOR-SEM-EVENTO', '-', 'não há acontecimentos estruturados')
    # Sem aprovação humana, esse atalho NUNCA é roteiro de publicação.
    if plano.get('tipo') != 'PROVA_VISUAL_PRIVADA' or plano.get('publicar') is not False:
        _erro('F-DIRETOR-SEM-GATE', '-', 'automação de prova ainda limitada a QA privada')
    if plano.get('media') not in ({}, None):
        _erro('F-DIRETOR-MIDIA', '-', 'não inventar mídia, créditos ou filme real no diretor físico')
    cenas, tempo, ids, fatos = [], 0., set(), set()
    for i, evento in enumerate(eventos):
        eid = str(evento.get('id') or f'evento-{i+1}') if isinstance(evento, dict) else f'evento-{i+1}'
        if not isinstance(evento, dict):
            _erro('F-DIRETOR-CONTRATO', eid, 'acontecimento deve ser objeto')
        d = evento.get('direcao_evento')
        if not isinstance(d, dict) or d.get('intencao') != 'demonstrar_acao':
            _erro('F-DIRETOR-INTENCAO', eid,
                  'somente demonstrar_acao com ações observáveis é suportado neste caminho')
        if not _texto(eid, maximo=64) or eid in ids:
            _erro('F-DIRETOR-ID', eid, 'ID vazio/repetido')
        ids.add(eid)
        fato, aprendizado = d.get('fato_id'), d.get('aprendizado')
        if not _texto(fato, maximo=100) or fato in fatos or not _texto(aprendizado, minimo=12):
            _erro('F-DIRETOR-SEM-FATO', eid, 'fato distinto e aprendizado explícito obrigatórios')
        fatos.add(fato)
        acoes, fases = _acoes(d.get('acoes_necessarias')), _acoes(d.get('fases_necessarias'))
        if not acoes or not fases:
            _erro('F-DIRETOR-SEM-ACOES', eid, 'declarar ações e fases necessárias em ordem')
        c = _selecionar(acoes, fases, eid)
        dur = evento.get('duracao_s')
        if (not isinstance(dur, (int,float)) or isinstance(dur,bool)
                or not math.isfinite(dur) or dur <= 0):
            _erro('F-DIRETOR-TEMPO', eid,
                  'duração medida/dirigida deve estar no evento; não inventar segundos')
        # O timing é propriedade da capacidade, não do nome da pauta.
        fator = dur / c.duracao_referencia
        momentos = [round(t*fator, 4) for t in c.tempos_referencia]
        if not momentos or momentos[0] != 0 or momentos[-1] >= dur:
            _erro('F-DIRETOR-TEMPO', eid, 'tempo insuficiente para início/fim da sequência')
        # Deixar o preflight do compositor verificar também as durações mínimas.
        for campo, tamanho in (('lead',70), ('headline',100), ('subject',250)):
            if not _texto(evento.get(campo), maximo=tamanho):
                _erro('F-DIRETOR-CONTEXTO', eid, f'{campo} do acontecimento ausente/longo')
        # Não permitir sobrescrever campos físicos/temporais por dados de roteiro.
        cues = [
            {'at': pos, 'action': action, 'label': label}
            for action, pos, label in zip(c.acoes, momentos, c.rotulos)
        ]
        cena = {
            'id': eid,
            'start': round(tempo, 4),
            'end': round(tempo+dur, 4),
            'type': 'mechanism',
            'mechanism': 'auto',
            'evidence': 'explainer',
            'lead': evento['lead'].strip(),
            'headline': evento['headline'].strip(),
            'subject': evento['subject'].strip(),
            'cues': cues,
            'estados_esperados': list(c.acoes),
            'processo_visual': {
                'acoes_necessarias': list(acoes),
                'fases_necessarias': list(fases),
            },
            'direcao_evento': {
                'intencao': d['intencao'],
                'fato_id': fato,
                'aprendizado': aprendizado.strip(),
            },
        }
        # Validar agora, e pela segunda vez no preflight central.
        resolved, issues = catalogo_mecanismos.decidir(cena)
        if issues or resolved != c.id:
            _erro('F-DIRETOR-IMPLEMENTACAO', eid,
                  'diretor e catálogo de render não concordam nas ações')
        cenas.append(cena)
        tempo = round(tempo+dur, 4)
    if plano.get('duracao') is not None:
        declared = plano['duracao']
        if not isinstance(declared,(float,int)) or isinstance(declared,bool) or not math.isfinite(declared) or abs(declared-tempo)>.05:
            _erro('F-DIRETOR-DURACAO', '-', 'duração do episódio diverge da soma das ações')
    return {
        **{k:v for k,v in plano.items() if k!='eventos_diretor'},
        'duracao': tempo,
        'media': {},
        'shots': cenas,
        'diretor_automatico': {
            'origem': 'EVENTOS_ESTRUTURADOS',
            'autonomia': 'MONTAGEM_DE_CAPACIDADES_JA_EXISTENTES',
            'fatos_verificados_externamente': False,
            'revisao_visual': 'PENDENTE',
        },
    }
