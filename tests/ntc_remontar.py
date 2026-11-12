"""Remonta um vídeo do NTC a partir do pacote (ou de um roteiro), sem IA e sem voz (Fase 4, CP1).

Uso:
  python -m tests.ntc_remontar PACOTE.json [saida.png]     → folha de contato (3 quadros por cena: antes · durante · depois)
  python -m tests.ntc_remontar ROTEIRO.json [saida.png]    → idem, com tempos sintéticos (roteiro antigo ou novo)

Com pacote, avisa se o motor mudou desde o vídeo (o desenho pode sair diferente)
e confere que os dados de montagem recalculados batem com os guardados.
"""
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from src import fabula, ntc_pacote
from tests import ntc_geometria as G

LARG = 216          # 1080 / 5


def _dados(arq: Path) -> tuple[dict, dict | None, list]:
    d = json.loads(arq.read_text(encoding='utf-8'))
    if 'formato_pacote' in d:
        pac = ntc_pacote.ler(arq)
        avisos = [f'motor mudou: {", ".join(m)}' for m in [ntc_pacote.conferir_motor(pac)] if m]
        refeito = fabula.dados_template(fabula.validar(json.loads(json.dumps(pac['roteiro']))), pac['tempos'],
                                        pac['legendas'], pac['dados_montagem']['duration'])
        if json.dumps(refeito, sort_keys=True) != json.dumps(pac['dados_montagem'], sort_keys=True):
            avisos.append('dados de montagem recalculados diferem dos guardados (o motor de montagem mudou)')
        return pac['dados_montagem'], pac, avisos
    return G.dados_do_roteiro(d), None, []


def instantes(cena: dict) -> list:
    """Antes, durante e depois da ação principal da cena."""
    a, b = cena['a'], cena['b']
    acao = a + min(b - a - 0.2, max([p.get('de', 0) for p in cena.get('props', [])] + [0]) + 0.5)
    return [a + 0.05, max(a + 0.1, acao), b - 0.05]


def folha(dados: dict, saida: Path) -> Path:
    from playwright.sync_api import sync_playwright
    cenas = dados['cenas']
    alt = LARG * 16 // 9
    img = Image.new('RGB', (LARG * 3 + 60, (alt + 6) * len(cenas)), 'white')
    dr = ImageDraw.Draw(img)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        pag = fabula._pagina(dados, Path(tmp) / 'render')
        nav = p.chromium.launch(args=['--allow-file-access-from-files'])
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(pag.as_uri()); pg.wait_for_function('window.READY===true', timeout=60000)
        for k, c in enumerate(cenas):
            y = k * (alt + 6)
            dr.text((6, y + 6), str(k + 1), fill='black')
            for j, t in enumerate(instantes(c)):
                pg.evaluate(f'seek({t:.3f})')
                q = Path(tmp) / 'q.png'
                pg.screenshot(path=str(q))
                img.paste(Image.open(q).resize((LARG, alt)), (60 + j * LARG, y))
        nav.close()
    img.save(saida)
    return saida


def main(argv):
    arq = Path(argv[0])
    saida = Path(argv[1]) if len(argv) > 1 else arq.with_suffix('.folha.png')
    dados, pac, avisos = _dados(arq)
    for a in avisos:
        print('⚠️', a)
    if pac:
        print(f"pacote: {pac['tema']} · motor {pac['motor']['hash_motor'][:8]} · {len(dados['cenas'])} cenas")
    print('folha:', folha(dados, saida))


if __name__ == '__main__':
    main(sys.argv[1:])
