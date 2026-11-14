"""COLETA CONTROLADA (Evidência V1, experimental) — roda UMA vez no GitHub Actions.

1. Metadados originais de cada imagem dos casos (Commons, NASA, páginas) — resposta BRUTA guardada, nada completado.
2. Download das imagens disponíveis (miniatura ≤ 1024 px).
3. Gemini com os prompts CEGOS do cofre (ramo evidencia-v1): por domínio, 1 catálogo + 1 casamento.
   Limite rígido: MAX_CHAMADAS. Um modelo, uma chave, SEM nova tentativa: erro é registrado e a coleta segue.

Saída: saida_evidencia/ (registros.json, imagens/, gemini/, log.txt). O workflow cifra e publica.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
OUT = RAIZ / 'saida_evidencia'
UA = {'User-Agent': 'coringa-evidencia-coleta/1.0 (pesquisa; contato via GitHub Heitor2404)'}
COMMONS = 'https://commons.wikimedia.org/w/api.php'
MAX_CHAMADAS = 18
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    LOG.append(s)


# ─── o que coletar: (domínio, chave da imagem no caso) → como achar ───
# commons: título exato · busca: pesquisa no Commons (registra o título achado) · nasa: nasa_id · local: arquivo do repositório
# pagina: og:image da página · indisponivel: não há arquivo real a coletar (imagem hipotética do gabarito)
EG = 'tests/piloto_ever_given/img/'
ALVOS = {
 'naval': {
  'a6_commons': [('local', EG + 'a11-g.jpg'), ('commons', "File:Container Ship 'Ever Given' stuck in the Suez Canal, Egypt - March 24th, 2021 cropped.jpg")],
  'a9_openverse': [('local', EG + 'a22-g.jpg')],
  'a8_iss': [('commons', 'File:Ever Given in Suez Canal viewed from ISS.jpg')],
  'a2_aster': [('local', EG + 'a3-g.jpg'), ('commons', 'File:Suez Canal Crisis (ASTER).jpg')],
  'a1_roterda': [('local', EG + 'a1-g.jpg'), ('commons', 'File:IMO 9811000 EVER GIVEN (09).jpg')],
  'a12_2020': [('local', EG + 'a27-g.jpg'), ('commons', 'File:EVER GIVEN (49643352087).jpg')],
  'a10_outro_navio': [('local', EG + 'a23-g.jpg'), ('busca', 'Ever Given container ship NOAA')],
  'a0_diagrama': [('local', EG + 'a0-g.jpg'), ('commons', 'File:SUEZCANAL SECTION.jpg')],
  'a5_arabe': [('local', EG + 'a10-g.jpg'), ('busca', 'SUEZCANAL SECTION-ar')],
  'a11_igreja': [('busca', 'A Church beside the Suez Canal')],
  'a14_placa': [('busca', 'Sign about delivery bottlenecks due to March 2021 Suez Canal obstruction at German supermarket')]},
 'geologia': {
  'a25_rosenquist': [('busca', 'Mount St. Helens Rosenquist landslide 1980')],
  'a18_post': [('busca', 'MSH80 eruption mount st helens 05-18-80')],
  'a23_animacao': [('busca', 'Mount St Helens landslide animation')],
  'a0_memorial': [('busca', 'Johnston Ridge memorial Mount St. Helens victims')]},
 'espaco_apollo11': {
  'as11_40_5903': [('commons', 'File:Aldrin Apollo 11.jpg')],
  'dvids_5903': [('indisponivel', 'mesma foto via DVIDS: API da DVIDS não usada pelo acervo')],
  's69_39525': [('nasa', 'S69-39525')], 'nhq2019': [('nasa', 'NHQ201907190146')], 'as11_36_5355': [('nasa', 'as11-36-5355')],
  'insignia': [('commons', 'File:Apollo 11 insignia.png')], 'lua_cheia': [('indisponivel', 'hipotética')]},
 'historia_muro_berlim': {
  'b1110_018': [('commons', 'File:Bundesarchiv Bild 183-1989-1110-018, Berlin, Checkpoint Charlie, Nacht des Mauerfalls.jpg')],
  'b1104_006': [('commons', 'File:Bundesarchiv Bild 183-1989-1104-006, Berlin, Demonstration.jpg')],
  'b1222_034': [('commons', 'File:Bundesarchiv Bild 183-1989-1222-034, Berlin, Grenzöffnung Brandenburger Tor.jpg')],
  'b1118_018': [('commons', 'File:Bundesarchiv Bild 183-1989-1118-018, Berlin, Grenzübergang Bornholmer Straße.jpg')],
  'b1109_030': [('busca', 'Bundesarchiv Bild 183-1989-1109-030 Schabowski Pressekonferenz')]},
 'engenharia_tacoma': {
  'commons_upload': [('commons', 'File:Tacoma-narrows-bridge-collapse.jpg')],
  'loc_46682': [('busca', 'Tacoma Narrows Bridge collapse 1940 Library of Congress')],
  'uw_290_52': [('indisponivel', 'acervo da University of Washington: sem API usada pelo acervo')],
  'uw_290_33': [('busca', 'Tacoma Narrows Bridge twisting 1940')],
  'fragmento': [('busca', 'Tacoma Narrows Bridge 1940 steel fragment')]},
 'biologia_metamorfose': {
  'jd_92417': [('pagina', 'https://www.jungledragon.com/image/92417/monarch_chrysalis_-_danaus_plexippus.html')],
  'jd_63251': [('pagina', 'https://www.jungledragon.com/image/63251/monarch_caterpillar_j-ing_-_danaus_plexippus.html')],
  'jd_92418': [('pagina', 'https://www.jungledragon.com/image/92418/empty_monarch_chrysalis_-_danaus_plexippus.html')],
  'merian': [('busca', 'Metamorphosis insectorum Surinamensium plate')]},
 'clima_katrina': {
  'fema_15008': [('commons', 'File:FEMA - 15008 - Photograph by Jocelyn Augustino taken on 08-30-2005 in Louisiana.jpg')],
  'fema_14891': [('commons', 'File:FEMA - 14891 - Photograph by Jocelyn Augustino taken on 08-30-2005 in Louisiana.jpg')],
  'fema_17284': [('commons', 'File:FEMA - 17284 - Photograph by Jocelyn Augustino taken on 08-30-2005 in Louisiana.jpg')]},
 'negativo_alexandria': {
  'goll_1876': [('busca', 'burning of the Library of Alexandria Hermann Göll')],
  'von_corven': [('busca', 'Ancientlibraryalex Von Corven Great Library of Alexandria')]},
}


def _get(url, **params):
    r = requests.get(url, params=params or None, headers=UA, timeout=40)
    r.raise_for_status()
    return r


def commons_info(titulo: str) -> dict | None:
    j = _get(COMMONS, action='query', titles=titulo, prop='imageinfo|categories', iiprop='url|size|mime|extmetadata|timestamp',
             iiurlwidth=1024, cllimit=50, format='json', formatversion=2).json()
    p = (j.get('query', {}).get('pages') or [{}])[0]
    return None if p.get('missing') or not p.get('imageinfo') else p


def commons_busca(q: str) -> str | None:
    j = _get(COMMONS, action='query', list='search', srsearch=f'{q} filetype:bitmap', srnamespace=6, srlimit=1, format='json', formatversion=2).json()
    h = j.get('query', {}).get('search') or []
    return h[0]['title'] if h else None


def nasa(nid: str) -> dict | None:
    j = _get('https://images-api.nasa.gov/search', nasa_id=nid).json()
    it = (j.get('collection', {}).get('items') or [None])[0]
    return it


def pagina_og(url: str) -> str | None:
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', _get(url).text)
    return m.group(1) if m else None


def baixar(url: str, dest: Path) -> bool:
    from PIL import Image
    im = Image.open(io.BytesIO(_get(url).content)).convert('RGB')
    im.thumbnail((1024, 1024))
    im.save(dest, 'JPEG', quality=88)
    return True


def coletar() -> dict:
    regs = {}
    (OUT / 'imagens').mkdir(parents=True, exist_ok=True)
    for dom, imgs in ALVOS.items():
        for chave, modos in imgs.items():
            r = {'dominio': dom, 'imagem': chave, 'tentativas': [], 'arquivo': None, 'bruto': None}
            dest = OUT / 'imagens' / f'{dom}__{chave}.jpg'
            for tipo, alvo in modos:
                try:
                    if tipo == 'indisponivel':
                        r['tentativas'].append({'tipo': tipo, 'motivo': alvo}); continue
                    if tipo == 'local':
                        from PIL import Image
                        Image.open(RAIZ / alvo).convert('RGB').save(dest, 'JPEG', quality=88)
                        r['arquivo'] = dest.name; r['tentativas'].append({'tipo': tipo, 'ok': alvo}); continue
                    if tipo in ('commons', 'busca'):
                        titulo = alvo if tipo == 'commons' else commons_busca(alvo)
                        r['tentativas'].append({'tipo': tipo, 'consulta': alvo, 'titulo_achado': titulo})
                        p = commons_info(titulo) if titulo else None
                        if not p:
                            r['tentativas'][-1]['erro'] = 'não encontrado'; continue
                        r['bruto'] = {'fonte': 'Commons', 'pagina': p}
                        if not r['arquivo']:
                            info = p['imageinfo'][0]
                            baixar(info.get('thumburl') or info['url'], dest); r['arquivo'] = dest.name
                    elif tipo == 'nasa':
                        it = nasa(alvo)
                        r['tentativas'].append({'tipo': tipo, 'consulta': alvo, 'achou': bool(it)})
                        if it:
                            r['bruto'] = {'fonte': 'NASA', 'item': it}
                            href = next((l['href'] for l in it.get('links') or [] if l.get('render') == 'image'), None)
                            if href:
                                baixar(href.replace('~thumb', '~medium'), dest); r['arquivo'] = dest.name
                    elif tipo == 'pagina':
                        og = pagina_og(alvo)
                        r['tentativas'].append({'tipo': tipo, 'consulta': alvo, 'og_image': og})
                        r['bruto'] = {'fonte': 'pagina', 'url': alvo, 'og_image': og}
                        if og:
                            baixar(og, dest); r['arquivo'] = dest.name
                except Exception as e:
                    r['tentativas'].append({'tipo': tipo, 'consulta': alvo, 'erro': str(e)[:200]})
                time.sleep(0.5)
            regs[f'{dom}/{chave}'] = r
            log(f'[coleta] {dom}/{chave}: arquivo={r["arquivo"]} registro={"sim" if r["bruto"] else "não"}')
    return regs


# ─── Gemini cego: uma chamada por pedido, sem nova tentativa ───
CHAMADAS = 0


def gemini_uma_vez(prompt: str, imagens: list[bytes], modelo: str) -> dict:
    global CHAMADAS
    if CHAMADAS >= MAX_CHAMADAS:
        return {'erro': f'limite de {MAX_CHAMADAS} chamadas atingido: não chamei'}
    CHAMADAS += 1
    from google import genai
    from google.genai import types
    cli = genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options=types.HttpOptions(timeout=240_000))
    partes = []
    for k, img in enumerate(imagens):
        partes += [f'IMAGEM {k}:', types.Part.from_bytes(data=img, mime_type='image/jpeg')]
    partes.append(prompt)
    t = time.time()
    try:
        r = cli.models.generate_content(model=modelo, contents=partes,
                                        config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.2))
        return {'modelo': modelo, 'segundos': round(time.time() - t, 1), 'texto': r.text}
    except Exception as e:
        return {'modelo': modelo, 'erro': str(e)[:400]}


def visao(regs: dict) -> dict:
    from src import cofre, gemini
    p_cat, p_cas = cofre.prompt('PROMPT_CATALOGO_EVIDENCIA'), cofre.prompt('PROMPT_CASAR_EVIDENCIA')
    if p_cat.startswith('[') or p_cas.startswith('['):
        log('[gemini] prompts cegos indisponíveis no cofre: nenhuma chamada'); return {}
    leve, principal = gemini.MODELOS_LEVES[0], gemini.MODELOS_TEXTO[0]
    fix = {}
    for arq in ('desenvolvimento.json', 'reservado.json'):
        d = json.loads((RAIZ / 'tests' / 'evidencia' / arq).read_text(encoding='utf-8'))
        fix.update(d['dominios'])
    out = {}
    (OUT / 'gemini').mkdir(exist_ok=True)
    for dom in ALVOS:
        itens = [(k.split('/', 1)[1], r['arquivo']) for k, r in regs.items() if r['dominio'] == dom and r['arquivo']]
        if not itens:
            log(f'[gemini] {dom}: nenhuma imagem real coletada: sem chamada'); continue
        imgs = [(OUT / 'imagens' / a).read_bytes() for _, a in itens]
        cat = gemini_uma_vez(p_cat.format(n=len(imgs)), imgs, leve)
        acs = '\n'.join(f"{k}: elemento={a['bruto'].get('sujeito')}; ação={a['bruto'].get('acao')}; antes={a['bruto'].get('estado_inicial') or '-'}; "
                        f"depois={a['bruto'].get('estado_final') or '-'}" for k, a in fix[dom]['acontecimentos'].items())
        cas = gemini_uma_vez(p_cas.format(n=len(imgs), primeiro='0', acontecimentos=acs), imgs, principal)
        out[dom] = {'ordem_das_imagens': [k for k, _ in itens], 'catalogo': cat, 'casamento': cas}
        (OUT / 'gemini' / f'{dom}.json').write_text(json.dumps(out[dom], ensure_ascii=False, indent=1), encoding='utf-8')
        log(f'[gemini] {dom}: {len(imgs)} imagens · catálogo {"ok" if "texto" in cat else cat.get("erro")} · casamento {"ok" if "texto" in cas else cas.get("erro")}')
        time.sleep(5)
    log(f'[gemini] chamadas feitas: {CHAMADAS} de no máximo {MAX_CHAMADAS}')
    return out


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    regs = coletar()
    (OUT / 'registros.json').write_text(json.dumps(regs, ensure_ascii=False, indent=1), encoding='utf-8')
    if '--sem-gemini' not in sys.argv:
        visao(regs)
    (OUT / 'log.txt').write_text('\n'.join(LOG), encoding='utf-8')
