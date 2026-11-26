import json
from src.v4 import fontes_contextuais_e359 as F
class R:
    status_code=200
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def iter_content(self,n):yield json.dumps(self.data).encode()
class S:
    def __init__(self,data):self.data=data;self.calls=[]
    def get(self,url,**kw):self.calls.append((url,kw));return R(self.data)
def test_pexels_portrait_and_scope():
    row=dict(id=1,url='https://www.pexels.com/video/test-1/',user={'name':'A'},duration=5,video_files=[
        dict(file_type='video/mp4',link='https://videos.pexels.com/a.mp4',width=1920,height=1080),
        dict(file_type='video/mp4',link='https://videos.pexels.com/b.mp4',width=720,height=1280),
        dict(file_type='video/mp4',link='https://evil.test/b.mp4',width=1080,height=1920)])
    s=S({'videos':[row]})
    r=F.pexels('factory',session=s,key='test')
    c=r['candidates'][0]
    assert c['variant']['h']==1280 and c['editorial_scope']=='CONTEXTO_APENAS'
    assert not c['publish'] and not c['permanent_cache']
    assert s.calls[0][1]['params']['orientation']=='portrait'
    assert F.pesquisar('factory',necessidade={'evidencia_visual':'movimento'})['status']=='ESCOPO_NAO_CONTEXTUAL'
def test_no_key_no_network(monkeypatch):
    monkeypatch.delenv('PEXELS_API_KEY',raising=False);monkeypatch.delenv('PIXABAY_API_KEY',raising=False)
    s=S({})
    assert F.pexels('factory',session=s)['status']=='CHAVE_AUSENTE'
    assert F.pixabay('factory',session=s)['status']=='CHAVE_AUSENTE'
    assert not s.calls
def test_pixabay_provenance():
    s=S({'hits':[dict(id=2,pageURL='https://pixabay.com/videos/test-2/',user='B',duration=7,tags='factory',
        videos={'large':dict(url='https://cdn.pixabay.com/video/a.mp4',width=720,height=1280)})]})
    c=F.pixabay('factory',session=s,key='test')['candidates'][0]
    assert c['author']=='B' and c['page'].endswith('2/') and c['rights']=='REVISAR_PAGINA_INDIVIDUAL'
