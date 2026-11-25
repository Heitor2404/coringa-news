"""E247 private pilot, reuse E246 acquisition and E238-E244 video observations."""
import hashlib,sys,os
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_pesquisa_documental_e246 as Q
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import diretor_visual_e202 as D,direcao_eventos as DE,revisao_documental as R
from src.v3.biblioteca import restaurar_catalogo
from src.v4.aquisicao_documental import Transporte

def main():
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);caseid=sys.argv[3]
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    case=next(c for c in spec['cases'] if c['id']==caseid)
    out.mkdir(parents=True,exist_ok=True);assets=out/'originais';assets.mkdir(exist_ok=True)
    tri=D.triagem_documental(case['necessidades'],case['fatos'])
    lib,rest=restaurar_catalogo(db=out/'biblioteca.sqlite3',armazem=out/'biblioteca')
    from src.v4.formatos import reuso_documental as RE
    from src.v3 import pacote_biblioteca as PB
    pack=os.getenv('CORINGA_PACOTE_PRIVADO')
    if pack:
        lib.fechar()
        lib,rest=PB.restaurar(pack,db=out/'biblioteca.sqlite3',armazem=out/'biblioteca')
    t=Transporte(max_http=14,max_bytes=140_000_000,max_wait=30)
    adaptive='--adaptativa' in sys.argv[4:]
    budget=2;calls=0;boards=[];results=[];seen_bytes=set();reuses=0
    def ask(prompt,images):
        nonlocal calls
        if calls>=budget:raise RuntimeError('E247-ORCAMENTO-VISAO')
        calls+=1
        from src import gemini
        return gemini.json_visao(prompt,images,leve=True)
    def inspect(c,n):
        nonlocal reuses
        if calls>=budget:return {'estado':'ORCAMENTO','motivo':'VISAO_ESGOTADA'}
        if c.get('fonte') not in ('nasa','biblioteca_v3') and (c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or not list(Q.variants(c))):
            return {'estado':'INSUFICIENTE','motivo':'PROCEDENCIA_OU_VARIANTE_PENDENTE'}
        try:
            if c.get('fonte')=='biblioteca_v3':
                meta,im,p=RE.amostra(lib,c,probe=E.probe,frame=E.frame);reuses+=1
            else:meta,im,p=Q.sample(c,assets,t)
        except Exception as e:return {'estado':'FALHA_AQUISICAO','motivo':str(e)[:200]}
        c['aquisicao']=meta
        if hashlib.sha256(p.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('E247-SHA')
        if adaptive:
            key=(n['id'],meta['sha256'])
            if key in seen_bytes:return {'estado':'INSUFICIENTE','motivo':'BYTES_JA_INSPECIONADOS'}
            seen_bytes.add(key)
        m={'id':c.get('source_id') or meta['sha256'],'expected_sha256':meta['sha256'],
           'width':meta['width'],'height':meta['height'],'duration_s':meta['duration_s'],
           'local_source':str(p)}
        if c['tipo']=='foto':
            im.thumbnail((960,960))
            try:q=R.revisar_foto(m,im,n,ask)
            except Exception as e:
                boards.append((c,[im],'FALHA_VISAO'));return {'estado':'FALHA_VISAO','motivo':type(e).__name__}
            c['revisao']=q;dec=R.decidir(n,c,q,tipo='foto')
            boards.append((c,[im],dec['motivo']));return dec
        span=min(3.8,meta['duration_s']-.15)
        starts=E.windows(m,span,review_technical=True)
        a=starts[0][0] if starts else 0.
        # Short sources are sampled from their actual start, not a fixed 2s offset.
        if meta['duration_s']<9:a=0.
        positions=[a]
        other=max(0.,meta['duration_s']-span-.05)
        if meta['duration_s']<15 and other-a>.5:positions.append(other)
        elif len(starts)>1:positions.append(starts[1][0])
        c['janelas']=[]
        for a in (positions[:1] if adaptive else positions):
            if calls>=budget:break
            frames=[E.frame(p,a+span*f,width=min(960,meta['width'])) for f in (0,.5,.9)]
            pack=DE.pacote_observacao(m,a,span,frames,fato_id=n['fatos'][0],necessidade=n['mostrar'],fracoes=(0,.5,.9))
            pack['diagnostico_tecnico']=DE.diagnosticar_janela(frames)
            try:q=DE.revisar_janela_visao(pack,frames,ask,permitir_chamada=True,evidencia_visual=n['evidencia_visual'])
            except Exception as e:
                boards.append((c,frames,'FALHA_VISAO'));c['janelas'].append({'pacote':pack,'falha':type(e).__name__});continue
            q={**q,'sha256_origem':meta['sha256'],'necessidade_id':n['id']}
            dec=R.decidir(n,c,q,tipo='video')
            pack['revisao_assistida']=q
            c['janelas'].append({'pacote':pack,'decisao':dec})
            boards.append((c,frames,dec['motivo']))
            if dec['estado']=='PERTINENTE_PRIVADO':
                c['selecao_janela']=DE.candidato_revisado(pack,m,fato_id=n['fatos'][0]);return dec
        return {'estado':'INSUFICIENTE','motivo':'SEM_JANELA_PERTINENTE_NO_ORCAMENTO'}
    try:
        if adaptive:
            reports=[]
            def search(n,limit):
                r=D.pesquisar_triagem([n],biblioteca_global=lib,max_buscas=limit)[0]
                if pack:r['candidatos']=RE.candidatos(lib,n)+r['candidatos']
                reports.append(r);return r
            for n in tri:
                results.append(R.cobertura_adaptativa(n,search,inspect,
                    lambda phase:calls<(1 if phase==0 else budget) and t.http<t.max_http and t.bytes<t.max_bytes))
        else:
            reports=D.pesquisar_triagem(tri,biblioteca_global=lib,max_buscas=8)
            for n,r in zip(tri,reports):
                results.append(D.revisar_cobertura_documental(n,r,inspect,max_candidatos=6))
    finally:lib.fechar()
    Q.write(out/'revisao.json',{'case':case,'triagem':tri,'pesquisa':reports,'cobertura':results,
        'restauracao':rest,'rede_aquisicao':t.resumo(),'visao_chamadas_logicas':calls,
        'visao_limite':budget,'modo_adaptativo':adaptive,'reuso_bytes_validado':reuses>0,'reusos_bytes':reuses,'publish':False,'pronto_para_render':False})
    for i,(c,ims,verdict) in enumerate(boards):
        board=Image.new('RGB',(1080,380*len(ims)+45),'#101c28');d=ImageDraw.Draw(board)
        d.text((12,10),verdict+' | '+c['aquisicao']['sha256'][:12],fill='white')
        for j,im in enumerate(ims):
            im=im.copy();im.thumbnail((1040,340));y=45+j*380
            board.paste(im,((1080-im.width)//2,y));d.text((12,y+344),f'Amostra {j+1} - {c["tipo"]} - revisao privada',fill='white')
        board.save(out/f'revisao-{i+1}.jpg',quality=94)
    print('E247 COVERAGE',caseid,'vision',calls,'boards',len(boards),'states',[r['estado'] for r in results],flush=True)

if __name__=='__main__':main()
