import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.v4.formatos import fontes_e35 as F

class E37(unittest.TestCase):
    def test_refuse_arbitrary_url_and_ref(self):
        for url in ("file:///etc","https://github.com.evil.test/a/b",
                    "https://user:secret@github.com/a/b","https://github.com/a/..",
                    "-oProxyCommand=anything","https://github.com/a/b?x=1"):
            with self.assertRaisesRegex(ValueError,"URL_NAO_CANONICA"):
                F.validar_fonte(url,"a"*40)
        with self.assertRaisesRegex(ValueError,"COMMIT_NAO_FIXADO"):
            F.validar_fonte("https://github.com/a/b","main")
        F.validar_fonte("https://github.com/a/b","a"*40)

    def test_no_tokens_or_config_in_environment(self):
        with patch.dict(os.environ,{"GH_TOKEN":"secret","GITHUB_TOKEN":"secret",
             "GIT_CONFIG_COUNT":"1","GIT_SSH_COMMAND":"untrusted"}):
            env=F.ambiente_git()
            for key in ("GH_TOKEN","GITHUB_TOKEN","GIT_CONFIG_COUNT","GIT_SSH_COMMAND"):
                self.assertNotIn(key,env)
            self.assertEqual(env["GIT_ALLOW_PROTOCOL"],"https")

    def test_existing_checkout_not_trusted(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/".git").mkdir()
            with self.assertRaisesRegex(ValueError,"DESTINO_EXISTENTE"):
                F.clonar("https://github.com/a/b",p,"a"*40)

    def test_symlink_license_not_read(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"repo";root.mkdir()
            lic=Path(d)/"external.txt"
            lic.write_text("Permission is hereby granted, free of charge")
            (root/"LICENSE").symlink_to(lic)
            (root/"model.step").write_text("fixture")
            (root/"external.step").symlink_to(lic)
            r=F.inventario(root,"example mechanism")
            self.assertEqual(r["licenca"]["classe"],"sem_licenca")
            self.assertEqual([a["caminho"] for a in r["arquivos"]],["model.step"])
            self.assertEqual(r["arquivos"][0]["direitos"],"NAO_VERIFICADOS_POR_ARQUIVO")
