import json
import pytest
from PIL import Image
from src.v3.biblioteca import Biblioteca
from src.v3 import pacote_biblioteca as P

def test_portable_bytes_and_quarantine(tmp_path):
    b=Biblioteca(tmp_path/'a.db',tmp_path/'a')
    f=tmp_path/'real.jpg';Image.new('RGB',(32,32),'red').save(f)
    r=b.ingerir(f,{'titulo':'Example glacier','licenca':'CC BY 4.0','url':'https://example.org/a.jpg'})
    p=tmp_path/'pack'
    i=P.exportar(b,[r['id']],p);b.fechar()
    c,rep=P.restaurar(p,db=tmp_path/'b.db',armazem=tmp_path/'b')
    try:
        assert rep['originais_restaurados']==1 and rep['direitos_aprovados'] is False
        assert c.obter(r['id'])['uso_comercial']=='indefinido'
        assert not c.buscar('glacier') and c.buscar('glacier',so_comercial=False)
        assert c.recuperar(r['id'],baixar=lambda *a:pytest.fail('network')) .read_bytes()==f.read_bytes()
    finally:c.fechar()
    (p/i['arquivos'][0]['arquivo']).write_bytes(b'broken')
    with pytest.raises(ValueError,match='E250-BYTES'):
        P.restaurar(p,db=tmp_path/'bad.db',armazem=tmp_path/'bad')
    assert not (tmp_path/'bad.db').exists()

def test_refuse_manifest_promotion(tmp_path):
    b=Biblioteca(tmp_path/'a.db',tmp_path/'a')
    f=tmp_path/'real.png';Image.new('RGB',(32,32),'blue').save(f)
    r=b.ingerir(f,{'titulo':'Example'})
    p=tmp_path/'pack';i=P.exportar(b,[r['id']],p);b.fechar()
    m=p/'manifesto.jsonl';rows=[json.loads(l) for l in m.read_text().splitlines()]
    rows[1]['uso_comercial']='sim'
    m.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
    i['manifesto_sha256']=P.sha(m);(p/'index.json').write_text(json.dumps(i))
    with pytest.raises(ValueError,match='E250-VINCULO'):
        P.restaurar(p,db=tmp_path/'b.db',armazem=tmp_path/'b')
