import hashlib,zipfile
import pytest
from src.v3 import pacote_biblioteca as P

def test_checkpoint_zip_flat_contract(tmp_path):
    z=tmp_path/'ok.zip'
    with zipfile.ZipFile(z,'w') as f:
        f.writestr('index.json','{}')
        f.writestr('manifesto.jsonl','{}')
        f.writestr('a'*64+'.webm',b'fixture')
    h=P.sha(z);dest=P.extrair_checkpoint(z,tmp_path/'safe',expected_sha256=h)
    assert (dest/('a'*64+'.webm')).read_bytes()==b'fixture'
    with pytest.raises(ValueError,match='E259-ZIP-SHA'):
        P.extrair_checkpoint(z,tmp_path/'wrong',expected_sha256='0'*64)

def test_checkpoint_zip_never_extracts_arbitrary_path(tmp_path):
    z=tmp_path/'bad.zip'
    with zipfile.ZipFile(z,'w') as f:
        f.writestr('index.json','{}');f.writestr('manifesto.jsonl','{}')
        f.writestr('../escape',b'unsafe')
    with pytest.raises(ValueError,match='E259-ZIP-NOME'):
        P.extrair_checkpoint(z,tmp_path/'bad',expected_sha256=P.sha(z))
    assert not (tmp_path/'escape').exists() and not (tmp_path/'bad').exists()
