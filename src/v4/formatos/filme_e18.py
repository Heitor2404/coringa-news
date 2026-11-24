"""E18–E20 — do arquivo CAD articulado ao filme privado, com auditoria.

    python -m src.v4.formatos.filme_e18 fixar <manifesto> <raiz_fonte>
    python -m src.v4.formatos.filme_e18 gerar <manifesto> <raiz_fonte> <saida> [--ids a,b] [--rapido]

O manifesto descreve FONTE (repositório, commit, licença, SHA256 de cada
arquivo lido), o QUE mostrar (atuador a percorrer ou poses-chave da fonte), a
MEDIDA (par de peças) e o ORÁCULO externo (ficha técnica com URL e tolerância
fixada antes da medição). Nenhum ramo de código depende do nome da máquina.
Saída: MP4 1080×1920 privado, folha de contato e QA.json. publish=false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import multicorpo_e18 as M
from . import raster_e18 as R

W, H, FPS = 1080, 1920, 30


def ffmpeg_exe():
    """ffmpeg do sistema; senão o binário estático do wheel imageio-ffmpeg."""
    import os
    import shutil
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()
AMBAR = np.array([0.93, 0.58, 0.16])
VERDE_AGUA = np.array([0.18, 0.66, 0.68])
AZUL_ACOPLADO = np.array([0.42, 0.58, 0.92])


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compilar(xml):
    """Compila MJCF ou URDF. Num URDF, o compilador do MuJoCo descarta por
    padrão as malhas VISUAIS e fica só com as de colisão; aqui a opção
    discardvisual="false" é injetada EM MEMÓRIA (a fonte conferida por hash
    não é alterada) e as malhas entram como assets lidos do disco."""
    import re
    import xml.etree.ElementTree as ET
    import mujoco
    xml = Path(xml)
    if xml.suffix.lower() != ".urdf":
        return mujoco.MjModel.from_xml_path(str(xml))
    texto = xml.read_text()
    if "<mujoco" in texto:
        raise ValueError("E18-URDF_COM_EXTENSAO_MUJOCO")
    texto2, n = re.subn(r"(<robot\b[^>]*>)", r'\1<mujoco><compiler discardvisual="false"/></mujoco>', texto, count=1)
    if n != 1:
        raise ValueError("E18-URDF_SEM_ROBOT")
    assets = {}
    for el in ET.fromstring(texto).iter("mesh"):
        nome = el.get("filename")
        if nome is None or nome.startswith(("package://", "/", "file:")):
            raise ValueError("E18-URDF_CAMINHO_DE_MALHA")
        assets[nome] = (xml.parent / nome).read_bytes()
    return mujoco.MjModel.from_xml_string(texto2, assets)


def carregar(modelo, raiz):
    """Confere o SHA256 de TODO arquivo que o compilador lê; só então compila."""
    import mujoco
    raiz = Path(raiz).resolve()
    if modelo["licenca_arquivo"] not in modelo["sha256"]:
        raise ValueError("E18-FONTE-LICENCA_SEM_HASH")
    for rel, dig in modelo["sha256"].items():
        if sha256(raiz / rel) != dig:
            raise ValueError(f"E18-FONTE-SHA256:{rel}")
    xml = raiz / modelo["xml"]
    m = compilar(xml)
    lidos = {modelo["xml"]}
    for adr in m.mesh_pathadr:
        if adr < 0:  # malha definida no próprio XML (sem arquivo)
            continue
        p = Path(m.paths[adr:].split(b"\x00")[0].decode())
        p = (p if p.is_absolute() else (xml.parent / p)).resolve()
        lidos.add(p.relative_to(raiz).as_posix())
    faltando = sorted(lidos - set(modelo["sha256"]))
    if faltando:
        raise ValueError("E18-FONTE-ARQUIVO_SEM_HASH:" + ",".join(faltando))
    return m, M.de_mujoco(m), sorted(lidos)


# ------------------------------------------------------------ movimento
def suave(n):
    return (1 - np.cos(np.linspace(0, math.pi, n))) / 2


def excluidos_da_fonte(m, mont):
    exc = [(int(x) >> 16, int(x) & 0xFFFF) for x in m.exclude_signature[: m.nexclude]]
    return M.pares_excluidos(mont, exc)


def plano_movimento(mont, modelo, solver_cache, m=None):
    mov = modelo["movimento"]
    dur = float(mov.get("duracao_s", 6.0))
    n = int(round(dur * FPS))
    if mov["tipo"] == "varredura_atuador":
        acion = dict(mont.atuadores)
        if "junta" in mov:
            # A fonte não declara atuador para esta junta: o manifesto escolhe
            # a junta de entrada (registrado no QA como escolha, não da fonte).
            nomes = [c.nome for c in mont.coords]
            if mov["junta"] not in nomes:
                raise ValueError("E18-JUNTA_DESCONHECIDA")
            nome = "junta:" + mov["junta"]
            acion[nome] = {nomes.index(mov["junta"]): 1.0}
            solver_cache["entrada_escolhida_no_manifesto"] = mov["junta"]
        else:
            nome = mov["atuador"]
        if nome not in acion:
            raise ValueError("E18-ATUADOR_DESCONHECIDO")
        # Todos os acionadores da fonte entram; só o nomeado varre, os outros
        # ficam no valor da pose inicial (servo de posição mantido).
        r = list(acion).index(nome)
        solver = M.Resolvedor(mont, acion)
        chave = mov.get("chave_inicial", "qpos0")
        if chave not in mont.chaves:
            raise ValueError("E18-CHAVE_DESCONHECIDA")
        # A pose-chave da fonte pode não fechar exatamente: projeta no fechamento.
        fixos_val = solver.linhas @ mont.chaves[chave]
        # Servos de posição: a chave guarda a pose no COMANDO (key_ctrl).
        comandos = getattr(mont, "comandos", {}).get(chave, {})
        usados = {}
        for k_, n_ in enumerate(acion):
            if n_ in getattr(mont, "servos", {}) and n_ in comandos:
                g_, b0_, b1_ = mont.servos[n_]
                fixos_val[k_] = (g_ * comandos[n_] + b0_) / (-b1_)
                usados[n_] = float(fixos_val[k_])
        solver_cache["comandos_da_chave"] = usados
        montar = lambda s_, v=fixos_val: np.concatenate([v[:r], [s_], v[r + 1:]])
        faixa = solver.faixa_acionador(r)
        inicio = float(np.clip(fixos_val[r], *faixa))
        q0, info0 = solver.resolver(montar(inicio), mont.chaves[chave])
        solver_cache["projecao_chave_inicial_rad"] = float(np.abs(q0 - mont.chaves[chave]).max())
        faixa, limitados = M.faixa_viavel(solver, faixa, inicio, q0, montar)
        if m is not None:
            # Contato NOVO entre peças (além do que a fonte já sobrepõe na
            # própria pose de referência) encerra o curso.
            colisor = M.Colisor(mont, excluidos_da_fonte(m, mont))
            ref = colisor.pares(q0)
            faixa, cortes_c, novos = M.faixa_sem_contato_novo(solver, colisor, faixa, inicio, q0, montar, ref)
            solver_cache.update(sobreposicao_referencia=ref, cortes_por_contato_novo=cortes_c,
                                pares_que_cortaram=novos)
        medida = modelo["medida"]
        if medida["tipo"] == "folga":
            faixa, cortes, eixo = M.corte_no_contato(mont, solver, faixa, medida["a"], medida["b"], q0,
                                                     montar=montar)
        else:
            cortes, eixo = [], None
        # O filme percorre o curso viável COMPLETO, começando pelo extremo
        # mais próximo da pose-chave (que é só o ponto de partida da fonte).
        perto = faixa[0] if abs(faixa[0] - inicio) <= abs(faixa[1] - inicio) else faixa[1]
        outro = faixa[1] if perto == faixa[0] else faixa[0]
        q0, _ = solver.resolver(montar(perto), q0)
        inicio = perto
        # Pausa · ida · pausa · volta · pausa (proporções fixas para todo modelo).
        p, v = int(n * .1), int(n * .35)
        perfil = np.concatenate([np.zeros(p), suave(v), np.ones(n - 2 * p - 2 * v), suave(v)[::-1], np.zeros(p)])
        alvos = np.array([montar(inicio + x * (outro - inicio)) for x in perfil])
        solver_cache.update(faixa=faixa, cortes=cortes, eixo=eixo, limitada_por_batente=limitados,
                            varrido=nome, indice_varrido=r)
        return acion, alvos, q0
    if mov["tipo"] == "poses_chave":
        chaves = [mont.chaves[k] for k in mov["chaves"]]
        acion = {f"junta_{k}": {k: 1.0} for k in range(mont.nq)}
        seg = len(chaves) - 1
        por = n // seg
        alvos = []
        for a, b in zip(chaves[:-1], chaves[1:]):
            pausa = int(por * .18)
            t = np.concatenate([np.zeros(pausa), suave(por - 2 * pausa), np.ones(pausa)])
            alvos.extend(a + (b - a) * x for x in t)
        while len(alvos) < n:
            alvos.append(chaves[-1])
        solver_cache.update(faixa=None, cortes=[], eixo=None, limitada_por_batente=[], varrido=None,
                            indice_varrido=None)
        return acion, np.array(alvos), chaves[0]
    raise ValueError("E18-MOVIMENTO_NAO_SUPORTADO")


def ponto_em(mont, X, nome, ponto):
    b = mont.indice_corpo(nome)
    return X[b][:3, :3] @ np.asarray(ponto, float) + X[b][:3, 3]


def medir(mont, q, medida, eixo, q_ref=None):
    if medida["tipo"] == "deslocamento":
        # Quanto um ponto de B andou desde a pose inicial, visto do corpo A.
        def local(qq):
            X = mont.poses(qq)
            A = X[mont.indice_corpo(medida["a"])]
            return A[:3, :3].T @ (ponto_em(mont, X, medida["b"], medida.get("ponto_b", [0, 0, 0])) - A[:3, 3])
        return float(np.linalg.norm(local(q) - local(q_ref)))
    if medida["tipo"] == "folga":
        return M.folga(mont, q, medida["a"], medida["b"], eixo)[0]
    if medida["tipo"] == "distancia":
        X = mont.poses(q)
        a, b = mont.indice_corpo(medida["a"]), mont.indice_corpo(medida["b"])
        pa = X[a][:3, :3] @ np.asarray(medida.get("ponto_a", [0, 0, 0])) + X[a][:3, 3]
        pb = X[b][:3, :3] @ np.asarray(medida.get("ponto_b", [0, 0, 0])) + X[b][:3, 3]
        return float(np.linalg.norm(pb - pa))
    raise ValueError("E18-MEDIDA_NAO_SUPORTADA")


def abaixo_da_base(mont, qs, pap):
    """Quanto (mm) alguma peça móvel desce abaixo do ponto mais baixo da
    estrutura fixa (plano de apoio implícito). 0 = nunca atravessa."""
    fixos = {b for b, p in pap.items() if p == "estrutura"}
    X0 = mont.poses(qs[0])
    piso = min(float((v.vertices @ (X0[v.corpo] @ v.local)[:3, :3].T + (X0[v.corpo] @ v.local)[:3, 3])[:, 2].min())
               for v in mont.visuais if v.corpo in fixos) if fixos else None
    if piso is None:
        return None
    pior = 0.0
    for q in qs[:: max(1, len(qs) // 30)]:
        X = mont.poses(q)
        for v in mont.visuais:
            if v.corpo in fixos:
                continue
            T = X[v.corpo] @ v.local
            pior = max(pior, piso - float((v.vertices @ T[:3, :3].T + T[:3, 3])[:, 2].min()))
    return pior * 1000


# ------------------------------------------------------- oráculo DH
def oraculo_dh(mont, dh, amostras=60):
    """Compara a cinemática da fonte com a tabela DH publicada pelo fabricante:
    mesmo vetor de juntas, ponto do último corpo, alinhamento rígido (Kabsch)."""
    rng = np.random.default_rng(0)
    corpo = mont.indice_corpo(dh["corpo"])
    ponto = np.asarray(dh["ponto"], float)
    P, Q = [], []
    for _ in range(amostras):
        q = rng.uniform(-math.pi, math.pi, mont.nq)
        X = mont.poses(q)
        P.append(X[corpo][:3, :3] @ ponto + X[corpo][:3, 3])
        T = np.eye(4)
        for th, d, a, al in zip(q, dh["d"], dh["a"], dh["alpha"]):
            ct, st, ca, sa = math.cos(th), math.sin(th), math.cos(al), math.sin(al)
            T = T @ np.array([[ct, -st*ca, st*sa, a*ct], [st, ct*ca, -ct*sa, a*st], [0, sa, ca, d], [0, 0, 0, 1]])
        Q.append(T[:3, 3])
    P, Q = np.array(P), np.array(Q)
    pc, qc = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    Rm = Vt.T @ D @ U.T
    erro = np.linalg.norm((P - pc) @ Rm.T + qc - Q, axis=1)
    return dict(amostras=amostras, erro_medio_mm=float(erro.mean() * 1000), erro_max_mm=float(erro.max() * 1000),
                rotacao_alinhamento=Rm.round(6).tolist())


# --------------------------------------------------------------- papéis
def papeis(mont, acion, qs, varrido=None):
    moveis = set()
    X0 = mont.poses(qs[0])
    for q in qs[:: max(1, len(qs) // 12)]:
        X = mont.poses(q)
        for b in range(len(mont.corpos)):
            if np.abs(X[b] - X0[b]).max() > 1e-7:
                moveis.add(b)
    entrada, laco = set(), set()
    nomes = [varrido] if varrido else (list(acion) if len(acion) == 1 else [])
    for n in nomes:
        for k in acion[n]:
            entrada.add(mont.coords[k].corpo)
    acoplado = set()
    for e in mont.igualdades:
        if e.tipo in ("connect", "weld"):
            laco.update((e.a, e.b))
        elif e.tipo == "joint":
            acoplado.update((mont.coords[e.a].corpo, mont.coords[e.b].corpo))
    out = {}
    for b in range(len(mont.corpos)):
        out[b] = ("entrada" if b in entrada else "laco" if b in laco else
                  "acoplado" if b in acoplado and b in moveis else
                  "movel" if b in moveis else "estrutura")
    return out


def cor_visual(v, papel):
    base = 0.24 + 0.68 * np.asarray(v.rgba[:3])
    if papel == "entrada":
        return AMBAR * 0.85 + base * 0.15, 0.7
    if papel == "laco":
        return VERDE_AGUA * 0.8 + base * 0.2, 0.6
    if papel == "acoplado":
        return AZUL_ACOPLADO * 0.75 + base * 0.25, 0.55
    if papel == "estrutura":   # o que não se move recua visualmente
        return base * 0.55, 0.3
    return base, 0.45


def escolher_camera(mont, qs, cima, regiao, fov=24):
    """Busca determinística do ponto de vista: guinada a cada 15° e três
    elevações. Pontuação = √(ocupação da região do quadro) × visibilidade do
    movimento (deslocamento projetado médio das peças móveis / altura da
    região). Nenhuma regra por máquina; o mesmo critério para todos."""
    amostra = qs[:: max(1, len(qs) // 16)]
    pontos, centros = [], []
    for q in amostra:
        X = mont.poses(q)
        for v in mont.visuais:
            T = X[v.corpo] @ v.local
            pontos.append(v.vertices[:: max(1, len(v.vertices) // 300)] @ T[:3, :3].T + T[:3, 3])
        centros.append([X[b][:3, 3] for b in range(len(mont.corpos))])
    pontos = np.vstack(pontos)
    centros = np.array(centros)  # (amostras, corpos, 3)
    moveis = [b for b in range(len(mont.corpos)) if np.ptp(centros[:, b], axis=0).max() > 1e-6]
    # Se o que se move é pequeno frente à máquina inteira, enquadra o
    # movimento e o entorno imediato (a máquina pode sair pelas bordas).
    pm = []
    for q in amostra:
        X = mont.poses(q)
        pm += [v.vertices[:: max(1, len(v.vertices) // 300)] @ (X[v.corpo] @ v.local)[:3, :3].T
               + (X[v.corpo] @ v.local)[:3, 3] for v in mont.visuais if v.corpo in moveis]
    foco = "tudo"
    if pm:
        pm = np.vstack(pm)
        if np.ptp(pm, axis=0).max() < 0.4 * np.ptp(pontos, axis=0).max():
            c, meia = (pm.max(0) + pm.min(0)) / 2, np.ptp(pm, axis=0).max() * 0.65
            dentro = np.all(np.abs(pontos - c) <= meia, axis=1)
            pontos, foco = pontos[dentro], "pecas_moveis"
    # Eixo principal 3D de cada peça móvel em cada pose amostrada: mede o
    # quanto as peças ficam escorçadas (apontando para a câmera).
    eixos = []  # lista por pose; a nota usa a PIOR pose (o espectador vê todas)
    for q in amostra[:: max(1, len(amostra) // 6)]:
        Xm = mont.poses(q)
        eixos.append([])
        for b in moveis:
            pts = [v.vertices @ (Xm[b] @ v.local)[:3, :3].T for v in mont.visuais if v.corpo == b]
            if pts:
                P = np.vstack(pts)
                _, sv, vt = np.linalg.svd(P - P.mean(0), full_matrices=False)
                eixos[-1].append(vt[0] * sv[0])
    e1 = np.cross(cima, [1.0, 0, 0]) if abs(cima[0]) < .9 else np.cross(cima, [0, 1.0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(cima, e1)
    x0, y0, x1, y1 = regiao
    melhor = None
    for elev in (12, 22, 32):
        for guinada in range(0, 360, 15):
            g, el = math.radians(guinada), math.radians(elev)
            d = math.cos(el) * (math.cos(g) * e1 + math.sin(g) * e2) - math.sin(el) * cima
            cam = R.enquadrar(pontos, d, cima, fov, W, H, regiao)
            u, v, _, _ = cam.projetar(pontos)
            ocup = (np.ptp(u) * np.ptp(v)) / ((x1 - x0) * W * (y1 - y0) * H)
            vis = 0.0
            for b in moveis:
                pu, pv, _, _ = cam.projetar(centros[:, b])
                vis += math.hypot(np.ptp(pu), np.ptp(pv)) / ((y1 - y0) * H)
            vis /= max(1, len(moveis))
            # Ponderado pelo tamanho: peças longas dominam a leitura.
            leg = min((sum(np.linalg.norm(e - d * (e @ d)) for e in pose) / sum(np.linalg.norm(e) for e in pose)
                       for pose in eixos if pose), default=1.0)
            nota = math.sqrt(ocup) * vis * leg
            if melhor is None or nota > melhor[0] + 1e-12:
                melhor = (nota, cam, dict(guinada_graus=guinada, elevacao_graus=elev,
                                          ocupacao=float(ocup), visibilidade=float(vis),
                                          legibilidade=float(leg), nota=float(nota), foco=foco))
    return melhor[1], melhor[2], pontos


# ---------------------------------------------------------------- filme
def fonte(n, negrito=False):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf", n)


_MEDIDOR = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def caber(texto, tam, largura, negrito=False, minimo=18):
    """Maior corpo ≤ tam em que o texto cabe na largura (px)."""
    while tam > minimo and _MEDIDOR.textlength(texto, font=fonte(tam, negrito)) > largura:
        tam -= 1
    return fonte(tam, negrito)


def linhas_titulo(titulo, largura=900, maximo=64, minimo=48):
    """Uma linha se couber com corpo ≥ mínimo; senão quebra no travessão ou no
    último espaço que deixa a 1ª linha caber, e ajusta as duas linhas."""
    f = caber(titulo, maximo, largura, True, minimo)
    if _MEDIDOR.textlength(titulo, font=f) <= largura:
        return [titulo], f
    if " — " in titulo:
        partes = titulo.split(" — ", 1)
        partes = [partes[0], "— " + partes[1]]
    else:
        palavras = titulo.split()
        k = max(i for i in range(1, len(palavras))
                if _MEDIDOR.textlength(" ".join(palavras[:i]), font=fonte(minimo, True)) <= largura)
        partes = [" ".join(palavras[:k]), " ".join(palavras[k:])]
    tam = min(caber(p, maximo, largura, True, 30).size for p in partes)
    return partes, fonte(tam, True)


def gerar(manifesto, modelo, raiz, saida, rapido=False):
    m, mont, lidos = carregar(modelo, raiz)
    cache = {}
    acion, alvos, semente = plano_movimento(mont, modelo, cache, m)
    traj, solver = M.trajetoria(mont, acion, alvos, semente)
    qs = [q for q, _ in traj]
    medida = modelo["medida"]
    serie = np.array([medir(mont, q, medida, cache["eixo"], qs[0]) for q in qs])
    # --- auditoria
    qa = dict(id=modelo["id"], quadros=len(qs), juntas=len(mont.juntas), coordenadas=mont.nq,
              tipos_junta=sorted({j.tipo for j in mont.juntas}), base_congelada=mont.base_congelada,
              igualdades=[e.tipo for e in mont.igualdades],
              atuadores=list(mont.atuadores), modos=sorted({i["modo"] for _, i in traj}),
              mobilidade_max=max(i["mobilidade"] for _, i in traj),
              residuo_max=max(i["residuo"] for _, i in traj), faixa_acionador=cache["faixa"],
              ociosos_max=max(i.get("ociosos", 0) for _, i in traj),
              faixa_limitada_por_batente=cache.get("limitada_por_batente"),
              projecao_chave_inicial_rad=cache.get("projecao_chave_inicial_rad"),
              entrada_escolhida_no_manifesto=cache.get("entrada_escolhida_no_manifesto"),
              comandos_da_chave=cache.get("comandos_da_chave"),
              cortes_por_contato=cache["cortes"], arquivos_conferidos=lidos)
    qa["oraculo_mujoco_cinematica"] = M.oraculo_cinematica(m, mont, qs[:: max(1, len(qs) // 24)])
    if qa["mobilidade_max"] > 0 and m.nu == 1 and len(acion) == 1:
        import mujoco
        m2 = compilar(Path(raiz).resolve() / modelo["xml"])
        lo, hi = float(alvos[:, 0].min()), float(alvos[:, 0].max())
        qa["oraculo_mujoco_dinamica"] = M.oraculo_simulacao(m2, mont, M.Resolvedor(mont, acion),
                                                             np.linspace(lo, hi, 5)[1:-1])
    elif qa["mobilidade_max"] > 0:
        qa["oraculo_mujoco_dinamica"] = "nao_aplicado: oráculo dinâmico implementado só para um atuador"
    colisor = M.Colisor(mont, excluidos_da_fonte(m, mont))
    ref = cache.get("sobreposicao_referencia")
    if ref is None:
        ref = colisor.pares(qs[0])
    ref_set = set(map(tuple, ref))
    amostra = sorted(set(range(0, len(qs), max(1, len(qs) // 24))) | {len(qs) - 1, int(np.argmin(serie)), int(np.argmax(serie))})
    # Só contam pares NOVOS; os já sobrepostos na pose de referência da fonte ficam registrados.
    qa["sobreposicao_na_referencia_da_fonte"] = [list(x) for x in ref]
    qa["interferencias"] = {str(i): [list(x) for x in sorted(set(colisor.pares(qs[i])) - ref_set)] for i in amostra}
    qa["cortes_por_contato_novo"] = cache.get("cortes_por_contato_novo", [])
    qa["pares_que_cortaram_o_curso"] = [list(x) for x in cache.get("pares_que_cortaram", [])]
    qa["abaixo_do_plano_da_base_mm"] = abaixo_da_base(mont, qs, pap_auditoria := papeis(mont, acion, qs, cache["varrido"]))
    qa["medida"] = dict(tipo=medida["tipo"], min_mm=float(serie.min() * 1000), max_mm=float(serie.max() * 1000))
    if "oraculo" in modelo:
        o = modelo["oraculo"]
        if o["tipo"] == "curso_mm":
            curso = qa["medida"]["max_mm"] - qa["medida"]["min_mm"]
            qa["oraculo_fabricante"] = dict(o, medido_mm=curso, diferenca_mm=curso - o["valor_mm"],
                                            dentro_da_tolerancia=abs(curso - o["valor_mm"]) <= o["tolerancia_mm"])
        elif o["tipo"] == "medida_maxima_mm":
            dif = qa["medida"]["max_mm"] - o["valor_mm"]
            qa["oraculo_fabricante"] = dict(o, medido_mm=qa["medida"]["max_mm"], diferenca_mm=dif,
                                            dentro_da_tolerancia=abs(dif) <= o["tolerancia_mm"])
        elif o["tipo"] == "dh":
            r = oraculo_dh(mont, o)
            qa["oraculo_fabricante"] = dict(o, **r, dentro_da_tolerancia=r["erro_max_mm"] <= o["tolerancia_mm"])
    # --- imagem
    cima = np.array([0, 0, 1.0])
    pap = papeis(mont, acion, qs, cache["varrido"])
    cam, escolha, pontos = escolher_camera(mont, qs, cima, (0.08, 0.15, 0.92, 0.64))
    chao = float(pontos[:, 2].min())
    fundo = R.fundo_gradiente(W, H)
    saida.mkdir(parents=True, exist_ok=True)
    filme = saida / f"{modelo['id']}.mp4"
    ff = [ffmpeg_exe(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
          "-metadata", "comment=" + modelo["credito"] + " | " + modelo["licenca"] + " | privado, nao publicar",
          str(filme)]
    legenda_papel = {"entrada": ("Peça acionada", AMBAR), "laco": ("Laço fechado", VERDE_AGUA),
                     "acoplado": ("Acoplada à entrada", AZUL_ACOPLADO)}
    # Título na largura útil (900 px): encolhe até 48 px; abaixo disso, 2 linhas.
    titulo_linhas, fonte_titulo = linhas_titulo(modelo["titulo"])
    tam = fonte_titulo.size
    y_resumo = 96 + int(tam * 1.25) * len(titulo_linhas) + 16
    rodape = [caber(t, 25, 900) for t in (modelo["credito"], modelo["natureza"],
                                           "Prévia privada de laboratório · não publicar")]
    # Legenda só para papéis que aparecem: pré-passada em 3 poses, pixels por peça.
    vis = {}
    for i in (0, len(qs) // 2, len(qs) - 1):
        X = mont.poses(qs[i])
        malhas = [(v.vertices @ (X[v.corpo] @ v.local)[:3, :3].T + (X[v.corpo] @ v.local)[:3, 3], v.faces,
                   np.ones(3), 0.0) for v in mont.visuais]
        _, inf = R.renderizar(cam, malhas, fundo, ss=1)
        for v, px in zip(mont.visuais, inf["pixels_por_malha"]):
            vis[pap[v.corpo]] = vis.get(pap[v.corpo], 0) + px
    minimo = 0.0015 * W * H * 3
    presentes = [p for p in ("entrada", "laco", "acoplado") if vis.get(p, 0) >= minimo]
    qa_legenda = dict(pixels_por_papel={k: int(v) for k, v in vis.items()}, legenda=presentes)
    n_lacos = sum(e.tipo in ("connect", "weld") for e in mont.igualdades)
    resumo = [f"{len(mont.juntas)} juntas"]
    if mont.atuadores:
        resumo.append(f"{len(mont.atuadores)} atuador" + ("es" if len(mont.atuadores) > 1 else ""))
    n_acopl = sum(e.tipo == "joint" for e in mont.igualdades)
    if n_acopl:
        resumo.append(f"{n_acopl} acoplamento" + ("s" if n_acopl > 1 else "") + " entre juntas")
    if n_lacos:
        resumo.append(f"{n_lacos} laço" + ("s" if n_lacos > 1 else "") + " fechado" + ("s" if n_lacos > 1 else ""))
    if qa["mobilidade_max"]:
        resumo.append(f"{qa['mobilidade_max']} GL passivos")
    fonte_resumo = caber(" · ".join(resumo), 32, 900)
    rotulo = medida["rotulo"]
    vmin, vmax = serie.min(), serie.max()
    grafico = [(90 + int(i * 900 / (len(serie) - 1)), int(1588 - (v - vmin) / max(vmax - vmin, 1e-9) * 120))
               for i, v in enumerate(serie)]
    hashes = hashlib.sha256()
    quadros_contato = {}
    indices = range(0, len(qs), 6) if rapido else range(len(qs))
    with subprocess.Popen(ff, stdin=subprocess.PIPE) as enc:
        for i in indices:
            X = mont.poses(qs[i])
            malhas = []
            for v in mont.visuais:
                T = X[v.corpo] @ v.local
                cor, brilho = cor_visual(v, pap[v.corpo])
                malhas.append((v.vertices @ T[:3, :3].T + T[:3, 3], v.faces, cor, brilho))
            rgb, info = R.renderizar(cam, malhas, fundo, chao=chao)
            im = Image.fromarray(rgb)
            d = ImageDraw.Draw(im)
            for k, linha in enumerate(titulo_linhas):
                d.text((90, 96 + int(tam * 1.25) * k), linha, font=fonte_titulo, fill="white")
            d.text((90, y_resumo), " · ".join(resumo), font=fonte_resumo, fill="#9fb6c8")
            y = 1290
            x = 90
            for p in presentes:
                nome, cor = legenda_papel[p]
                d.ellipse((x, y + 8, x + 22, y + 30), fill=tuple(int(c * 255) for c in cor))
                d.text((x + 34, y), nome, font=fonte(30), fill="#d5e1ea")
                x += 60 + int(d.textlength(nome, font=fonte(30)))
            valor = f"{serie[i]*1000:.1f} mm".replace(".", ",")
            larg_valor = d.textlength(f"{serie.max()*1000:.1f} mm", font=fonte(48, True))
            d.text((90, 1370), rotulo, font=caber(rotulo, 36, 900 - larg_valor - 30), fill="white")
            d.text((990 - d.textlength(valor, font=fonte(48, True)), 1360), valor, font=fonte(48, True), fill="#f2b94b")
            d.line(grafico, fill="#3b5163", width=4)
            d.line(grafico[: i + 1], fill="#f2b94b", width=6)
            u, vv = grafico[i]
            d.ellipse((u - 9, vv - 9, u + 9, vv + 9), fill="white")
            if "oraculo_fabricante" in qa:
                for k, linha in enumerate(linha_oraculo(qa["oraculo_fabricante"])):
                    d.text((90, 1636 + 38 * k), linha, font=caber(linha, 28, 900),
                           fill="#9fb6c8" if qa["oraculo_fabricante"]["dentro_da_tolerancia"] else "#ff8a7a")
            for k, (t, ft) in enumerate(zip((modelo["credito"], modelo["natureza"],
                                             "Prévia privada de laboratório · não publicar"), rodape)):
                d.text((90, 1762 + 36 * k), t, font=ft, fill="#7f97aa")
            buf = np.asarray(im).tobytes()
            hashes.update(buf)
            enc.stdin.write(buf)
            if i in (0, len(qs) // 4, len(qs) // 2, 3 * len(qs) // 4, len(qs) - 1) or rapido:
                quadros_contato[i] = np.asarray(im)
        enc.stdin.close()
        if enc.wait():
            raise RuntimeError("E18-CODIFICACAO")
    chaves = sorted(quadros_contato)
    escolhidos = [quadros_contato[k] for k in chaves[:: max(1, len(chaves) // 5)]][:5]
    folha = np.concatenate([np.asarray(Image.fromarray(x).resize((360, 640))) for x in escolhidos], axis=1)
    Image.fromarray(folha).save(saida / f"{modelo['id']}_folha.jpg", quality=90)
    qa.update(video=filme.name, sha256_mp4=sha256(filme), sha256_quadros_rgb=hashes.hexdigest(),
              camera=dict(olho=cam.olho.tolist(), **escolha), cobertura_ultimo=info["cobertura"],
              legenda=qa_legenda, tamanho_titulo=tam,
              verificacao_video=conferir_video(filme, len(list(indices))), publish=False, visual_approved=False)
    return qa


def linha_oraculo(o):
    if o["tipo"] == "curso_mm":
        txt = f"Curso na ficha do fabricante: {o['valor_mm']:g} mm · neste modelo: {o['medido_mm']:.1f} mm"
    elif o["tipo"] == "medida_maxima_mm":
        txt = f"Ficha do fabricante: {o['valor_mm']:g} mm · neste modelo: {o['medido_mm']:.1f} mm"
    else:
        txt = f"Tabela DH do fabricante: desvio máx. {o['erro_max_mm']:.1f} mm em {o['amostras']} poses"
    linhas = [txt.replace(".", ",")]
    if not o["dentro_da_tolerancia"]:
        linhas.append(f"Fora da tolerância de ±{o['tolerancia_mm']:g} mm".replace(".", ","))
    return linhas


def conferir_video(path, esperados):
    import re
    info = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    streams = re.findall(r"Stream #\d+:\d+.*?: (Video|Audio|Data|Subtitle): (.*)", info)
    if len(streams) != 1 or streams[0][0] != "Video" or not streams[0][1].startswith("h264") \
            or not re.search(rf"\b{W}x{H}\b", streams[0][1]):
        raise ValueError("E18-VIDEO-FORMATO")
    dados = subprocess.check_output([ffmpeg_exe(), "-v", "error", "-i", str(path), "-vf", "scale=270:480",
                                     "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    fr = np.frombuffer(dados, np.uint8).reshape(-1, 480, 270, 3).astype(np.int16)
    if len(fr) != esperados:
        raise ValueError("E18-VIDEO-QUADROS")
    roi = fr[:, 70:310]
    mud = (np.abs(roi - roi[0]).max(axis=-1) > 18).sum(axis=(1, 2))
    if mud.max() < 300:
        raise ValueError("E18-VIDEO-SEM_MOVIMENTO")
    return dict(quadros=len(fr), pico_pixels_mudados=int(mud.max()), retorno_pixels=int(mud[-1]))


def fixar(manifesto_path, raiz):
    """Calcula os SHA256 dos arquivos lidos por cada modelo num checkout no commit fixado."""
    import mujoco
    man = json.loads(Path(manifesto_path).read_text())
    raiz = Path(raiz).resolve()
    for modelo in man["modelos"]:
        xml = raiz / modelo["xml"]
        m = compilar(xml)
        arquivos = {modelo["xml"], modelo["licenca_arquivo"]} | set(modelo.get("arquivos_extra", []))
        for adr in m.mesh_pathadr:
            if adr < 0:
                continue
            p = Path(m.paths[adr:].split(b"\x00")[0].decode())
            arquivos.add(((p if p.is_absolute() else xml.parent / p).resolve()).relative_to(raiz).as_posix())
        modelo["sha256"] = {a: sha256(raiz / a) for a in sorted(arquivos)}
    Path(manifesto_path).write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["fixar", "gerar"])
    ap.add_argument("manifesto", type=Path)
    ap.add_argument("raiz", type=Path)
    ap.add_argument("saida", type=Path, nargs="?")
    ap.add_argument("--ids")
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    if a.acao == "fixar":
        fixar(a.manifesto, a.raiz)
        return
    man = json.loads(a.manifesto.read_text())
    ids = set(a.ids.split(",")) if a.ids else None
    relatorio = []
    for modelo in man["modelos"]:
        if ids and modelo["id"] not in ids:
            continue
        try:
            r = gerar(man, modelo, a.raiz, a.saida, a.rapido)
            r["estado"] = "PASS"
        except ValueError as e:
            r = dict(id=modelo["id"], estado="BLOCKED", motivo=str(e))
        relatorio.append(r)
        print(json.dumps(r, ensure_ascii=False, default=float))
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "QA.json").write_text(json.dumps(dict(fonte=man["fonte"], modelos=relatorio), indent=2,
                                                ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
