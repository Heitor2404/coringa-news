from pathlib import Path
from src.v4.formatos import revisao_documental as R,ponte_cobertura_filme as P
def test_e254_rejects_generic_association():
    need={'id':'n','exigir_evidencia_direta':True,'evidencia_visual':'estatica'}
    c={'aquisicao':{'sha256':'a'*64}}
    r={'sha256_origem':'a'*64,'necessidade_id':'n','revisao_id':'r','resposta':{'veredito':'pertinente','natureza_visual':'registro_compativel'}}
    assert R.decidir(need,c,r,tipo='foto')['motivo']=='EVIDENCIA_DIRETA_NAO_LOCALIZADA'
    r['resposta']['evidencia_direta']={'classe':'direta','detalhe':'Detalhe identificavel de evidencia visual direta','bbox':[.1,.1,.7,.8]}
    assert R.decidir(need,c,r,tipo='foto')['estado']=='PERTINENTE_PRIVADO'
def test_e254_insufficient_coverage_never_starts_voice():
    case={'chapters':[{'needs':['n']}]}
    chosen,gate=P.preparar_cobertura({'publish':False,'triagem':[{'id':'n'}],'cobertura':[{'necessidade_id':'n','estado':'LACUNA_PENDENTE'}]},case)
    assert not chosen and not gate['pronto_para_tts'] and gate['capacidade_s']==0


def test_nasa_documentary_receipt_reaches_private_bridge_without_rights_promotion():
    from src.v4.formatos import filme_editorial as F
    a={'sha256':'a'*64,'bytes':1200,'url_adquirida':'https://images-assets.nasa.gov/video/EXAMPLE/EXAMPLE~medium.mp4'}
    c={'fonte':'nasa_video','pagina':'https://images.nasa.gov/details/EXAMPLE','credito':'NASA — individual review pending','licenca':'',
       'recibo_nasa':{'nasa_id':'EXAMPLE','asset_response_sha256':'b'*64,'direitos':'PENDENTE_AUDITORIA_INDIVIDUAL',
                      'variantes_declaradas':[{'href_https':a['url_adquirida']}]}}
    x=P.licenca_documental(c,a)
    assert x['license']=='REVIEW_PENDING' and F.recibo_documental_valido(x)
    assert x['documentary_receipt']['direitos_aprovados'] is False
    c['pagina']='https://images.nasa.gov/details/OTHER'
    assert P.licenca_documental(c,a) is None

def test_archive_private_receipt_normalizes_explicit_license_and_survives_restore():
    from src.v4.formatos import filme_editorial as F
    a={'sha256':'a'*64,'bytes':1200,'url_adquirida':'https://ia123.us.archive.org/12/items/example/video.mp4'}
    c={'fonte':'archive_video','pagina':'https://archive.org/details/example','credito':'Author','licenca':'CC0 1.0',
       'recibo_archive':{'identifier':'example','metadata_sha256':'b'*64,'licenca_url':'https://creativecommons.org/publicdomain/zero/1.0',
          'direitos':'PENDENTE_AUDITORIA_INDIVIDUAL','variantes':[{'url':a['url_adquirida'],'size':1200,'md5':'c'*32}]}}
    x=P.licenca_documental(c,a)
    assert x['license']=='CC0' and F.recibo_documental_valido(x)
    restored={**c,'fonte':'biblioteca_v3','recibo_restaurado':{'fonte':'archive_video','pagina':c['pagina'],'aquisicao':a,
        'recibos':{'recibo_archive':c['recibo_archive']}}}
    assert P.licenca_documental(restored,a)==x
    assert P.licenca_documental(restored,{**a,'bytes':1}) is None
    assert P.licenca_documental({**c,'licenca':'CC BY 4.0'},a) is None
    assert P.licenca_documental({**c,'recibo_archive':None},a) is None


def test_preflight_respects_verified_minimum_and_uses_feasible_capacity():
    from scripts.qa_documentario_integral_e254 import prever_tempos
    import pytest,math
    ids=[str(i) for i in range(16)]
    case={'chapters':[{'needs':ids[:8]},{'needs':ids[8:]}]}
    chosen={i:{'min':3.7,'cap':3.8} if i=='0' else {'min':1.4,'cap':3.8} for i in ids}
    ends=prever_tempos(case,chosen)
    assert ends[-1]==1800
    assert ends[0]>=math.ceil(3.7*30)+7*108
    with pytest.raises(ValueError,match='CAPACIDADE'):
        prever_tempos(case,{i:{'min':1.4,'cap':3.6} for i in ids})
    with pytest.raises(ValueError,match='TEMPO-PREFLIGHT'):
        prever_tempos(case,{**chosen,'0':{'min':3.9,'cap':3.8}})
