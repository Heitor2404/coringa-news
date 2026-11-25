"""Regressão: a configuração do Remotion precisa estar na "remotion root".

Causa-raiz (25/11, prova geográfica de Corinto): o CLI do Remotion 4 só carrega `remotion.config.{ts,js}` da pasta do
`package.json` mais próximo do cwd (`RenderInternals.findRemotionRoot`). O único `package.json` é `motor4/`, mas a
configuração ficava em `motor4/remotion/`, então nunca era aplicada ("No config file loaded"): REMOTION_CHROME, o
renderizador GL `swangle` e a qualidade JPEG eram ignorados e o Remotion tentava baixar o Chrome Headless Shell,
mesmo com o Chrome instalado. Uma config `.ts` na raiz exigiria `motor4/tsconfig.json`; por isso a config é `.js`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MOTOR4 = RAIZ / 'motor4'


def _remotion_root(cwd: Path) -> Path:
    """Mesma regra de findRemotionRoot: sobe até o primeiro package.json."""
    for d in [cwd, *cwd.parents]:
        if (d / 'package.json').is_file():
            return d
    return cwd


@pytest.mark.parametrize('cwd', [MOTOR4, MOTOR4 / 'remotion'])
def test_config_esta_na_remotion_root_dos_dois_cwds_usados(cwd):
    root = _remotion_root(cwd)
    assert root == MOTOR4
    ts, js = root / 'remotion.config.ts', root / 'remotion.config.js'
    assert js.is_file() or ts.is_file(), 'config fora da remotion root nunca é carregada'
    if ts.is_file():
        assert (root / 'tsconfig.json').is_file(), 'config .ts exige tsconfig.json na raiz'


def test_config_resolve_navegador_local_e_preserva_parametros():
    txt = (MOTOR4 / 'remotion.config.js').read_text(encoding='utf8')
    assert 'setBrowserExecutable' in txt and 'REMOTION_CHROME' in txt and 'CORINGA_CHROME' in txt
    assert "setChromiumOpenGlRenderer" in txt and 'swangle' in txt
    assert 'setJpegQuality(92)' in txt
    assert ' as any' not in txt, 'arquivo JS não aceita anotações TypeScript'


@pytest.mark.skipif(not shutil.which('npx') or not (MOTOR4 / 'node_modules' / '@remotion' / 'cli').is_dir()
                    or not any(Path(p).is_file() for p in ('/usr/bin/google-chrome', '/usr/bin/chromium')),
                    reason='Remotion/Chrome locais ausentes')
def test_cli_aplica_config_e_nao_baixa_navegador():
    env = {k: v for k, v in os.environ.items() if k not in ('REMOTION_CHROME',)}
    p = subprocess.run(['npx', '--no-install', 'remotion', 'compositions', 'remotion/src/index.ts', '--log=verbose'],
                       cwd=MOTOR4, env=env, capture_output=True, text=True, timeout=400)
    saida = p.stdout + p.stderr
    assert 'Applied configuration from' in saida and 'remotion.config.js' in saida, saida[-2000:]
    assert 'No config file loaded' not in saida
    assert 'Downloading Chrome' not in saida, 'tentou baixar navegador com Chrome local disponível'
    assert p.returncode == 0 and 'FilmeEditorial' in saida
