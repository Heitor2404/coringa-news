"""Mídia REAL para os planos do vídeo, escolhida a dedo, com IA só quando não existe nada de verdade.

Para cada frase o sistema junta até 3 candidatos por fonte e um FISCAL (o Gemini, que enxerga imagens) escolhe o que
mais combina com a frase — ou reprova todos. Fontes:
- foto:    foto histórica real do Wikimedia Commons (acervo de imagens da Wikipédia), com crédito e licença;
- arquivo: filmagem antiga real do Wikimedia Commons;
- video:   vídeo de banco grátis do Pixabay (mar, tempestade, multidão...), com movimento de verdade;
- mapa:    desenhado no próprio vídeo;
- ia:      imagem gerada (FLUX), em estilo realista, quando nada acima serve.
"""
import io, os, re, subprocess
from pathlib import Path

import requests
from src import cofre

UA = {'User-Agent': 'CoringaExplicaBot/1.4 (https://github.com/Heitor2404/coringa-news; educational short videos) python-requests'}
COMMONS = 'https://commons.wikimedia.org/w/api.php'
LICENCAS_OK = ('public domain', 'pd', 'cc0', 'cc by', 'cc-by', 'no restrictions', 'attribution')
PROIBIDO_TITULO = ('signature', 'assinatura', 'logo', 'coat of arms', 'brasão', 'flag of', 'bandeira', 'icon', 'diagram',
                   'chart', 'graph', 'screenshot', 'youtube', 'captura de tela', 'still from', '.svg', '.pdf', '.djvu',
                   '.tif', 'map of', 'locator', 'stamp', 'selo')
_PARADAS = {'the', 'and', 'with', 'from', 'that', 'this', 'into', 'over', 'photo', 'photograph', 'image', 'film',
            'footage', 'video', 'real', 'historic', 'historical', 'old', 'black', 'white', 'year'}
POR_FONTE = 3
MIN_LADO = 900          # foto menor que isso fica borrada ao ser ampliada para 1080x1920


# ───────────────────────── utilidades ─────────────────────────
def _palavras(busca: str) -> list[str]:
    return [w for w in re.findall(r'[a-zà-ú0-9]+', busca.lower()) if len(w) > 3 and w not in _PARADAS and not w.isdigit()]


def _txt(meta: dict, chave: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', str((meta.get(chave) or {}).get('value', '')))).strip()


def _ano(meta: dict) -> int | None:
    """Ano em que a imagem foi FEITA (DateTimeOriginal). O campo DateTime é a data de envio ao site: não serve
    (era por isso que uma charge de 1910 aparecia como 2026)."""
    import datetime
    m = re.search(r'\b(1[5-9]\d\d|20\d\d)\b', _txt(meta, 'DateTimeOriginal'))
    if m and int(m.group(1)) < datetime.date.today().year:
        return int(m.group(1))
    return None


def _licenca_ok(lic: str) -> bool:
    l = lic.lower()
    return any(x in l for x in LICENCAS_OK) and not re.search(r'\b(nc|nd)\b', l)


def _relevante(titulo: str, busca: str) -> bool:
    t = titulo.lower()
    if any(p in t for p in PROIBIDO_TITULO):
        return False
    pal = _palavras(busca)
    return not pal or any(p in t for p in pal)


def _baixar(url: str, destino: Path, timeout: int = 180, cab: dict | None = None) -> Path:
    r = requests.get(url, headers=cab or UA, timeout=timeout)
    r.raise_for_status()
    destino.parent.mkdir(parents=True, exist_ok=True)     # a pasta pode ainda não existir (clipe do acervo, 10/11)
    destino.write_bytes(r.content)
    return destino


def miniatura_jpg(dados: bytes, lado: int = 512) -> bytes:
    from PIL import Image
    im = Image.open(io.BytesIO(dados)).convert('RGB')
    im.thumbnail((lado, lado))
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=82)
    return buf.getvalue()


def quadro_do_meio(clipe: Path) -> bytes | None:
    """Um quadro do meio do vídeo, para o fiscal olhar."""
    try:
        total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(clipe)],
                                     capture_output=True, text=True).stdout.strip() or 2)
        r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(total / 2), '-i', str(clipe), '-frames:v', '1', '-vf',
                            'scale=512:-2', '-f', 'image2', '-c:v', 'mjpeg', '-'], capture_output=True, check=True)
        return r.stdout or None
    except Exception:
        return None


# ───────────────────────── candidatos de cada fonte ─────────────────────────
def _commons(busca: str, video: bool) -> list[dict]:
    params = {'action': 'query', 'format': 'json', 'formatversion': 2, 'generator': 'search', 'gsrnamespace': 6,
              'gsrlimit': 15, 'gsrsearch': f'{busca} filetype:{"video" if video else "bitmap"}'}
    filtro = 'LicenseShortName|Artist|DateTimeOriginal|DateTime'
    if video:
        params.update(prop='videoinfo', viprop='url|size|mime|extmetadata|derivatives', viurlwidth=640,
                      viextmetadatafilter=filtro)
    else:
        params.update(prop='imageinfo', iiprop='url|size|mime|extmetadata', iiurlwidth=1400, iiextmetadatafilter=filtro)
    r = requests.get(COMMONS, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    return sorted(r.json().get('query', {}).get('pages', []), key=lambda p: p.get('index', 99))


def _limite(ano_max) -> int | None:
    try:
        return int(str(ano_max)[:4]) if ano_max else None
    except ValueError:
        return None


def _legenda(titulo: str, ano: int | None) -> str:
    """Etiqueta da foto real tirada do PRÓPRIO arquivo (título e data), nunca de um chute da IA. Curta (até 26 letras):
    se o nome do arquivo for "sujo" (código, parênteses, traços, palavras de catálogo), fica só o ano."""
    t = re.sub(r'[_]+', ' ', str(titulo or ''))
    t = re.sub(r'\.(jpe?g|png|tiff?)$', '', t, flags=re.I)
    t = re.sub(r'\b(cropped|crop|restored|retouched|edit(ed)?|colou?ri[sz]ed)\b', '', t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip(' -,.')
    sujo = (re.search(r'[()\[\]#/|]| - |–|\b(book|promotion|promotions|cover|page|img|dsc|file|scan|photo|foto|nby|loc|lccn)\b', t, re.I)
            or re.search(r'\d', re.sub(r'\b1[5-9]\d\d\b|\b20\d\d\b', '', t))
            or len(t.split()) > 4 or len(t) < 4)
    if sujo:
        t = ''
    else:
        t = re.sub(r',?\s*\b(1[5-9]\d\d|20\d\d)\b', '', t).strip(' ,.-–')
    if ano and t:
        t = f'{t}, {ano}'
    elif ano:
        t = str(ano)
    return t[:26].rstrip(' ,')


def candidatos_foto(busca: str, ano_max=None) -> list[dict]:
    out, lim = [], _limite(ano_max)
    try:
        for p in _commons(busca, video=False):
            info = (p.get('imageinfo') or [{}])[0]
            meta = info.get('extmetadata') or {}
            lic, ano = _txt(meta, 'LicenseShortName'), _ano(meta)
            if not _relevante(p.get('title', ''), busca) or not _licenca_ok(lic):
                continue
            if info.get('mime') not in ('image/jpeg', 'image/png') or (info.get('width') or 0) < MIN_LADO:
                continue
            if lim and ano and ano > lim + 2:          # foto moderna de outra pessoa com o mesmo nome
                continue
            titulo = p['title'].removeprefix('File:').rsplit('.', 1)[0]
            url = info.get('thumburl') or info.get('url')
            out.append({'tipo': 'foto', 'historica': True, 'url': url, 'thumb': url, 'descricao': titulo,
                        'legenda': _legenda(titulo, ano),
                        'credito': f"{titulo} — {_txt(meta, 'Artist')[:60] or 'autor desconhecido'} ({lic}), Wikimedia Commons"})
            if len(out) >= POR_FONTE:
                break
    except Exception as e:
        print(f'  [mídia/foto] {busca!r} falhou: {str(e)[:120]}')
    return out


def candidatos_arquivo(busca: str) -> list[dict]:
    out = []
    try:
        for p in _commons(busca, video=True):
            info = (p.get('videoinfo') or [{}])[0]
            meta = info.get('extmetadata') or {}
            lic = _txt(meta, 'LicenseShortName')
            if not _relevante(p.get('title', ''), busca) or not _licenca_ok(lic):
                continue
            ders = [d for d in info.get('derivatives') or [] if d.get('src') and 360 <= (d.get('height') or 0) <= 1080]
            ders.sort(key=lambda d: (-(d.get('height') or 0), 'webm' not in d.get('type', '')))   # a maior até 1080p
            url = ders[0]['src'] if ders else info.get('url')
            if not url or (not ders and (info.get('size') or 0) > 150_000_000):
                continue
            titulo = p['title'].removeprefix('File:').rsplit('.', 1)[0]
            alt = (ders[0].get('height') if ders else info.get('height')) or 0
            larg = (ders[0].get('width') if ders else info.get('width')) or 0
            out.append({'tipo': 'video', 'url': url, 'thumb': info.get('thumburl'), 'descricao': titulo,
                        'w': larg, 'h': alt, 'dur': float(info.get('duration') or 0), 'ano': _ano(meta),
                        'credito': f"{titulo} — {_txt(meta, 'Artist')[:60] or 'autor desconhecido'} ({lic}), Wikimedia Commons"})
            if len(out) >= POR_FONTE:
                break
    except Exception as e:
        print(f'  [mídia/arquivo] {busca!r} falhou: {str(e)[:120]}')
    return out


def candidatos_pixabay(busca: str) -> list[dict]:
    chave = os.getenv('PIXABAY_API_KEY')
    if not chave:
        return []
    out = []
    try:
        r = requests.get('https://pixabay.com/api/videos/', timeout=30,
                         params={'key': chave, 'q': busca[:100], 'per_page': 12, 'safesearch': 'true'})
        r.raise_for_status()
        for h in r.json().get('hits', []):
            vs = h.get('videos') or {}
            op = next((vs[k] for k in ('large', 'medium') if (vs.get(k) or {}).get('url')), None)
            if not op or (h.get('duration') or 0) < 3:
                continue
            if re.search(r'green ?screen|chroma|croma|template|intro|logo|countdown|overlay|transition|background', str(h.get('tags', '')), re.I):
                continue                                   # tela verde, vinheta, fundo genérico: nunca
            out.append({'tipo': 'video', 'url': op['url'], 'thumb': op.get('thumbnail') or (vs.get('medium') or {}).get('thumbnail'),
                        'descricao': f"pixabay #{h.get('id')}: {h.get('tags', '')}", 'credito': '',
                        'w': op.get('width') or 0, 'h': op.get('height') or 0, 'dur': float(h.get('duration') or 0)})
            if len(out) >= POR_FONTE:
                break
    except Exception as e:
        print(f'  [mídia/vídeo] {busca!r} falhou: {str(e)[:120]}')
    return out


def candidatos_nasa_video(busca: str) -> list[dict]:
    """Vídeos da NASA (domínio público, sem chave): espaço, foguetes, a Terra vista de cima, laboratório da estação."""
    out = []
    try:
        r = requests.get('https://images-api.nasa.gov/search', headers=UA, timeout=30,
                         params={'q': busca[:100], 'media_type': 'video', 'page_size': 12})
        r.raise_for_status()
        for it in (r.json().get('collection') or {}).get('items') or []:
            d = (it.get('data') or [{}])[0]
            nid = d.get('nasa_id')
            thumb = next((l.get('href') for l in it.get('links') or [] if l.get('render') == 'image'), None)
            if not nid or not thumb:
                continue
            m = requests.get(f'https://images-api.nasa.gov/asset/{nid}', headers=UA, timeout=30).json()
            hrefs = [x.get('href', '') for x in (m.get('collection') or {}).get('items') or []]
            url = next((h for suf in ('~large.mp4', '~medium.mp4', '~orig.mp4') for h in hrefs if h.endswith(suf)), None)
            if not url:
                continue
            out.append({'tipo': 'video', 'url': url.replace('http://', 'https://'), 'thumb': thumb,
                        'descricao': f"NASA: {d.get('title', '')} — {str(d.get('description', ''))[:160]}",
                        'w': 1280, 'h': 720, 'dur': 0.0, 'ano': _ano({'DateTimeOriginal': {'value': d.get('date_created', '')}}),
                        'credito': f"{d.get('title', '')} (NASA, domínio público)"})
            if len(out) >= POR_FONTE:
                break
    except Exception as e:
        print(f'  [mídia/nasa] {busca!r} falhou: {str(e)[:120]}')
    return out


def candidatos_archive(busca: str) -> list[dict]:
    """Internet Archive: filmes antigos de DOMÍNIO PÚBLICO (coleção Prelinger e afins), sem chave. Só arquivos até ~80 MB."""
    out = []
    try:
        q = (f'({busca[:80]}) AND mediatype:movies AND (collection:prelinger OR licenseurl:*publicdomain*)')
        r = requests.get('https://archive.org/advancedsearch.php', headers=UA, timeout=30,
                         params={'q': q, 'fl[]': ['identifier', 'title', 'year'], 'rows': 8, 'output': 'json'})
        r.raise_for_status()
        for doc in (r.json().get('response') or {}).get('docs') or []:
            ident = doc.get('identifier')
            if not ident:
                continue
            meta = requests.get(f'https://archive.org/metadata/{ident}', headers=UA, timeout=30).json()
            mp4 = [f for f in meta.get('files') or [] if str(f.get('name', '')).lower().endswith('.mp4')
                   and 0 < int(f.get('size') or 0) <= 80_000_000]
            if not mp4:
                continue
            f = max(mp4, key=lambda f: int(f.get('height') or 0))
            out.append({'tipo': 'video', 'url': f"https://archive.org/download/{ident}/{f['name']}",
                        'thumb': f'https://archive.org/services/img/{ident}',
                        'descricao': f"Arquivo: {doc.get('title', '')}", 'w': int(f.get('width') or 640),
                        'h': int(f.get('height') or 480), 'dur': float(f.get('length') or 0) if str(f.get('length', '')).replace('.', '', 1).isdigit() else 0.0,
                        'ano': int(doc['year']) if str(doc.get('year', '')).isdigit() else None,
                        'credito': f"{doc.get('title', '')} (Internet Archive, domínio público)"})
            if len(out) >= POR_FONTE:
                break
    except Exception as e:
        print(f'  [mídia/archive] {busca!r} falhou: {str(e)[:120]}')
    return out


def candidatos_openverse(busca: str) -> list[dict]:
    """Openverse (WordPress): milhões de imagens com licença aberta (Flickr e outros), sem chave. Só licenças que permitem uso comercial."""
    out = []
    try:
        r = requests.get('https://api.openverse.org/v1/images/', headers=UA, timeout=30,
                         params={'q': busca[:100], 'license_type': 'commercial', 'page_size': 12, 'mature': 'false'})
        r.raise_for_status()
        for h in r.json().get('results', []):
            if min(h.get('width') or 0, h.get('height') or 0) < 700 or (h.get('width') or 0) < 1000 or not h.get('url') \
                    or not _relevante(h.get('title') or busca, ''):
                continue
            lic = f"CC {str(h.get('license', '')).upper()} {h.get('license_version') or ''}".strip()
            out.append({'tipo': 'foto', 'url': h['url'], 'thumb': h.get('thumbnail') or h['url'], 'descricao': f"openverse: {h.get('title', '')}",
                        'credito': f"{h.get('title') or 'foto'} — {h.get('creator') or 'autor desconhecido'} ({lic}), via Openverse"})
            if len(out) >= POR_FONTE:
                break
    except Exception as e:
        print(f'  [mídia/openverse] {busca!r} falhou: {str(e)[:100]}')
    return out


def candidatos_pixabay_img(busca: str, tipo: str = 'photo') -> list[dict]:
    """Pixabay imagens: foto, ilustração ou vetor (licença do Pixabay: uso livre, sem crédito obrigatório)."""
    chave = os.getenv('PIXABAY_API_KEY')
    if not chave:
        return []
    out = []
    try:
        r = requests.get('https://pixabay.com/api/', timeout=30, params={'key': chave, 'q': busca[:100], 'image_type': tipo,
                                                                         'per_page': 12, 'safesearch': 'true'})
        r.raise_for_status()
        for h in r.json().get('hits', []):
            if not h.get('largeImageURL') or (h.get('imageWidth') or 0) < 800:
                continue
            if re.search(r'background|template|logo|frame|banner|texture|pattern|wallpaper', str(h.get('tags', '')), re.I):
                continue
            out.append({'tipo': 'foto', 'url': h['largeImageURL'], 'thumb': h.get('webformatURL') or h['largeImageURL'],
                        'descricao': f"pixabay {tipo} #{h.get('id')}: {h.get('tags', '')}", 'credito': ''})
            if len(out) >= POR_FONTE:
                break
    except Exception as e:
        print(f'  [mídia/pixabay-{tipo}] {busca!r} falhou: {str(e)[:100]}')
    return out


def _todas(fontes: list) -> list[dict]:
    """Consulta várias fontes AO MESMO TEMPO e intercala os resultados (uma de cada fonte por vez)."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(len(fontes) or 1) as ex:
        listas = list(ex.map(lambda f: f(), fontes))
    out, vistos = [], set()
    for i in range(max((len(l) for l in listas), default=0)):
        for l in listas:
            if i < len(l) and l[i]['url'] not in vistos:
                vistos.add(l[i]['url']); out.append(l[i])
    return out


_PARADAS_EN = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'with', 'and', 'shot', 'close', 'up', 'wide', 'medium', 'angle', 'view',
               'cinematic', 'lighting', 'light', 'vertical', 'composition', 'scene', 'style', 'photorealistic', 'realistic', 'film', 'still'}


def _busca_do_prompt(c: dict) -> str:
    texto = c.get('busca') or c.get('prompt_imagem') or c.get('cenario') or ''
    pal = [w for w in re.findall(r'[a-zA-Z]+', texto) if w.lower() not in _PARADAS_EN and len(w) > 2]
    return ' '.join(pal[:5])


# ───────────────────────── fiscal: o modelo principal do Gemini confere (sim/não) ─────────────────────────
PROMPT_FISCAL = cofre.prompt('PROMPT_FISCAL')

NOTA_MIN = 7


def fiscal(fala: str, contexto: str, pedido: str, miniaturas: list[bytes]) -> int | None:
    """Índice da imagem aprovada, None se todas forem reprovadas. Usa o modelo PRINCIPAL (o "lite" aprovava imagem errada).
    Se o fiscal estiver fora do ar, fica com a primeira opção (melhor do que nada na tela)."""
    if not miniaturas:
        return None
    from .orcamento import sobra
    if not os.getenv('GEMINI_API_KEY') or sobra() < 40:
        return 0                                     # sem fiscal (ou sem tempo): fica com a primeira opção
    try:
        from . import gemini
        r = gemini.json_visao(PROMPT_FISCAL.format(fala=fala.replace('*', ''), contexto=contexto, pedido=pedido,
                                                   n=len(miniaturas)), miniaturas, leve=False)
        if isinstance(r, list):
            r = r[0] if r else {}
        av = {}
        for a in r.get('avaliacoes') or []:
            try:
                av[int(a.get('i'))] = a
            except (TypeError, ValueError, AttributeError):
                pass
        e = r.get('escolha')
        if e is None or not str(e).lstrip('-').isdigit() or not (0 <= int(e) < len(miniaturas)):
            print(f"  [fiscal] reprovou todas: {str(r.get('motivo', ''))[:100]}")
            return None
        e = int(e)
        a = av.get(e, {})
        mostra = a.get('mostra', True)
        if isinstance(mostra, str):
            mostra = mostra.strip().lower() in ('sim', 'true', 'yes', 's')
        try:
            nota = float(a.get('nota', NOTA_MIN))
        except (TypeError, ValueError):
            nota = NOTA_MIN
        if not mostra or nota < NOTA_MIN:
            print(f"  [fiscal] a escolhida não passa (mostra={mostra}, nota {nota:.0f}): {str(r.get('motivo', ''))[:80]}")
            return None
        return e
    except Exception as ex:
        print(f'  [fiscal] indisponível ({str(ex)[:80]}); fico com a primeira opção')
        return 0


def _miniatura_de(c: dict) -> bytes | None:
    try:
        if not c.get('thumb'):
            return None
        r = requests.get(c['thumb'], headers=UA, timeout=30)
        r.raise_for_status()
        return miniatura_jpg(r.content)
    except Exception:
        return None


# ───────────────────────── quadros de vídeo para o render ─────────────────────────
# cor única do vídeo (fotos, vídeos e imagens de IA com o mesmo "look" de documentário): contraste leve, cor um pouco
# contida, sombras levemente frias, altas luzes quentes e grão de filme
COR_FFMPEG = 'eq=contrast=1.06:saturation=0.9,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.03,noise=alls=7:allf=t'


def quadros(clipe: Path, dur: float, pasta: Path, fps: int = 30, desloc: float = 0.0, moldura: bool = False) -> int:
    """Converte o trecho do vídeo que vai aparecer em quadros verticais 720x1280 (o render mostra um por vez).
    desloc: segundos já usados por um plano anterior da mesma ideia (o 2º plano continua o vídeo, não repete).
    moldura=True: vídeo deitado que vai DENTRO da moldura — quadros com 960 px de largura, SEM cortar (o corte 9:16
    jogava fora 70% da imagem e esticava o resto)."""
    pasta.mkdir(parents=True, exist_ok=True)
    total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(clipe)],
                                 capture_output=True, text=True).stdout.strip() or 0)
    precisa = dur + 0.8
    ini = (1.0 if total > precisa + desloc + 2.5 else 0.0) + desloc     # pula o comecinho (às vezes é uma tela preta)
    if total > 120 and total > precisa + desloc + 40:                    # filme longo (arquivo antigo): pula os créditos
        ini = total * 0.25 + desloc
    if total and total - ini < precisa:
        ini = max(0.0, total - precisa) if total > precisa else 0.0
    filtro = (f'fps={fps},scale=960:-2,{COR_FFMPEG}' if moldura else
              f'fps={fps},scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,{COR_FFMPEG}')
    fonte = clipe
    if total and total - ini < precisa:                  # vídeo mais curto que a cena: vai e volta (sem congelar)
        fonte = pasta / 'pingpong.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(clipe), '-an', '-filter_complex',
                        f'[0:v]{filtro},split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]', '-map', '[v]',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', str(fonte)], check=True)
        filtro, ini = 'null', 0.0
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *(['-stream_loop', '-1'] if fonte != clipe else []), '-ss', str(ini),
                    '-i', str(fonte), '-an', '-vf', filtro, '-frames:v', str(int(precisa * fps)),
                    '-q:v', '3', str(pasta / 'f_%04d.jpg')], check=True)
    return len(list(pasta.glob('f_*.jpg')))


# ───────────────────────── tudo junto ─────────────────────────
def obter(cenas: list[dict], pasta: Path, contexto: str = '') -> tuple[dict, list[str], list[str]]:
    """Para cada plano: junta candidatos reais, o fiscal escolhe, baixa o escolhido.
    Devolve ({id: {'tipo','arq'}}, ids que ainda precisam de imagem de IA, créditos)."""
    pasta.mkdir(parents=True, exist_ok=True)
    achou, falta, creditos, usos = {}, [], [], {}
    for c in cenas:
        iid = c.get('imagem')
        if not iid or iid in achou or iid in falta or c.get('tipo') == 'fechamento':
            continue
        if (c.get('tipo') == 'mapa' and c.get('pontos')) or c.get('tipo') == 'simulacao':
            continue
        tipo, busca = (c.get('midia') or 'ia'), (c.get('busca') or '').strip()
        cands = []
        if busca:      # todas as fontes que servem para esse tipo de plano, ao mesmo tempo; o fiscal escolhe a melhor
            ano = c.get('ano_max')
            if tipo == 'foto':
                cands = _todas([lambda: candidatos_foto(busca, ano), lambda: candidatos_openverse(busca),
                                lambda: candidatos_pixabay_img(busca, 'photo')])
            elif tipo in ('arquivo', 'video'):
                cands = _todas([lambda: candidatos_arquivo(busca), lambda: candidatos_pixabay(busca)] if tipo == 'arquivo'
                               else [lambda: candidatos_pixabay(busca), lambda: candidatos_arquivo(busca)])
        cands = [x for x in cands if usos.get(x['url'], 0) < 2]          # a mesma foto/vídeo no máximo 2 vezes no vídeo
        cands = cands[:6]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(6) as ex:
            mm = list(ex.map(_miniatura_de, cands))
        mins = [(k, m) for k, m in enumerate(mm) if m]
        escolha = fiscal(c.get('fala_ideia') or c.get('fala', ''), contexto, f'{tipo}: {busca}', [m for _, m in mins]) if mins else None
        if escolha is None:
            falta.append(iid)
            continue
        cand = cands[mins[escolha][0]]
        try:
            ext = '.jpg' if cand['tipo'] == 'foto' else '.' + cand['url'].rsplit('.', 1)[-1].split('?')[0][:5]
            arq = _baixar(cand['url'], pasta / f'm_{iid}{ext}', cab=UA if 'wikimedia' in cand['url'] else {})
            # só foto de acervo histórico ganha a etiqueta "FOTO REAL"; foto de banco/ilustração entra como imagem comum
            achou[iid] = {'tipo': 'video' if cand['tipo'] == 'video' else ('foto' if cand.get('historica') else 'img'), 'arq': arq,
                          'legenda': cand.get('legenda', '')}
            usos[cand['url']] = usos.get(cand['url'], 0) + 1
            if cand.get('credito'):
                creditos.append(cand['credito'])
            print(f"  [mídia/{tipo}] {busca!r} → {cand['descricao'][:70]}")
        except Exception as e:
            print(f'  [mídia] não consegui baixar ({str(e)[:80]}); vai de IA')
            falta.append(iid)
    return achou, falta, creditos


def resgate(cenas: list[dict], ids: list[str], pasta: Path, contexto: str = '') -> tuple[dict, list[str]]:
    """Plano que ficou sem imagem de IA (cota acabou, recusa...): procura ilustração, vetor e foto em todas as fontes ao mesmo tempo."""
    achou, creditos = {}, []
    pasta.mkdir(parents=True, exist_ok=True)
    for c in cenas:
        iid = c.get('imagem')
        if iid not in ids or iid in achou:
            continue
        q = _busca_do_prompt(c)
        if not q:
            continue
        cands = _todas([lambda: candidatos_pixabay_img(q, 'illustration'), lambda: candidatos_pixabay_img(q, 'photo'),
                        lambda: candidatos_openverse(q), lambda: candidatos_pixabay_img(q, 'vector')])[:6]
        mins = [(k, m) for k, m in ((k, _miniatura_de(x)) for k, x in enumerate(cands)) if m]
        e = fiscal(c.get('fala_ideia') or c.get('fala', ''), contexto, q, [m for _, m in mins]) if mins else None
        if e is None:
            continue
        cand = cands[mins[e][0]]
        try:
            arq = _baixar(cand['url'], pasta / f'r_{iid}.jpg', cab={})
            achou[iid] = arq
            if cand.get('credito'):
                creditos.append(cand['credito'])
            print(f"  [resgate] {q!r} → {cand['descricao'][:70]}")
        except Exception as ex:
            print(f'  [resgate] falhou: {str(ex)[:80]}')
    return achou, creditos


_SESSAO_REC = None


def recorte(img: Path) -> Path | None:
    """Recorta o personagem/objeto principal (fundo transparente) para a animação em camadas: o fundo e o recorte se
    movem em velocidades diferentes, dando profundidade. Usa o rembg (modelo pequeno u2netp, roda no próprio GitHub)."""
    global _SESSAO_REC
    import subprocess, sys
    try:
        from rembg import remove, new_session
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'rembg[cpu]'], check=True, timeout=600)
        from rembg import remove, new_session
    if _SESSAO_REC is None:
        _SESSAO_REC = new_session('u2netp')
    from PIL import Image
    saida = img.with_name(img.stem + '-rec.png')
    im = Image.open(io.BytesIO(remove(img.read_bytes(), session=_SESSAO_REC))).convert('RGBA')
    a = im.getchannel('A')
    cobertura = sum(1 for v in a.resize((64, 112)).getdata() if v > 128) / (64 * 112)
    if not (0.04 < cobertura < 0.75):          # recorte vazio ou "pegou a imagem inteira": não serve para camadas
        return None
    im.save(saida)
    return saida


# ───────────────────────── cor única + grão (pré-processado: não pesa no render) ─────────────────────────
def _lut(desl_sombra: float, desl_luz: float):
    return [max(0, min(255, int(round(i + desl_sombra * (1 - i / 255) ** 2 + desl_luz * (i / 255) ** 2)))) for i in range(256)]


def graduar(img: Path, lado_max: int = 1800) -> Path:
    """Aplica o mesmo 'look' em todas as imagens do vídeo (foto real, banco ou IA): contraste leve, cor contida,
    sombras frias, luzes quentes e grão fino. Devolve um arquivo novo; se falhar, devolve o original."""
    try:
        from PIL import Image, ImageEnhance
        saida = img.with_name(img.stem + '-g.jpg')
        if saida.exists():
            return saida
        im = Image.open(img).convert('RGB')
        if max(im.size) > lado_max:
            im.thumbnail((lado_max, lado_max))
        im = ImageEnhance.Contrast(im).enhance(1.06)
        im = ImageEnhance.Color(im).enhance(0.9)
        r, g, b = im.split()
        r, b = r.point(_lut(-6, 8)), b.point(_lut(9, -8))
        im = Image.merge('RGB', (r, g, b))
        try:
            import numpy as np
            a = np.asarray(im).astype(np.int16)
            ruido = np.random.default_rng(7).normal(0, 6, a.shape[:2])[..., None]
            im = Image.fromarray(np.clip(a + ruido, 0, 255).astype(np.uint8))
        except ImportError:
            pass
        im.save(saida, 'JPEG', quality=92)
        return saida
    except Exception as e:
        print(f'  [cor] não consegui tratar {img.name}: {str(e)[:80]}')
        return img


def fundo(img: Path, estilo: str = 'estudio') -> Path:
    """Fundo atrás da foto/vídeo em moldura: ESTÚDIO ESCURO — quase preto, com uma luz suave atrás da moldura na cor
    dominante da própria foto e um grão leve (como documentário). Antes: a foto desfocada, que atrás de gravura ou foto
    cinza virava uma mancha bege sem forma (10/11)."""
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageStat
        saida = img.with_name(img.stem + f'-fundo-{estilo}.jpg')
        if saida.exists():
            return saida
        W, H = 540, 960
        if estilo == 'ceu':                                     # B: céu noturno (temas de espaço) — combina com os gráficos
            import random
            rnd = random.Random(img.name)
            im = Image.new('RGB', (W, H), (6, 12, 26))
            d = ImageDraw.Draw(im)
            for k in range(0, W, 45):
                d.line([(k, 0), (k, H)], fill=(16, 27, 48))
            for k in range(0, H, 45):
                d.line([(0, k), (W, k)], fill=(16, 27, 48))
            for _ in range(110):
                x, y, rr = rnd.randrange(W), rnd.randrange(H), rnd.choice([0.6, 0.8, 1.2])
                c = rnd.randint(150, 230)
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(c, c + 8 if c < 247 else c, 255))
            brilho = Image.new('L', (W, H), 0)
            ImageDraw.Draw(brilho).ellipse([60, 170, W - 60, 660], fill=255)
            brilho = brilho.filter(ImageFilter.GaussianBlur(100))
            im = Image.composite(Image.new('RGB', (W, H), (28, 56, 112)), im, brilho)
            im.save(saida, 'JPEG', quality=90)
            return saida
        r, g, b = (ImageStat.Stat(Image.open(img).convert('RGB').resize((48, 48))).mean[:3])
        cinza = (r + g + b) / 3
        sat = 1.6                                               # puxa a cor (gravura cinza ganha um tom quente)
        r, g, b = (cinza + (c - cinza) * sat for c in (r, g, b))
        if max(r, g, b) - min(r, g, b) < 12:                    # foto sem cor nenhuma: luz âmbar suave (combina com a marca)
            r, g, b = cinza * 1.05 + 20, cinza * 0.92 + 10, cinza * 0.75
        # escuro UNIFORME com um leve degradê vertical na cor da foto (antes: uma luz oval que virava mancha, 10/11)
        topo = tuple(int(max(0, min(255, c * 0.16 + 10))) for c in (r, g, b))
        fim = (7, 8, 11)
        im = Image.new('RGB', (W, H))
        d = ImageDraw.Draw(im)
        for y in range(H):
            k = min(1.0, max(0.0, (y - 120) / (H * 0.85)))
            d.line([(0, y), (W, y)], fill=tuple(int(topo[i] + (fim[i] - topo[i]) * k) for i in range(3)))
        grao = Image.effect_noise((W, H), 22).convert('RGB')
        im = Image.blend(im, grao, 0.05)
        im.save(saida, 'JPEG', quality=90)
        return saida
    except Exception:
        return img


ESPACO = ('espaço', 'espacial', 'estrela', 'meteoro', 'meteorito', 'planeta', 'galáxia', 'galaxia', 'universo', 'cosmo',
          'cometa', 'asteroide', 'astronauta', 'nasa', 'órbita', 'orbita', 'buraco negro', 'eclipse', 'constelação',
          'lua ', ' lua', 'marte', 'júpiter', 'saturno', 'vênus', 'mercúrio', 'netuno', 'urano', 'plutão', 'sol ', 'solar',
          'satélite', 'foguete', 'telescópio', 'aurora', 'céu', 'leônidas', 'via láctea', 'big bang', 'supernova')


def estilo_fundo(*textos: str) -> str:
    """B ('ceu') para tema de espaço/céu; A ('estudio') para todo o resto. Decide pelo título e pela pergunta do tema."""
    t = ' '.join(str(x or '') for x in textos).lower()
    t = t.replace('lua de mel', '')
    return 'ceu' if any(re.search(rf'(?<![\wà-ú]){re.escape(k.strip())}s?(?![\wà-ú])', t) for k in ESPACO) else 'estudio'


def neutra(img: Path) -> Path:
    """Fundo neutro: a imagem desfocada e escura (para um plano que não tem imagem certa; aparece a palavra-chave grande
    por cima). Melhor do que mostrar uma imagem errada."""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        saida = img.with_name(img.stem + '-neutra.jpg')
        if saida.exists():
            return saida
        im = Image.open(img).convert('RGB')
        im.thumbnail((720, 720))
        im = im.filter(ImageFilter.GaussianBlur(26))
        im = ImageEnhance.Brightness(im).enhance(0.45)
        im = ImageEnhance.Color(im).enhance(0.7)
        im.save(saida, 'JPEG', quality=88)
        return saida
    except Exception:
        return img
