"""Imagens dos planos do vídeo.

Ordem: Cloudflare FLUX.2 [klein] (vertical, grátis dentro da cota diária) → Cloudflare FLUX.1 schnell → [Gemini, se
GEMINI_IMAGENS=1] → sem imagem (fundo gráfico).

Personagem consistente: quando a história tem protagonista, primeiro é gerado um "retrato de referência" dele e esse
retrato vai junto em todos os planos em que ele aparece (o FLUX.2 aceita imagens de referência), para ele ter o mesmo
rosto, cabelo e roupa no vídeo inteiro.
"""
import base64, io, os, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ESTILO = ('cinematic photorealistic photo, vibrant saturated colors, high contrast, dramatic lighting, depth of field, '
          'editorial magazine quality')
PROIBIDO = 'no text, no letters, no captions, no logos, no watermark'
MODELO_IMG = os.getenv('GEMINI_MODELO_IMAGEM', 'gemini-2.5-flash-image')
ESTILO_ANIM = ('flat vector illustration, clean minimal explainer animation style, simple geometric shapes, flat colors with '
               'subtle shading, muted warm palette (cream beige, teal, mustard yellow, brick red, charcoal), thin dark outlines, '
               'soft paper grain texture, expressive simple characters, clear readable action')
LARG, ALT = 864, 1536          # 9:16 (mesmo custo de cota que 768x1344) (o vídeo é 1080x1920; a imagem é ampliada com leve movimento de câmera)
_RETRATOS: dict[str, bytes] = {}   # retrato de referência do protagonista, reaproveitado na mesma execução
_klein_off = False             # cota do FLUX.2 acabou nesta execução: usa o schnell direto


def _cf_url(modelo: str) -> str:
    return f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CF_ACCOUNT_ID')}/ai/run/@cf/black-forest-labs/{modelo}"


def _cf_ok() -> bool:
    return bool(os.getenv('CF_ACCOUNT_ID') and os.getenv('CF_API_TOKEN'))


def _cf_resposta(r: requests.Response) -> bytes:
    if r.status_code >= 400:
        raise RuntimeError(f'{r.status_code} {r.text[:200]}')
    if r.headers.get('content-type', '').startswith('image/'):
        return r.content
    j = r.json()
    res = j.get('result') if isinstance(j.get('result'), dict) else j
    return base64.b64decode(res['image'])


def _klein(prompt: str, ref: bytes | None = None, seed: int | None = None) -> bytes | None:
    """FLUX.2 [klein] 4B: bem melhor que o schnell, aceita tamanho vertical e imagem de referência."""
    global _klein_off
    if not _cf_ok() or _klein_off or os.getenv('IMAGEM_MODELO') == 'schnell':
        return None
    campos = {'prompt': (None, prompt[:2000]), 'width': (None, str(LARG)), 'height': (None, str(ALT))}
    if seed is not None:
        campos['seed'] = (None, str(seed))
    if ref:
        campos['input_image_0'] = ('ref.jpg', ref, 'image/jpeg')
    r = requests.post(_cf_url(os.getenv('IMAGEM_MODELO') or 'flux-2-klein-4b'),
                      headers={'Authorization': f"Bearer {os.getenv('CF_API_TOKEN')}"}, files=campos, timeout=120)
    if r.status_code in (429, 402) or (r.status_code >= 400 and any(w in r.text.lower() for w in ('neurons', 'allocation', 'quota'))):
        _klein_off = True
        print('  [imagem] cota diária do FLUX.2 acabou; sigo com o FLUX.1 schnell')
    return _cf_resposta(r)


def _schnell(prompt: str, ref: bytes | None = None, seed: int | None = None) -> bytes | None:
    if not _cf_ok():
        return None
    corpo = {'prompt': prompt[:2000], 'steps': 8}     # o schnell do Cloudflare não aceita mais "seed" (erro 400)
    r = requests.post(_cf_url('flux-1-schnell'), headers={'Authorization': f"Bearer {os.getenv('CF_API_TOKEN')}"},
                      json=corpo, timeout=90)
    return _cf_resposta(r)


import threading
_POLL = threading.Lock()


def _pollinations(prompt: str, ref: bytes | None = None, seed: int | None = None) -> bytes | None:
    """Pollinations.ai (FLUX grátis, sem chave): mais lento e às vezes fora do ar, então é reserva do Cloudflare.
    Um pedido por vez (o plano grátis limita a frequência)."""
    from urllib.parse import quote
    with _POLL:
        r = requests.get(f'https://image.pollinations.ai/prompt/{quote(prompt[:900])}', timeout=180,
                         params={'width': LARG, 'height': ALT, 'nologo': 'true', 'model': 'flux', 'seed': seed or 1})
        time.sleep(46)        # plano grátis: 1 imagem a cada 45 s
    if r.status_code >= 400 or not r.headers.get('content-type', '').startswith('image/'):
        raise RuntimeError(f'{r.status_code} {r.text[:120]}')
    return r.content


def _gemini(prompt: str, ref: bytes | None = None, seed: int | None = None) -> bytes | None:
    if os.getenv('GEMINI_IMAGENS') != '1' or not os.getenv('GEMINI_API_KEY'):
        return None
    from google.genai import types
    from .gemini import cliente
    try:
        cfg = types.GenerateContentConfig(response_modalities=['IMAGE'], image_config=types.ImageConfig(aspect_ratio='9:16'))
    except Exception:
        cfg = types.GenerateContentConfig(response_modalities=['IMAGE'])
    conteudo = [prompt]
    if ref:
        conteudo.insert(0, types.Part.from_bytes(data=ref, mime_type='image/jpeg'))
    r = cliente().models.generate_content(model=MODELO_IMG, contents=conteudo, config=cfg)
    for parte in r.candidates[0].content.parts:
        if getattr(parte, 'inline_data', None) and parte.inline_data.data:
            d = parte.inline_data.data
            return d if isinstance(d, bytes) else base64.b64decode(d)
    return None


def _miniatura(dados: bytes, lado: int = 500) -> bytes:
    """Referência para o FLUX.2 precisa ser menor que 512x512."""
    from PIL import Image
    im = Image.open(io.BytesIO(dados)).convert('RGB')
    im.thumbnail((lado, lado))
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=90)
    return buf.getvalue()


def _uma(prompt: str, ref: bytes | None, seed: int, rotulo: str) -> bytes | None:
    motores = [('flux2', _klein), ('schnell', _schnell), ('pollinations', _pollinations), ('gemini', _gemini)]
    if os.getenv('GEMINI_IMAGENS') == '1':
        motores.insert(0, motores.pop())
    for nome, fn in motores:
        for tentativa in range(2):
            try:
                p = prompt if not tentativa else prompt[:400]
                # o schnell não usa referência: reforça a descrição no texto
                d = fn(p, ref if nome in ('flux2', 'gemini') else None, seed)
                if d:
                    print(f'  [imagem/{nome}] ok: {rotulo}')
                    return d
                break
            except Exception as e:
                print(f'  [imagem/{nome}] {rotulo} falhou: {str(e)[:140]}')
                time.sleep(2)
    return None


def gerar(imagens: list[dict], pasta: Path, estilo: str = '', personagem: str = '') -> dict[str, Path]:
    """Recebe [{'id','prompt','personagem'}] e devolve {id: caminho} das que deram certo.
    'estilo' deixa todas as imagens com a mesma cara (um filme só); 'personagem' mantém o protagonista igual."""
    pasta.mkdir(parents=True, exist_ok=True)
    estilo = (estilo or ESTILO).strip(', ')
    seed = abs(hash(estilo + personagem)) % 2_000_000_000

    ref = _RETRATOS.get(personagem)
    if ref is None and personagem and any(i.get('personagem') for i in imagens):
        retrato = _uma(f'character reference portrait: {personagem}. Front-facing medium close-up, neutral expression, '
                       f'full head and shoulders visible, plain softly lit studio background. {estilo}. {PROIBIDO}',
                       None, seed, 'retrato do personagem')
        if retrato:
            (pasta / 'personagem.png').write_bytes(retrato)
            ref = _RETRATOS[personagem] = _miniatura(retrato)

    def tarefa(im):
        texto = im['prompt']
        usa = ref is not None and im.get('personagem')
        if im.get('personagem') and personagem:
            texto = (f'The same character as in reference image 0 (identical face, hair and clothes: {personagem}). ' if usa
                     else f'Main character: {personagem}. ') + texto
        texto = f'{texto}. Style: {estilo}. Vertical 9:16 composition. {PROIBIDO}'
        d = _uma(texto, ref if usa else None, seed, im['id'])
        if not d:
            return im['id'], None
        arq = pasta / f"img_{im['id']}.png"
        arq.write_bytes(d)
        return im['id'], arq

    out = {}
    with ThreadPoolExecutor(3) as ex:          # 3 de cada vez: rápido sem estourar o limite por minuto
        for iid, arq in ex.map(tarefa, imagens):
            if arq:
                out[iid] = arq
    print(f'  [imagem] {len(out)}/{len(imagens)} imagens geradas')
    return out


def sequencia(prompts: list[str], pasta: Path, iid: str, estilo: str = '', personagem: str = '') -> list[Path]:
    """'Simulação' de uma ação (ex.: o navio batendo no iceberg) em 2–3 quadros do MESMO cenário:
    o 1º quadro vira referência dos seguintes, para a cena parecer contínua quando os quadros se sucedem."""
    pasta.mkdir(parents=True, exist_ok=True)
    estilo = (estilo or ESTILO).strip(', ')
    seed = abs(hash(iid + estilo)) % 2_000_000_000
    out, ref = [], None
    for j, p in enumerate(prompts[:3]):
        quem = f' Main character: {personagem}.' if personagem and j == 0 else ''
        if ref:
            texto = (f'Same scene, same camera angle, same objects and lighting as reference image 0, a moment later: {p}. '
                     f'Style: {estilo}. Vertical 9:16 composition. {PROIBIDO}')
        else:
            texto = f'{p}.{quem} Style: {estilo}. Vertical 9:16 composition. {PROIBIDO}'
        d = _uma(texto, ref, seed, f'{iid}.{j + 1}')
        if not d:
            break
        arq = pasta / f'seq_{iid}_{j}.png'
        arq.write_bytes(d)
        out.append(arq)
        if ref is None:
            ref = _miniatura(d)
    return out
