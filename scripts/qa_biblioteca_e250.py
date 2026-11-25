"""E250 private cross-runner byte reuse proof using known E249 sources."""
import json,sys
from pathlib import Path
from src.v3.biblioteca import Biblioteca
from src.v3 import pacote_biblioteca as P

def acquire(root):
    from scripts.qa_pesquisa_documental_e246 import sample
    from src.v4.aquisicao_documental import Transporte
    root.mkdir(parents=True,exist_ok=True);originals=root/'originais';originals.mkdir(exist_ok=True)
    b=Biblioteca(root/'local.db',root/'local');t=Transporte(max_http=10,max_bytes=30_000_000,max_wait=20)
    ids=[];receipts=[]
    try:
        for nid in ('PIA06538','PIA12639'):
            c={'source_id':nid,'fonte':'nasa','tipo':'foto'}
            m,im,p=sample(c,originals,t)
            r=b.ingerir(p,{'titulo':nid,'desc':'Saturn Cassini candidate; rights pending',
                'fonte':'nasa','url':m['url_adquirida'],'wh':[m['width'],m['height']],
                'licenca_prova':'individual audit pending'})
            ids.append(r['id']);receipts.append({'id':r['id'],'aquisicao':m,'recibo_nasa':c['recibo_nasa']})
        idx=P.exportar(b,ids,root/'pacote')
        (root/'pacote'/'recibos.json').write_text(json.dumps({'publicar':False,'receipts':receipts,'rede':t.resumo()},indent=2))
    finally:b.fechar()

def restore(root):
    pack=root/'pacote'
    b,r=P.restaurar(pack,db=root/'fresh.db',armazem=root/'fresh')
    def no_network(*args):raise AssertionError('source network forbidden')
    try:
        idx=json.loads((pack/'index.json').read_text());checks=[]
        for e in idx['arquivos']:
            p=b.recuperar(e['id'],baixar=no_network)
            if not p or P.sha(p)!=e['sha256']:raise ValueError('E250-REUSO')
            d=b.obter(e['id'])
            if d['uso_comercial']!='indefinido':raise ValueError('E250-DIREITOS')
            checks.append({'id':e['id'],'sha256':e['sha256'],'bytes':p.stat().st_size,'reuso':True})
        if b.buscar('Saturn',so_comercial=True):raise ValueError('E250-QUARENTENA')
        (root/'revisao.json').write_text(json.dumps({'publicar':False,'direitos_aprovados':False,
            'relatorio':r,'checks':checks,'consultas_fonte':0,'visao_chamadas':0},indent=2))
        print('E250 REUSO',len(checks),'originais; zero consultas de origem')
    finally:b.fechar()

if __name__=='__main__':
    action,root=sys.argv[1:];{'acquire':acquire,'restore':restore}[action](Path(root))
