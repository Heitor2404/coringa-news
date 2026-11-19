"""Portão editorial dos FORMATOS, reaproveitando a máquina de estados da V3.

Executar DEPOIS da prévia privada, antes de concluir o workflow. Não é aprovação
humana nem mecanismo de publicação. Nunca transforma status verde do CI em aprovação.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.v3 import estado_final

_PORTOES = ('audio_ok', 'ritmo_ok', 'legenda_ok')


def avaliar(resultado: dict | None) -> dict:
    """Retorna BLOQUEADO ou AGUARDANDO_APROVACAO_HUMANA, usando o estado V3.

    Não confia somente em resultado['estado']: exige gates reais, MP4 presente e
    nao_publicado=True. O fiscal pode ter sido ignorado pelo chamador do render.
    """
    r = resultado or {}
    motivos = list(r.get('motivos_bloqueio') or [])
    if r.get('estado') not in (estado_final.BLOQUEADO, estado_final.AGUARDANDO):
        motivos.append('G-ESTADO: render não retornou estado editorial automático válido')
    elif r.get('estado') == estado_final.BLOQUEADO and not motivos:
        motivos.append('G-ESTADO: render declarou BLOQUEADO sem detalhar motivo')
    if r.get('nao_publicado') is not True:
        motivos.append('G-PUBLICACAO: formatos só autorizam prévia privada')
    portas = r.get('portoes')
    if not isinstance(portas, dict):
        motivos.append('G-PORTOES: resultado não contém verificações do MP4')
    else:
        if portas.get('preto_ou_congelado'):
            motivos.append('G-MP4: existe janela preta/congelada')
        for chave in _PORTOES:
            if portas.get(chave) is not True:
                motivos.append(f'G-{chave.upper()}: verificação ausente ou reprovada')
    estado = estado_final.decidir({
        'mp4': r.get('mp4'),
        'bloqueios': list(dict.fromkeys(motivos)),
        'revisoes': r.get('revisoes') or [],
        'revisao_multimodal': r.get('revisao_multimodal'),
    })
    return {**estado, 'estado_render': r.get('estado'), 'nao_publicado': True}


def conferir(saida: Path) -> dict:
    """Grava o estado, inclusive sem MP4. O comando CLI decide o exit code."""
    saida = Path(saida)
    arq = saida / 'resultado.json'
    if arq.exists():
        try:
            r = json.loads(arq.read_text(encoding='utf-8'))
            if not isinstance(r, dict):
                r = {}
        except (ValueError, OSError):
            r = {}
    else:
        r = {}
    estado = avaliar(r)
    saida.mkdir(parents=True, exist_ok=True)
    estado_final.gravar(estado, saida / 'estado_editorial.json')
    return estado
