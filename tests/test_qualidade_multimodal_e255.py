from src.v4.formatos import revisao_documental as R,cobertura_documental as C
from scripts.qa_pesquisa_documental_e246 import sample
from PIL import Image
import io

def evidence(box):
    return {'classe':'direta','detalhe':'Elemento concreto descrito na imagem original',
            'escala':'xy_0_1000','bbox':dict(zip(('esquerda','topo','direita','base'),box))}

def test_legibility_depends_on_inspected_pixels():
    e=R.normalizar_evidencia_direta(evidence([331,273,353,303]))
    assert not R.medir_legibilidade_foto(e,[960,230])['suficiente']
    assert R.medir_legibilidade_foto(e,[4000,3000])['suficiente']
    assert R.normalizar_evidencia_direta(evidence([0,0,1.5,1000])) is None
    n={'id':'n','evidencia_visual':'estatica','exigir_evidencia_direta':True,'exigir_legibilidade':True}
    c={'aquisicao':{'sha256':'a'*64}}
    r={'necessidade_id':'n','sha256_origem':'a'*64,'revisao_id':'r','px':[960,230],
       'resposta':{'veredito':'pertinente','natureza_visual':'registro_compativel','evidencia_direta':evidence([331,273,353,303])}}
    assert R.decidir(n,c,r,tipo='foto')['motivo']=='DETALHE_PEQUENO_NA_AMOSTRA'
    r['px']=[4000,3000]
    assert R.decidir(n,c,r,tipo='foto')['estado']=='PERTINENTE_PRIVADO'

def test_routes_never_make_failed_search_an_animation():
    n={'id':'n','fatos':['f'],'mostrar':'ação específica','necessidade':'lacuna_explicativa','lacuna':'interior'}
    def row(reason):
        return {'estado':'LACUNA_PENDENTE','rodadas':[{'cobertura':{'trilha':[{'decisao':{'motivo':reason}}]}}]}
    assert C.encaminhar(n,row('ORIGEM_NAO_AUTORIZADA'))['rota']=='REPLANEJAR_REGISTRO'
    assert C.encaminhar(n,row('SEM_PERTINENCIA'))['animacao_autorizada'] is False
    assert C.encaminhar({**n,'necessidade':'registro'},row('SEM_PERTINENCIA'))['rota']=='REPLANEJAR_REGISTRO'
    assert C.encaminhar(n,{'estado':'DELEGAR_ATLAS'})['rota']=='ATLAS'
    assert C.encaminhar(n,{'estado':'CANDIDATO_PRIVADO_REVISADO'})['rota']=='REGISTRO_REAL'

def test_oversized_original_uses_declared_thumbnail_without_extra_http(tmp_path):
    class T:
        max_bytes=1000000
        bytes=0
        def get(self,url,hosts,cap):
            assert url=='https://thumb.wikimedia.org/a.jpg' and 'thumb.wikimedia.org' in hosts
            b=io.BytesIO();Image.new('RGB',(800,600)).save(b,format='JPEG');return b.getvalue()
    c={'tipo':'foto','fonte':'commons','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA',
       'url':'https://upload.wikimedia.org/a.jpg','tamanho_declarado':2000000,
       'variantes':[{'url':'https://thumb.wikimedia.org/a.jpg'}]}
    m,im,p=sample(c,tmp_path,T())
    assert m['width']==800 and p.exists()
