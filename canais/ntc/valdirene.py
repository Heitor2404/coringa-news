"""Valdirene: personagem desenhada por código (SVG), sempre idêntica; muda só a pose e a expressão."""
O = '#2A1E1A'      # contorno
PELE, CABELO, VESTIDO, AVENTAL, CHINELO, BOCHECHA = '#D9A07A', '#2B1D17', '#6B2E45', 'url(#xadrez)', '#F2C14E', '#E07A6B'
W = 6

def braco(x0, y0, pts, mao=True):
    d = f'M{x0} {y0} ' + ' '.join(f'L{x} {y}' for x, y in pts)
    s = f'<path d="{d}" fill="none" stroke="{O}" stroke-width="{42+2*W}" stroke-linecap="round" stroke-linejoin="round"/>'
    s += f'<path d="{d}" fill="none" stroke="{VESTIDO}" stroke-width="42" stroke-linecap="round" stroke-linejoin="round"/>'
    if mao:
        x, y = pts[-1]
        s += f'<circle cx="{x}" cy="{y}" r="24" fill="{PELE}" stroke="{O}" stroke-width="{W}"/>'
    return s

def rosto(exp):
    olhos = {'neutra': ('<circle cx="272" cy="190" r="7"/><circle cx="328" cy="190" r="7"/>',
                        '<path d="M258 170 L284 166 M316 166 L342 170"/>', '<path d="M282 228 Q300 240 318 228"/>'),
             'susto': ('<circle cx="272" cy="190" r="12" fill="#fff" stroke="%s" stroke-width="5"/><circle cx="272" cy="190" r="5"/><circle cx="328" cy="190" r="12" fill="#fff" stroke="%s" stroke-width="5"/><circle cx="328" cy="190" r="5"/>' % (O, O),
                       '<path d="M256 160 L286 152 M314 152 L344 160"/>', '<ellipse cx="300" cy="236" rx="14" ry="18" fill="%s"/>' % O),
             'feliz': ('<path d="M262 192 Q272 180 282 192 M318 192 Q328 180 338 192" fill="none"/>',
                       '<path d="M258 164 L284 160 M316 160 L342 164"/>', '<path d="M278 222 Q300 252 322 222 Z" fill="#7A2A2A"/>'),
             'brava': ('<circle cx="272" cy="194" r="7"/><circle cx="328" cy="194" r="7"/>',
                       '<path d="M258 166 L286 178 M314 178 L342 166"/>', '<path d="M284 236 Q300 226 316 236"/>'),
             'choro': ('<path d="M260 192 Q272 200 284 192 M316 192 Q328 200 340 192" fill="none"/>',
                       '<path d="M256 172 L286 162 M314 162 L344 172"/>',
                       '<path d="M276 232 Q300 214 324 232 Q324 258 300 258 Q276 258 276 232 Z" fill="#7A2A2A"/><path d="M262 204 Q258 240 262 268 M338 204 Q342 240 338 268" stroke="#6FC3E8" stroke-width="8"/>'),
             'explica': ('<circle cx="272" cy="190" r="7"/><circle cx="328" cy="190" r="7"/>',
                         '<path d="M258 168 L284 166 M316 160 L342 158"/>', '<path d="M284 228 Q304 238 320 226"/>')}[exp]
    e, s, b = olhos
    g = f'<g class="olhos" fill="{O}" stroke="{O}" stroke-width="6" stroke-linecap="round">{e}</g>'
    g += f'<g fill="none" stroke="{O}" stroke-width="7" stroke-linecap="round">{s}</g>'
    g += f'<g class="boca" fill="none" stroke="{O}" stroke-width="6" stroke-linecap="round">{b}</g>'
    g += f'<circle cx="250" cy="220" r="13" fill="{BOCHECHA}" opacity=".55"/><circle cx="350" cy="220" r="13" fill="{BOCHECHA}" opacity=".55"/>'
    g += '<ellipse cx="352" cy="214" rx="12" ry="7" fill="#fff" opacity=".85"/>'   # farinha na bochecha
    g += (f'<g fill="none" stroke="#8B3A2E" stroke-width="6"><rect x="250" y="176" width="44" height="30" rx="9"></rect>'
          f'<rect x="306" y="176" width="44" height="30" rx="9"></rect><path d="M294 188 L306 188 M250 186 L232 180 M350 186 L368 180"></path></g>')
    return g

def corpo(pose, exp, extra=''):
    braços = {
        'neutra':  (braco(230, 304, [(176, 390), (226, 450)]), braco(370, 304, [(424, 390), (374, 450)])),          # mãos na cintura
        'susto':   (braco(230, 304, [(200, 266), (234, 232)]), braco(370, 304, [(400, 266), (366, 232)])),          # mãos no rosto
        'explica': (braco(230, 304, [(196, 400), (210, 480)]), braco(370, 304, [(440, 262), (508, 205)])),          # apontando
        'desespero': (braco(230, 304, [(168, 210), (236, 118)]), braco(370, 304, [(432, 210), (364, 118)])),
        'feliz':   (braco(230, 304, [(178, 222), (166, 130)]), braco(370, 304, [(422, 222), (434, 130)])),          # braços pra cima
    }[pose]
    pernas = (f'<rect x="252" y="610" width="40" height="200" rx="14" fill="#3A3F4A" stroke="{O}" stroke-width="{W}"/>'
              f'<rect x="308" y="610" width="40" height="200" rx="14" fill="#3A3F4A" stroke="{O}" stroke-width="{W}"/>'
              f'<ellipse cx="266" cy="815" rx="38" ry="15" fill="{CHINELO}" stroke="{O}" stroke-width="{W}"/>'
              f'<ellipse cx="334" cy="815" rx="38" ry="15" fill="{CHINELO}" stroke="{O}" stroke-width="{W}"/>')
    vestido = f'<path d="M222 292 Q300 262 378 292 Q448 450 420 624 Q300 650 180 624 Q152 450 222 292 Z" fill="{VESTIDO}" stroke="{O}" stroke-width="{W}" stroke-linejoin="round"/>'
    avental = (f'<path d="M254 330 L346 330 Q396 460 380 604 Q300 622 220 604 Q204 460 254 330 Z" fill="{AVENTAL}" stroke="{O}" stroke-width="{W}" stroke-linejoin="round"/>'
               f'<path d="M220 604 Q236 620 252 608 Q268 622 284 610 Q300 624 316 610 Q332 622 348 608 Q364 620 380 604" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/>'
               f'<path d="M254 330 Q300 298 346 330" fill="none" stroke="{O}" stroke-width="{W}"/>'
               # bolso com cupcake
               f'<rect x="278" y="450" width="44" height="40" rx="8" fill="#fff" stroke="{O}" stroke-width="4"/>'
               f'<path d="M288 472 L312 472 L308 486 L292 486 Z" fill="#C46A3A"/><path d="M286 472 Q300 456 314 472 Z" fill="#F28AA8" stroke="{O}" stroke-width="3"/>'
               '<ellipse cx="330" cy="400" rx="16" ry="9" fill="#fff" opacity=".8"/>')   # farinha
    pescoco = f'<rect x="282" y="250" width="36" height="34" fill="{PELE}" stroke="{O}" stroke-width="{W}"/>'
    cabeca = (f'<circle cx="300" cy="80" r="44" fill="{CABELO}" stroke="{O}" stroke-width="{W}"/>'            # coque
              f'<path d="M270 60 L330 100" stroke="{CHINELO}" stroke-width="9" stroke-linecap="round"/>'     # lápis no coque
              f'<ellipse cx="300" cy="194" rx="80" ry="76" fill="{PELE}" stroke="{O}" stroke-width="{W}"/>'
              f'<path d="M228 192 Q228 112 300 112 Q372 112 372 192 Q360 150 330 142 Q300 160 270 144 Q240 152 228 192 Z" fill="{CABELO}" stroke="{O}" stroke-width="{W}" stroke-linejoin="round"/>'
              f'<path d="M232 200 Q216 222 236 238" fill="none" stroke="{CABELO}" stroke-width="10" stroke-linecap="round"/>')
    esq, dir_ = braços
    # GRUPOS para animar no vídeo: be/bd (braços, giram no ombro), cab (cabeça, gira no pescoço), olhos (piscam), boca (fala)
    bracos = f'<g class="be">{esq}</g><g class="bd">{dir_}{extra}</g>'
    cab = f'<g class="cab">{cabeca}{rosto(exp)}</g>'
    frente = pose in ('susto', 'desespero')
    partes = pernas + vestido + avental + (pescoco + cab + bracos if frente else bracos + pescoco + cab)
    defs = ('<defs><pattern id="xadrez" width="28" height="28" patternUnits="userSpaceOnUse">'
            '<rect width="28" height="28" fill="#FFFFFF"></rect><rect width="14" height="28" fill="#F28AA8" opacity=".75"></rect>'
            '<rect width="28" height="14" fill="#F28AA8" opacity=".75"></rect></pattern></defs>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 860" width="600" height="860">{defs}{partes}</svg>'

ROLO = (f'<g transform="rotate(-25 175 130)"><rect x="110" y="116" width="130" height="28" rx="12" fill="#E8C690" stroke="{O}" stroke-width="5"/>'
        f'<rect x="88" y="122" width="26" height="16" rx="6" fill="#B07A44" stroke="{O}" stroke-width="4"/><rect x="236" y="122" width="26" height="16" rx="6" fill="#B07A44" stroke="{O}" stroke-width="4"/></g>')
BOLO = (f'<g><rect x="370" y="70" width="110" height="60" rx="8" fill="#F6E3C4" stroke="{O}" stroke-width="5"/>'
        f'<path d="M370 86 Q385 100 400 86 Q415 100 430 86 Q445 100 460 86 Q470 96 480 86 L480 78 Q425 62 370 78 Z" fill="#F28AA8" stroke="{O}" stroke-width="4"/>'
        f'<rect x="420" y="40" width="8" height="28" fill="#fff" stroke="{O}" stroke-width="3"/><path d="M424 30 Q430 38 424 42 Q418 38 424 30" fill="{CHINELO}"/></g>')

POSES = {'desesperada': ('desespero', 'choro', ''), 'neutra': ('neutra', 'neutra', ''), 'susto': ('susto', 'susto', ''),
         'explica': ('explica', 'explica', ''), 'comemora': ('feliz', 'feliz', BOLO), 'brava': ('neutra', 'brava', '')}

if __name__ == '__main__':
    import sys, pathlib
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent / 'val'); out.mkdir(parents=True, exist_ok=True)
    for nome, (p, e, x) in POSES.items():
        (out / f'{nome}.svg').write_text(corpo(p, e, x), encoding='utf-8')
    print('ok')
