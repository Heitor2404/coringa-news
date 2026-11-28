import base64,hashlib,json
from scripts import espelhar_revisao_cofre as E

def test_large_json_roundtrip(tmp_path):
    p=tmp_path/'revisao.json'
    p.write_text(json.dumps({'texto':'evidência glacial çã🌎'*80000},ensure_ascii=False),encoding='utf8')
    original=p.read_bytes()
    assert len(original)>E.MAX_FILE
    files,entries=E.collect([p])
    manifest=json.loads(files['revisao-partes.json'])
    reconstructed=b''.join(base64.b64decode(json.loads(files[name])['base64'],validate=True) for name in manifest['partes'])
    assert reconstructed==original
    assert manifest['sha256']==hashlib.sha256(original).hexdigest()
    assert manifest['bytes']==len(original)
    assert all(len(v)<=E.MAX_FILE for v in files.values())
    assert all(hashlib.sha256(files[e['arquivo']]).hexdigest()==e['sha256'] for e in entries)

def test_small_json_keeps_original(tmp_path):
    p=tmp_path/'integral.json';p.write_text('{"publicar":false}')
    files,entries=E.collect([p])
    assert files=={p.name:p.read_bytes()}
    assert entries[0]['tipo']=='relatorio'
