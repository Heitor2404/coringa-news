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


def test_usgs_curated_page_receipt_private_and_bound():
    from scripts.qa_pesquisa_documental_e246 import candidato_pagina_usgs,usgs_receipt
    from src.v4.formatos import filme_editorial as F
    import pytest
    need={'id':'n','evidencia_visual':'movimento'}
    row={'necessidade_id':'n','tipo':'video','pagina':'https://www.usgs.gov/media/videos/example','credito':'Declared curator credit'}
    c=candidato_pagina_usgs(row,need)
    url='https://prd-wret.s3.us-west-2.amazonaws.com/example.mp4'
    class T:
        def get(self,p,hosts,lim):
            assert p==row['pagina'] and hosts=={'www.usgs.gov'}
            return ('<h1>Source title</h1><p>Sources/Usage Public Domain</p><a href="'+url+'">Download video</a><a href="https://prd-wret.s3.us-west-2.amazonaws.com.evil.test/x.mp4">Download video</a>').encode()
    choices,hosts=usgs_receipt(c,T())
    assert len(choices)==1 and choices[0]['url']==url
    a={'sha256':'a'*64,'bytes':1200,'url_adquirida':url}
    x=P.licenca_documental(c,a)
    assert F.recibo_documental_valido(x) and x['rights_status']=='REVIEW_PENDING'
    assert P.licenca_documental(c,{**a,'url_adquirida':'https://evil.test/a.mp4'}) is None
    assert P.licenca_documental({**c,'pagina':row['pagina']+'-other'},a) is None
    restored={**c,'fonte':'biblioteca_v3','recibo_restaurado':{'fonte':'usgs_pagina','pagina':c['pagina'],'aquisicao':a,'recibos':{'recibo_usgs':c['recibo_usgs']}}}
    assert P.licenca_documental(restored,a)==x
    with pytest.raises(ValueError,match='USGS-PAGINA'):
        candidato_pagina_usgs({**row,'pagina':'https://www.usgs.gov.evil.test/media/videos/example'},need)
    with pytest.raises(ValueError,match='USGS-TIPO-EVIDENCIA'):
        candidato_pagina_usgs({**row,'tipo':'foto'},need)
    class Restricted(T):
        def get(self,*args):return super().get(*args).replace(b'Public Domain',b'Copyright')
    with pytest.raises(ValueError,match='USGS-LICENCA'):usgs_receipt(c,Restricted())

def test_credit_compacts_actual_commons_suffix_without_truncating_attribution():
    from src.v4.formatos.ponte_cobertura_filme import credito_em_tela
    assert credito_em_tela('"Landscape" — Author Name (CC BY 2.0), via Wikimedia Commons')=='Author Name (CC BY 2.0), via Wikimedia Commons'
    assert credito_em_tela('Archive — Full institutional credit')=='Archive — Full institutional credit'


def test_caption_groups_respect_a_real_narration_pause():
    from src.v4.formatos.legenda_sync import grupos
    words = [{'w': 'Maré.', 's': 0.0, 'e': 0.2}, {'w': 'Depois', 's': 2.0, 'e': 2.55}]
    groups = grupos(words, maximo=3)
    assert [group['txt'] for group in groups] == ['Maré.', 'Depois']
    assert groups[0]['fim'] < 1.0


def test_measured_word_end_survives_voice_caption_round_trip():
    from src import voz
    from src.v4.formatos.diretor_visual_e202 import palavras_de_caps
    original = [{'w': 'Maré', 'start': .1, 'end': .34}, {'w': 'alta', 'start': .5, 'end': .86}]
    restored = palavras_de_caps(voz.legendas(original, set()))
    assert [word['e'] for word in restored] == [.34, .86]
    assert palavras_de_caps([{'end': .8, 'words': [{'w': 'MARÉ', 's': .2}]}])[0]['e'] == .8


def test_e305_sync_failure_never_leaves_renderable_props(tmp_path):
    import json
    from scripts.qa_documentario_integral_e254 import gate_sincronia
    gate={'pronto_para_tts':True,'pronto_para_render_privado':True}
    for sync in ({'ok':False},{},{'ok':'true'}):
        (tmp_path/'props.json').write_text('{}')
        assert not gate_sincronia(tmp_path,gate,sync,64)
        assert not (tmp_path/'props.json').exists()
        data=json.loads((tmp_path/'integral.json').read_text())
        assert data['pronto_para_render_privado'] is False and data['publicar'] is False
        assert data['motivo']=='SINCRONIA_MEDIDA_REPROVADA'
    assert gate_sincronia(tmp_path,gate,{'ok':True},64)
    assert json.loads((tmp_path/'sincronia-medida.json').read_text())['ok'] is True
