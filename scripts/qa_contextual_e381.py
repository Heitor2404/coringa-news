"""Private contextual fragment from the actual E378 cached lead.
No factual coverage, no new search, no persistent stock bytes or MP4."""
import json,os,subprocess
from pathlib import Path
from src.v4.formatos import stock_contextual_e381 as E,filme_editorial as F
from src.v4.fontes_contextuais_e359 import pixabay
from src.v4.cache_stock_e365 import CacheStock
from src.v4.aquisicao_documental import Transporte
from scripts.qa_documentario_geografia_e219 import frame,probe
def main():
    root=Path('stage_documental/e381');root.mkdir(parents=True,exist_ok=True)
    public=Path('motor4/remotion/public')
    t=Transporte(max_http=1,max_bytes=18_000_000,max_wait=8)
    class Replay(CacheStock):
        def fetch(self,provider,request,load):
            def unavailable():raise ValueError('CACHE_MISS_NO_REQUEST')
            return super().fetch(provider,request,unavailable)
    n=dict(id='context',necessidade='registro',evidencia_visual='contexto',exigir_evidencia_direta=False,sujeito='Chuva na janela',mostrar='Contexto visual de chuva em janela',fatos=['context-only-fixture'],preferir_imersao_vertical=True)
    row=dict(status='PENDING',publish=False,semantic_approval=False,proof_factual=False,new_ai=0,new_tts=0)
    try:
        r=pixabay('rain falling window',cache=Replay(os.environ['CORINGA_STOCK_CACHE_DB']))
        report=dict(id=n['id'],stock_contextual=dict(estado=r['status'],prova_factual=False,publicar=False,candidatos=r.get('candidates',[])))
        if not r.get('cache_hit'):raise ValueError('CACHE_MISS_NO_REQUEST')
        with E.materializar(n,report,'217105',t,public) as asset:
            plan=E.previa(n,asset,start=1.0,span=3.2)
            # Keep all derivative media and props inside the temporary session.
            stage=Path(asset['local_source']).parent
            props=F.preparar(plan,stage/'preview',public,fragmento_misto=True)
            video=stage/'context-preview.mp4'
            subprocess.run(['npx','--no-install','remotion','render','remotion/src/index.ts','FilmeEditorial',str(video.resolve()),'--props='+str(Path(props['props']).resolve()),'--codec=h264','--scale=0.5','--muted','--concurrency=2','--public-dir=remotion/public','--log=error'],cwd='motor4',check=True,timeout=300)
            w,h,dur=probe(video)
            if (w,h)!=(540,960) or abs(dur-3.2)>.1:raise ValueError('E381-RENDER')
            for j,at in enumerate((.4,1.6,2.8)):frame(video,at,width=540).convert('RGB').save(root/f'preview-{j}.jpg',quality=87)
            row.update(status='PRIVATE_CONTEXT_RENDERED_PENDING_REVIEW',asset_sha256=asset['expected_sha256'],source_page=asset['page'],dimensions=[w,h],duration_s=dur)
            src=Path(asset['local_source']);copy=public/'film_editorial'/(asset['expected_sha256']+'.mp4')
        row['ephemeral_cleanup_verified']=not src.exists() and not copy.exists()
        if not row['ephemeral_cleanup_verified']:raise ValueError('E381-CLEANUP')
    except Exception as exc:row.update(status='ERROR',reason=type(exc).__name__+': '+str(exc)[:160])
    (root/'proof.json').write_text(json.dumps({**row,'transport':t.resumo()},ensure_ascii=False,indent=2))
    print('E381',row['status'])
if __name__=='__main__':main()
