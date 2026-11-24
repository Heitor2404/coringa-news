"""Posicionamento vertical geométrico compartilhado de animações técnicas.

Calcula TRANSLATION apenas: nunca altera escala, ângulos, conexões, física nem
desenho. As caixas são fornecidas pelos componentes e exigem revisão: este
módulo não afirma detectá-las automaticamente em imagens arbitrárias.

O papel dos perfis de UI/legenda completos continua em layout.py e
plataformas.json. Aqui só há limites INTERNOS de palco 540x960, usados
por provas privadas SVG (compressor completo e motor Otto).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CaixaVisivel:
    esquerda: float
    topo: float
    direita: float
    base: float


@dataclass(frozen=True)
class PalcoVertical:
    largura: int
    altura: int
    caixa: CaixaVisivel
    editorial_termina_y: float
    rodape_comeca_y: float
    folga_superior: float = 8.0
    folga_inferior: float = 0.0

    def _validar(self) -> None:
        v = (self.caixa.esquerda, self.caixa.topo, self.caixa.direita,
             self.caixa.base, self.editorial_termina_y,
             self.rodape_comeca_y, self.folga_superior, self.folga_inferior)
        if (not all(math.isfinite(x) for x in v) or
                self.largura <= 0 or self.altura <= 0 or
                self.caixa.esquerda < 0 or self.caixa.direita > self.largura or
                self.caixa.topo < 0 or self.caixa.base > self.altura or
                self.caixa.esquerda >= self.caixa.direita or
                self.caixa.topo >= self.caixa.base or
                self.folga_superior < 0 or self.folga_inferior < 0 or
                self.editorial_termina_y < 0 or
                self.rodape_comeca_y > self.altura or
                self.editorial_termina_y >= self.rodape_comeca_y):
            raise ValueError("F-PALCO-GEOMETRIA-INVALIDA")

    def deslocar(self, subida_px: float | None = None) -> float:
        """Menor y livre desejado; o autor pode escolher menos subida.

        A cena permanece 1:1. Se não couber, BLOQUEIA em vez de
        encolher automaticamente, cortar uma peça ou ocultar legenda.
        """
        self._validar()
        maximo = round(
            self.caixa.topo -
            (self.editorial_termina_y + self.folga_superior), 5
        )
        if maximo < 0:
            raise ValueError("F-PALCO-SEMPRE-INVADIRIA-EDITORIAL")
        lift = maximo if subida_px is None else subida_px
        if (not isinstance(lift, (int, float)) or
                not math.isfinite(lift) or lift < 0 or lift > maximo + 1e-7):
            raise ValueError("F-PALCO-SUBIDA-FORA-DA-AREA")
        if (self.caixa.topo - lift < self.editorial_termina_y + self.folga_superior - 1e-6
                or self.caixa.base - lift > self.rodape_comeca_y - self.folga_inferior + 1e-6):
            raise ValueError("F-PALCO-INTERSECAO-RODAPE-OU-TEXTO")
        return float(lift)

    def faixa_resultante(self, subida_px: float | None = None) -> tuple[float, float]:
        lift = self.deslocar(subida_px)
        return (self.caixa.topo - lift, self.caixa.base - lift)


# E215: envelope de pixels de TODOS os quadros do grupo físico, não do
# canvas inteiro. Perfil candidato para QA; não homologado para interfaces.
@dataclass(frozen=True)
class EnquadramentoEditorial:
    caixa: CaixaVisivel
    viewport: CaixaVisivel
    escala: float
    x: int
    y: int
    largura: int
    altura: int

def ajustar_envelope(caixa: CaixaVisivel, viewport: CaixaVisivel,
                     escala_max: float=1.35) -> EnquadramentoEditorial:
    """Plano-mestre constante. Não distorce, não corta, não muda por quadro."""
    w,h=caixa.direita-caixa.esquerda,caixa.base-caixa.topo
    vw,vh=viewport.direita-viewport.esquerda,viewport.base-viewport.topo
    valores=(w,h,vw,vh,escala_max,caixa.esquerda,caixa.topo,
             viewport.esquerda,viewport.topo)
    if not all(math.isfinite(v) for v in valores) or min(w,h,vw,vh,escala_max)<=0:
        raise ValueError('E215-ENVELOPE')
    escala=min(vw/w,vh/h,escala_max)
    nw,nh=math.floor(w*escala+1e-7),math.floor(h*escala+1e-7)
    if min(nw,nh)<1:
        raise ValueError('E215-ESCALA')
    x=math.floor(viewport.esquerda+(vw-nw)/2)
    y=math.floor(viewport.topo+(vh-nh)/2)
    return EnquadramentoEditorial(caixa,viewport,escala,x,y,nw,nh)

def extrair_grupo_svg(svg: str, grupo: str, *, margem: int=80):
    """Isola um grupo físico explicitamente identificado pelo renderer.
    Preserva defs e transform originais. Overscan revela elementos que
    poderiam estar cortados pelo canvas histórico. Só SVG autoral local.
    """
    import copy
    import xml.etree.ElementTree as ET
    ns='http://www.w3.org/2000/svg'
    ET.register_namespace('',ns)
    r=ET.fromstring(svg)
    if r.tag!='{'+ns+'}svg' or r.get('viewBox')!='0 0 540 960':
        raise ValueError('E215-SVG-VIEWBOX')
    def local(e): return e.tag.split('}')[-1]
    if any(local(e) in ('script','foreignObject','image','use') for e in r.iter()):
        raise ValueError('E215-SVG-RECURSO')
    # Direct child only: never drop an ancestor transform or mask.
    g=[e for e in r if e.get('id')==grupo and local(e)=='g']
    if len(g)!=1:
        raise ValueError('E215-GRUPO')
    out=ET.Element(r.tag,{'width':str(540+2*margem),'height':str(960+2*margem),
                          'viewBox':f'{-margem} {-margem} {540+2*margem} {960+2*margem}'})
    for d in r:
        if local(d)=='defs':
            out.append(copy.deepcopy(d))
    out.append(copy.deepcopy(g[0]))
    return ET.tostring(out,encoding='unicode')
