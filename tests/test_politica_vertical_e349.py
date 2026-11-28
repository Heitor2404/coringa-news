from src.midia import reter_video_vertical
from src.v4.formatos.imersao_documental_e328 import classificar_ocupacao

def test_vertical_reservation_retains_first_two_and_no_extra_results():
    rows=[{'id':i,'w':1920,'h':1080} for i in range(5)]
    rows.append({'id':5,'w':1080,'h':1920})
    assert [r['id'] for r in reter_video_vertical(rows,3)]==[0,1,5]
    rows[-1]['w']=100
    assert [r['id'] for r in reter_video_vertical(rows,3)]==[0,1,2]

def test_occupancy_is_advisory_and_observed_crop_changes_priority():
    assert classificar_ocupacao(.3164)['estado']=='ALTERNATIVA_PRIORITARIA'
    assert classificar_ocupacao(.3164,.5625)['estado']=='ACEITAVEL_CANDIDATA'
    assert classificar_ocupacao(1)['estado']=='PREFERENCIAL'
    assert classificar_ocupacao(None)['estado']=='DIMENSAO_PENDENTE'
    assert not classificar_ocupacao(.1)['excluir_automaticamente']
