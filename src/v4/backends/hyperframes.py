"""Backend HyperFrames (CLI/runtime 0.9.58, registro no commit fixado do catálogo).

Dois modos, mesmo contrato de cena:
- composição do Coringa (motor4/hyperframes/coringa/<nome>/<nome>.html): `params` → window.CORINGA_PARAMS;
- QUALQUER item do registro (bloco ou componente) por nome do catálogo (motor4/catalogo/hyperframes.json): os arquivos do
  item são instalados no projeto (o mesmo que `hyperframes add` faz, sem rede: lê o checkout fixado), variáveis tipadas
  vão em `data-variable-values`, e o GSAP do CDN é trocado pela cópia local fixada (render sem rede).
Regras que o adaptador impõe (não só o prompt): item em paisagem/quadrado NÃO vira tela cheia (seria cartão sobre fundo)
→ recusa com motivo; item que carrega three/fontes por CDN só roda com rede e isso fica registrado.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from src.v4.util import CHROME, FPS, H, HF_REGISTRO, MOTOR4, W, FalhaBackend, rodar

CATALOGO = json.loads((MOTOR4 / 'catalogo' / 'hyperframes.json').read_text(encoding='utf-8'))
POR_NOME = {i['nome']: i for i in CATALOGO['itens']}
NM = MOTOR4 / 'node_modules'
GSAP_CDN = re.compile(r'https://cdn\.jsdelivr\.net/npm/gsap@([\d.]+)/dist/([\w.-]+\.js)')
GSAP_VENDOR = MOTOR4 / 'vendor' / 'gsap'          # cópias EXATAS das versões que os blocos pedem (npm pack)


class Recusado(FalhaBackend):
    """o item existe mas viola uma regra do canal para o uso pedido (motivo explícito)"""


def _fontes(proj: Path) -> str:
    from src.v4.util import IDENT
    d = proj / 'assets' / 'fonts'
    d.mkdir(parents=True, exist_ok=True)
    css = []
    for fam, grupo in (('Mont', IDENT['fontes']['titulo']), ('JBM', IDENT['fontes']['dado'])):
        for peso, arq in list(grupo['arquivos'].items()) + list((grupo.get('ext') or {}).items()):
            shutil.copy(MOTOR4 / 'identidade' / 'fontes' / arq, d / arq)
            css.append(f"@font-face{{font-family:{fam};font-weight:{peso};src:url(assets/fonts/{arq}) format('woff2')}}")
    return '\n'.join(css)


def _vendor(proj: Path, pixi: bool = False):
    v = proj / 'assets' / 'vendor'
    (v / 'gsap').mkdir(parents=True, exist_ok=True)
    for f in (NM / 'gsap' / 'dist').glob('*.min.js'):
        shutil.copy(f, v / 'gsap' / f.name)
    if pixi:
        shutil.copy(NM / 'pixi.js' / 'dist' / 'pixi.min.js', v / 'pixi.min.js')


def _localizar_gsap(html: str, proj: Path | None = None) -> str:
    """CDN do GSAP → cópia local da MESMA versão (sem rede); versão sem cópia local → a fixada do motor (registrado)"""
    def troca(m):
        ver, arq = m.group(1), m.group(2)
        if proj is not None and (GSAP_VENDOR / ver / arq).exists():
            d = proj / 'assets' / 'vendor' / f'gsap-{ver}'
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy(GSAP_VENDOR / ver / arq, d / arq)
            return f'assets/vendor/gsap-{ver}/{arq}'
        return f'assets/vendor/gsap/{arq}'
    return GSAP_CDN.sub(troca, html)


def _raiz(proj: Path, dur: float, filho: str, src: str, extras: str = '', vars_: dict | None = None, wh=(W, H)) -> None:
    vv = f" data-variable-values='{json.dumps(vars_, ensure_ascii=False)}'" if vars_ else ''
    (proj / 'index.html').write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<script src="assets/vendor/gsap/gsap.min.js"></script>{extras}
<style>{_fontes(proj)}\nhtml,body{{margin:0;background:#0B0F17}}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="{W}" data-height="{H}">
  <div id="cena" class="clip" data-composition-id="{filho}" data-composition-src="{src}" data-start="0" data-duration="{dur:.3f}"
       data-track-index="1" data-width="{wh[0]}" data-height="{wh[1]}"{vv}></div>
</div>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""", encoding='utf-8')


def _render(proj: Path, saida: Path, dur: float, log: Path) -> dict:
    reg = rodar(['npx', '--prefix', MOTOR4, 'hyperframes', 'render', proj, '-o', saida, '--fps', FPS, '--quality', 'looks', '--workers', '1',
                 '--no-best-effort', '--quiet'], cwd=MOTOR4, env={'PUPPETEER_EXECUTABLE_PATH': CHROME, 'HYPERFRAMES_CHROME': CHROME}, timeout=1800, log=log)
    if not saida.exists():
        raise FalhaBackend(f'hyperframes não gerou {saida.name}')
    return reg


def render_coringa(nome: str, params: dict, assets: dict[str, Path], dur: float, trab: Path, saida: Path) -> dict:
    """composição própria do Coringa (ex.: camadas): assets = {chave_no_params: arquivo}"""
    trab, saida = Path(trab).resolve(), Path(saida).resolve()
    proj = trab / f'hf_{nome}'
    shutil.rmtree(proj, ignore_errors=True)
    (proj / 'compositions').mkdir(parents=True)
    _vendor(proj, pixi=True)
    p = json.loads(json.dumps(params))
    for chave, arq in assets.items():
        dest = proj / 'assets' / 'midia' / Path(arq).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(arq, dest)
        p[chave] = {**(p.get(chave) or {}), 'src': f'assets/midia/{dest.name}'}
    src = MOTOR4 / 'hyperframes' / 'coringa' / nome / f'{nome}.html'
    shutil.copy(src, proj / 'compositions' / f'{nome}.html')
    extras = f'\n<script src="assets/vendor/pixi.min.js"></script>\n<script>window.CORINGA_PARAMS = {json.dumps(p, ensure_ascii=False)};</script>'
    _raiz(proj, dur, nome, f'compositions/{nome}.html', extras)
    reg = _render(proj, saida, dur, trab / f'hf_{nome}.log')
    return {**reg, 'backend': 'hyperframes', 'modo': 'coringa', 'composicao': nome}


def render_registro(nome: str, variaveis: dict, dur: float, trab: Path, saida: Path) -> dict:
    """qualquer bloco do catálogo; recusa (com motivo) o que violaria regra do canal em tela cheia 9:16"""
    item = POR_NOME.get(nome)
    if not item:
        raise Recusado(f'item {nome!r} não existe no catálogo {CATALOGO["commit"][:12]}')
    if item['tipo'] != 'block':
        raise Recusado(f'{nome} é {item["tipo"]}: componentes entram DENTRO de uma composição, não como cena')
    if item['compat_9x16'] == 'recompor':
        raise Recusado(f'{nome} é {item["orientacao"]} {item["dimensoes"]}: em 9:16 viraria cartão sobre fundo (proibido)')
    pasta = HF_REGISTRO / 'registry' / item['pasta'].split('registry/')[-1] if 'registry/' in item['pasta'] else HF_REGISTRO / 'registry' / item['pasta']
    if not pasta.exists():
        pasta = HF_REGISTRO / item['pasta']
    if not pasta.exists():
        raise FalhaBackend(f'checkout do registro ausente: {pasta} (CORINGA_HF_REGISTRO)')
    trab, saida = Path(trab).resolve(), Path(saida).resolve()
    proj = trab / f'hf_reg_{nome}'
    shutil.rmtree(proj, ignore_errors=True)
    proj.mkdir(parents=True)
    _vendor(proj)
    alvo = None
    # instala pelos destinos declarados no registry-item.json (o mesmo que `hyperframes add`, sem rede)
    meta = json.loads((pasta / 'registry-item.json').read_text(encoding='utf-8'))
    for f in meta.get('files') or []:
        src_, dst_ = pasta / f['path'], proj / f['target']
        if not src_.exists():
            continue
        dst_.parent.mkdir(parents=True, exist_ok=True)
        if src_.suffix == '.html':
            dst_.write_text(_localizar_gsap(src_.read_text(encoding='utf-8'), proj), encoding='utf-8')
            if f.get('type') == 'hyperframes:composition' and alvo is None:
                alvo = dst_
        else:
            shutil.copy(src_, dst_)
    if not alvo:
        raise FalhaBackend(f'{nome}: HTML principal não encontrado')
    validas = {v['id'] for v in item['parametros']}
    desconhecidas = set(variaveis) - validas
    if desconhecidas:
        raise Recusado(f'{nome}: variáveis inexistentes {sorted(desconhecidas)} (válidas: {sorted(validas)})')
    d = item.get('dimensoes') or {'width': W, 'height': H}
    _raiz(proj, min(dur, item.get('duracao') or dur), nome, str(alvo.relative_to(proj)), vars_=variaveis or None, wh=(d['width'], d['height']))
    reg = _render(proj, saida, dur, trab / f'hf_reg_{nome}.log')
    return {**reg, 'backend': 'hyperframes', 'modo': 'registro', 'item': nome, 'versao': item['versao'],
            'requer_rede': item['requisitos']['requer_rede'], 'cdn_restante': [u for u in item['requisitos']['cdn'] if 'gsap@' not in u]}
