"""Acervo do V4: para cada cena com `busca`, procura no Commons (fotos) ou em fontes de vídeo livres (Commons/Archive/
Pixabay se houver chave), baixa, escolhe a mídia que MOSTRA o pedido e localiza o objeto principal (ROI).

- Licença e crédito saem do PRÓPRIO arquivo (metadados da fonte); o crédito exibido é sempre o do asset da cena.
- Mídia não reutilizada entre cenas (regra de repetição); vídeo curto demais para a cena é descartado.
- Escolha por visão (Gemini, cota grátis) quando disponível; senão a maior resolução vertical útil (registrado).
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
from pathlib import Path

import requests

LIC = re.compile(r'\(([^()]*(?:CC|Public domain|PD|domínio|Domínio|No restrictions|CC0)[^()]*)\)', re.I)
UA = {'User-Agent': 'CoringaExplica/4.0 (contato via GitHub heitor2404/coringa-news)'}


def _licenca(credito: str) -> str | None:
    m = LIC.search(credito or '')
    return m.group(1).strip() if m else None


def _miniatura(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers=UA, timeout=40)
        r.raise_for_status()
        from PIL import Image
        im = Image.open(io.BytesIO(r.content)).convert('RGB')
        im.thumbnail((512, 512))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=82)
        return b.getvalue()
    except Exception:
        return None


def candidatos(busca: dict) -> list[dict]:
    from src import acervo
    q = [x for x in busca.get('consultas_en') or [] if x][:4]
    if busca.get('tipo') == 'video':                    # acervo._seguro chama a fonte SEM argumentos: lambda
        return [c for c in acervo._seguro(lambda: acervo.f_videos(q)) if c.get('video')]
    return acervo._seguro(lambda: acervo.f_commons(q))


def escolher(cands: list[dict], deve_mostrar: str, usados: set[str]) -> tuple[dict | None, dict]:
    cands = [c for c in cands if c.get('url') not in usados and (_licenca(c.get('credito')) or c.get('video'))]
    if not cands:
        return None, {'motivo': 'sem candidato com licença'}
    cands = sorted(cands, key=lambda c: -(min(c.get('w') or 0, c.get('h') or 0)))[:6]
    if os.getenv('GEMINI_API_KEY'):
        try:
            from src.gemini import json_visao
            imgs = [_miniatura(c['url']) for c in cands]
            ok = [(c, b) for c, b in zip(cands, imgs) if b]
            r = json_visao(f"""Escolha a imagem que MELHOR mostra: "{deve_mostrar}". Rejeite as que não mostram (ou mostram
outra coisa, outro lugar, ou só texto). Responda JSON {{"escolha": índice ou -1, "motivo": "...",
"roi": [x, y, w, h] normalizado do objeto principal na imagem escolhida}}. Imagens: 0..{len(ok) - 1}.""", [b for _, b in ok], leve=False)
            k = int(r.get('escolha', -1))
            if 0 <= k < len(ok):
                return ok[k][0], {'metodo': 'visao_gemini', 'motivo': r.get('motivo'), 'roi': r.get('roi')}
            return None, {'metodo': 'visao_gemini', 'motivo': 'nenhuma mostra o pedido: ' + str(r.get('motivo'))[:160]}
        except Exception as e:
            info = {'metodo': 'resolucao', 'visao_falhou': str(e)[:160]}
            return cands[0], info
    return cands[0], {'metodo': 'resolucao', 'visao': 'indisponível'}


def baixar(c: dict, pasta: Path, aid: str) -> dict:
    from src import acervo
    pasta.mkdir(parents=True, exist_ok=True)
    if c.get('video'):
        bruto = pasta / f'{aid}_bruto'
        r = requests.get(c['video']['url'], headers=UA, timeout=300)
        r.raise_for_status()
        bruto.write_bytes(r.content)
        arq = pasta / f'{aid}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(bruto), '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', str(arq)], check=True)
        bruto.unlink(missing_ok=True)
        x = dict(c, arq=str(arq))
    else:
        x = acervo._baixar_item(dict(c), pasta / f'{aid}.jpg')
        if not x.get('arq'):
            raise RuntimeError(f'download falhou: {c.get("url")}')
        x['arq'] = str(x['arq'])
        x.pop('mini', None)
    from PIL import Image
    if not c.get('video'):
        x['w'], x['h'] = Image.open(x['arq']).size
    return x


def montar(ep: dict, pasta: Path) -> tuple[dict, list[dict]]:
    """preenche params.asset das cenas com busca; devolve (acervo{id: item}, registro)"""
    acv, reg, usados = {}, [], set()
    pasta.mkdir(parents=True, exist_ok=True)
    for c in ep['cenas']:
        b = c.get('busca')
        if not b or (c.get('params') or {}).get('asset') not in (None, 'auto'):
            continue
        aid = f"{'v' if b.get('tipo') == 'video' else 'a'}{len(acv) + 1}"
        try:
            cands = candidatos(b)
            esc, info = escolher(cands, b.get('deve_mostrar') or c.get('o_que_precisa_aparecer', ''), usados)
            if not esc:
                reg.append({'cena': c['id'], 'estado': 'sem_midia', 'candidatos': len(cands), **info})
                c['params']['asset'] = None
                continue
            x = baixar(esc, pasta, aid)
            usados.add(esc['url'])
            acv[aid] = {'id': aid, 'arq': x['arq'], 'wh': [x.get('w'), x.get('h')], 'titulo': x.get('titulo'), 'desc': x.get('desc'),
                        'ano': x.get('ano'), 'credito': x.get('credito'), 'licenca': _licenca(x.get('credito')) or ('livre (Pixabay)' if 'pixabay' in str(x.get('url')) else None),
                        'fonte_url': x.get('url'), 'video': x.get('video'), 'roi': info.get('roi'), 'escolha': info}
            c['params']['asset'] = aid
            reg.append({'cena': c['id'], 'estado': 'ok', 'asset': aid, 'candidatos': len(cands), **info})
        except Exception as e:
            reg.append({'cena': c['id'], 'estado': 'erro', 'erro': str(e)[:200]})
            c['params']['asset'] = None
    (pasta / 'acervo.json').write_text(json.dumps(acv, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return acv, reg
