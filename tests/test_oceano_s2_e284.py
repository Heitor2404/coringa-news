"""E284: borda curva S2 vem do próprio dado EOX (faixa costeira de oceano); o mar fora do litoral passa a vir da base
batimétrica já usada nos zooms menores, com máscara de terra Natural Earth e faixa costeira suavizada."""
import numpy as np
from PIL import Image

from scripts import formatos_raster as R


def test_composicao_mantem_terra_e_faixa_costeira_e_troca_mar_aberto():
    z = 10
    x0, y0 = [int(v) for v in R.tile_xy(-155.6, 19.7, z)]
    w = h = 512
    s2 = np.full((h, w, 3), (120, 125, 130), np.uint8)          # "halo" claro do S2 no mar
    s2[:, :, :] = (120, 125, 130)
    oceano = Image.new('RGB', (64, 64), (10, 30, 70))           # base batimétrica escura
    lon0, lat0 = R.tile_lonlat(x0, y0, z)
    lon1, lat1 = R.tile_lonlat(x0 + 2, y0 + 2, z)
    cx, cy = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    ilha = [[cx - .05, cy - .05], [cx + .05, cy - .05], [cx + .05, cy + .05], [cx - .05, cy + .05], [cx - .05, cy - .05]]
    s2[200:312, 200:312] = (40, 160, 40)                        # "terra" verde perto do centro
    out, frac = R.compor_oceano(Image.fromarray(s2), (x0, y0), z, [ilha], oceano, lat_ref=cy)
    a = np.asarray(out)
    assert 0 < frac < .2
    assert tuple(a[256, 256]) == (40, 160, 40)                  # terra preservada
    assert np.abs(a[5, 5].astype(int) - (10, 30, 70)).max() <= 2  # mar aberto = base batimétrica
    # Sem terra no recorte: tudo vira oceano batimétrico (sem borda do halo S2).
    out2, frac2 = R.compor_oceano(Image.fromarray(s2), (x0, y0), z, [], oceano, lat_ref=cy)
    assert frac2 == 0 and np.abs(np.asarray(out2).astype(int) - (10, 30, 70)).max() <= 2
