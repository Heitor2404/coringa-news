"""Indexa o catálogo INTEIRO do registro HyperFrames de um checkout fixado → motor4/catalogo/hyperframes.json.

uso: python scripts/v4_catalogo_hyperframes.py <checkout-hyperframes> [saida.json]

Cada entrada: nome, tipo, título, descrição, tags, autor, versão (commit do registro), parâmetros tipados, duração,
dimensões, demo (preview), licença (do item ou do repositório), requisitos (bibliotecas, CDN, rede, binários, fontes),
perfil/família, compatibilidade com 9:16 e as funções narrativas do Coringa às quais o item pode servir. Nada é
"aprovado" aqui: compatibilidade é uma leitura objetiva dos metadados; qualidade visual só depois de render + humano.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

LIBS = {'gsap': r'gsap', 'three': r'\bthree(\.module)?(\.min)?\.js|from ["\']three["\']|THREE\.', 'd3': r'\bd3[\.-]',
        'maplibre': r'maplibre', 'mapbox': r'mapbox', 'leaflet': r'leaflet', 'pixi': r'pixi', 'lottie': r'lottie',
        'anime': r'anime(\.min)?\.js', 'matter': r'matter(\.min)?\.js', 'opentype': r'opentype', 'webgl': r'getContext\(["\']webgl'}
CDN = re.compile(r'https?://(cdn\.jsdelivr\.net|unpkg\.com|fonts\.googleapis\.com|fonts\.gstatic\.com|cdnjs\.cloudflare\.com|[a-z0-9.-]+\.heygen\.(ai|com))[^"\'\s)]*')
BIN = {'.glb', '.gltf', '.wav', '.mp3', '.mp4', '.webm', '.mov', '.png', '.jpg', '.jpeg', '.webp', '.hdr', '.exr', '.ttf', '.otf', '.woff', '.woff2'}

# funções narrativas do Coringa ← tags/descrição (leitura de metadados, não julgamento estético)
FUNCOES = {
    'mapa': r'\bmap|globe|geo|route|flight|country|world',
    'dados': r'chart|graph|data|count|number|stat|bar-|line-|pie|metric|infographic',
    'tipografia': r'kinetic|title|type|text|headline|letters|word|quote',
    'legenda': r'caption|subtitle|karaoke',
    'transicao': r'transition|wipe|cut|swipe|whip|iris|zoom-through',
    'sobreposicao': r'overlay|lower[- ]third|hud|grain|vignette|frame|texture|film',
    'esquema': r'diagram|flow|process|step|timeline|explainer|annotat|callout|arrow|highlight',
    'comparacao': r'before-after|compare|versus|\bvs\b|split',
    '3d': r'\b3d\b|three|orbit|depth|cuboid|webgl',
    'linha_do_tempo': r'timeline|chronolog|history|year',
    'camera': r'camera|shake|pan|dolly|push',
    'ui_marketing': r'mock-ui|chat|app|saas|brand|product|marketing|ad-template|social|ios|macos|iphone|browser|cta|logo|subscribe',
}


def ler(d: Path) -> str:
    """só o que roda (html/js/css/json de dados) — registry-item.json, demo e documentação não contam como requisito"""
    out = []
    for f in d.rglob('*'):
        if f.is_file() and f.suffix in ('.html', '.js', '.css', '.json') and f.name != 'registry-item.json' and f.stat().st_size < 3_000_000:
            try:
                out.append(f.read_text(encoding='utf-8', errors='ignore'))
            except Exception:
                pass
    return '\n'.join(out)


def entrada(item_json: Path, commit: str) -> dict:
    d = json.loads(item_json.read_text(encoding='utf-8'))
    pasta = item_json.parent
    texto = ler(pasta)
    dims = d.get('dimensions') or {}
    w, h = dims.get('width'), dims.get('height')
    orient = 'retrato' if w and h and h > w else 'quadrado' if w and w == h else 'paisagem' if w else 'responsivo'
    binarios = sorted(str(f.relative_to(pasta)) for f in pasta.rglob('*') if f.is_file() and f.suffix.lower() in BIN)
    cdns = sorted({u for u in (m.group(0).split('?')[0] for m in CDN.finditer(texto)) if '/schema/' not in u and not u.rstrip('/').endswith(('heygen.com', 'heygen.ai'))})
    libs = sorted(k for k, rx in LIBS.items() if re.search(rx, texto, re.I))
    vars_ = [{k: v.get(k) for k in ('id', 'type', 'role', 'label', 'description', 'default', 'options', 'min', 'max') if k in v}
             for v in d.get('variables') or []]
    alvo = ' '.join([d.get('name', ''), d.get('title', ''), d.get('description', ''), ' '.join(d.get('tags') or [])]).lower()
    funcoes = sorted(f for f, rx in FUNCOES.items() if re.search(rx, alvo))
    # 9:16: retrato nativo; responsivo (componentes sem dimensão) adapta ao host; paisagem/quadrado exige recomposição
    compat = {'retrato': 'nativo', 'responsivo': 'adapta_ao_host', 'quadrado': 'recompor', 'paisagem': 'recompor'}[orient]
    return {
        'nome': d['name'], 'tipo': d['type'].split(':')[-1], 'titulo': d.get('title'), 'descricao': d.get('description'),
        'tags': d.get('tags') or [], 'autor': d.get('author'), 'versao': f'registry@{commit[:12]}',
        'familia': d.get('family'), 'perfil': d.get('profile'), 'estabilidade': d.get('stability'),
        'dimensoes': dims or None, 'orientacao': orient, 'compat_9x16': compat, 'duracao': d.get('duration'),
        'parametros': vars_, 'parametros_tipados': bool(vars_), 'sync_points': bool(d.get('syncPoints')),
        'demo': d.get('preview'), 'licenca': d.get('license') or 'Apache-2.0 (repositório heygen-com/hyperframes)',
        'requisitos': {'bibliotecas': libs, 'cdn': cdns, 'requer_rede': bool(cdns), 'binarios': binarios,
                       'dependencias_registro': d.get('registryDependencies') or [], 'gsap_licenca_standard': 'gsap' in libs},
        'funcoes_coringa': funcoes, 'arquivos': [f.get('path') if isinstance(f, dict) else f for f in d.get('files') or []],
        'pasta': str(pasta.relative_to(item_json.parents[2])),
    }


def main():
    raiz = Path(sys.argv[1])
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / 'motor4' / 'catalogo' / 'hyperframes.json'
    commit = subprocess.run(['git', '-C', str(raiz), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip() or 'desconhecido'
    reg = json.loads((raiz / 'registry' / 'registry.json').read_text())
    itens = sorted((entrada(f, commit) for f in (raiz / 'registry').glob('*/*/registry-item.json')), key=lambda e: (e['tipo'], e['nome']))
    nomes_reg = {i['name'] for i in reg['items']}
    resumo = {'total': len(itens), 'por_tipo': {}, 'por_orientacao': {}, 'por_funcao': {}, 'requer_rede': sum(i['requisitos']['requer_rede'] for i in itens),
              'parametros_tipados': sum(i['parametros_tipados'] for i in itens), 'gsap': sum(i['requisitos']['gsap_licenca_standard'] for i in itens),
              'fora_do_registry_json': sorted({i['nome'] for i in itens} - nomes_reg), 'so_no_registry_json': sorted(nomes_reg - {i['nome'] for i in itens})}
    for i in itens:
        resumo['por_tipo'][i['tipo']] = resumo['por_tipo'].get(i['tipo'], 0) + 1
        resumo['por_orientacao'][i['orientacao']] = resumo['por_orientacao'].get(i['orientacao'], 0) + 1
        for f in i['funcoes_coringa'] or ['sem_funcao']:
            resumo['por_funcao'][f] = resumo['por_funcao'].get(f, 0) + 1
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps({'fonte': 'https://github.com/heygen-com/hyperframes', 'commit': commit, 'cli': 'hyperframes@0.9.58',
                                 'licenca_repositorio': 'Apache-2.0', 'resumo': resumo, 'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(resumo, ensure_ascii=False)[:1500])


if __name__ == '__main__':
    main()
