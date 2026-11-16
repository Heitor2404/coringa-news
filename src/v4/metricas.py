"""Métricas de edição e engenharia reversa do MP4 final (V4). Tudo medido sobre o vídeo REAL + a linha do tempo.

Por segundo: área vazia (blocos uniformes e escuros na zona de conteúdo), movimento (diferença média entre quadros),
brilho. Por cena: duração, cortes reais × planejados (PySceneDetect), movimento/estático × o que o componente promete,
repetição perceptual entre cenas (dHash), salto de cor/brilho nos cortes (continuidade), demonstração de ação.
Episódio: cortes/minuto, LUFS/pico/48 kHz, resolução, custo, revisão multimodal (Gemini) — se falhar: PENDENTE.

Nenhuma métrica isolada é "qualidade". Limites são PROVISÓRIOS (só se calibram com feedback do Heitor sobre este vídeo);
o relatório traz os números e a interpretação objetiva, e deixa a estética como pendente humana.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from src.v4.componentes import DEMONSTRAM_ACAO
from src.v4.util import H, W

ZONA = (270, 1240)                    # zona de conteúdo (entre a interface do app no topo e a faixa de legendas)
MOVIMENTO_ESPERADO = {'esquema_2d', 'cena_3d', 'composicao_25d', 'registro_video', 'mapa', 'dados', 'tipografia'}


def _quadros(mp4: Path, fps: float = 2.0, largura: int = 270) -> np.ndarray:
    alt = int(largura * H / W)
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-vf', f'fps={fps},scale={largura}:{alt}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, alt, largura, 3)


def _vazio(q: np.ndarray) -> float:
    """fração da zona de conteúdo em blocos 8×8 quase uniformes e escuros (fundo sem informação)"""
    h = q.shape[0]
    z = q[int(ZONA[0] / H * h):int(ZONA[1] / H * h)].astype(np.float32).mean(axis=2)
    hh, ww = (z.shape[0] // 8) * 8, (z.shape[1] // 8) * 8
    b = z[:hh, :ww].reshape(hh // 8, 8, ww // 8, 8)
    return float(((b.std(axis=(1, 3)) < 3.0) & (b.mean(axis=(1, 3)) < 40)).mean())


def _dhash(q: np.ndarray) -> int:
    from PIL import Image
    g = np.asarray(Image.fromarray(q).convert('L').resize((9, 16)), np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return int(''.join('1' if x else '0' for x in bits), 2)


def _cortes_reais(mp4: Path) -> list[float]:
    from scenedetect import ContentDetector, detect
    return [round(a.get_seconds(), 2) for a, _ in detect(str(mp4), ContentDetector(threshold=27.0))[1:]]


def medir(mp4: Path, linha: list[dict]) -> dict:
    from src.fiscal import medir_audio
    fps = 2.0
    qs = _quadros(mp4, fps)
    seg = []
    for i in range(len(qs)):
        mov = float(np.abs(qs[i].astype(np.int16) - qs[i - 1].astype(np.int16)).mean()) if i else 0.0
        seg.append({'t': round(i / fps, 2), 'vazio': round(_vazio(qs[i]), 3), 'movimento': round(mov, 2), 'brilho': round(float(qs[i].mean()), 1)})
    cortes = _cortes_reais(mp4)
    cenas = []
    hashes = []
    for c in linha:
        idx = [i for i, s in enumerate(seg) if c['ini'] <= s['t'] < c['fim']]
        if not idx:
            continue
        sub = [seg[i] for i in idx]
        meio = qs[idx[len(idx) // 2]]
        hashes.append((c['cena'], _dhash(meio)))
        mov = float(np.mean([s['movimento'] for s in sub[1:]] or [0]))
        estatico = mov < .6
        cenas.append({'cena': c['cena'], 'ini': c['ini'], 'fim': c['fim'], 'duracao': round(c['fim'] - c['ini'], 2), 'modalidade': c['modalidade'],
                      'componente': c['componente'], 'backend': c.get('backend'), 'vazio_medio': round(float(np.mean([s['vazio'] for s in sub])), 3),
                      'vazio_max': max(s['vazio'] for s in sub), 'movimento_medio': round(mov, 2), 'estatico': estatico,
                      'estatico_com_movimento_prometido': estatico and c['modalidade'] in MOVIMENTO_ESPERADO,
                      # estrutural: modalidade capaz, render ok e quadro com conteúdo. NÃO é prova de demonstração — a prova
                      # semântica vem da revisão (combinar_revisao); c6 preta e c5 com vídeo errado contavam como "demonstra"
                      'demonstra_acao': (c['modalidade'] in DEMONSTRAM_ACAO and c.get('estado') == 'renderizado'
                                         and float(np.mean([s['vazio'] for s in sub])) < .9),
                      'demonstra_semantico': 'pendente',
                      'cortes_reais_dentro': [t for t in cortes if c['ini'] + .2 < t < c['fim'] - .2]})
    rep = []
    for i in range(len(hashes)):
        for j in range(i + 2, len(hashes)):
            d = bin(hashes[i][1] ^ hashes[j][1]).count('1')
            if d <= 10:
                rep.append({'cenas': [hashes[i][0], hashes[j][0]], 'distancia_dhash': d})
    cont = []
    for c in linha[1:]:
        k = int(c['ini'] * fps)
        if 0 < k < len(seg):
            cont.append({'corte': c['ini'], 'salto_brilho': round(seg[k]['brilho'] - seg[k - 1]['brilho'], 1)})
    dur = linha[-1]['fim'] if linha else 0
    try:
        audio = medir_audio(mp4)
    except Exception as e:
        audio = {'erro': str(e)[:120]}
    planejados = [c['ini'] for c in linha[1:]]
    return {'por_segundo': seg, 'por_cena': cenas, 'repeticao_perceptual': rep, 'continuidade': cont, 'audio': audio,
            'cortes': {'reais': cortes, 'planejados': planejados, 'por_minuto_planejados': round(len(planejados) / max(1, dur) * 60, 1),
                       'nao_planejados': [t for t in cortes if all(abs(t - p) > .3 for p in planejados)],
                       'planejados_nao_detectados': [p for p in planejados if all(abs(t - p) > .3 for t in cortes)]},
            'resumo': {'duracao': dur, 'cenas': len(linha), 'plano_medio_s': round(dur / max(1, len(linha)), 2),
                       'vazio_medio': round(float(np.mean([s['vazio'] for s in seg])), 3) if seg else None,
                       'pct_estatico': round(100 * float(np.mean([s['movimento'] < .6 for s in seg[1:]])), 1) if len(seg) > 1 else None,
                       'pct_cenas_que_demonstram': round(100 * sum(c['demonstra_acao'] for c in cenas) / max(1, len(cenas)), 1)}}


def folha_de_contato(mp4: Path, linha: list[dict], saida: Path) -> Path:
    """1 quadro no meio de cada cena, numerado (sem precisar assistir ao MP4)"""
    from PIL import Image, ImageDraw
    fr = []
    for c in linha:
        t = (c['ini'] + c['fim']) / 2
        r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', str(mp4), '-frames:v', '1', '-vf', 'scale=216:384', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           capture_output=True)
        if len(r.stdout) == 216 * 384 * 3:
            im = Image.fromarray(np.frombuffer(r.stdout, np.uint8).reshape(384, 216, 3))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 216, 22], fill=(0, 0, 0))
            d.text((4, 4), f"{c['cena']} {c['ini']:.1f}s {c['componente']}", fill=(255, 210, 31))
            fr.append(im)
    n = 8
    lin = -(-len(fr) // n)
    folha = Image.new('RGB', (216 * n, 384 * max(1, lin)), (11, 15, 23))
    for i, im in enumerate(fr):
        folha.paste(im, ((i % n) * 216, (i // n) * 384))
    folha.save(saida, quality=85)
    return saida


def salvar(m: dict, saida: Path):
    saida.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')


def combinar_revisao(m: dict, revisao: dict) -> dict:
    """a revisão semântica decide: 'sim' confirma; 'parcial'/'nao' derruba; sem revisão fica PENDENTE (nunca aprovado
    por omissão). Recalcula a porcentagem só com as confirmadas."""
    por = {}
    for pl in (revisao or {}).get('planos') or []:
        v = pl.get('veredito') or {}
        por[pl.get('evento_id')] = 'pendente' if '_nao_revisado' in v else str(v.get('demonstra') or 'pendente')
    for c in m['por_cena']:
        sem = por.get(c['cena'], 'pendente')
        c['demonstra_semantico'] = sem
        c['demonstra_acao'] = bool(c['demonstra_acao'] and sem == 'sim')
    n = max(1, len(m['por_cena']))
    m['resumo']['pct_cenas_que_demonstram'] = round(100 * sum(c['demonstra_acao'] for c in m['por_cena']) / n, 1)
    m['resumo']['cenas_demonstracao_pendente'] = [c['cena'] for c in m['por_cena'] if c['demonstra_semantico'] == 'pendente']
    return m
