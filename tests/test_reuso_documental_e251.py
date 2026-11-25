from PIL import Image
import pytest
from src.v3.biblioteca import Biblioteca
from src.v4.formatos import reuso_documental as R
from src.v4.formatos import revisao_documental as V

def need(ev='estatica'):
    return {'id':'n','necessidade':'registro','evidencia_visual':ev,'pesquisa':{'consultas_en':['glacier']},'mostrar':'glacier'}

def test_reuse_real_local_bytes_and_no_motion_in_photo(tmp_path):
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    f=tmp_path/'a.jpg';Image.new('RGB',(800,600),'blue').save(f)
    try:
        d=b.ingerir(f,{'titulo':'glacier','url':'https://example.org/a.jpg'})
        c=R.candidatos(b,need())[0]
        assert R.candidatos(b,need('movimento'))==[]
        m,im,p=R.amostra(b,c)
        assert m['sha256']==d['sha256'] and m['reuso_biblioteca'] and not m['direitos_aprovados']
        assert im.size==(800,600)
        verdict=V.decidir(need(),{**c,'aquisicao':m},{},tipo='foto')
        assert verdict['estado']=='INSUFICIENTE'
        p.write_bytes(b'bad')
        assert R.candidatos(b,need())==[]
        with pytest.raises(ValueError,match='E251-BYTES'):R.amostra(b,c)
    finally:b.fechar()

def test_library_candidate_is_not_automatic_coverage():
    c={'fonte':'biblioteca_v3','source_id':'cm-x','tipo':'foto'}
    result=V.fila_cobertura(need(),[c],lambda c,n:{'estado':'INSUFICIENTE','motivo':'SEM_PERTINENCIA'})
    assert result['estado']=='LACUNA_PENDENTE'


def test_explanatory_need_reuses_real_media_before_animation(tmp_path):
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    f=tmp_path/'a.jpg';Image.new('RGB',(800,600),'blue').save(f)
    try:
        d=b.ingerir(f,{'titulo':'glacier','url':'https://example.org/a.jpg'})
        n={**need(),'necessidade':'lacuna_explicativa','lacuna':'detalhe não mostrado'}
        c=R.candidatos(b,n)
        assert c and c[0]['sha_catalogo']==d['sha256'] and c[0]['publicar'] is False
        assert R.candidatos(b,{**n,'evidencia_visual':'movimento'})==[]
        assert R.candidatos(b,{**n,'necessidade':'territorio'})==[]
    finally:b.fechar()
