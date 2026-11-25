import pytest
from scripts.reparar_manifesto_documental import validar_relatorio

def test_repair_requires_exact_report_bound_zip():
    mid='cm-'+'a'*12;name=mid+'.zip';digest='b'*64
    row={'id':mid,'arquivo':name,'sha256':digest,'estado':'PRIVADO_LOCAL'}
    r={'publish':False,'modo_progressivo':True,'checkpoints':[row]}
    a={name:{'digest':'sha256:'+digest,'size':100}}
    assert validar_relatorio(r,a)==a
    with pytest.raises(ValueError):validar_relatorio(r,{name:{'digest':'sha256:'+'c'*64,'size':100}})
    with pytest.raises(ValueError):validar_relatorio({**r,'publish':True},a)
    with pytest.raises(ValueError):validar_relatorio(r,{**a,'cm-'+'c'*12+'.zip':{'digest':'sha256:'+digest,'size':100}})
