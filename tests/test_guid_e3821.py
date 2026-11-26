import pytest
from src.v4 import fontes_culturais_e366 as C
def test_prefer_primary_or_provider_ark_without_new_hosts():
    guid='http://n2t.net/ark:/65665/ng49ca746b1-4fbb-704b-e053-15f76fa0b4fa'
    assert C.smithsonian_record_page({'record_link':'https://www.si.edu/object/test','guid':guid})==('https://www.si.edu/object/test','record_link')
    assert C.smithsonian_record_page({'record_link':'https://old.invalid/object','guid':guid})==(guid.replace('http:','https:'),'guid')
    assert C.smithsonian_record_page({'guid':guid})==(guid.replace('http:','https:'),'guid')
@pytest.mark.parametrize('guid',['https://evil.example/ark:/65665/abcde1','https://n2t.net/ark:/99999/abcde1','https://n2t.net/ark:/65665/abcde1?redirect=evil','https://n2t.net/ark:/65665/../abcde1','https://user@n2t.net/ark:/65665/abcde1'])
def test_reject_unrelated_or_unsafe_ark(guid):
    assert C.smithsonian_record_page({'guid':guid})==(None,None)
def test_maquette_is_a_representation_unless_requested():
    assert C.object_hint('steam engine photograph','Governor for Steam Engines',['Sculpture-Maquette'])=='POSSIVEL_REPRESENTACAO_DE_OUTRO_REFERENTE'
    assert C.object_hint('steam engine sculpture','Governor for Steam Engines',['Sculpture-Maquette'])=='SEM_INCOMPATIBILIDADE_DECLARADA'
