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
AMBAR = np.array([0.93, 0.58, 0.16])
VERDE_AGUA = np.array([0.18, 0.66, 0.68])


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
    m = mujoco.MjModel.from_xml_path(str(xml))
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


def plano_movimento(mont, modelo, solver_cache):
    mov = modelo["movimento"]
    dur = float(mov.get("duracao_s", 6.0))
    n = int(round(dur * FPS))
    if mov["tipo"] == "varredura_atuador":
        nome = mov["atuador"]
        if nome not in mont.atuadores:
            raise ValueError("E18-ATUADOR_DESCONHECIDO")
        acion = {nome: mont.atuadores[nome]}
        solver = M.Resolvedor(mont, acion)
        faixa = solver.faixa_acionador(0)
        medida = modelo["medida"]
        if medida["tipo"] == "folga":
            faixa, cortes, eixo = M.corte_no_contato(mont, solver, faixa, medida["a"], medida["b"],
                                                     mont.chaves["qpos0"])
        else:
            cortes, eixo = [], None
        q0 = mont.chaves["qpos0"]
        inicio = float(solver.linhas[0] @ q0)
        if not faixa[0] - 1e-9 <= inicio <= faixa[1] + 1e-9:
            inicio = faixa[0]
        outro = faixa[1] if abs(faixa[1] - inicio) >= abs(faixa[0] - inicio) else faixa[0]
        # Pausa · ida · pausa · volta · pausa (proporções fixas para todo modelo).
        p, v = int(n * .1), int(n * .35)
        perfil = np.concatenate([np.zeros(p), suave(v), np.ones(n - 2 * p - 2 * v), suave(v)[::-1], np.zeros(p)])
        alvos = (inicio + perfil * (outro - inicio))[:, None]
        solver_cache["faixa"] = faixa
        solver_cache["cortes"] = cortes
        solver_cache["eixo"] = eixo
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
        solver_cache["faixa"] = None
        solver_cache["cortes"] = []
        solver_cache["eixo"] = None
        return acion, np.array(alvos), chaves[0]
    raise ValueError("E18-MOVIMENTO_NAO_SUPORTADO")


def medir(mont, q, medida, eixo):
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
def papeis(mont, acion, qs):
    moveis = set()
    X0 = mont.poses(qs[0])
    for q in qs[:: max(1, len(qs) // 12)]:
        X = mont.poses(q)
        for b in range(len(mont.corpos)):
            if np.abs(X[b] - X0[b]).max() > 1e-7:
                moveis.add(b)
    entrada, laco = set(), set()
    if len(acion) == 1:
        for coef in acion.values():
            for k in coef:
                entrada.add(mont.juntas[k].corpo)
    for e in mont.igualdades:
        if e.tipo in ("connect", "weld"):
            laco.update((e.a, e.b))
    out = {}
    for b in range(len(mont.corpos)):
        out[b] = ("entrada" if b in entrada else "laco" if b in laco else
                  "movel" if b in moveis else "estrutura")
    return out


def cor_visual(v, papel):
    base = 0.24 + 0.68 * np.asarray(v.rgba[:3])
    if papel == "entrada":
        return AMBAR * 0.85 + base * 0.15, 0.7
    if papel == "laco":
        return VERDE_AGUA * 0.8 + base * 0.2, 0.6
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
                                          legibilidade=float(leg), nota=float(nota)))
    return melhor[1], melhor[2], pontos


# ---------------------------------------------------------------- filme
def fonte(n, negrito=False):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf", n)


def gerar(manifesto, modelo, raiz, saida, rapido=False):
    m, mont, lidos = carregar(modelo, raiz)
    cache = {}
    acion, alvos, semente = plano_movimento(mont, modelo, cache)
    traj, solver = M.trajetoria(mont, acion, alvos, semente)
    qs = [q for q, _ in traj]
    medida = modelo["medida"]
    serie = np.array([medir(mont, q, medida, cache["eixo"]) for q in qs])
    # --- auditoria
    qa = dict(id=modelo["id"], quadros=len(qs), juntas=mont.nq, igualdades=[e.tipo for e in mont.igualdades],
              atuadores=list(mont.atuadores), modos=sorted({i["modo"] for _, i in traj}),
              mobilidade_max=max(i["mobilidade"] for _, i in traj),
              residuo_max=max(i["residuo"] for _, i in traj), faixa_acionador=cache["faixa"],
              cortes_por_contato=cache["cortes"], arquivos_conferidos=lidos)
    qa["oraculo_mujoco_cinematica"] = M.oraculo_cinematica(m, mont, qs[:: max(1, len(qs) // 24)])
    if qa["mobilidade_max"] > 0 and m.nu == 1:
        import mujoco
        m2 = mujoco.MjModel.from_xml_path(str(Path(raiz).resolve() / modelo["xml"]))
        lo, hi = float(alvos.min()), float(alvos.max())
        qa["oraculo_mujoco_dinamica"] = M.oraculo_simulacao(m2, mont, M.Resolvedor(mont, acion),
                                                             np.linspace(lo, hi, 5)[1:-1])
    exc = [(int(s) >> 16, int(s) & 0xFFFF) for s in m.exclude_signature[: m.nexclude]]
    excl = M.pares_excluidos(mont, exc)
    amostra = sorted({0, len(qs) // 4, len(qs) // 2, 3 * len(qs) // 4, len(qs) - 1, int(np.argmin(serie)), int(np.argmax(serie))})
    qa["interferencias"] = {str(i): M.interferencias(mont, qs[i], excl) for i in amostra}
    qa["abaixo_do_plano_da_base_mm"] = abaixo_da_base(mont, qs, pap_auditoria := papeis(mont, acion, qs))
    qa["medida"] = dict(tipo=medida["tipo"], min_mm=float(serie.min() * 1000), max_mm=float(serie.max() * 1000))
    if "oraculo" in modelo:
        o = modelo["oraculo"]
        if o["tipo"] == "medida_maxima_mm":
            dif = qa["medida"]["max_mm"] - o["valor_mm"]
            qa["oraculo_fabricante"] = dict(o, medido_mm=qa["medida"]["max_mm"], diferenca_mm=dif,
                                            dentro_da_tolerancia=abs(dif) <= o["tolerancia_mm"])
        elif o["tipo"] == "dh":
            r = oraculo_dh(mont, o)
            qa["oraculo_fabricante"] = dict(o, **r, dentro_da_tolerancia=r["erro_max_mm"] <= o["tolerancia_mm"])
    # --- imagem
    cima = np.array([0, 0, 1.0])
    pap = papeis(mont, acion, qs)
    cam, escolha, pontos = escolher_camera(mont, qs, cima, (0.08, 0.15, 0.92, 0.64))
    chao = float(pontos[:, 2].min())
    fundo = R.fundo_gradiente(W, H)
    saida.mkdir(parents=True, exist_ok=True)
    filme = saida / f"{modelo['id']}.mp4"
    ff = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
          "-metadata", "comment=" + modelo["credito"] + " | " + modelo["licenca"] + " | privado, nao publicar",
          str(filme)]
    legenda_papel = {"entrada": ("Entrada (atuador)", AMBAR), "laco": ("Laço fechado", VERDE_AGUA)}
    presentes = [p for p in ("entrada", "laco") if p in pap.values()]
    n_lacos = sum(e.tipo in ("connect", "weld") for e in mont.igualdades)
    resumo = [f"{mont.nq} juntas", f"{len(mont.atuadores)} atuador" + ("es" if len(mont.atuadores) > 1 else "")]
    if n_lacos:
        resumo.append(f"{n_lacos} laço" + ("s" if n_lacos > 1 else "") + " fechado" + ("s" if n_lacos > 1 else ""))
    if qa["mobilidade_max"]:
        resumo.append(f"{qa['mobilidade_max']} GL passivos")
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
            d.text((90, 96), modelo["titulo"], font=fonte(64, True), fill="white")
            d.text((90, 186), " · ".join(resumo), font=fonte(32), fill="#9fb6c8")
            y = 1290
            x = 90
            for p in presentes:
                nome, cor = legenda_papel[p]
                d.ellipse((x, y + 8, x + 22, y + 30), fill=tuple(int(c * 255) for c in cor))
                d.text((x + 34, y), nome, font=fonte(30), fill="#d5e1ea")
                x += 60 + int(d.textlength(nome, font=fonte(30)))
            d.text((90, 1370), rotulo, font=fonte(36), fill="white")
            valor = f"{serie[i]*1000:.1f} mm".replace(".", ",")
            d.text((990 - d.textlength(valor, font=fonte(48, True)), 1360), valor, font=fonte(48, True), fill="#f2b94b")
            d.line(grafico, fill="#3b5163", width=4)
            d.line(grafico[: i + 1], fill="#f2b94b", width=6)
            u, vv = grafico[i]
            d.ellipse((u - 9, vv - 9, u + 9, vv + 9), fill="white")
            if "oraculo_fabricante" in qa:
                for k, linha in enumerate(linha_oraculo(qa["oraculo_fabricante"])):
                    d.text((90, 1636 + 38 * k), linha, font=fonte(28),
                           fill="#9fb6c8" if qa["oraculo_fabricante"]["dentro_da_tolerancia"] else "#ff8a7a")
            d.text((90, 1762), modelo["credito"], font=fonte(25), fill="#7f97aa")
            d.text((90, 1798), modelo["natureza"], font=fonte(25), fill="#7f97aa")
            d.text((90, 1834), "Prévia privada de laboratório · não publicar", font=fonte(25), fill="#7f97aa")
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
              verificacao_video=conferir_video(filme, len(list(indices))), publish=False, visual_approved=False)
    return qa


def linha_oraculo(o):
    if o["tipo"] == "medida_maxima_mm":
        txt = f"Ficha do fabricante: {o['valor_mm']:g} mm · neste modelo: {o['medido_mm']:.1f} mm"
    else:
        txt = f"Tabela DH do fabricante: desvio máx. {o['erro_max_mm']:.1f} mm em {o['amostras']} poses"
    linhas = [txt.replace(".", ",")]
    if not o["dentro_da_tolerancia"]:
        linhas.append(f"Fora da tolerância de ±{o['tolerancia_mm']:g} mm".replace(".", ","))
    return linhas


def conferir_video(path, esperados):
    s = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)]))["streams"]
    if len(s) != 1 or (s[0]["width"], s[0]["height"]) != (W, H) or s[0]["codec_name"] != "h264":
        raise ValueError("E18-VIDEO-FORMATO")
    dados = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "scale=270:480",
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
        m = mujoco.MjModel.from_xml_path(str(xml))
        arquivos = {modelo["xml"], modelo["licenca_arquivo"]}
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
