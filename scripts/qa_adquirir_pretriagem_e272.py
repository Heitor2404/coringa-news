"""Stage only explicitly selected, scoped provider preview leads; no AI or approval."""
import hashlib,json,shutil,sys
from pathlib import Path
from urllib.parse import urlsplit,unquote
from src import acervo
from src.v3.biblioteca import restaurar_catalogo
from src.v3 import pacote_biblioteca as P
from src.v4 import acervo_v4 as A
from src.v4.aquisicao_documental import Transporte
from src.v4.formatos import diretor_visual_e202 as D,reuso_documental as RE,ponte_cobertura_filme as PF
from scripts import qa_pesquisa_documental_e246 as Q

def selecionados(spec,report,choices):
    if any(x.get('publicar',x.get('publish')) is not False for x in (spec,report,choices)):raise ValueError('E272-PRIVADO')
    case=next(c for c in spec['cases'] if c['id']==choices['case'])
    needs={n['id']:n for n in D.triagem_documental(case['necessidades'],case['fatos'],progressivo=True)}
    if len({x['id'] for x in choices['selecao']})!=len(choices['selecao']):raise ValueError('E272-DUPLICADO')
    out=[]
    for x in choices['selecao']:
        n=needs[x['id']]
        if n['mostrar']!=x['mostrar'] or n['evidencia_visual']=='movimento' or n['necessidade']!='registro':raise ValueError('E272-ESCOPO')
        rows=[a for g in report['necessidades'] if g['id']==x['id'] for a in g['amostras'] if a['preview_sha256']==x['preview_sha256'] and a['pagina']==x['pagina'] and a.get('estado')=='PRETRIAGEM_PENDENTE' and a.get('publicar') is False]
        if len(rows)!=1:raise ValueError('E272-PREVIEW-VINCULO')
        a=rows[0];u=urlsplit(a['pagina'])
        if x.get('observacao_previa'):
            a={**a,'observacao_previa':x['observacao_previa']}
        if u.scheme!='https' or u.hostname!='commons.wikimedia.org' or u.username or u.password or not u.path.startswith('/wiki/File:'):raise ValueError('E272-PAGINA')
        out.append((n,a))
    return out

def main():
    spec,report,choices=[json.loads(Path(x).read_text()) for x in sys.argv[1:4]]
    root=Path(sys.argv[4]);root.mkdir(parents=True,exist_ok=False)
    assets=root/'originais';assets.mkdir()
    if len(sys.argv)>5:
        if len(sys.argv)!=7 or sys.argv[5]!='--observacoes':raise ValueError('E278-MODO')
        from src.v4.pretriagem_documental import escolhas_observadas
        choices=escolhas_observadas(spec,report,choices,Path(sys.argv[6]))
        Q.write(root/'escolhas-observadas.json',choices)
    selected=selecionados(spec,report,choices)
    t=Transporte(max_http=9,max_bytes=45_000_000,max_wait=25)
    lib,_=restaurar_catalogo(db=root/'biblioteca.sqlite3',armazem=root/'biblioteca');saved=set();results=[]
    try:
        for idx,(n,a) in enumerate(selected):
            row={'id':n['id'],'pagina':a['pagina'],'preview_sha256':a['preview_sha256'],'publicar':False}
            old=t.max_bytes;t.max_bytes=t.bytes+(old-t.bytes)//(len(selected)-idx)
            try:
                title=unquote(urlsplit(a['pagina']).path.removeprefix('/wiki/')).replace('_',' ')
                hits=acervo._commons_infos([title],'Commons')
                raw=next(v for v in hits if v.get('source_id')==a['source_id'] and v.get('pagina')==a['pagina'])
                c=A._candidato_documental(raw,'commons','foto')
                if not c or c['direitos']!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA':raise ValueError('E272-DIREITOS')
                meta,im,p=Q.sample(c,assets,t,progressivo=True,max_variantes=2)
                if PF.licenca_documental(c,meta) is None or meta['bytes']>P.MAX_TOTAL:raise ValueError('E272-PROCEDENCIA')
                h=meta['sha256']
                d=lib.ingerir(p,{'titulo':c['titulo'],'desc':c['descricao'],'url':meta['url_adquirida'],'pagina':c['pagina'],'fonte':c['fonte'],'wh':[meta['width'],meta['height']],'licenca_prova':'Revisao privada; direitos pendentes'})
                lib.gravar_analise(h,'documental:recibo:'+hashlib.sha256(c['pagina'].encode()).hexdigest(),{'publicar':False,'direitos_aprovados':False,'aquisicao':meta,'fonte':c['fonte'],'pagina':c['pagina'],'licenca_declarada':c['licenca'],'credito_declarado':c['credito'],'recibos':{}},origem='E272')
                scope=RE.escopo(n)
                key='documental:'+hashlib.sha256(json.dumps({'contrato':'E266.pista','escopo':scope},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                hint={'sha256':h,'pagina':c['pagina'],'tipo':'foto','estado':'BYTES_VERIFIED_SEMANTICS_PENDING','publicar':False}
                lib.gravar_analise(h,key,{'publicar':False,'direitos_aprovados':False,'escopo_pesquisa':scope,'pista_aquisicao_pendente':hint,'pretriagem':{'preview_sha256':a['preview_sha256'],'pagina':a['pagina'],'origem':'INSPECAO_ASSISTIDA_PENDENTE','observacao_previa':a.get('observacao_previa')}},origem='E272')
                saved.add(d['id']);im.thumbnail((1000,750));im.save(root/(n['id']+'.jpg'),quality=92)
                row.update(estado='BYTES_VERIFIED_SEMANTICS_PENDING',aquisicao=meta,id_biblioteca=d['id'],arquivo_master=meta['url_adquirida']==c['url'])
            except Exception as e:row.update(estado='FALHA_AQUISICAO',motivo=str(e)[:200])
            finally:t.max_bytes=old
            results.append(row)
        lib.exportar_manifesto(root/'manifesto-revisoes.jsonl')
        for mid in sorted(saved):
            dest=root/'checkpoints'/mid;P.exportar(lib,[mid],dest,incluir_analises_privadas=True);shutil.make_archive(str(dest),'zip',root_dir=dest)
    finally:lib.fechar()
    out={'publicar':False,'direitos_aprovados':False,'visao':0,'cobertura_nova':0,'resultados':results,'rede':t.resumo()}
    (root/'aquisicao.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print('E272 AQUISICAO',[(x['id'],x['estado']) for x in results],t.http,t.bytes,flush=True)
if __name__=='__main__':main()
