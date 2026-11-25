"""Recover exact originals from prior private reports, not old semantic approvals."""
import hashlib,json,re,shutil,sys
from pathlib import Path
from urllib.parse import urlsplit
from src.v3.biblioteca import restaurar_catalogo
from src.v3 import pacote_biblioteca as P
from src.v4.aquisicao_documental import Transporte
from src.v4.formatos import ponte_cobertura_filme as B
from PIL import Image
import io

def recuperar(row,t,root,lib):
    a=row['aquisicao'];sha=a['sha256'];url=a['url_adquirida']
    if row.get('publicar') is not False or row.get('direitos_aprovados') is not False or row.get('fonte')!='commons' or row.get('tipo')!='foto':raise ValueError('E264-ESCOPO')
    if not re.fullmatch('[0-9a-f]{64}',sha) or type(a['bytes']) is not int or not 0<a['bytes']<=26_000_000:raise ValueError('E264-RECIBO')
    page=urlsplit(row['pagina'])
    if page.scheme!='https' or page.hostname!='commons.wikimedia.org' or page.username or page.password or page.port not in (None,443) or not page.path.startswith('/wiki/File:'):raise ValueError('E264-PAGINA')
    if row.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or B.licenca_documental(row,a) is None:raise ValueError('E264-LICENCA')
    raw=t.get(url,{'upload.wikimedia.org','thumb.wikimedia.org'},26_000_000)
    if len(raw)!=a['bytes'] or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('E264-ORIGINAL-MUDOU')
    with Image.open(io.BytesIO(raw)) as im:
        if im.format not in ('JPEG','PNG','WEBP') or min(im.size)<600 or list(im.size)!=[a['width'],a['height']]:raise ValueError('E264-PIXELS')
        ext={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[im.format];im.verify()
    path=root/(sha+ext);path.write_bytes(raw)
    saved=lib.ingerir(path,{'titulo':row['titulo'],'desc':row.get('descricao') or '', 'url':url,
        'pagina':row['pagina'],'fonte':'commons','wh':[a['width'],a['height']],
        'licenca_prova':'Revisao privada; direitos pendentes'})
    lib.gravar_analise(sha,'documental:recibo:'+hashlib.sha256(row['pagina'].encode()).hexdigest(),
        {'publicar':False,'direitos_aprovados':False,'aquisicao':a,'fonte':'commons','pagina':row['pagina'],
         'licenca_declarada':row['licenca'],'credito_declarado':row['credito'],'recibos':{},
         'relatorio_historico':row['relatorio']},origem='E264')
    # Export a real original, not a thumbnail or an old verdict for a new need.
    dest=root/'checkpoints'/saved['id']
    P.exportar(lib,[saved['id']],dest,incluir_analises_privadas=True)
    zip_path=shutil.make_archive(str(dest),'zip',root_dir=dest)
    return {'id':saved['id'],'sha256':sha,'arquivo':Path(zip_path).name,'estado':'ORIGINAL_RECUPERADO',
            'revisao_semantica_nova':'PENDENTE','publicar':False}

def main():
    spec=json.loads(Path(sys.argv[1]).read_text());root=Path(sys.argv[2]);root.mkdir(parents=True,exist_ok=True)
    if spec.get('publicar') is not False or len(spec['originais'])>8:raise ValueError('E264-PRIVADO')
    lib,_=restaurar_catalogo(db=root/'biblioteca.sqlite3',armazem=root/'biblioteca')
    t=Transporte(max_http=12,max_bytes=60_000_000,max_wait=25)
    rows=[]
    try:
        for row in spec['originais']:
            try:rows.append(recuperar(row,t,root,lib))
            except Exception as e:rows.append({'sha256':row['aquisicao']['sha256'],'estado':'FALHA_RECUPERACAO','motivo':str(e)[:200]})
        lib.exportar_manifesto(root/'manifesto-revisoes.jsonl')
    finally:lib.fechar()
    (root/'recuperacao.json').write_text(json.dumps({'publicar':False,'direitos_aprovados':False,'resultados':rows,'rede':t.resumo(),'visao':0},ensure_ascii=False,indent=2))
    print('E264 RECUPERACAO',rows,flush=True)
if __name__=='__main__':main()
