import json
from src.v4.cache_stock_e365 import CacheStock
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
def test_pexels_portrait_and_scope(tmp_path):
    row=dict(id=1,url='https://www.pexels.com/video/test-1/',user={'name':'A'},duration=5,video_files=[
        dict(file_type='video/mp4',link='https://videos.pexels.com/a.mp4',width=1920,height=1080),
        dict(file_type='video/mp4',link='https://videos.pexels.com/b.mp4',width=720,height=1280),
        dict(file_type='video/mp4',link='https://evil.test/b.mp4',width=1080,height=1920)])
    s=S({'videos':[row]})
    r=F.pexels('factory',session=s,key='test',cache=CacheStock(tmp_path/'stock.db'))
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
def test_pixabay_provenance(tmp_path):
    s=S({'hits':[dict(id=2,pageURL='https://pixabay.com/videos/test-2/',user='B',duration=7,tags='factory',
        videos={'large':dict(url='https://cdn.pixabay.com/video/a.mp4',width=720,height=1280)})]})
    c=F.pixabay('factory',session=s,key='test',cache=CacheStock(tmp_path/'stock.db'))['candidates'][0]
    assert c['author']=='B' and c['page'].endswith('2/') and c['rights']=='REVISAR_PAGINA_INDIVIDUAL'

def test_required_cache_and_24h_replay(tmp_path,monkeypatch):
    monkeypatch.delenv('CORINGA_STOCK_CACHE_DB',raising=False)
    s=S({'hits':[]})
    assert F.pixabay('test',session=s,key='test')['status']=='CACHE_24H_AUSENTE'
    assert not s.calls
    now=[1000.]
    cache=CacheStock(tmp_path/'stock.db',clock=lambda:now[0])
    first=F.pixabay('test',session=s,key='test',cache=cache)
    second=F.pixabay('test',session=s,key='test',cache=CacheStock(tmp_path/'stock.db',clock=lambda:now[0]))
    assert first['status']=='EMPTY' and not first['cache_hit'] and second['cache_hit']
    assert len(s.calls)==1
    now[0]+=24*3600
    assert not F.pixabay('test',session=s,key='test',cache=cache)['cache_hit']
    assert len(s.calls)==2
def test_disabled_context_no_network(monkeypatch):
    monkeypatch.delenv('CORINGA_STOCK_CONTEXT_ENABLED',raising=False)
    assert F.pesquisar('factory',necessidade={'evidencia_visual':'contexto'})['status']=='STOCK_OPT_IN_DESATIVADO'

def test_pixabay_alternate_portrait_without_dropping_original(tmp_path):
    def row(id,w,h):return dict(id=id,pageURL=f'https://pixabay.com/videos/id-{id}/',user='B',duration=7,
        tags='street pedestrian',type='film',videos={'large':dict(url=f'https://cdn.pixabay.com/video/{id}.mp4',width=w,height=h)})
    class Replies(S):
        def get(self,url,**kw):
            self.calls.append((url,kw))
            return R({'hits':[row(1,1920,1080)] if not kw['params']['q'].startswith('vertical') else [row(2,720,1280),row(1,1920,1080)]})
    session=Replies({});cache=CacheStock(tmp_path/'stock.db')
    r=F.pixabay_retrato('street pedestrian',session=session,key='test',cache=cache)
    assert [c['id'] for c in r['candidates']]==['2','1'] and len(session.calls)==2
    again=F.pixabay_retrato('street pedestrian',session=session,key='test',cache=cache)
    assert again['cache_hits']==[True,True] and len(session.calls)==2

def test_context_tags_before_unrelated_high_resolution_or_portrait():
    rows=[dict(id='irrelevant',title='basketball sports',variant={'w':2160,'h':3840}),
          dict(id='street',title='street pedestrian city',variant={'w':1920,'h':1080}),
          dict(id='portrait',title='street pedestrian urban',variant={'w':720,'h':1280})]
    result=F.ordenar_stock('vertical street pedestrian',rows)
    assert [x['id'] for x in result]==['portrait','street','irrelevant']
    assert F.pertinencia_stock('vertical street pedestrian',rows[1])==1
    assert len(result)==len(rows)
