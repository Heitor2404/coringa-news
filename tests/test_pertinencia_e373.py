import json
from src.v4.fontes_culturais_e366 import smithsonian,object_hint
from src.v4.fontes_publicas_e354 import usgs
from src.v4.galerias_oficiais_e356 import candidatos
from src.v4.acervo_v4 import _candidato_documental
from src.v4.prioridade_fontes_e369 import candidato_promissor
class T:
    def __init__(self,raw):self.raw=raw
    def get(self,*a):return self.raw if isinstance(self.raw,bytes) else json.dumps(self.raw).encode()
def item(i,title,typ):
    return dict(id=str(i),title=title,content=dict(indexedStructured={'object_type':[typ]},descriptiveNonRepeating=dict(
      record_link='https://www.si.edu/object/'+str(i),data_source='Museum',
      online_media={'media':[dict(type='Images',idsId=str(i),content='https://ids.si.edu/ids/deliveryService/id/'+str(i),usage={'access':'CC0'})]})))
def test_smithsonian_reorders_before_cap_and_retains_artifact_intent():
    rows=[item(i,'Steam locomotive postage stamp','Stamp') for i in range(4)]+[item(4,'Steam locomotive photograph','Photograph')]
    d={};out=smithsonian('steam locomotive photograph',transport=T({'response':{'rows':rows}}),key='fixture',diagnostico=d)
    assert out[0]['titulo']=='Steam locomotive photograph' and len(out)==4
    assert d['eligible_media']==5 and d['retained_possible_mismatch']==3
    assert object_hint('locomotive postage stamp','Steam locomotive postage stamp',['Stamp'])=='SEM_INCOMPATIBILIDADE_DECLARADA'
    c=_candidato_documental(out[1],'smithsonian','foto')
    assert c['pista_objeto']=='POSSIVEL_REPRESENTACAO_DE_OUTRO_REFERENTE' and not c['publicar']
    assert not candidato_promissor({'necessidade':'registro','pesquisa':{'consultas_en':['steam locomotive']}},c)
def test_usgs_thumbnail_label_not_video_title():
    raw=b'<a href="/media/videos/kilauea-lava">Color photograph of lava fountain</a>'
    c=usgs('Kilauea lava','video',transport=T(raw))[0]
    assert c['titulo']=='kilauea lava' and c['descricao']=='Color photograph of lava fountain'
    assert c['recibo_fonte']['title_origin']=='PAGE_SLUG_NOT_OFFICIAL_TITLE'
def test_noaa_generic_label_uses_explicitly_marked_slug():
    raw=b'<section><p>Octopus</p><a href="/multimedia/deep-sea-octopus/">Watch Video</a></section>'
    c=candidatos('octopus','noaa','video',transport=T(raw))[0]
    assert c['titulo']=='deep sea octopus' and c['recibo_fonte']['title_origin']=='PAGE_SLUG_NOT_OFFICIAL_TITLE'

def test_subject_match_beats_unrelated_compatible_object_and_model_name():
    rows=[item(1,'John Stevens','Painting'),item(2,'Woman walking','Photograph'),item(3,'Steam locomotive postage stamp','Stamp'),item(4,'Steam locomotive photograph','Photograph')]
    out=smithsonian('steam locomotive photograph',transport=T({'response':{'rows':rows}}),key='fixture')
    assert [c['titulo'] for c in out[:2]]==['Steam locomotive photograph','Steam locomotive postage stamp']
    assert object_hint('Ford automobile','Ford Model T',['Automobile'])=='SEM_INCOMPATIBILIDADE_DECLARADA'
    assert object_hint('steam locomotive','Portrait of engineer',['Painting'])=='POSSIVEL_REPRESENTACAO_DE_OUTRO_REFERENTE'
