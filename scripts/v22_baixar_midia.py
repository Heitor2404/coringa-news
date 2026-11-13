"""Baixa a mídia de teste do manifesto (roda no GitHub Actions, que tem internet). Sem nada pago.

Para cada item grava <id>.<ext> e <id>.json (URL de origem, licença, autor e crédito segundo a API do Commons/LoC,
dimensões, fps, duração). Vídeo: trecho curto reencodado (H.264, mesma taxa de quadros e orientação). Áudio: trecho
em Opus + alinhamento por palavra com faster-whisper (modelo pequeno, gratuito) em <id>.palavras.json.
Uso: python scripts/v22_baixar_midia.py tests/midia/manifesto.json <saida>
"""
import json, re, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

UA = {'User-Agent': 'coringa-news-teste/1.0 (github.com/Heitor2404/coringa-news; midia de teste)'}
LIVRES = re.compile(r'(public domain|pd|cc0|cc[- ]by|no known restrictions)', re.I)


def get(url, dest=None, limite=400_000_000):
    for t in range(7):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                if dest is None:
                    return r.read()
                with open(dest, 'wb') as f:
                    n = 0
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        n += len(b); f.write(b)
                        if n > limite:
                            break
                return dest
        except Exception as e:
            print('  tentativa', t, e); time.sleep(min(90, 8 * 2 ** t))   # o upload.wikimedia.org limita a taxa
    raise RuntimeError('falhou: ' + url)


def api(params):
    q = urllib.parse.urlencode({**params, 'format': 'json'})
    return json.loads(get('https://commons.wikimedia.org/w/api.php?' + q))


def info_commons(titulo, largura=None):
    p = {'action': 'query', 'titles': 'File:' + titulo, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata'}
    if largura:
        p['iiurlwidth'] = largura
    pg = next(iter(api(p)['query']['pages'].values()))
    ii = pg['imageinfo'][0]; em = ii.get('extmetadata', {})
    val = lambda k: re.sub('<[^>]+>', '', (em.get(k) or {}).get('value', '')).strip()
    return {'titulo': titulo, 'pagina': ii.get('descriptionurl'), 'url': ii['url'], 'url_reduzida': ii.get('thumburl'),
            'largura': ii.get('width'), 'altura': ii.get('height'), 'mime': ii.get('mime'), 'licenca': val('LicenseShortName'),
            'licenca_url': val('LicenseUrl'), 'autor': val('Artist')[:200], 'credito': val('Credit')[:200], 'termos': val('UsageTerms')[:200],
            'descricao': val('ImageDescription')[:300], 'data': val('DateTimeOriginal')[:40]}


def ffprobe(arq):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,sample_rate,channels:format=duration',
                        '-of', 'json', str(arq)], capture_output=True, text=True)
    return json.loads(r.stdout or '{}')


def main():
    man = json.loads(Path(sys.argv[1]).read_text()); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    tmp = out / '_bruto'; tmp.mkdir(exist_ok=True)
    rel = []
    for it in man['itens']:
        i = it['id']; print('==', i, flush=True)
        try:
            if it['tipo'] == 'busca':
                r = api({'action': 'query', 'generator': 'search', 'gsrsearch': it['busca'] + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 15,
                         'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata', 'iiurlwidth': 2000})
                cands = sorted(r.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
                esc = None
                for c in cands:
                    ii = (c.get('imageinfo') or [{}])[0]; lic = ((ii.get('extmetadata') or {}).get('LicenseShortName') or {}).get('value', '')
                    if ii.get('width', 0) >= 1600 and LIVRES.search(lic) and 'nc' not in lic.lower() and 'nd' not in lic.lower().split():
                        esc = c['title'][5:]; break
                if not esc:
                    raise RuntimeError('nenhum resultado livre ≥ 1600 px')
                meta = info_commons(esc, 2000); arq = out / f'{i}.jpg'; get(meta['url_reduzida'] or meta['url'], arq)
            elif it['tipo'] == 'imagem':
                meta = info_commons(it['commons'])
                ext = Path(urllib.parse.urlparse(meta['url']).path).suffix.lower()
                bruto = tmp / f'{i}{ext}'; get(meta['url'], bruto)
                arq = out / f'{i}.jpg'
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(bruto), '-q:v', '2', str(arq)], check=True)
            elif it['tipo'] == 'loc':
                j = json.loads(get(it['loc'].rstrip('/') + '/?fo=json'))
                urls = [u for r_ in j.get('resources', []) for f in (r_.get('files') or []) for x in f if isinstance(x, dict) and str(x.get('mimetype', '')).startswith('image/') for u in [x]]
                maior = max(urls, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0)) if urls else None
                if not maior:
                    raise RuntimeError('sem imagem no registro')
                bruto = tmp / (i + Path(urllib.parse.urlparse(maior['url']).path).suffix); get(maior['url'], bruto)
                arq = out / f'{i}.jpg'
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(bruto), '-q:v', '2', str(arq)], check=True)
                item = j.get('item', {})
                meta = {'pagina': it['loc'], 'url': maior['url'], 'largura': maior.get('width'), 'altura': maior.get('height'),
                        'titulo': item.get('title'), 'licenca': '; '.join(item.get('rights_advisory') or item.get('rights') or [])[:300] or 'ver página',
                        'data': item.get('date'), 'credito': 'Library of Congress, Prints & Photographs Division'}
            elif it['tipo'] == 'video':
                meta = info_commons(it['commons'])
                if it.get('streaming'):        # arquivo grande: ffmpeg busca só o trecho por HTTP (cabeçalho de user-agent)
                    bruto = meta['url']
                else:
                    bruto = tmp / f'{i}.webm'; get(meta['url'], bruto, limite=200_000_000)
                arq = out / f'{i}.mp4'
                ua = ['-user_agent', UA['User-Agent']] if it.get('streaming') else []
                subprocess.run(['ffmpeg', '-v', 'error', '-y', *ua, '-ss', str(it['inicio']), '-t', str(it['dur']), '-i', str(bruto),
                                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', str(arq)], check=True)
            elif it['tipo'] == 'audio':
                meta = info_commons(it['commons'])
                bruto = tmp / f'{i}{Path(meta["url"]).suffix}'; get(meta['url'], bruto)
                arq = out / f'{i}.ogg'
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(it['inicio']), '-t', str(it['dur']), '-i', str(bruto),
                                '-ac', '1', '-ar', '48000', '-c:a', 'libopus', '-b:a', '64k', str(arq)], check=True)
                if it.get('alinhar'):
                    from faster_whisper import WhisperModel
                    m = WhisperModel('small', device='cpu', compute_type='int8')
                    import numpy as np   # decodifica com ffmpeg (independe da versão do PyAV usada pelo faster-whisper)
                    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(arq), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
                    onda = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
                    segs, inf = m.transcribe(onda, language=it['alinhar'], word_timestamps=True, vad_filter=False)
                    pal = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3), 'p': round(w.probability, 3)} for s in segs for w in (s.words or [])]
                    (out / f'{i}.palavras.json').write_text(json.dumps({'modelo': 'faster-whisper small int8', 'idioma': inf.language, 'palavras': pal}, ensure_ascii=False, indent=0))
            meta.update(id=i, uso=it.get('uso'), arquivo=arq.name, sonda=ffprobe(arq), bytes=arq.stat().st_size)
            meta['licenca_livre'] = bool(LIVRES.search(str(meta.get('licenca', ''))))
            (out / f'{i}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
            rel.append({'id': i, 'ok': True, 'arquivo': arq.name, 'licenca': meta.get('licenca'), 'bytes': meta['bytes']})
        except Exception as e:
            print('  ERRO', e, flush=True); rel.append({'id': i, 'ok': False, 'erro': str(e)[:300]})
    (out / 'RELATORIO.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1))
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps(rel, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
