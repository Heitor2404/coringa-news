import pytest
from PIL import Image
from src.v3.biblioteca import Biblioteca
from src.v3 import pacote_biblioteca as P
from scripts.validar_arquivo_documental import validar
import shutil,json

def test_archive_guard_real_checkpoint_with_index(tmp_path):
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    try:
        f=tmp_path/'a.jpg';Image.new('RGB',(800,600),'blue').save(f)
        d=b.ingerir(f,{'titulo':'fixture'})
        key='documental:'+'a'*64
        b.gravar_analise(d['sha256'],key,{'publicar':False,'direitos_aprovados':False,'observacao':'fixture'})
        p=tmp_path/d['id']
        P.exportar(b,[d['id']],p,incluir_analises_privadas=True)
        z=shutil.make_archive(str(p),'zip',root_dir=p)
        manifest=tmp_path/'manifesto-revisoes.jsonl';b.exportar_manifesto(manifest)
        assert validar([z,manifest])==1
        with pytest.raises(ValueError,match='MANIFESTO_AUSENTE'):validar([z])
        rows=[json.loads(l) for l in manifest.read_text().splitlines()]
        for row in rows:
            if row.get('id')==d['id']:row['analises']={}
        manifest.write_text('\n'.join(json.dumps(r) for r in rows))
        with pytest.raises(ValueError,match='ANALISE_NAO_INDEXADA'):validar([z,manifest])
        assert validar([f])==0
    finally:b.fechar()
