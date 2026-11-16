"""Envio de PRÉVIA PRIVADA ao Telegram (canal oficial de avaliação do Heitor). Enviar prévia NÃO é publicar.

Permissões separadas (decisão de 16/11):
  * prévia privada — autorizada para qualquer estado (inclusive BLOQUEADO ou pendente), sempre com o estado visível;
  * publicação em redes — continua proibida (estado_final.pode_publicar exige PUBLICAVEL; não há código que publique).
Destino único: TELEGRAM_CHAT_ID do bot atual, e só se o Telegram confirmar que é um chat PRIVADO (getChat → 'private').
Não há parâmetro de destino: grupos, canais e outros chats ficam de fora por construção.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import requests

LIMITE_MB = 49            # sendVideo do Bot API aceita até 50 MB
LEGENDA = 1000


class EnvioRecusado(RuntimeError):
    pass


def _api(metodo: str, data: dict, arquivo=None, tok: str | None = None):
    tok = tok or os.environ['TELEGRAM_BOT_TOKEN']
    for tentativa in range(3):
        try:
            if arquivo:
                with open(arquivo[1], 'rb') as f:
                    r = requests.post(f'https://api.telegram.org/bot{tok}/{metodo}', data=data, files={arquivo[0]: f}, timeout=300)
            else:
                r = requests.post(f'https://api.telegram.org/bot{tok}/{metodo}', data=data, timeout=60)
            if r.ok:
                return r.json().get('result')
            if r.status_code == 429:
                time.sleep(int((r.json().get('parameters') or {}).get('retry_after', 10)) + 1)
                continue
            raise EnvioRecusado(f'{metodo}: {r.status_code} {r.text[:150]}')
        except requests.RequestException as e:
            if tentativa == 2:
                raise EnvioRecusado(f'{metodo}: {str(e)[:150]}')
            time.sleep(5)
    raise EnvioRecusado(f'{metodo}: limite de tentativas')


def chat_autorizado() -> str:
    """O único destino possível. Recusa se faltar configuração ou se o chat não for privado."""
    tok, chat = os.getenv('TELEGRAM_BOT_TOKEN'), (os.getenv('TELEGRAM_CHAT_ID') or '').strip()
    if not (tok and chat):
        raise EnvioRecusado('TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ausentes')
    if not chat.lstrip('-').isdigit() or chat.startswith('-'):
        raise EnvioRecusado('TELEGRAM_CHAT_ID não é um chat privado (grupos e canais têm id negativo)')
    info = _api('getChat', {'chat_id': chat}) or {}
    if info.get('type') != 'private':
        raise EnvioRecusado(f"chat {info.get('type')!r} não é privado: não envio")
    return chat


def _caber(mp4: Path) -> Path:
    if mp4.stat().st_size <= LIMITE_MB * 1024 * 1024:
        return mp4
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(mp4)],
                               capture_output=True, text=True).stdout or 60)
    kbps = int(LIMITE_MB * 8 * 1024 * 0.92 / dur) - 192
    out = mp4.with_name(mp4.stem + '_telegram.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', f'{kbps}k',
                    '-maxrate', f'{kbps}k', '-bufsize', f'{2 * kbps}k', '-c:a', 'copy', '-movflags', '+faststart', str(out)], check=True)
    return out


def legenda(estado: dict, titulo: str) -> str:
    st = estado.get('estado', '?')
    return (f'PRÉVIA PRIVADA — NÃO PUBLICADO\n{titulo}\nSTATUS: {st}'
            + (f"\nMotivos: {'; '.join(estado.get('motivos') or [])[:300]}" if estado.get('motivos') else '')
            + '\nPublicação em redes: proibida sem aprovação e autorização do Heitor.')[:LEGENDA]


def enviar(mp4: Path, estado: dict, titulo: str, relatorio: str) -> dict:
    """MP4 + estado + relatório (fiscal e custos) só para o chat privado autorizado."""
    from src.v3 import estado_final
    if not estado_final.pode_enviar_previa(estado):
        raise EnvioRecusado(f"estado desconhecido {estado.get('estado')!r}: sem status visível não envio")
    chat = chat_autorizado()
    envio = _caber(Path(mp4))
    _api('sendVideo', {'chat_id': chat, 'caption': legenda(estado, titulo), 'supports_streaming': 'true'}, ('video', envio))
    partes = [relatorio[i:i + 3900] for i in range(0, len(relatorio), 3900)] or ['(sem relatório)']
    for p in partes:
        _api('sendMessage', {'chat_id': chat, 'text': p})
    return {'chat': 'privado autorizado', 'arquivo': envio.name, 'mb': round(envio.stat().st_size / 1048576, 1), 'mensagens': len(partes)}
