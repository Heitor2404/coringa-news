"""Cache privado dos intermediários de uma prévia ATLAS já validada."""
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.v3 import material

QUADROS = ["quadros/relatorio.json", "quadros/styleframes.jpg", "quadros/celular.jpg"]


def fontes(*caminhos):
    # Apenas blobs versionados: pyc, logs e datas de checkout não são entradas.
    return subprocess.check_output(["git", "ls-tree", "-r", "-z", "HEAD", "--", *caminhos])


def digest(*partes):
    h = hashlib.sha256()
    for p in partes:
        h.update(len(p).to_bytes(8, "big"))
        h.update(p)
    return h.hexdigest()


def chaves(saida):
    from src.v4.formatos import plano as P, produzir
    pl = json.loads((saida / "plano_resolvido.json").read_bytes())
    can = P.canal(pl["canal"])
    c, = [c for c in pl["clipes"] if c["componente"] == "mecanismo.eclusa"]
    ambiente = os.environ["ATLAS_AMBIENTE"].encode()
    params = json.dumps([c["componente"], c["t1"] - c["t0"], c.get("fonte"),
                         produzir.params_clipe(c, can)], sort_keys=True).encode()
    v2 = digest(fontes("src/render", "src/v2", "src/v4/backends/legado.py", "src/v4/util.py",
                       "src/v4/formatos/produzir.py", "motor4/identidade", "package-lock.json"),
                ambiente, params)
    visual = digest(fontes("motor4", "src", "assets", "scripts/atlas_cache.py",
                           "scripts/atlas_previa_curta.py", "scripts/formatos_validar.py",
                           ".github/workflows/atlas-previa-curta.yml", "requirements.txt"),
                    v2.encode(), ambiente, os.environ["ATLAS_MODO"].encode(),
                    *((saida / f).read_bytes() for f in ("plano_resolvido.json", "ativos.json", "narracao.json")))
    return {"ATLAS_ECLUSA_KEY": "eclusa-v2-" + v2, "ATLAS_VISUAL_KEY": "atlas-visual-v1-" + visual}


def pacote(saida, salvar):
    from scripts.atlas_previa_curta import janelas
    pl = json.loads((saida / "plano_resolvido.json").read_bytes())
    meta = json.loads((saida / "narracao.json").read_bytes())
    nomes = QUADROS + [f"_amostra/{nome}_video.mp4" for nome, _, _ in janelas(pl, meta)]
    chave = material._segredo()
    if not chave:
        raise ValueError("sem chave para o cache privado")
    cifra = AESGCM(hashlib.sha256(b"atlas-cache-v1:" + chave.encode()).digest())
    chave_visual = os.environ["ATLAS_VISUAL_KEY"].encode()
    arq = saida / "intermediarios.enc"
    if salvar:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for nome in nomes:
                z.write(saida / nome, nome)
        nonce = os.urandom(12)
        arq.write_bytes(nonce + cifra.encrypt(nonce, buf.getvalue(), chave_visual))
    else:
        dados = arq.read_bytes()
        with zipfile.ZipFile(io.BytesIO(cifra.decrypt(dados[:12], dados[12:], chave_visual))) as z:
            if set(z.namelist()) != set(nomes) or not json.loads(z.read(QUADROS[0]))["ok"]:
                raise ValueError("cache incompleto ou sem validação visual")
            for nome in nomes:
                dest = saida / nome
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(nome))


if __name__ == "__main__":
    cmd, saida = sys.argv[1], Path(sys.argv[2])
    if cmd == "chaves":
        for k, v in chaves(saida).items():
            print(f"{k}={v}")
    elif cmd in ("salvar", "restaurar"):
        pacote(saida, cmd == "salvar")
    else:
        raise SystemExit("comando de cache desconhecido")
