from copy import deepcopy
from pathlib import Path
from scripts.qa_comparacao_e311 import preparar
from src.v4.formatos import ponte_cobertura_filme as P
from src.v4.formatos.direcao_short_e306 import diagnosticar

def test_actual_bridge_and_negative_packets(tmp_path,monkeypatch):
    import shutil
    src=Path(__file__).resolve().parents[1]/'tests/midia'
    monkeypatch.chdir(tmp_path)
    (Path('tests')/'midia').mkdir(parents=True)
    for name in ('foto_horizontal_roraima','foto_vertical_salto_angel'):
        for ext in ('.jpg','.json'):shutil.copyfile(src/(name+ext),Path('tests/midia')/(name+ext))
    case,chosen,p=preparar('stage_documental/e311','public')
    assert not diagnosticar(p)['pronto_para_analise_visual'] # pair alone is not sufficient to approve a film
    plain=P.plano({**case,'comparacoes_revisadas':[]},chosen,[180])
    assert [(s['asset'],s['start'],s['end']) for s in p['shots']]==[(s['asset'],s['start'],s['end']) for s in plain['shots']]
    for key,value in [('sha256','0'*64),('fatos',['other']),('revisao_id','other'),('criterio_observado','other')]:
        bad=deepcopy(case);bad['comparacoes_revisadas'][0]['membros'][1][key]=value
        out=P.plano(bad,chosen,[180])
        assert out['shots']==plain['shots']
        assert out['comparacoes_documentais'][0]['estado']=='PAR_SEM_VINCULO_OU_FONTES_DISTINTAS'
    bad=deepcopy(case);bad['comparacoes_revisadas'][0]['inferir_cronologia']=True
    assert P.plano(bad,chosen,[180])['shots']==plain['shots']

def test_panel_crop_preserves_observed_region_and_refuses_unreadable():
    from src.v4.formatos.comparacao_documental_e311 import recorte_painel
    box=[.35,.20,.83,.30];crop=recorte_painel(box,1800,1200)
    assert crop[0]<=box[0] and crop[1]<=box[1] and crop[2]>=box[2] and crop[3]>=box[3]
    assert abs((crop[2]-crop[0])*1800/((crop[3]-crop[1])*1200)-2.7)<1e-6
    assert recorte_painel([.5,.5,.51,.51],1800,1200) is None
    assert recorte_painel([0,0,1,1],946,1600) is None
