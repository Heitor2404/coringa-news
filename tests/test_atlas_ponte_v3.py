"""Ponte V3→ATLAS: prova humana explícita, SHA, licença e inexistência de banco paralelo.
Tudo offline: banco temporário e fotografia sintética local; nenhuma API externa.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from src.v3.biblioteca import Biblioteca
from src.v4.formatos import ponte_biblioteca, produzir


def _arquivo_e_banco(monkeypatch, tmp_path):
    imagem = tmp_path / "foto_gerada_para_teste.png"
    Image.new("RGB", (120, 100), (23, 30, 55)).save(imagem)
    banco = tmp_path / "v3.sqlite"
    armazem = tmp_path / "armazen"
    monkeypatch.setenv("BIBLIOTECA_DB", str(banco))
    monkeypatch.setenv("BIBLIOTECA_ARMAZEM", str(armazem))
    bib = Biblioteca(db=banco, armazem=armazem)
    reg = bib.ingerir(imagem, {
        "titulo": "Foto gerada para teste de importação",
        "credito": "Obra original — Autor Teste (CC BY 4.0)",
        "licenca": "CC BY 4.0",
        "licenca_prova": "https://exemplo.invalid/licenca",
        "pagina": "https://exemplo.invalid/foto",
        "url": "https://exemplo.invalid/foto",
        "mostra": "figura totalmente sintética, não é fotografia real",
        "wh": [120, 100],
    })
    bib.fechar()
    return reg, imagem


def _aprovar(monkeypatch, tmp_path, reg, **alteracoes):
    prova = {
        "midia_corresponde": True,
        "revisor": "curadoria-teste",
        "evidencia": "inspecao offline do arquivo gerado",
        "acontecimento": "teste do adaptador, não um evento histórico",
        "licenca_evidencia": "https://exemplo.invalid/licenca",
    }
    ap = {"midia_id": reg["id"], "sha256": reg["sha256"], "prova": prova}
    ap.update(alteracoes)
    arquivo = tmp_path / "aprovacoes.json"
    arquivo.write_text(json.dumps({"versao": 1, "aprovacoes": [ap]}), encoding="utf-8")
    monkeypatch.setenv("CORINGA_ATLAS_APROVACOES_V3", str(arquivo))
    return arquivo


def test_sem_manifesto_nada_se_insere_automaticamente(monkeypatch, tmp_path):
    reg, _ = _arquivo_e_banco(monkeypatch, tmp_path)
    monkeypatch.delenv("CORINGA_ATLAS_APROVACOES_V3", raising=False)
    itens = ponte_biblioteca.catalogo()["itens"]
    assert not any(x["id"] == "v3:" + reg["id"] for x in itens)


def test_aprovacao_explicitamente_verificada_reusa_bytes_v3(monkeypatch, tmp_path):
    reg, imagem = _arquivo_e_banco(monkeypatch, tmp_path)
    _aprovar(monkeypatch, tmp_path, reg)
    item = next(i for i in ponte_biblioteca.catalogo()["itens"]
                if i["id"] == "v3:" + reg["id"])
    assert item["sha256_origem"] == hashlib.sha256(imagem.read_bytes()).hexdigest()
    assert item["prova"]["revisor"] == "curadoria-teste"
    assert "CC BY 4.0" in item["credito"]
    data, origem = ponte_biblioteca.bytes_originais(item)
    assert data == imagem.read_bytes()
    assert origem.startswith("biblioteca-v3:")

    monkeypatch.setattr(produzir, "PUBLICO", tmp_path / "public" / "_formato")
    p = {"beats": [{"camadas": [{"p": {"asset": item["id"]}}]}],
         "clipes": [], "rasters": []}
    data = produzir.ativos(p, tmp_path / "saida")
    arq = tmp_path / "public" / data[item["id"]]["src"]
    assert arq.is_file()
    assert data[item["id"]]["tipo"] == "foto"
    assert data[item["id"]]["origem_conferida"]


def test_licenca_sem_prova_e_revisao_nao_autorizam(monkeypatch, tmp_path):
    reg, _ = _arquivo_e_banco(monkeypatch, tmp_path)
    arquivo = _aprovar(monkeypatch, tmp_path, reg)
    dados = json.loads(arquivo.read_text())
    dados["aprovacoes"][0]["prova"].pop("licenca_evidencia")
    arquivo.write_text(json.dumps(dados))
    with pytest.raises(RuntimeError, match="revisão editorial"):
        ponte_biblioteca.catalogo()


def test_sha_alterado_ou_arquivo_corrompido_bloqueiam(monkeypatch, tmp_path):
    reg, img = _arquivo_e_banco(monkeypatch, tmp_path)
    ap = _aprovar(monkeypatch, tmp_path, reg, sha256="0" * 64)
    with pytest.raises(RuntimeError, match="mudou"):
        ponte_biblioteca.catalogo()

    _aprovar(monkeypatch, tmp_path, reg)
    armazenado = Path(monkeypatch.getenv("BIBLIOTECA_ARMAZEM")) if hasattr(monkeypatch, "getenv") else tmp_path / "armazen"
    origem = armazenado / reg["sha256"][:2] / (reg["sha256"] + ".png")
    origem.write_bytes(b"conteudo-adulterado")
    with pytest.raises(RuntimeError, match="original local íntegro"):
        ponte_biblioteca.catalogo()


def test_sem_banco_v3_explicita_falha(monkeypatch, tmp_path):
    reg, _ = _arquivo_e_banco(monkeypatch, tmp_path)
    _aprovar(monkeypatch, tmp_path, reg)
    monkeypatch.setenv("BIBLIOTECA_DB", str(tmp_path / "nao-existe.sqlite"))
    with pytest.raises(RuntimeError, match="banco global V3 indisponível"):
        ponte_biblioteca.catalogo()


def test_manifesto_de_aprovacao_nao_vira_banco_separado(monkeypatch, tmp_path):
    reg, _ = _arquivo_e_banco(monkeypatch, tmp_path)
    arq = _aprovar(monkeypatch, tmp_path, reg)
    assert set(json.loads(arq.read_text())) == {"versao", "aprovacoes"}


def test_diretor_recebe_so_midias_aprovadas_relevantes(monkeypatch, tmp_path):
    from src.v4.formatos import diretor

    reg, _ = _arquivo_e_banco(monkeypatch, tmp_path)
    aprovacoes = _aprovar(monkeypatch, tmp_path, reg)
    fatos = [{"id": "f1", "texto": "Uma foto gerada para teste ajuda a mostrar uma evidência."}]
    inventario = ponte_biblioteca.inventario_para_diretor(fatos)
    assert "v3:" + reg["id"] in inventario
    assert "licença CC BY 4.0" in inventario
    assert "prova" not in inventario.lower() or "comprovada" in inventario

    # O diretor opt-in recebe o mesmo catálogo sem reconstruir um garimpo paralelo.
    prompt = diretor.prompt(fatos, "atlas", None, None)
    assert "v3:" + reg["id"] in prompt

    # Material apenas encontrado na V3, sem aprovação explícita, não vai ao prompt.
    monkeypatch.delenv("CORINGA_ATLAS_APROVACOES_V3", raising=False)
    sem = ponte_biblioteca.inventario_para_diretor(fatos)
    assert "v3:" + reg["id"] not in sem


def test_mesmo_sha_da_biblioteca_v4_nao_gera_duplicata(monkeypatch, tmp_path):
    from src.v4 import viabilidade

    reg, _ = _arquivo_e_banco(monkeypatch, tmp_path)
    _aprovar(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(viabilidade, "carregar", lambda: {
        "itens": [{"id": "foto:ja-aprovada", "sha256_origem": reg["sha256"]}],
        "reprovados": []
    })
    with pytest.raises(RuntimeError, match="reuse o ID existente"):
        ponte_biblioteca.catalogo()


def test_inventario_nao_oferece_fabrica_generica_com_uma_palavra_em_comum(monkeypatch):
    from src.v4 import viabilidade

    monkeypatch.delenv("CORINGA_ATLAS_APROVACOES_V3", raising=False)
    monkeypatch.setattr(viabilidade, "carregar", lambda: {
        "itens": [{"id": "foto:fabrica-generica", "natureza": "foto",
                   "titulo": "fábrica genérica",
                   "mostra": "uma fábrica não identificada",
                   "licenca": "CC BY 4.0", "credito": "Autor · CC BY 4.0",
                   "prova": {"midia_corresponde": True}}],
        "reprovados": []
    })
    s = ponte_biblioteca.inventario_para_diretor([
        {"id": "f1", "texto": "A fábrica da TSMC em Taiwan utiliza equipamentos de litografia."}
    ])
    assert "foto:fabrica-generica" not in s
    assert "nenhum registro comprovado pertinente" in s
