"""Envio de PRÉVIA PRIVADA ao Telegram (canal oficial de avaliação do Heitor). Enviar prévia NÃO é publicar.

Permissões separadas (decisão de 16/11):
  * prévia privada — autorizada para qualquer estado (inclusive BLOQUEADO ou pendente), sempre com o estado visível;
  * publicação em redes — continua proibida (estado_final.pode_publicar exige PUBLICAVEL; não há código que publique).
Destino único: TELEGRAM_CHAT_ID do bot atual (o canal privado de avaliação), e só se o Telegram confirmar que não é
público: conversa privada, ou grupo/canal sem @nome e com no máximo MAX_MEMBROS membros. Não há parâmetro de destino.
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
            if r.status_code >= 500 and tentativa < 2:      # falha passageira do Telegram (502 na execução V4 43956541084)
                time.sleep(15 * (tentativa + 1))
                continue
            raise EnvioRecusado(f'{metodo}: {r.status_code} {r.text[:150]}')
        except requests.RequestException as e:
            if tentativa == 2:
                raise EnvioRecusado(f'{metodo}: {str(e)[:150]}')
            time.sleep(5)
    raise EnvioRecusado(f'{metodo}: limite de tentativas')


MAX_MEMBROS = 5          # grupo/canal privado do dono + bot(s); mais que isso já não é "privado"


def chat_autorizado() -> tuple[str, dict]:
    """O único destino possível: o TELEGRAM_CHAT_ID do bot atual. Recusa se faltar configuração, se o chat for PÚBLICO
    (tem @nome) ou se for grupo/canal com mais de MAX_MEMBROS membros. Devolve (chat, {tipo, membros}) sem o id."""
    tok, chat = os.getenv('TELEGRAM_BOT_TOKEN'), (os.getenv('TELEGRAM_CHAT_ID') or '').strip()
    if not (tok and chat):
        raise EnvioRecusado('TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ausentes')
    if not chat.lstrip('-').isdigit():
        raise EnvioRecusado('TELEGRAM_CHAT_ID não é um id numérico (@canal público não é aceito)')
    info = _api('getChat', {'chat_id': chat}) or {}
    tipo = info.get('type')
    if tipo not in ('private', 'group', 'supergroup', 'channel'):
        raise EnvioRecusado(f'tipo de chat desconhecido {tipo!r}: não envio')
    if info.get('username') and tipo != 'private':
        raise EnvioRecusado(f'{tipo} público (@nome): não envio prévia')
    membros = 2 if tipo == 'private' else int(_api('getChatMemberCount', {'chat_id': chat}) or 0)
    if tipo != 'private' and not 0 < membros <= MAX_MEMBROS:
        raise EnvioRecusado(f'{tipo} com {membros} membros (> {MAX_MEMBROS}): não é privado, não envio')
    return chat, {'tipo': tipo, 'membros': membros}


def _caber(mp4: Path) -> Path:
    """Cópia recomprimida para o limite do Bot API (o original fica intacto). Mede o resultado e reduz a taxa até caber."""
    limite = LIMITE_MB * 1024 * 1024
    if mp4.stat().st_size <= limite:
        return mp4
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(mp4)],
                               capture_output=True, text=True).stdout or 60)
    kbps = max(200, int(limite * 8 / 1024 * 0.90 / dur) - 160)
    out = mp4.with_name(mp4.stem + '_telegram.mp4')
    for _ in range(6):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', f'{kbps}k',
                        '-maxrate', f'{kbps}k', '-bufsize', f'{kbps}k', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
                        str(out)], check=True)
        if out.stat().st_size <= limite:
            return out
        kbps = max(100, int(kbps * 0.8))
    raise EnvioRecusado(f'não consegui deixar o MP4 abaixo de {LIMITE_MB} MB')


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
    chat, info = chat_autorizado()
    envio = _caber(Path(mp4))
    _api('sendVideo', {'chat_id': chat, 'caption': legenda(estado, titulo), 'supports_streaming': 'true'}, ('video', envio))
    partes = [relatorio[i:i + 3900] for i in range(0, len(relatorio), 3900)] or ['(sem relatório)']
    for p in partes:
        _api('sendMessage', {'chat_id': chat, 'text': p})
    return {'chat': f"{info['tipo']} privado autorizado ({info['membros']} membros)", 'arquivo': envio.name, 'mb': round(envio.stat().st_size / 1048576, 1), 'mensagens': len(partes)}
