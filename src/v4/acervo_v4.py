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

LIC = re.compile(r'\b(?:CC[ -]?(?:BY|0|PDM)|CC0|GFDL|FAL|OGL|Public domain|PD\b|PD-|domínio público|No restrictions|Attribution|Creative Commons|ShareAlike)', re.I)
UA = {'User-Agent': 'CoringaExplica/4.0 (contato via GitHub heitor2404/coringa-news)'}


def _licenca(credito: str) -> str | None:
    """a licença está no ÚLTIMO parêntese do crédito montado pelo acervo ('… — autor (LICENÇA), via …'); só a lista
    fixa de padrões deixava sem licença um vídeo do Commons com outra grafia (execução 43956541084)"""
    grupos = [g.strip() for g in re.findall(r'\(([^()]{2,60})\)', credito or '') if LIC.search(g)]
    return grupos[-1] if grupos else None      # só parêntese com cara de licença: "(1913)" não é licença


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


GENERICOS = {'canal', 'canals', 'lock', 'locks', 'ship', 'ships', 'video', 'videos', 'transit', 'construction', 'the', 'of', 'and',
             'river', 'sea', 'ocean', 'port', 'boat', 'water', 'aerial', 'view', 'old', 'history', 'historic'}


def _sem_acento(t: str) -> str:
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFD', str(t or '').lower()) if unicodedata.category(ch) != 'Mn')


def nomes_proprios(consultas: list[str]) -> set[str]:
    """nomes próprios das consultas (Panama, Miraflores, Gatun): o que identifica o LUGAR, não o tipo de coisa"""
    return {_sem_acento(w) for q in consultas or [] for w in re.findall(r'\b[A-ZÁÉÍÓÚ][\wÀ-ÿ]{2,}', q) if _sem_acento(w) not in GENERICOS}


def mesmo_lugar(c: dict, nomes: set[str]) -> bool:
    """vídeo de banco (Pixabay etc.) só se identifica pelas tags: sem nenhum nome próprio do pedido, é outro lugar.
    Execução 43972774128: 'sunset, canal, city' (Holanda) passou na visão como eclusa do Panamá."""
    if not nomes:
        return True
    texto = _sem_acento(f"{c.get('titulo', '')} {c.get('desc', '')} {c.get('descricao', '')} {c.get('url', '')}")
    return any(n in texto for n in nomes)


def _roi_valida(roi) -> list | None:
    """o modelo às vezes devolve pixels; ROI só vale normalizada em [0, 1]"""
    try:
        r = [float(v) for v in roi]
        return r if len(r) == 4 and all(0 <= v <= 1 for v in r) and r[2] > 0 and r[3] > 0 else None
    except Exception:
        return None


def escolher(cands: list[dict], deve_mostrar: str, usados: set[str], consultas: list[str] | None = None) -> tuple[dict | None, dict]:
    cands = [c for c in cands if c.get('url') not in usados and (_licenca(c.get('credito')) or c.get('video'))]
    nomes = nomes_proprios(consultas or [])
    fora = [c for c in cands if c.get('video') and not mesmo_lugar(c, nomes)]
    cands = [c for c in cands if c not in fora]
    if not cands:
        return None, {'motivo': 'sem candidato com licença' + (f' e do mesmo lugar ({sorted(nomes)}; {len(fora)} vídeo(s) de outro lugar descartados)' if fora else '')}
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
                return ok[k][0], {'metodo': 'visao_gemini', 'motivo': r.get('motivo'), 'roi': _roi_valida(r.get('roi')),
                                  **({'roi_descartada': r.get('roi')} if r.get('roi') and not _roi_valida(r.get('roi')) else {})}
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
            esc, info = escolher(cands, b.get('deve_mostrar') or c.get('o_que_precisa_aparecer', ''), usados, b.get('consultas_en'))
            if not esc:
                reg.append({'cena': c['id'], 'estado': 'sem_midia', 'candidatos': len(cands), **info})
                c['params']['asset'] = None
                continue
            x = baixar(esc, pasta, aid)
            usados.add(esc['url'])
            pix = 'pixabay' in str(x.get('url')) or 'pixabay' in str((x.get('video') or {}).get('url'))
            cred = x.get('credito') or (f"{x.get('titulo') or 'vídeo'} (Pixabay Content License), via Pixabay" if pix else '')
            acv[aid] = {'id': aid, 'arq': x['arq'], 'wh': [x.get('w'), x.get('h')], 'titulo': x.get('titulo'), 'desc': x.get('desc'),
                        'ano': x.get('ano'), 'credito': cred, 'licenca': _licenca(cred) or ('Pixabay Content License' if pix else None),
                        'fonte_url': x.get('url'), 'video': x.get('video'), 'roi': info.get('roi'), 'escolha': info}
            c['params']['asset'] = aid
            reg.append({'cena': c['id'], 'estado': 'ok', 'asset': aid, 'candidatos': len(cands), **info})
        except Exception as e:
            reg.append({'cena': c['id'], 'estado': 'erro', 'erro': str(e)[:200]})
            c['params']['asset'] = None
    (pasta / 'acervo.json').write_text(json.dumps(acv, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return acv, reg
