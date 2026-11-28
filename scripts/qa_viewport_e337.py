"""E337: compare exact same private sources/time, no new semantic approval."""
from pathlib import Path
from scripts import qa_replay_multitema_e330 as E,qa_recuperacao_real_e333 as L
def main():
    cfg=E.read('benchmarks/e330/replay.json');root=Path('stage_documental/e337');root.mkdir(parents=True,exist_ok=False)
    meta=E.api('');E.check(meta['private'] is True and meta['id']==1454059520 and cfg['publish'] is False,'E337-COFRE')
    releases={r['tag_name']:r for r in E.listar_releases(300)}
    result={'publish':False,'new_ai':0,'new_tts':0,'semantic_approval':False,'full_documentary':False,'records':[]}
    for row in cfg['cases']:
        try:
            run=L.run_one if row['id']=='lava' else E.run_one
            r=run(row,cfg['ref'],releases,root,composition='PRIVATE_V3')
            props=E.read(root/row['id']/'props.json')
            s=props['shots'][0]
            r['trial_authorized']=s.get('documentary_observed_viewport_trial') is True
            r['viewport']=s.get('documentary_viewport')
            r['dimensions']=s.get('source_dimensions')
            r['integral_required']=s.get('documentary_integral_required',False)
            result['records'].append(r)
        except Exception as exc:result['records'].append({'id':row['id'],'status':'BLOCKED','reason':str(exc)[:1000]})
        E.write(root/'replay.json',result)
    E.check(all(r['status']=='READY_PRIVATE_FRAGMENT' for r in result['records']),'E337-PREPARACAO')
if __name__=='__main__':main()
