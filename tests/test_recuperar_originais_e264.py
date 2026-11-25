import hashlib,io
from PIL import Image
import pytest
from src.v3.biblioteca import Biblioteca
from scripts.qa_recuperar_originais_e264 import recuperar

def test_recovery_only_exact_original_and_no_semantic_approval(tmp_path):
    im=Image.new('RGB',(800,600),'blue')
    b=io.BytesIO();im.save(b,format='PNG');raw=b.getvalue();sha=hashlib.sha256(raw).hexdigest()
    row={'fonte':'commons','tipo':'foto','titulo':'Glacier fixture','pagina':'https://commons.wikimedia.org/wiki/File:Example.png',
         'credito':'Author','licenca':'CC BY 4.0','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA',
         'aquisicao':{'sha256':sha,'bytes':len(raw),'width':800,'height':600,'url_adquirida':'https://upload.wikimedia.org/example.png'},
         'relatorio':'test fixture','publicar':False,'direitos_aprovados':False}
    class T:
        def get(self,*args):return raw
    lib=Biblioteca(tmp_path/'db',tmp_path/'files')
    try:
        result=recuperar(row,T(),tmp_path,lib)
        assert result['revisao_semantica_nova']=='PENDENTE'
        assert result['publicar'] is False and (tmp_path/'checkpoints'/result['arquivo']).is_file()
        assert lib.obter(result['id'])['uso_comercial']!='sim'
        class Changed:
            def get(self,*args):return raw+b'x'
        with pytest.raises(ValueError,match='ORIGINAL-MUDOU'):recuperar(row,Changed(),tmp_path,lib)
    finally:lib.fechar()
