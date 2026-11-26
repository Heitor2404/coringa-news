"""Actual registered clip bytes and real footage; assisted scope only."""
import json,shutil,math
from pathlib import Path
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F,politica_animacao as PA
from src.v4.formatos.direcao_short_e306 import diagnosticar
def main():
    root=Path('stage_documental/e314');root.mkdir(parents=True,exist_ok=True)
    src=Path('stage_lock/ECLUSA_HIDRAULICA_MODERNA_PRIVADA.mp4')
    clip=root/'lock.mp4';shutil.copyfile(src,clip)
    entry=PA.POLICY['external_candidates']['render_eclusa_hidraulica_2d.py']
    need={'id':'mechanism','fatos':['f2'],'mostrar':'Entrada, enchimento e saída de um navio',
          'sujeito':'Ciclo de eclusa','necessidade':'lacuna_explicativa','lacuna':'Conduto interno não visível na tomada externa',
          'papel_visual':'mecanismo','evidencia_visual':'movimento'}
    packet={'necessidade_id':need['id'],'fatos':need['fatos'],'acao':need['mostrar'],'lacuna':need['lacuna'],
            'origem':'INSPECAO_ASSISTIDA_PRIVADA','revisao_id':'E213-reuso-E314','midia_adequada':False,
            'motivo_lacuna':'IMPOSSIVEL_FILMAR','justificativa':'A tomada externa não mostra o conduto interno; reutilizar candidato de laboratório E213, sem homologação.',
            'renderer':'render_eclusa_hidraulica_2d.py','local_source':str(clip),
            'sha256':entry['reference_sha256'],'referencia':entry['source'],'publicar':False,'direitos_aprovados':False}
    video=Path('tests/midia/video_horizontal_navio.mp4');target=root/'ship.mp4';shutil.copyfile(video,target)
    meta=json.loads(video.with_suffix('.json').read_text())
    n={'id':'ship','fatos':['f1'],'mostrar':'Vista da proa no trânsito do canal','sujeito':'Navio em trânsito',
       'necessidade':'registro','papel_visual':'contexto','evidencia_visual':'contexto','exigir_evidencia_direta':True}
    c={'fonte':'commons','source_id':'ship','tipo':'video','pagina':meta['pagina'],'credito':meta['autor']+' · '+meta['licenca'],
       'licenca':meta['licenca'],'local_source':str(target),'aquisicao':{'sha256':P.sha(target),'width':1280,'height':720,'duration_s':6.006},
       'decisao':{'estado':'PERTINENTE_PRIVADO','necessidade_id':'ship','revisao_id':'E314-assisted-context','publicar':False,'direitos_aprovados':False},
       'selecao_janela':{'source_in_seconds':0,'duracao_s':3}}
    report={'publish':False,'triagem':[n,need],'cobertura':[{'necessidade_id':'ship','estado':'CANDIDATO_PRIVADO_REVISADO',
         'selecionado':['commons','ship'],'rodadas':[{'pesquisa':{'candidatos':[c]}}]},
         {'necessidade_id':'mechanism','estado':'LACUNA_PENDENTE','rodadas':[]}]}
    case={'tema':'Registro e princípio de eclusa','chapters':[{'title':'Registro e ilustração','needs':['ship','mechanism']}]}
    chosen,gate=P.preparar_cobertura(report,case,animacoes={'mechanism':packet},minimo_s=1.4)
    assert gate['pronto_para_tts'],gate
    span=chosen['mechanism']['cap'];assert span==chosen['mechanism']['min']
    frames=90+round(span*30)
    p=P.plano(case,chosen,[frames])
    assert [x['type'] for x in p['shots']]==['video','animation_clip']
    assert diagnosticar(p)['pronto_para_analise_visual']
    F.preparar(p,root,Path('motor4/remotion/public'),fragmento_misto=True)
    props=json.loads((root/'props.json').read_text())
    assert props['private_review_only'] and props['shots'][1]['asset'].startswith('animation_e213/')
    for bad in ({**packet,'sha256':'0'*64},{**packet,'fatos':['wrong']},{**packet,'midia_adequada':True},
                {**packet,'motivo_lacuna':'BUSCA_SEM_REGISTRO_ADEQUADO'},{**packet,'publicar':True}):
        _,g=P.preparar_cobertura(report,case,animacoes={'mechanism':bad},minimo_s=1.4)
        assert not g['pronto_para_tts'],g
    from copy import deepcopy
    q=deepcopy(p);q['shots'][1]['end']-=1/30;q['duracao']-=1/30
    assert not F.avaliar(q,fragmento_misto=True)['pronto']
    q=deepcopy(p);q['publicar']=True
    assert not F.avaliar(q,fragmento_misto=True)['pronto']
    q=deepcopy(p);q['shots'][1]['animation_review']['fatos']=['wrong']
    assert not F.avaliar(q,fragmento_misto=True)['pronto']
    (root/'proof.json').write_text(json.dumps({'publish':False,'visual_approval':'PENDING','gate':gate,'duracao':p['duracao'],
       'scope':'Integração privada, não prova de que o navio filmado está na eclusa ilustrada.', 'plan':p},ensure_ascii=False))
if __name__=='__main__':main()
