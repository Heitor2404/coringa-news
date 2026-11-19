"""Ponte real, sem usar o renderizador vetorial elementar ou IA simulada de qualidade.

Prova: plano ATLAS aprovado -> arquivo Formato original -> mídia autenticada
-> FilmEditorial. Sem MP4 válido, mapa não entra; sem licença, não entra.
"""
import copy
import hashlib
import json
from pathlib import Path
import pytest

from src.v4.formatos import ponte_mapa_atlas as BR
from src.v4.formatos import filme_editorial as FILM
from src.v4.formatos import plano as ATLAS
from src.v4.formatos import direcao_eventos as D
from src.v4.formatos import contrato_visual_comum as C

ROOT=Path(__file__).resolve().parents[1]
ATLAS_FIX=ROOT/"tests/dados/formatos_atlas_resolvido.json"
FILME_FIX=ROOT/"docs/v4/formatos/filme_taiwan_prova.json"


def _atlas():
    p=json.loads(ATLAS_FIX.read_text(encoding="utf-8"))
    return ATLAS.resolver_tempos(p,[])


def _film():
    return json.loads(FILME_FIX.read_text(encoding="utf-8"))


def _primeiro_intervalo(p):
    # Não inventar centro do país; usar mapa e ROI que já existem no ATLAS.
    keys=[x for x in p["palco"] if x["tipo"]=="mapa"]
    assert keys
    a=keys[0]["t"]
    idx=p["palco"].index(keys[0])
    end=p["palco"][idx+1]["t"] if idx+1<len(p["palco"]) else p["duracao"]
    return float(a), min(3.0,float(end)-float(a))


def test_fiscal_original_valida_o_mapa_antes_de_preparar():
    p=_atlas()
    assert not [x for x in ATLAS.validar(p) if x['gravidade']=='erro']
    a,d=_primeiro_intervalo(p)
    q=BR.verificar_plano(p,a,d)
    assert q["palco"]=="PalcoMapa/MapLibre"
    assert q["rasters_ativos"] and q["roi"]
    assert all(len(r["sha256"])==64 for r in q["rasters_ativos"])


def test_fonte_rejeita_raster_ausente_ou_alterado():
    p=_atlas();p["rasters"]=[]
    a,d=_primeiro_intervalo(p)
    with pytest.raises(ValueError,match="reprovação no fiscal ATLAS"):
        BR.verificar_plano(p,a,d)


def test_ponte_so_aceita_intervalo_cartografico_do_atlas():
    p=_atlas(); a,d=_primeiro_intervalo(p)
    with pytest.raises(ValueError):
        BR.verificar_plano(p,a,p["duracao"]+1)
    with pytest.raises(ValueError):
        BR.verificar_plano(p,-1,d)


def test_props_usam_palco_original_e_copiam_raster_byte_a_byte(tmp_path):
    p=_atlas();a,d=_primeiro_intervalo(p)
    r=BR.preparar(p,a,d,tmp_path/"stage",tmp_path/"public")
    props=json.loads((tmp_path/"stage/props_atlas_formato.json").read_text())
    assert r["renderer"]=="ATLAS/Formato/PalcoMapa/MapLibre"
    assert props["formato"]=="atlas"
    assert props["palco"] and props["rasters"] and props["geo"]["topo"]
    assert r["frame_inicio"]>=0 and r["frame_fim_inclusivo"]>r["frame_inicio"]
    assert r["status"]=="PREPARADO_NAO_RENDERIZADO"
    for rr in props["rasters"]:
        cp=tmp_path/"public"/rr["src"]
        assert cp.exists()
        assert BR.sha256(cp)==ATLAS.raster_info(rr["nome"])["sha256"]
    assert (ROOT/"motor4/remotion/src/formatos/NarrativeMapStage.tsx").exists() is False


def _prova(tmp_path,plano_film):
    """Comprovante sintético explicitamente usado só para teste do gate, não QA real."""
    clip=Path("stage_atlas/carteira/mapa.mp4")
    proof=Path("stage_atlas/carteira/comprovante_atlas.json")
    (tmp_path/clip).parent.mkdir(parents=True,exist_ok=True)
    (tmp_path/clip).write_bytes(b"clipe-NAO-REAL-para-teste-de-integridade"*3400)
    sh=hashlib.sha256((tmp_path/clip).read_bytes()).hexdigest()
    span=plano_film["shots"][0]["end"]-plano_film["shots"][0]["start"]
    data={"schema":1,"renderer":"ATLAS/Formato/PalcoMapa/MapLibre",
          "status":"PRONTO_PARA_REVISAO_HUMANA",
          "mapeamento":{"roi":[116.0,19.0,126.0,27.0],
                        "rasters_ativos":[{"nome":"ne2_asia_leste","sha256":"a"*64,
                          "atribuicao":"Natural Earth II"}]},
          "video_sha256":sh,"duracao_s":span,"quadros_reais":[{"t":1.0,"luminancia":75}],
          "aprovacao_humana":"PENDENTE","publicado":False}
    (tmp_path/proof).write_text(json.dumps(data))
    return clip,proof


def test_filme_aceita_so_clipe_atlas_autenticado_sem_alterar_outros_planos(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    p=_film()
    old=copy.deepcopy(p)
    clip,proof=_prova(tmp_path,p)
    res=BR.inserir_no_filme(p,p["shots"][0]["id"],clip,proof)
    assert p==old
    assert res["shots"][0]["type"]=="atlas_map"
    assert res["shots"][0]["evidence"]=="explainer"
    assert res["shots"][1:]==old["shots"][1:]
    assert res["shots"][0]["atlas_direcao"]["palco"]=="ATLAS/Formato/PalcoMapa"
    assert FILM.avaliar(res)["pronto"], FILM.avaliar(res)["bloqueios"]
    shared=C.auditar(res)
    assert shared["estrutura_declarada_ok"]
    assert shared["prova_visual"]=="NAO_INSPECIONADA"
    assert shared["aprovacao_humana"]=="PENDENTE"


def test_mesmo_clipe_alterado_e_reprovado_antes_da_montagem(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    p=_film();clip,proof=_prova(tmp_path,p)
    res=BR.inserir_no_filme(p,p["shots"][0]["id"],clip,proof)
    (tmp_path/clip).write_bytes(b"substituicao-tentou-se-passar-por-mapa"*5000)
    errs={e["codigo"] for e in FILM.avaliar(res)["bloqueios"]}
    assert "F-ATLAS-COMPROVANTE" in errs
    with pytest.raises(ValueError,match="não validado"):
        BR.inserir_no_filme(p,p["shots"][0]["id"],clip,proof)


def test_falta_de_comprovante_bloqueia_mapa(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    p=_film();clip,proof=_prova(tmp_path,p)
    res=BR.inserir_no_filme(p,p["shots"][0]["id"],clip,proof)
    (tmp_path/proof).unlink()
    assert "F-ATLAS-COMPROVANTE" in {e["codigo"] for e in FILM.avaliar(res)["bloqueios"]}


def test_mapa_elementar_continua_proibido_sem_fallback():
    p=_film()
    p["shots"][0]["type"]="map"
    p["shots"][0]["map"]={"kind":"country"}
    assert "F-MAPA-PROIBIDO" in {e["codigo"] for e in FILM.avaliar(p)["bloqueios"]}


def test_intencoes_geograficas_roteadas_ao_atlas_comprovado(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    p=_film();clip,proof=_prova(tmp_path,p)
    r=BR.inserir_no_filme(p,p["shots"][0]["id"],clip,proof)
    assert not D.verificar([r["shots"][0]])
    q=copy.deepcopy(r["shots"][0]);q["type"]="photo"
    assert "D-EXIGE-CARTOGRAFIA-ATLAS" in {e["codigo"] for e in D.verificar([q])}


def test_nao_inventa_timbre_gemini_ou_publicacao(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    p=_film();clip,proof=_prova(tmp_path,p)
    r=BR.inserir_no_filme(p,p["shots"][0]["id"],clip,proof)
    assert r["tipo"]=="PROVA_VISUAL_PRIVADA"
    assert "narrador" not in r or (r["narrador"].get("motor") != "edge")
    r["tipo"]="PRODUCAO"
    assert "F-VOZ-TESTE-EM-PRODUCAO" in {x["codigo"] for x in FILM.avaliar(r)["bloqueios"]}
