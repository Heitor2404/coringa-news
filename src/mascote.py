"""Coringa 3D: gera versões do mascote com a IA grátis da Cloudflare, recorta o fundo e salva as expressões.

    python main.py --mascote gerar   → 4 versões, enviadas ao Telegram para escolher
    python main.py --mascote 3       → gera as expressões da versão 3 e salva em assets/mascote3d/
"""
import base64, json, os, subprocess, sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / 'assets' / 'mascote3d'
SEMENTES = [1107, 2213, 3319, 4421]

PERSONAGEM = ('a friendly young court jester news reporter character, three-pointed jester hat in black and golden yellow '
              'with one red point and small golden bells on the tips, big expressive eyes, warm mischievous smile, '
              'black reporter jacket with a small white press badge, golden yellow collar with zigzag edge, '
              'holding a black handheld microphone')
ESTILO = ('stylized 3D animated feature film character, high-end CGI, soft studio lighting, subsurface skin shading, '
          'full body, centered, facing the camera, plain flat light gray background, no text, no logos')
POSES = {
    'falando': 'talking enthusiastically, mouth open mid-sentence, microphone near the mouth, one hand gesturing',
    'surpreso': 'shocked and amazed, eyes wide open, mouth open in surprise, free hand on the cheek',
    'apontando': 'pointing forward at the viewer with the index finger, confident big smile',
    'pensando': 'thinking, hand on the chin, eyes looking up, curious expression',
    'comemorando': 'celebrating, both arms raised, huge happy smile, jumping slightly',
}


def _flux(prompt: str, semente: int) -> bytes:
    conta, token = os.getenv('CF_ACCOUNT_ID'), os.getenv('CF_API_TOKEN')
    if not (conta and token):
        raise RuntimeError('faltam as chaves da Cloudflare (CF_ACCOUNT_ID / CF_API_TOKEN)')
    url = f'https://api.cloudflare.com/client/v4/accounts/{conta}/ai/run/@cf/black-forest-labs/flux-1-schnell'
    corpo = {'prompt': prompt, 'steps': 8, 'seed': semente}
    r = requests.post(url, headers={'Authorization': f'Bearer {token}'}, json=corpo, timeout=120)
    if r.status_code == 400:   # caso o modelo não aceite 'seed'
        corpo.pop('seed')
        r = requests.post(url, headers={'Authorization': f'Bearer {token}'}, json=corpo, timeout=120)
    r.raise_for_status()
    return base64.b64decode(r.json()['result']['image'])


def _sem_fundo(png: Path) -> Path:
    """Recorta o fundo (deixa só o personagem) com o rembg, que roda no próprio GitHub."""
    try:
        from rembg import remove
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'rembg[cpu]'], check=True)
        from rembg import remove
    saida = png.with_name(png.stem + '-recorte.png')
    saida.write_bytes(remove(png.read_bytes()))
    return saida


def _telegram_foto(arq: Path, legenda: str):
    tok, chat = os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
    if not (tok and chat):
        return
    with open(arq, 'rb') as f:
        requests.post(f'https://api.telegram.org/bot{tok}/sendPhoto', data={'chat_id': chat, 'caption': legenda},
                      files={'photo': f}, timeout=120)


def gerar_versoes(saida: Path):
    saida.mkdir(parents=True, exist_ok=True)
    for i, semente in enumerate(SEMENTES, 1):
        arq = saida / f'coringa-versao-{i}.png'
        arq.write_bytes(_flux(f'{PERSONAGEM}, {POSES["falando"]}, {ESTILO}', semente))
        print(f'  versão {i} pronta')
        _telegram_foto(arq, f'🃏 Coringa 3D — versão {i}. Para escolher: Run workflow → campo "Mascote" = {i}')


def gerar_expressoes(versao: int, saida: Path):
    semente = SEMENTES[max(1, min(versao, len(SEMENTES))) - 1]
    PASTA.mkdir(parents=True, exist_ok=True)
    saida.mkdir(parents=True, exist_ok=True)
    for nome, pose in POSES.items():
        bruto = saida / f'{nome}.png'
        bruto.write_bytes(_flux(f'{PERSONAGEM}, {pose}, {ESTILO}', semente))
        recorte = _sem_fundo(bruto)
        (PASTA / f'{nome}.png').write_bytes(recorte.read_bytes())
        print(f'  expressão "{nome}" pronta')
        _telegram_foto(recorte, f'🃏 Coringa 3D — {nome}')
    (PASTA / 'info.json').write_text(json.dumps({'versao': versao, 'semente': semente}, indent=1), encoding='utf-8')
    print('  ✔ expressões salvas em assets/mascote3d (os próximos vídeos e capas já usam o Coringa 3D)')


def poses_disponiveis() -> dict[str, Path]:
    return {p.stem: p for p in PASTA.glob('*.png')} if PASTA.exists() else {}
