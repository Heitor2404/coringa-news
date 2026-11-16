"""Estado final de um vídeo V3 (Plano Mestre §6). Zero bloqueios NUNCA vira publicável por omissão.

BLOQUEADO                     → defeito objetivo, sem MP4, ou fiscal que bloqueou.
AGUARDANDO_APROVACAO_HUMANA   → MP4 existe e o fiscal não bloqueou (revisões e pendências listadas). Estado máximo automático.
APROVADO_HUMANO               → só por registro humano explícito (quem, data, vídeo).
PUBLICAVEL                    → só a partir de APROVADO_HUMANO e com autorização de publicação separada. Nenhum código
                                desta etapa chega aqui; publicação automática não existe.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

BLOQUEADO = 'BLOQUEADO'
AGUARDANDO = 'AGUARDANDO_APROVACAO_HUMANA'
APROVADO = 'APROVADO_HUMANO'
PUBLICAVEL = 'PUBLICAVEL'
ESTADOS = (BLOQUEADO, AGUARDANDO, APROVADO, PUBLICAVEL)
_HUMANO = re.compile(r'^humano:[^:]+:\d{4}-\d{2}-\d{2}$')


def decidir(res: dict) -> dict:
    """Resultado de pipeline.montar_video → {'estado', 'motivos', 'pendencias'}. Máximo automático: AGUARDANDO."""
    mp4 = res.get('mp4')
    if res.get('bloqueios'):
        return {'estado': BLOQUEADO, 'motivos': list(res['bloqueios']), 'pendencias': []}
    if not mp4 or not Path(mp4).exists() or Path(mp4).stat().st_size == 0:
        return {'estado': BLOQUEADO, 'motivos': ['montagem terminou sem MP4 no disco'], 'pendencias': []}
    pend = list(dict.fromkeys(list(res.get('revisoes') or []) + list(res.get('revisoes_obrigatorias') or [])))
    mm = res.get('revisao_multimodal')
    if not mm:
        pend.append('revisão multimodal não executada (pendente)')
    elif not mm.get('chamadas'):
        pend.append('revisão multimodal sem visão disponível (pendente)')
    if (res.get('custo') or {}).get('pendente'):
        pend.append('custo não fechado: ' + str(res['custo']['pendente']))
    return {'estado': AGUARDANDO, 'motivos': [], 'pendencias': pend}


def aprovar_humano(estado: dict, autor: str, video: str, nota: str = '') -> dict:
    """Transição AGUARDANDO → APROVADO_HUMANO. `autor` no formato humano:<nome>:<AAAA-MM-DD>. Sem isso, recusa."""
    if estado.get('estado') != AGUARDANDO:
        raise ValueError(f"só se aprova o que aguarda aprovação (estado atual: {estado.get('estado')})")
    if not _HUMANO.match(autor or ''):
        raise ValueError('aprovação humana exige autor no formato humano:<nome>:<AAAA-MM-DD>')
    return {**estado, 'estado': APROVADO, 'aprovacao': {'autor': autor, 'video': video, 'nota': nota,
                                                        'registrado': datetime.now().isoformat(timespec='seconds')}}


def liberar_publicacao(estado: dict, autorizacao: str) -> dict:
    """APROVADO_HUMANO → PUBLICAVEL, com autorização de publicação separada (também humana). Não há chamador nesta etapa."""
    if estado.get('estado') != APROVADO or not (estado.get('aprovacao') or {}).get('autor'):
        raise ValueError('publicável só depois de APROVADO_HUMANO registrado')
    if not _HUMANO.match(autorizacao or ''):
        raise ValueError('publicação exige autorização humana no formato humano:<nome>:<AAAA-MM-DD>')
    return {**estado, 'estado': PUBLICAVEL, 'publicacao': {'autorizacao': autorizacao}}


def pode_enviar(estado: dict) -> bool:
    """Único portão para qualquer saída (Telegram, redes). Só PUBLICAVEL passa."""
    return (estado or {}).get('estado') == PUBLICAVEL


def gravar(estado: dict, arq: Path) -> None:
    Path(arq).write_text(json.dumps(estado, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
