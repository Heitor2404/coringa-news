"""E35 — leitura de STEP em corpos nomeados com feições analíticas.

Só dados: lê o STEP com OCP (XCAF, nomes de produto), unidade declarada no
cabeçalho, e para cada sólido: volume, centroide, faces cilíndricas (eixo,
raio, côncava/convexa, extensão angular) e planas (normal para fora,
centro, área, vértices). Não infere juntas nem papéis: isso é da inferência.
Comprimentos saem em MILÍMETROS (como o OCP entrega) e a unidade original
do arquivo fica registrada; a conversão para metro é feita na montagem.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


def fail(codigo):
    raise ValueError("E35-BREP-" + codigo)


@dataclass
class Cilindro:
    raio: float
    origem: np.ndarray
    eixo: np.ndarray
    concavo: bool          # face voltada para o eixo (furo/rasgo) vs convexa (pino/eixo)
    extensao_graus: float
    area: float
    zmin: float            # extensão ao longo do eixo (coordenada no próprio eixo)
    zmax: float


@dataclass
class Plano:
    normal: np.ndarray     # para fora do material
    centro: np.ndarray
    area: float
    vertices: np.ndarray   # amostra de pontos da face (mm)


@dataclass
class Corpo:
    indice: int
    nome: str              # nome de produto no STEP (evidência textual)
    volume: float
    centroide: np.ndarray
    caixa: tuple
    cilindros: list = field(default_factory=list)
    planos: list = field(default_factory=list)
    vertices: np.ndarray | None = None
    faces: np.ndarray | None = None
    forma: object = None


UNIDADES = {".MILLI.": 1e-3, "$": 1.0, ".CENTI.": 1e-2, ".MICRO.": 1e-6}


def unidade_comprimento(texto):
    """Fator arquivo→metro a partir de SI_UNIT(...,.METRE.) do cabeçalho; e
    polegada declarada por CONVERSION_BASED_UNIT('INCH'). Ambíguo → recusa."""
    pol = re.search(r"CONVERSION_BASED_UNIT\s*\(\s*'(INCH|FOOT)'", texto, re.I)
    si = re.findall(r"SI_UNIT\s*\(\s*([^,]*)\s*,\s*\.METRE\.\s*\)", texto)
    prefixos = {p.strip() for p in si}
    if pol:
        return dict(fator_metro=0.0254 if pol.group(1).upper() == "INCH" else 0.3048,
                    declarada=pol.group(1).lower(), fonte="CONVERSION_BASED_UNIT")
    # Áreas/volumes usam o mesmo SI_UNIT; '$' (metro puro) aparece junto do
    # prefixo do comprimento em muitos exportadores. Prefere o prefixado.
    com_prefixo = [p for p in prefixos if p != "$"]
    if len(com_prefixo) > 1:
        fail("UNIDADE_AMBIGUA")
    p = com_prefixo[0] if com_prefixo else ("$" if "$" in prefixos else None)
    if p is None or p not in UNIDADES:
        fail("UNIDADE_DESCONHECIDA")
    return dict(fator_metro=UNIDADES[p], declarada=f"SI_UNIT({p},.METRE.)", fonte="SI_UNIT")


def _nomes_por_solido(caminho):
    """Lista (nome do produto, forma) de cada sólido folha, via XCAF."""
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDF import TDF_LabelSequence, TDF_Label
    from OCP.TDataStd import TDataStd_Name
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer

    doc = TDocStd_Document(TCollection_ExtendedString("e35"))
    r = STEPCAFControl_Reader()
    r.SetNameMode(True)
    if int(r.ReadFile(str(caminho))) != 1:
        fail("LEITURA")
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def nome(l):
        a = TDataStd_Name()
        return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else ""

    saida = []

    def visitar(l, loc, nome_inst):
        if st.IsAssembly_s(l):
            comps = TDF_LabelSequence()
            st.GetComponents_s(l, comps)
            for i in range(1, comps.Length() + 1):
                c = comps.Value(i)
                ref = TDF_Label()
                st.GetReferredShape_s(c, ref)
                visitar(ref, loc.Multiplied(st.GetLocation_s(c)), nome(c) or nome(ref))
            return
        forma = st.GetShape_s(l).Moved(loc)
        ex = TopExp_Explorer(forma, TopAbs_SOLID)
        k = 0
        while ex.More():
            saida.append((nome(l) or nome_inst, ex.Current(), k))
            k += 1
            ex.Next()

    livres = TDF_LabelSequence()
    st.GetFreeShapes(livres)
    for i in range(1, livres.Length() + 1):
        visitar(livres.Value(i), TopLoc_Location(), "")
    return saida


def ler(caminho, tolerancia_tess=0.1, angular_tess=0.15, excluir=None):
    """`excluir(nome)` → True pula o sólido (registrado em `excluidos`)."""
    import cadquery as cq
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
    from OCP.TopAbs import TopAbs_REVERSED

    caminho = Path(caminho)
    dados = caminho.read_bytes()
    # A seção DATA pode declarar as unidades em qualquer ponto do arquivo.
    texto = " ".join(m.decode("latin-1") for m in re.findall(
        rb"SI_UNIT\s*\([^;]*?\.METRE\.\s*\)|CONVERSION_BASED_UNIT\s*\(\s*'[A-Z]+'", dados))
    unidade = unidade_comprimento(texto)
    corpos, excluidos = [], []
    for nome, forma, sub in _nomes_por_solido(caminho):
        if excluir is not None and excluir(nome):
            excluidos.append(nome)
            continue
        idx = len(corpos)
        so = cq.Solid(forma)
        c = so.Center()
        bb = so.BoundingBox()
        corpo = Corpo(idx, nome + (f"#{sub}" if sub else ""), float(so.Volume()), np.array([c.x, c.y, c.z]),
                      ((bb.xmin, bb.ymin, bb.zmin), (bb.xmax, bb.ymax, bb.zmax)), forma=so)
        for f in so.Faces():
            ad = BRepAdaptor_Surface(f.wrapped)
            invertida = f.wrapped.Orientation() == TopAbs_REVERSED
            if ad.GetType() == GeomAbs_Cylinder:
                cy = ad.Cylinder()
                ax = cy.Axis()
                o = np.array([ax.Location().X(), ax.Location().Y(), ax.Location().Z()])
                d = np.array([ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z()])
                d = d / np.linalg.norm(d)
                # Concavidade: a normal de saída do material aponta para o eixo?
                u = 0.5 * (ad.FirstUParameter() + ad.LastUParameter())
                v = 0.5 * (ad.FirstVParameter() + ad.LastVParameter())
                from OCP.gp import gp_Pnt, gp_Vec
                p, du, dv = gp_Pnt(), gp_Vec(), gp_Vec()
                ad.D1(u, v, p, du, dv)
                n = np.cross([du.X(), du.Y(), du.Z()], [dv.X(), dv.Y(), dv.Z()])
                n = n / (np.linalg.norm(n) or 1.0)
                if invertida:
                    n = -n
                P = np.array([p.X(), p.Y(), p.Z()])
                radial = (P - o) - np.dot(P - o, d) * d
                concavo = float(np.dot(n, radial)) < 0
                pts = np.array([[v_.X, v_.Y, v_.Z] for v_ in f.Vertices()]) if f.Vertices() else P[None]
                z = (pts - o) @ d
                corpo.cilindros.append(Cilindro(float(cy.Radius()), o, d, concavo,
                                                float(np.degrees(ad.LastUParameter() - ad.FirstUParameter())),
                                                float(f.Area()), float(z.min()), float(z.max())))
            elif ad.GetType() == GeomAbs_Plane:
                pl = ad.Plane()
                nd = pl.Axis().Direction()
                n = np.array([nd.X(), nd.Y(), nd.Z()])
                if invertida:
                    n = -n
                fc = f.Center()
                vs = np.array([[v_.X, v_.Y, v_.Z] for v_ in f.Vertices()])
                corpo.planos.append(Plano(n / np.linalg.norm(n), np.array([fc.x, fc.y, fc.z]),
                                          float(f.Area()), vs))
        vt, ft = so.tessellate(tolerancia_tess, angular_tess)
        corpo.vertices = np.asarray([p_.toTuple() for p_ in vt], float)
        corpo.faces = np.asarray(ft, dtype=int)
        corpos.append(corpo)
    if len(corpos) + len(excluidos) < 2:
        fail("MENOS_DE_DOIS_SOLIDOS")
    return dict(corpos=corpos, excluidos=excluidos, unidade=unidade,
                sha256=hashlib.sha256(dados).hexdigest(), bytes=len(dados))
