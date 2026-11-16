"""Backends de registro real (fotos/documentos/vídeo), reaproveitando o que já funciona:

- foto/documento → palco V2 (Chromium com seek determinístico, `doc.plano`), com a decisão de layout e câmera de
  `src/v3/decisao.py` (vertical → editorial → revisão; câmera FIXA salvo `revela`). Marca, selo e crédito NÃO são
  desenhados aqui: vêm da camada única de identidade (Remotion `Camada`), igual em todos os backends.
- vídeo real → FFmpeg: recorte 9:16 FIXO no objeto principal (ROI), sem zoom/pan; trecho [inicio, inicio+dur];
  vídeo mais curto que a cena é recusado (nada de congelar quadro para esticar).
"""
from __future__ import annotations

import json
from pathlib import Path

from src.v4.util import FPS, H, W, FalhaBackend, rodar, sondar


def render_foto(arq: Path, wh: list, roi: list | None, camera: dict, layout_pedido: str | None, natureza: str, dur: float,
                trab: Path, saida: Path, critico: bool = False) -> dict:
    from src.render.render import _trecho
    from src.v2 import diretor, palco
    from src.v3 import decisao
    trab.mkdir(parents=True, exist_ok=True)
    foco = roi
    enq_obj = diretor.enquadramento('objeto', roi, foco, wh)
    enq_det = diretor.enquadramento('detalhe', roi, foco, wh)
    if camera.get('tipo') == 'revelar' and camera.get('de') and camera.get('ate'):
        cam = [{'t': 0, 'caixa': diretor.enquadramento(camera['de'], roi, foco, wh)}, {'t': dur * .92, 'caixa': diretor.enquadramento(camera['ate'], roi, foco, wh)}]
    else:
        cam = [{'t': 0, 'caixa': diretor.enquadramento(camera.get('enquadramento') or ('objeto' if roi else 'geral'), roi, foco, wh)}]
    pl = {'layout': layout_pedido, 'critico': critico, 'objeto_principal': 'roi' if roi else None,
          'revela': camera.get('revela') or [], 'movimento_camera': camera.get('tipo', 'fixo')}
    x = {'titulo': natureza, 'desc': natureza, 'wh': wh}
    dec = decisao.decidir(pl, x, wh, cam, roi, {}, enq_obj, enq_det, None, gancho=bool(camera.get('gancho')))
    params = {'img': str(arq), 'wh': wh, 'cam': dec['cam'], 'layout': dec['layout'], 'anot': [], 'selo': None, 'credito': None,
              'tratamento': 'atual', 'natureza': dec['natureza']}
    if dec.get('visao_geral'):
        params['visao_geral'] = dec['visao_geral']
    dados = {'meta': {'motor': 'v2', 'marca': False}, 'duration': dur, 'captions': [], 'creditos': [],
             'scenes': [{'comp': 'doc.plano', 'start': 0, 'end': dur, 'transicao': 'corte', 'origem': [0], 'fala': '', 'params': params}]}
    d2 = palco.preparar(json.loads(json.dumps(dados)))
    pagina = palco.pagina(d2, trab)
    bruto = trab / 'palco.mp4'
    _trecho((str(pagina), 0, int(round(dur * FPS)), str(bruto), palco.NAVEGADOR))
    if not bruto.exists():
        raise FalhaBackend('palco não gerou quadros')
    bruto.rename(saida)
    return {'backend': 'legacy', 'comp': 'doc.plano', 'layout': dec['layout'], 'cam': dec['cam'], 'decisao': dec['degradacoes'],
            'params': {k: v for k, v in params.items() if k != 'img'}}


def render_video(arq: Path, wh: list, roi: list | None, inicio: float, dur: float, saida: Path, trab: Path) -> dict:
    info = sondar(arq)
    if info['duracao'] and info['duracao'] < inicio + dur - .05:
        raise FalhaBackend(f"vídeo tem {info['duracao']:.1f}s; a cena pede {inicio:.1f}+{dur:.1f}s (não se congela quadro para esticar)")
    iw, ih = info['w'] or wh[0], info['h'] or wh[1]
    # recorte 9:16 fixo: maior janela vertical que cabe, centrada no ROI (ou no centro)
    cw = min(iw, ih * W / H); ch = cw * H / W
    cx = (roi[0] + roi[2] / 2) * iw if roi else iw / 2
    cy = (roi[1] + roi[3] / 2) * ih if roi else ih / 2
    x = min(max(0, cx - cw / 2), iw - cw); y = min(max(0, cy - ch / 2), ih - ch)
    escala = W / cw
    if escala > 2.6:
        raise FalhaBackend(f'vídeo {iw}×{ih}: recorte vertical precisaria de {escala:.1f}× (borrado no celular)')
    trab.mkdir(parents=True, exist_ok=True)
    rodar(['ffmpeg', '-v', 'error', '-y', '-ss', f'{inicio:.3f}', '-i', arq, '-t', f'{dur:.3f}', '-vf',
           f'crop={int(cw)}:{int(ch)}:{int(x)}:{int(y)},scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p', '-an', '-c:v', 'libx264',
           '-preset', 'veryfast', '-crf', '17', saida], log=trab / 'ffmpeg_video.log')
    return {'backend': 'ffmpeg', 'recorte': [int(x), int(y), int(cw), int(ch)], 'escala': round(escala, 2), 'fonte_wh': [iw, ih]}
