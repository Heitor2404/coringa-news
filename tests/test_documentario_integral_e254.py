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
