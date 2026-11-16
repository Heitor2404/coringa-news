"""Registro de capacidades do motor V4: ferramenta → função → instalado → integrado → executável no CI → qualidade
visual testada → limitações → licença → custo → evidência. Status HONESTOS: 'sim' só com evidência; `not_tested` e
`blocked` são resultados válidos. Qualidade visual = SEMPRE 'pendente_humano' até o Heitor avaliar.

`python -m src.v4.capacidades sondar` confere versões instaladas e grava motor4/capacidades.json + docs/v4/CAPACIDADES.md.
O workflow do episódio acrescenta a evidência do CI (render real de cada backend usado) em `executavel_ci`.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.v4.util import MOTOR4, RAIZ, VENV_MANIM, VENV_REMBG

P = 'pendente_humano'
CAP = [
    # ferramenta, função, integrado(onde), limitações, licença, custo, evidência local (16/11)
    ('HyperFrames CLI/runtime/producer 0.9.58', 'render HTML+GSAP determinístico (composições do Coringa e itens do registro)', 'src/v4/backends/hyperframes.py',
     'Studio/player instalados mas só para prévia (não usados no CI); serviços Pro (reverse/style, HeyGen) NÃO ativados', 'Apache-2.0', 'gratuito',
     'camadas (Pixi+rembg) renderizou 4 s em 42 s; registro notes-reveal renderizou 4 s em 12 s'),
    ('HyperFrames — 9 skills', 'instruções de autoria para agentes (não renderizam)', '.claude/skills/{hyperframes,hyperframes-cli,hyperframes-registry,media-use,remotion-to-hyperframes,reverse-any-video,slideshow,style-sampling,figma}',
     'media-use/reverse-any-video/style-sampling têm partes pagas (HeyGen/Pro): não usadas; telemetria desligada', 'Apache-2.0', 'gratuito',
     'instaladas via `hyperframes skills update` e idênticas ao commit 95e4e7f (diff vazio)'),
    ('HyperFrames — registro (457 itens)', 'catálogo indexado e acessível ao diretor; qualquer bloco em retrato/responsivo pode virar cena', 'motor4/catalogo/hyperframes.json + componentes.buscar_registro + hf.registro',
     '203 blocos em paisagem não entram em tela cheia (seriam cartão sobre fundo); 416 itens dependem de CDN (GSAP trocado por cópia local da mesma versão; fontes/three ainda pedem rede); flowchart-vertical falha no runtime 0.9.58 (tl.labels indefinido, também com GSAP 3.14.2 exato)',
     'Apache-2.0 (+ licenças de assets por item, CREDITS.md)', 'gratuito', 'índice gerado do commit 95e4e7f; 2 itens testados: 1 ok, 1 falha registrada'),
    ('Remotion 4.0.544 (+cli, renderer, bundler)', 'render React headless: mapa, 3D, tipografia+Lottie, camada de identidade/legendas', 'motor4/remotion + src/v4/backends/js.py',
     'licença Remotion: gratuita só para pessoa física/empresa até 3 pessoas — CONFIRMAR enquadramento do Heitor; WebGL por SwiftShader (CPU)', 'Remotion License (não OSI)', 'gratuito se elegível',
     'stills de MapaRota, Camara3D, Camada, TipoLottie renderizados'),
    ('@remotion/captions', 'legendas por palavra com destaque ativo (camada única para todos os backends)', 'remotion/src/Camada.tsx', '', 'MIT', 'gratuito', 'still da Camada com palavra ativa'),
    ('@remotion/three + three 0.170 + @react-three/fiber 9.8.2', 'corte 3D simples (câmara, água, navio)', 'remotion/src/Camara3D.tsx',
     'sem fotorrealismo; rótulos por projeção da mesma câmera', 'MIT', 'gratuito', 'still renderizado (SwiftShader)'),
    ('@remotion/lottie + lottie-web 5.13', 'ícone animado em tipografia', 'remotion/src/TipoLottie.tsx', 'animação Lottie original do canal (motor4/lottie/gerar.py)', 'MIT', 'gratuito', 'still renderizado'),
    ('@remotion/transitions, @remotion/media-utils', 'transições/áudio no Remotion', 'instalados, NÃO usados', 'transições ficam no compositor (corte por padrão; dissolve justificado)', 'UNLICENSED / MIT', '—', 'not_tested'),
    ('MapLibre GL JS 6.18.0', 'mapa vetorial real (sem tiles externos)', 'remotion/src/MapaRota.tsx',
     'carregado como ESM da pasta pública (o bundler quebrava o worker); 5.24→6.18 por vulnerabilidade XSS crítica', 'BSD-3', 'gratuito', 'still com Natural Earth, rótulos e localizador'),
    ('Natural Earth 5.1.2', 'países, lagos, rios, mares', 'scripts/v2_natural_earth.py → geo/preparar.mjs', '', 'domínio público', 'gratuito', 'baixado e recortado'),
    ('OpenStreetMap (Overpass)', 'geometria REAL de rotas (ex.: canal)', 'src/v4/geo.py', 'só com rede (Actions); sem geometria → sem rota (nunca linha inventada)', 'ODbL (atribuição)', 'gratuito', 'not_tested (bloqueado neste ambiente; roda no Actions)'),
    ('TopoJSON (server 3.0.1 / client 3.1.0)', 'empacotar/ler camadas', 'geo/preparar.mjs, MapaRota', '', 'ISC', 'gratuito', 'topologia gerada e lida no mapa'),
    ('D3 Geo 3.1.1', 'localizador (globo ortográfico)', 'MapaRota.Localizador', '', 'ISC', 'gratuito', 'still'),
    ('Turf 7.4.0', 'comprimento da rota, recorte, animação ao longo da linha', 'geo/preparar.mjs, MapaRota', '', 'MIT', 'gratuito', 'usado no recorte; medida de rota not_tested sem OSM'),
    ('GSAP 3.15.1 (+3.14.2/3.15.0 p/ registro)', 'timelines determinísticas no HyperFrames', 'composições HF + registro', 'licença Standard (não OSI; uso comercial permitido)', 'GSAP Standard License', 'gratuito', 'camadas e notes-reveal'),
    ('PixiJS 8.23', 'camadas 2.5D (foto, recorte, água) desenhadas por tempo', 'hyperframes/coringa/camadas', 'WebGL por SwiftShader', 'MIT', 'gratuito', 'render camadas'),
    ('rembg 2.0.87 (isnet-general-use)', 'recorte de objeto para 2.5D', 'src/v4/backends/rembg_camadas.py',
     'máscara aceita só com cobertura/fragmentos/borda/bordas dentro dos limites (provisórios)', 'MIT (modelo: Apache-2.0)', 'gratuito (CPU)', 'recorte de teste medido e RECUSADO por borda serrilhada (verificação funcionou)'),
    ('Revideo 0.11.0 (API Motion Canvas)', 'mecanismo 2D paramétrico com render headless', 'motor4/revideo + js.revideo', 'telemetria PostHog desligada (DISABLE_TELEMETRY=true)', 'MIT', 'gratuito', 'nivel_vasos renderizou 6 s'),
    ('Motion Canvas 3.17.2', 'explicação vetorial 2D', 'instalado; cenas na mesma API via Revideo',
     'BLOQUEIO: a distribuição oficial só exporta pelo editor (sem renderer headless); pacotes sem atualização desde 02/2025', 'MIT', 'gratuito', 'blocked — substituído por Revideo (fork MIT com renderer)'),
    ('Manim Community 0.19.0', 'dados/relações físicas com precisão', 'motor4/manim/cenas.py + js.manim', 'exige libcairo2-dev/libpango1.0-dev; sem LaTeX (Text/Pango)', 'MIT', 'gratuito', 'EscalaAltura renderizou 5 s'),
    ('dotLottie web 0.83.2', 'player .lottie', 'instalado, NÃO integrado', 'o caminho Lottie em uso é @remotion/lottie', 'MIT', 'gratuito', 'not_tested'),
    ('Rive runtime @rive-app/canvas 2.50', 'animações paramétricas .riv', 'instalado, NÃO integrado',
     'BLOQUEIO: sem arquivo .riv licenciado (criação exige o editor Rive)', 'MIT (runtime) — arquivos .riv têm licença própria', 'gratuito', 'blocked'),
    ('FFmpeg 6.1 / ffprobe', 'normalizar clipes, vídeo real (recorte fixo), compor, mixar, masterizar', 'util, legado.render_video, compositor, som', '', 'LGPL/GPL', 'gratuito', 'usado em todos os testes'),
    ('Playwright/Chromium (palco V2)', 'fotos/documentos com a decisão de layout do V3', 'legado.render_foto', '', 'Apache-2.0', 'gratuito', 'herdado (V3)'),
    ('PySceneDetect 0.7.3 + OpenCV', 'cortes reais × planejados', 'metricas.medir', '', 'BSD-3', 'gratuito', 'not_tested no V4 até o episódio'),
    ('faster-whisper', 'tempos por palavra da narração', 'voz.narrar (herdado)', '', 'MIT', 'gratuito', 'herdado'),
    ('Gemini (TTS/visão) cota grátis', 'voz, escolha de mídia, revisão multimodal', 'voz, acervo_v4, episodio._revisao', 'falha → PENDENTE (nunca aprovado)', 'termos Google', 'cota grátis', 'herdado'),
    ('Claude Code (assinatura)', 'diretor V4', 'diretor.pedir', 'consumo de assinatura registrado pelo caixa', '—', 'assinatura', 'herdado'),
]


def _versao_npm(pac: str) -> str | None:
    f = MOTOR4 / 'node_modules' / pac / 'package.json'
    return json.loads(f.read_text()).get('version') if f.exists() else None


def _versao_pip(venv: Path, pac: str) -> str | None:
    r = subprocess.run([str(venv / 'bin' / 'python'), '-c', f'import importlib.metadata as m;print(m.version("{pac}"))'], capture_output=True, text=True)
    return r.stdout.strip() or None


def sondar() -> list[dict]:
    inst = {'HyperFrames CLI': _versao_npm('hyperframes'), 'Remotion 4': _versao_npm('remotion'), '@remotion/captions': _versao_npm('@remotion/captions'),
            '@remotion/three': _versao_npm('@remotion/three'), '@remotion/lottie': _versao_npm('@remotion/lottie'), '@remotion/transitions': _versao_npm('@remotion/transitions'),
            'MapLibre': _versao_npm('maplibre-gl'), 'TopoJSON': _versao_npm('topojson-server'), 'D3 Geo': _versao_npm('d3-geo'), 'Turf': _versao_npm('@turf/turf'),
            'GSAP': _versao_npm('gsap'), 'PixiJS': _versao_npm('pixi.js'), 'Revideo': _versao_npm('@revideo/renderer'), 'Motion Canvas': _versao_npm('@motion-canvas/core'),
            'dotLottie': _versao_npm('@lottiefiles/dotlottie-web'), 'Rive': _versao_npm('@rive-app/canvas'), 'rembg': _versao_pip(VENV_REMBG, 'rembg'),
            'Manim': _versao_pip(VENV_MANIM, 'manim')}
    skills = sorted(p.name for p in (RAIZ / '.claude' / 'skills').iterdir() if (p / 'SKILL.md').exists())
    out = []
    for nome, func, integ, lim, lic, custo, evid in CAP:
        ver = next((v for k, v in inst.items() if k.split()[0].lower() in nome.lower()), None)
        instalado = 'sim' if ver or any(x in nome for x in ('Natural Earth', 'OpenStreetMap', 'FFmpeg', 'Playwright', 'PySceneDetect', 'faster', 'Gemini', 'Claude', 'skills', 'registro')) else 'nao'
        integrado = 'nao' if 'NÃO' in integ or 'instalado;' in integ else 'sim'
        estado = 'blocked' if 'BLOQUEIO' in lim else ('not_tested' if evid.startswith('not_tested') else 'operacional_local')
        out.append({'ferramenta': nome, 'funcao': func, 'versao_instalada': ver, 'instalado': instalado, 'integrado': integrado, 'onde': integ,
                    'executavel_ci': 'not_tested', 'qualidade_visual_testada': P, 'estado': estado, 'limitacoes': lim, 'licenca': lic, 'custo': custo, 'evidencia': evid})
    out.append({'ferramenta': 'skills instaladas', 'lista': skills})
    return out


def documento(caps: list[dict]) -> str:
    L = ['# Motor V4 — registro de capacidades', '', 'Gerado por `python -m src.v4.capacidades sondar`. "Importa sem erro" não é "integrado"; '
         'qualidade visual só depois da avaliação do Heitor.', '',
         '| Ferramenta | Função | Versão | Instalado | Integrado | CI | Estado | Qualidade visual | Licença | Custo | Limitações | Evidência |', '|' + '---|' * 12]
    for c in caps:
        if 'lista' in c:
            continue
        L.append(f"| {c['ferramenta']} | {c['funcao']} | {c['versao_instalada'] or '—'} | {c['instalado']} | {c['integrado']} | {c['executavel_ci']} | "
                 f"{c['estado']} | {c['qualidade_visual_testada']} | {c['licenca']} | {c['custo']} | {c['limitacoes'] or '—'} | {c['evidencia']} |")
    sk = next((c['lista'] for c in caps if 'lista' in c), [])
    L += ['', f'Skills em `.claude/skills/`: {", ".join(sk)}']
    return '\n'.join(L) + '\n'


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'sondar':
    caps = sondar()
    (MOTOR4 / 'capacidades.json').write_text(json.dumps(caps, ensure_ascii=False, indent=1), encoding='utf-8')
    (RAIZ / 'docs' / 'v4').mkdir(parents=True, exist_ok=True)
    (RAIZ / 'docs' / 'v4' / 'CAPACIDADES.md').write_text(documento(caps), encoding='utf-8')
    print(json.dumps([{k: c.get(k) for k in ('ferramenta', 'versao_instalada', 'instalado', 'integrado', 'estado')} for c in caps if 'lista' not in c], ensure_ascii=False)[:2500])
