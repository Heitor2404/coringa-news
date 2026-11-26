import hashlib
from pathlib import Path
import pytest
from src.v4.formatos import stock_contextual_e381 as S,filme_editorial as F

def fixture():
    n=dict(id='n',necessidade='registro',evidencia_visual='contexto',exigir_evidencia_direta=False,sujeito='Chuva na janela',fatos=['f'],mostrar='Contexto visual de chuva',preferir_imersao_vertical=True)
    raw=b'fake test media bytes'
    c=dict(id='217105',provider='pixabay',page='https://pixabay.com/videos/id-217105/',author='Author',license_url=S.LICENSE,title='rain window',editorial_scope='CONTEXTO_APENAS',permanent_cache=False,publish=False,semantic_approval=False,variants=[dict(url='https://cdn.pixabay.com/video/fixture.mp4',w=720,h=1280,size=len(raw))])
    r=dict(id='n',stock_contextual=dict(estado='LEADS',prova_factual=False,publicar=False,candidatos=[c]))
    class T:
        def get(self,url,hosts,cap):
            assert hosts=={'cdn.pixabay.com'}
            return raw
    return n,r,c,T(),raw
def test_ephemeral_private_receipt_and_cleanup(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    n,r,c,t,raw=fixture()
    public=Path('public');(public/'film_editorial').mkdir(parents=True)
    with S.materializar(n,r,c['id'],t,public,probe=lambda p:(720,1280,10)) as a:
        assert F.recibo_documental_valido(a)
        plan=S.previa(n,a)
        assert plan['shots'][0]['source_display'].startswith(S.LABEL)
        assert plan['shots'][0]['evidence']=='representative'
        path=Path(a['local_source']);assert path.is_file()
        copy=public/'film_editorial'/(a['expected_sha256']+'.mp4');copy.write_bytes(raw)
        bad={**n,'exigir_evidencia_direta':True}
        with pytest.raises(ValueError,match='E381'):S.previa(bad,a)
        wrong={**a,'page':'https://pixabay.com/videos/id-999/'}
        assert not F.recibo_documental_valido(wrong)
    assert not path.exists() and not copy.exists()
@pytest.mark.parametrize('key,value',[('evidencia_visual','movimento'),('exigir_evidencia_direta',True),('necessidade','territorio')])
def test_context_scope_rejects_factual_needs(key,value):
    n,r,c,t,raw=fixture()
    with pytest.raises(ValueError,match='E381-SCOPE'):S.candidate_for({**n,key:value},r,c['id'])
def test_synthetic_rejected():
    n,r,c,t,raw=fixture()
    c['title']='AI generated rain'
    with pytest.raises(ValueError,match='E381-CANDIDATE'):S.candidate_for(n,r,c['id'])
