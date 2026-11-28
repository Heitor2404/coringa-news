"""Stage new or already discovered gap candidates with no semantic approval."""
import copy,hashlib,json,shutil,sys
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3.biblioteca import restaurar_catalogo
from src.v3 import pacote_biblioteca as P
from src.v4 import acervo_v4 as A
from src.v4.aquisicao_documental import Transporte
from src.v4.formatos import diretor_visual_e202 as D,revisao_documental as R,reuso_documental as RE,ponte_cobertura_filme as PF,filme_editorial as FE
from scripts import qa_pesquisa_documental_e246 as Q

def candidatos_anteriores(row):
    out=[];seen=set()
    for rd in row.get('rodadas') or []:
        for c in (rd.get('pesquisa') or {}).get('candidatos') or []:
            k=(c.get('fonte'),c.get('source_id') or c.get('url'))
            if k in seen or c.get('fonte')=='biblioteca_v3' or c.get('decisao') or c.get('aquisicao'):continue
            seen.add(k);out.append(copy.deepcopy(c))
    return out

def main():
    old=json.loads(Path(sys.argv[1]).read_text());spec=json.loads(Path(sys.argv[2]).read_text());root=Path(sys.argv[3])
    if old.get('publish') is not False or spec.get('publish') is not False:raise ValueError('E266-PRIVADO')
    case=next(c for c in spec['cases'] if c['id']==old['case']['id'])
    tri={n['id']:n for n in D.triagem_documental(case['necessidades'],case['fatos'],progressivo=True)}
    prev={n['id']:n for n in old['triagem']}
    gaps=[row for row in old['cobertura'] if row['estado']=='LACUNA_PENDENTE']
    root.mkdir(parents=True,exist_ok=False);assets=root/'originais';assets.mkdir()
    lib,_=restaurar_catalogo(db=root/'biblioteca.sqlite3',armazem=root/'biblioteca')
    t=Transporte(max_http=18,max_bytes=65_000_000,max_wait=25)
    reports=[];saved=set()
    try:
        for idx,row in enumerate(gaps):
            nid=row['necessidade_id'];n=tri[nid]
            if RE.escopo(n)!=RE.escopo(prev[nid]):raise ValueError('E266-ESCOPO')
            if n['necessidade']=='territorio':continue
            attempted={(q.get('tipo'),q.get('fonte'),q['consulta'].casefold()) for rd in row.get('rodadas',[]) for q in (rd.get('pesquisa') or {}).get('buscas',[]) if isinstance(q.get('consulta'),str)}
            discovery=A.pesquisar_cobertura(n,max_buscas=4,max_candidatos=64,progressivo=True,buscas_vistas=attempted)
            # Preserve both old discoveries and new alternatives; choose at
            # most two actual samples per obligation in this bounded QA pass.
            candidates=R.ordenar_candidatos(n,discovery['candidatos']+candidatos_anteriores(row))
            pending=[];errors=[];seen=set();old_http=t.max_http;old_bytes=t.max_bytes
            later=len(gaps)-idx
            t.max_http=t.http+(old_http-t.http)//later
            t.max_bytes=t.bytes+(old_bytes-t.bytes)//later
            try:
                for c in candidates:
                    k=(c.get('fonte'),c.get('source_id') or c.get('url'))
                    if k in seen:continue
                    seen.add(k)
                    if len(pending)>=2 or t.http>=t.max_http or t.bytes>=t.max_bytes:break
                    if c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA':continue
                    if c.get('fonte') not in ('commons','commons_video','nasa','nasa_video','archive_video','figshare'):continue
                    if c.get('fonte') in ('commons','commons_video','figshare') and c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA':continue
                    try:
                        a,im,p=Q.sample(c,assets,t,progressivo=True,max_variantes=2,min_video_px=FE.MIN_VIDEO_COMPOSITION_PX)
                        if PF.licenca_documental(c,a) is None:raise ValueError('PROCEDENCIA_PENDENTE')
                        if a['bytes']>P.MAX_TOTAL:raise ValueError('LIMITE_PACOTE_ORIGINAL')
                        h=a['sha256'];d=lib.ingerir(p,{'titulo':c['titulo'],'desc':c.get('descricao',''),'url':a['url_adquirida'],'pagina':c.get('pagina'),'fonte':c['fonte'],'wh':[a['width'],a['height']],'licenca_prova':'Revisao privada; direitos pendentes'})
                        if h in {x['aquisicao']['sha256'] for x in pending}:continue
                        lib.gravar_analise(h,'documental:recibo:'+hashlib.sha256(str(c.get('pagina') or c.get('source_id')).encode()).hexdigest(),{'publicar':False,'direitos_aprovados':False,'aquisicao':a,'fonte':c['fonte'],'pagina':c.get('pagina'),'licenca_declarada':c.get('licenca'),'credito_declarado':c.get('credito'),'recibos':{k:c[k] for k in ('recibo_nasa','recibo_archive','recibo_cientifico','recibo_usgs') if k in c}},origem='E266')
                        scope=RE.escopo(n)
                        hint={'sha256':h,'pagina':c.get('pagina'),'tipo':c['tipo'],'estado':'BYTES_VERIFIED_SEMANTICS_PENDING','publicar':False}
                        key='documental:'+hashlib.sha256(json.dumps({'contrato':'E266.pista','escopo':scope},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                        lib.gravar_analise(h,key,{'publicar':False,'direitos_aprovados':False,'escopo_pesquisa':scope,'pista_aquisicao_pendente':hint},origem='E266')
                        saved.add(d['id'])
                        im=im.copy();im.thumbnail((1000,650))
                        board=Image.new('RGB',(1080,720),'#101c28');draw=ImageDraw.Draw(board)
                        draw.text((15,12),nid+' '+c['tipo']+' '+h[:12]+' PENDENTE - NAO APROVADO',fill='white')
                        board.paste(im,((1080-im.width)//2,40))
                        board.save(root/(nid+'-'+str(len(pending)+1)+'.jpg'),quality=90)
                        pending.append({'titulo':c['titulo'],'pagina':c['pagina'],'tipo':c['tipo'],'aquisicao':a,'id':d['id'],'estado':'BYTES_VERIFIED_SEMANTICS_PENDING','publicar':False})
                    except Exception as e:errors.append({'source_id':c.get('source_id'),'motivo':str(e)[:180]})
            finally:t.max_http=old_http;t.max_bytes=old_bytes
            reports.append({'id':nid,'buscas':discovery['buscas'],'candidatos_anteriores':len(candidatos_anteriores(row)),'candidatos_novos':len(discovery['candidatos']),'amostras':pending,'falhas':errors,'publicar':False})
        lib.exportar_manifesto(root/'manifesto-revisoes.jsonl')
        for mid in sorted(saved):
            dest=root/'checkpoints'/mid;P.exportar(lib,[mid],dest,incluir_analises_privadas=True);shutil.make_archive(str(dest),'zip',root_dir=dest)
    finally:lib.fechar()
    result={'publicar':False,'direitos_aprovados':False,'visao':0,'amostras':sum(len(x['amostras']) for x in reports),'necessidades':reports,'rede':t.resumo()}
    (root/'lacunas.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print('E266 LACUNAS',[(x['id'],len(x['amostras'])) for x in reports],t.http,t.bytes,flush=True)
if __name__=='__main__':main()
