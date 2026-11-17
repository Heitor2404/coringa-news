"""Portões de qualidade do V4 (auditoria de 16/11 sobre a execução 43972774128). Decisões no CÓDIGO, não no prompt:

1. `validar_clipe`: um clipe só entra no episódio se tiver a duração e o tamanho certos, conteúdo (não preto) e, quando a
   cena promete ação, mudança VISUAL na zona de conteúdo (a faixa de legenda não conta). Clipe reprovado = backend falhou
   → próxima alternativa pré-validada; sem alternativa → a cena NÃO está pronta (nunca tela preta como conteúdo).
2. `decidir`: o estado final vem dos portões. Cena não renderizada → DIAGNÓSTICO (o MP4 é material de diagnóstico, não
   episódio). Revisão semântica 'nao' em acontecimento essencial ou mídia que não corresponde ao fato → BLOQUEADO.
   'parcial', revisão ausente, informação parada > 4 s → revisão humana obrigatória. Nunca há aprovação aqui.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from src.v4.util import H, W

PENDENTE = 'AGUARDANDO_APROVACAO_HUMANA'
BLOQUEADO = 'BLOQUEADO'
DIAGNOSTICO = 'DIAGNOSTICO_NAO_EDITORIAL'
CONTEUDO = (150, 1170)          # linhas do quadro 1080×1920 com o assunto (sem a faixa de legenda 1180–1440 e sem o rodapé)
PRETO_MAX = .90                 # fração de pixels quase pretos na zona de conteúdo a partir da qual o quadro é "preto"
PARADO_DIFF = 1.0               # diferença média (0–255) entre o primeiro e o último quadro abaixo da qual nada mudou
INFO_PARADA_S = 4.0             # alarme (revisão), não fórmula: o Heitor decide se o plano parado se justifica
REGISTRO = {'registro_foto', 'registro_video', 'documento'}


def amostras(mp4: Path, n: int = 6, largura: int = 108) -> np.ndarray:
    alt = int(largura * H / W)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(mp4)],
                               capture_output=True, text=True).stdout.strip() or 0)
    if dur <= 0:
        return np.zeros((0, alt, largura, 3), np.uint8)
    qs = []
    for k in range(n):
        t = dur * (k + .5) / n
        r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1', '-vf', f'scale={largura}:{alt}',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
        if len(r.stdout) == alt * largura * 3:
            qs.append(np.frombuffer(r.stdout, np.uint8).reshape(alt, largura, 3))
    return np.array(qs) if qs else np.zeros((0, alt, largura, 3), np.uint8)


def _zona(q: np.ndarray) -> np.ndarray:
    h = q.shape[0]
    return q[int(CONTEUDO[0] / H * h):int(CONTEUDO[1] / H * h)].astype(np.float32)


def avaliar_quadros(qs: np.ndarray, exige_movimento: bool) -> list[str]:
    """motivos de reprovação a partir dos quadros amostrados (separado para teste)"""
    if not len(qs):
        return ['SEM-QUADROS: o clipe não tem quadros legíveis']
    motivos = []
    preto = [float((_zona(q).max(axis=2) < 14).mean()) for q in qs]
    if float(np.median(preto)) >= PRETO_MAX:
        motivos.append(f'PRETO: {np.median(preto):.0%} da zona de conteúdo quase preta')
    if exige_movimento and len(qs) > 1:
        dif = float(np.abs(_zona(qs[-1]) - _zona(qs[0])).mean())
        if dif < PARADO_DIFF:
            motivos.append(f'CONGELADO: a cena promete ação e o conteúdo não muda (diferença {dif:.2f})')
    return motivos


def validar_clipe(clipe: Path, dur: float, exige_movimento: bool) -> dict:
    from src.v4.util import sondar
    s = sondar(clipe)
    motivos = []
    if (s.get('w'), s.get('h')) != (W, H):
        motivos.append(f"TAMANHO: {s.get('w')}×{s.get('h')} (esperado {W}×{H})")
    if abs((s.get('duracao') or 0) - dur) > .2:
        motivos.append(f"DURACAO: {s.get('duracao')} s (esperado {dur:.2f} s)")
    motivos += avaliar_quadros(amostras(clipe), exige_movimento)
    return {'ok': not motivos, 'motivos': motivos}


def decidir(cenas: list[dict], regs: list[dict], revisao: dict | None, metricas_cena: list[dict] | None) -> dict:
    """portões por cena → {estado, bloqueios, revisoes}. `cenas` do episódio; `regs` do render; revisão multimodal."""
    bloq, rev = [], []
    ver = {p.get('evento_id'): (p.get('veredito') or {}) for p in (revisao or {}).get('planos') or []}
    met = {m['cena']: m for m in metricas_cena or []}
    nao_prontas = [c['id'] for c, r in zip(cenas, regs) if r.get('estado') != 'renderizado']
    for c, r in zip(cenas, regs):
        cid = c['id']
        if cid in nao_prontas:
            bloq.append(f"G-CENA-NAO-PRONTA {cid} ({c['componente']}): " + '; '.join(r.get('motivos') or [str(r.get('erro', ''))[:160]]))
            continue
        v = ver.get(cid)
        essencial = bool(c.get('acao_fisica') or c.get('essencial'))
        if not v or '_nao_revisado' in v:
            rev.append(f'G-SEM-REVISAO {cid}: revisão semântica ausente/falhou — pendente humano')
        else:
            dem = str(v.get('demonstra') or '').lower()
            if c['modalidade'] in REGISTRO and v.get('midia_corresponde') is False:
                bloq.append(f"G-MIDIA-ERRADA {cid}: a mídia não corresponde ao fato narrado ({'; '.join(map(str, v.get('problemas') or []))[:160]})")
            if dem == 'nao':
                (bloq if essencial else rev).append(f"G-NAO-DEMONSTRA {cid}: a cena não mostra o que a fala diz" + (' (acontecimento essencial)' if essencial else ''))
            elif dem == 'parcial':
                rev.append(f'G-DEMONSTRA-PARCIAL {cid}: correção dirigida ou decisão humana')
        m = met.get(cid) or {}
        if (m.get('informacao_parada_s') or 0) > INFO_PARADA_S:
            rev.append(f"G-INFO-PARADA {cid}: {m['informacao_parada_s']:.1f} s sem mudança no conteúdo (alarme; plano parado só com intenção)")
    estado = DIAGNOSTICO if nao_prontas else (BLOQUEADO if bloq else PENDENTE)
    return {'estado': estado, 'bloqueios': bloq, 'revisoes': rev, 'cenas_nao_prontas': nao_prontas}
