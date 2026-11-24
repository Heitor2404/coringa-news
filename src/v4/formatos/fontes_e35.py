"""E35 — aquisição, procedência, licença por arquivo e identidade de fontes CAD.

Entrada: a consulta e uma lista de candidatos (repositórios públicos) vinda de
qualquer camada de descoberta (E34 REST, envelope Agent-Reach, busca web do
agente). A lista é DADO: nenhum candidato é preferido por nome no código.

Para cada candidato: clona em commit congelado (só dados; nada do repositório
é executado), inventaria arquivos, classifica a licença pelo TEXTO do arquivo
de licença (não pelo rótulo do GitHub), marca arquivos de provável terceiro
(peças compradas, motores, rolamentos, fixadores) que a licença da raiz não
cobre, e pontua a identidade textual contra a consulta. A escolha final só
acontece depois da análise geométrica (pipeline_e35).

Classes de uso (separadas): ``permissiva`` (MIT/BSD/Apache/CC BY/CERN-OHL-P),
``reciproca`` (CC BY-SA, CERN-OHL-S/W, GPL), ``nao_comercial`` (CC BY-NC*),
``sem_licenca`` (recusa). ``gratuito`` nunca implica ``comercial``.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

EXT_CAD = {".step": "STEP", ".stp": "STEP", ".urdf": "URDF", ".sdf": "SDF", ".xml": "MJCF?",
           ".stl": "MALHA", ".f3z": "FUSION_PROPRIETARIO", ".sldprt": "SOLIDWORKS_PROPRIETARIO",
           ".sldasm": "SOLIDWORKS_PROPRIETARIO", ".fcstd": "FREECAD", ".dxf": "DESENHO_2D",
           ".pdf": "DOCUMENTO", ".scad": "CODIGO_OPENSCAD"}

LICENCAS = [  # (spdx, classe, padrão no texto) — ordem importa (NC antes de BY)
    ("CC-BY-NC", "nao_comercial", r"NonCommercial|creativecommons\.org/licenses/by-nc"),
    ("CC-BY-SA", "reciproca", r"ShareAlike|creativecommons\.org/licenses/by-sa"),
    ("CC-BY", "permissiva", r"Attribution 4\.0|creativecommons\.org/licenses/by/"),
    ("CERN-OHL-S", "reciproca", r"CERN Open Hardware Licence Version 2 - Strongly Reciprocal"),
    ("CERN-OHL-W", "reciproca", r"CERN Open Hardware Licence Version 2 - Weakly Reciprocal"),
    ("CERN-OHL-P", "permissiva", r"CERN Open Hardware Licence Version 2 - Permissive"),
    ("GPL", "reciproca", r"GNU GENERAL PUBLIC LICENSE"),
    ("Apache-2.0", "permissiva", r"Apache License,?\s+Version 2\.0"),
    ("MIT", "permissiva", r"Permission is hereby granted, free of charge"),
    ("BSD", "permissiva", r"Redistribution and use in source and binary forms"),
]

# Indícios de peça de terceiro (catálogos e componentes comprados). Genérico:
# códigos de catálogo e categorias de componente, não nomes de projeto.
TERCEIRO = re.compile(r"\b\d{4,5}[A-Z]\d{2,4}\b|nema\s*-?\s*\d+|bearing|rolamento|kugellager|screw|"
                      r"\bnut\b|washer|\bDIN\s*\d+|\bISO\s*\d+|encoder|\bmotor\b|kaydon|ebm-?papst|"
                      r"\bball\b|inner ring|outer ring|\bshield\b|separator|\bcage\b|2RS\d?\b|\w+ZZ\b|"
                      r"\bM\d(\.\d)?x\d+", re.I)


def fail(codigo):
    raise ValueError("E35-FONTE-" + codigo)


def classificar_licenca(texto):
    if not texto.strip():
        return dict(spdx=None, classe="sem_licenca")
    for spdx, classe, pad in LICENCAS:
        if re.search(pad, texto, re.I):
            nota = None
            if spdx in ("MIT", "BSD", "Apache-2.0", "GPL"):
                nota = ("licença de SOFTWARE aplicada a arquivos CAD pela raiz do repositório: "
                        "interpretação de que cobre a geometria; não é parecer jurídico")
            return dict(spdx=spdx, classe=classe, nota=nota,
                        uso_comercial={"permissiva": "permitido_com_atribuicao",
                                       "reciproca": "permitido_com_obrigacoes_reciprocas",
                                       "nao_comercial": "PROIBIDO"}[classe])
    return dict(spdx="DESCONHECIDA", classe="sem_licenca")


def tokens(s):
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) > 2 and t not in {"cad", "the", "and", "for"}}


def identidade_textual(consulta, textos):
    q = tokens(consulta)
    alvo = tokens(" ".join(textos))
    return dict(termos_consulta=sorted(q), presentes=sorted(q & alvo),
                pontuacao=len(q & alvo) / max(1, len(q)), evidencia="comprovado_textual")


def validar_fonte(url,commit):
    if (not isinstance(url,str) or
        not re.fullmatch(r"https://github\.com/[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}",url)
        or url.rsplit("/",1)[-1] in (".","..")):
        fail("URL_NAO_CANONICA")
    if not isinstance(commit,str) or not re.fullmatch(r"[0-9a-f]{40}",commit):
        fail("COMMIT_NAO_FIXADO")


def ambiente_git():
    # Never inherit user-level Git configuration, credential helpers or
    # tokens from the documentary pipeline. Public HTTPS is the sole route.
    env={k:os.environ[k] for k in ("PATH","LANG","LC_ALL","SYSTEMROOT")
         if k in os.environ}
    env.update(GIT_CONFIG_NOSYSTEM="1",GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0",GIT_ALLOW_PROTOCOL="https",
               GIT_LFS_SKIP_SMUDGE="1")
    return env


def _git(args,cwd=None,timeout=600):
    cmd=["git","-c","core.hooksPath="+os.devnull,
         "-c","credential.helper=","-c","http.followRedirects=false",
         "-c","protocol.file.allow=never","-c","protocol.ext.allow=never"]+args
    try:
        r=subprocess.run(cmd,cwd=cwd,env=ambiente_git(),capture_output=True,
                         text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired):
        fail("GIT_EXECUCAO")
    if r.returncode:
        fail("GIT_REPROVADO")
    return r.stdout.strip()


def clonar(url,destino,commit=None):
    """Only public canonical HTTPS and pinned revision; no repository code."""
    validar_fonte(url,commit)
    destino=Path(destino)
    if destino.is_symlink():
        fail("DESTINO_SYMLINK")
    if destino.exists():
        # Fresh isolated input preferred; reuse only exact clean checkout.
        git=destino/".git"
        if git.is_symlink() or not git.is_dir():
            fail("DESTINO_EXISTENTE")
        # Do not trust local repository configuration in an existing checkout:
        # no subprocess may read it. Reuse is deliberately refused.
        fail("DESTINO_EXISTENTE")
    destino.parent.mkdir(parents=True,exist_ok=True)
    _git(["clone","-q","--depth","1","--no-recurse-submodules","--no-checkout",
          "--",url,str(destino)])
    # Fetch exact commit rather than accept a mutable default branch.
    _git(["fetch","-q","--depth","1","--no-recurse-submodules","origin",commit],cwd=destino)
    _git(["checkout","-q","--detach",commit],cwd=destino)
    atual=_git(["rev-parse","HEAD"],cwd=destino,timeout=15)
    if atual!=commit:
        fail("COMMIT_DIVERGENTE")
    return atual


def inventario(raiz, consulta):
    raiz = Path(raiz)
    arquivos, licencas = [], []
    for p in sorted(raiz.rglob("*")):
        if ".git" in p.relative_to(raiz).parts or p.is_symlink() or not p.is_file():
            continue
        rel = p.relative_to(raiz).as_posix()
        if re.match(r"(LICEN[CS]E|COPYING)(\.|$)", p.name, re.I):
            licencas.append((rel, p.read_text("utf-8", "replace")))
        tipo = EXT_CAD.get(p.suffix.lower())
        if tipo:
            arquivos.append(dict(caminho=rel, tipo=tipo, bytes=p.stat().st_size,
                                 sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                 terceiro_provavel=bool(TERCEIRO.search(p.name))))
    raiz_lic = [l for l in licencas if "/" not in l[0]]
    lic = classificar_licenca(raiz_lic[0][1]) if raiz_lic else dict(spdx=None, classe="sem_licenca")
    if raiz_lic:
        lic.update(arquivo=raiz_lic[0][0], sha256=hashlib.sha256(raiz_lic[0][1].encode()).hexdigest())
    readme = next((p for p in raiz.glob("README*") if p.is_file() and not p.is_symlink()), None)
    texto = (readme.read_text("utf-8", "replace") if readme else "")
    ident = identidade_textual(consulta, [raiz.name.replace("_", " "), texto[:20000]] + [a["caminho"] for a in arquivos])
    lic["escopo"]="LICENCA_RAIZ_CANDIDATA; DIREITOS_POR_SOLIDO_NAO_VERIFICADOS"
    for arq in arquivos:
        arq["direitos"]="NAO_VERIFICADOS_POR_ARQUIVO"
    return dict(arquivos=arquivos, licenca=lic, licencas_em_subpastas=[l[0] for l in licencas if "/" in l[0]],
                identidade_textual=ident, readme=texto)


def triagem(inv):
    """Elegibilidade ANTES da geometria. Devolve (elegivel, motivo, steps)."""
    if inv["licenca"]["classe"] == "sem_licenca":
        return False, "SEM_LICENCA", []
    if inv["licenca"]["classe"] == "nao_comercial":
        return False, "LICENCA_NAO_COMERCIAL", []
    # O filtro de terceiros é por SÓLIDO (nome de produto no STEP), na geometria;
    # o nome do arquivo só informa (ex.: um projeto próprio adaptado a um motor).
    steps = [a for a in inv["arquivos"] if a["tipo"] == "STEP"]
    if not steps:
        outros = sorted({a["tipo"] for a in inv["arquivos"]})
        return False, "SEM_STEP:" + ",".join(outros), []
    if inv["identidade_textual"]["pontuacao"] < 0.5:
        return False, "IDENTIDADE_TEXTUAL_FRACA", steps
    return True, None, steps
