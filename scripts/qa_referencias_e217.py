"""Replay actual prior source/solver audit; no new source or artistic approval."""
import json
from pathlib import Path
from src.v4.formatos import prova_rotas_e40 as E40, diretor_visual_e202 as D

def read(p):return json.loads(Path(p).read_text())
def main():
    prev=read('fonte_e217/E40_REAL.json')
    manifest=read('benchmarks/e12_independent_planar_json_v1.json')
    cs=E40.esquemas_e12(manifest,prev['fonte_e12'])
    assert cs
    out=[]
    for c in cs:
        n={'id':'a','necessidade':'lacuna_explicativa','mostrar':'Movimento entre as juntas declaradas',
           'lacuna':'Visualizar relação cinemática isolada','fatos':['f']}
        rev={'id':'a','acao':n['mostrar'],'fatos':['f'],'origem':'CURADORIA_HUMANA',
             'midia_adequada':False,'justificativa':'Fixture editorial de laboratório, não busca de mídia real',
             'motivo':'IMPOSSIVEL_FILMAR','alvo_tecnico':c['alvo'],'exige_contorno_industrial':False}
        ref={**c,'acao_revisada':n['mostrar'],'fatos_revisados':['f']}
        r=D.selecionar_complemento(n,rev,[ref])
        assert r['rota']['decisao'] and not r['pronto_para_render']
        assert D.selecionar_complemento(n,{**rev,'exige_contorno_industrial':True},[ref])['rota']['decisao'] is None
        assert D.selecionar_complemento(n,{**rev,'midia_adequada':True},[ref])['decisao']=='USAR_MIDIA_REAL'
        out.append(r)
    Path('E217_REAL.json').write_text(json.dumps({'resultados':out,'publish':False,
        'natureza':'replay de auditorias reais E12, lacunas manuais LAB, sem novo render'},ensure_ascii=False,indent=2))
    print('E217-REAL',len(out),'referencias; nenhuma promovida a contorno industrial')
if __name__=='__main__':main()
