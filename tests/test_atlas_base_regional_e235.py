"""Regional ATLAS source registration tests: no external network or generated footage."""
import hashlib
import json
import pytest
from PIL import Image
from scripts import formatos_raster as R

@pytest.mark.parametrize("dataset,z,endpoint",[("bmng",7,R.BMNG_BATI),("s2_2016",12,R.S2)])
def test_register_licensed_region(tmp_path,monkeypatch,dataset,z,endpoint):
    bbox=[-79.61,8.99,-79.60,9.00]
    def mosaic(url,region,zoom,mode):
        assert url==endpoint
        x0,y0=R.tile_xy(region[0],region[3],zoom)
        x1,y1=R.tile_xy(region[2],region[1],zoom)
        xs,ys=range(int(x0),int(x1)+1),range(int(y0),int(y1)+1)
        nw=R.tile_lonlat(xs.start,ys.start,zoom)
        se=R.tile_lonlat(xs.stop,ys.stop,zoom)
        return Image.new('RGB',(256*len(xs),256*len(ys))),[nw,[se[0],nw[1]],se,[nw[0],se[1]]]
    monkeypatch.setattr(R,"mosaico",mosaic)
    meta=R.registrar_base_regional("fixture",bbox,z,dataset,saida=tmp_path)
    assert meta["dataset"]==dataset and meta["atribuicao"]
    assert meta["sha256"]==hashlib.sha256((tmp_path/"fixture.jpg").read_bytes()).hexdigest()
    assert meta["px_por_grau_fonte"]==256*2**z/360
    assert json.loads((tmp_path/"fixture.json").read_text())==meta

@pytest.mark.parametrize("bbox,z,dataset,error",[
    ([-79.61,8.99,-79.60,9],9,"bmng","GEO-ZOOM"),
    ([-79.61,8.99,-79.60,9],12,"esri","GEO-DATASET"),
    ([179,-1,-179,1],7,"bmng","GEO-BBOX"),
    ([-100,-50,100,50],14,"s2_2016","GEO-ORCAMENTO"),
])
def test_reject_before_network(tmp_path,monkeypatch,bbox,z,dataset,error):
    monkeypatch.setattr(R,"mosaico",lambda *a:pytest.fail("network must not be called"))
    with pytest.raises(ValueError,match=error):
        R.registrar_base_regional("fixture",bbox,z,dataset,saida=tmp_path)
