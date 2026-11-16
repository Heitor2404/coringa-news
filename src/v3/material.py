"""Material cifrado PARA o GitHub Actions (narração e outros insumos que não podem ir em claro para o repositório público).

O workflow conhece o segredo CHECKPOINT_KEY; daqui não se conhece. Dele o workflow DERIVA um par X25519 determinístico:
a parte pública pode ser publicada sem risco (`python -m src.v3.material publica`), e quem tem só a pública consegue
cifrar (`cifrar`), mas só o workflow decifra (`python -m src.v3.material decifrar ARQ.enc DESTINO`).
Formato: pública efêmera (32) | nonce (12) | AES-256-GCM(dados). Chave do AES = HKDF-SHA256 do segredo compartilhado.
"""
from __future__ import annotations

import base64
import hashlib
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

INFO = b'coringa-material-v1'


def _privada(segredo: str) -> X25519PrivateKey:
    if not segredo:
        raise ValueError('sem segredo para derivar a chave do material')
    return X25519PrivateKey.from_private_bytes(hashlib.sha256(b'coringa-material-x25519:' + segredo.encode()).digest())


def _cru(pub) -> bytes:
    return pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def publica(segredo: str) -> str:
    return base64.b64encode(_cru(_privada(segredo).public_key())).decode()


def _chave(compartilhado: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=INFO).derive(compartilhado)


def cifrar(pub_b64: str, dados: bytes) -> bytes:
    efemera = X25519PrivateKey.generate()
    k = _chave(efemera.exchange(X25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))))
    nonce = os.urandom(12)
    return _cru(efemera.public_key()) + nonce + AESGCM(k).encrypt(nonce, dados, INFO)


def decifrar(segredo: str, blob: bytes) -> bytes:
    k = _chave(_privada(segredo).exchange(X25519PublicKey.from_public_bytes(blob[:32])))
    return AESGCM(k).decrypt(blob[32:44], blob[44:], INFO)


def _segredo() -> str:
    s = os.getenv('CHECKPOINT_KEY') or ''
    if not s and os.getenv('COFRE_TOKEN'):
        s = hashlib.sha256(('coringa-checkpoint-v1:' + os.environ['COFRE_TOKEN']).encode()).hexdigest()
    return s


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'publica':
        print(publica(_segredo()))
    elif cmd == 'decifrar':
        Path(sys.argv[3]).write_bytes(decifrar(_segredo(), Path(sys.argv[2]).read_bytes()))
    elif cmd == 'cifrar':                       # local: python -m src.v3.material cifrar PUB_B64 ENTRADA SAIDA
        Path(sys.argv[4]).write_bytes(cifrar(sys.argv[2], Path(sys.argv[3]).read_bytes()))
