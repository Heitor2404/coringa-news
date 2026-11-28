"""Pesquisa sob contrato: filtrar ruido SEM dar prova visual a metadados."""
from src.v4.formatos import garimpo_reference_first as G


def fake_discover(brief, buscar=None, get=None):
    if "compressor" in brief["id"]:
        candidates=[
            {"id":"g-1","titulo":"Reciprocating air compressor piston valve cutaway",
             "midia":"video","provedor":"Commons","pagina":"https://example.org/ref",
             "origem_media":"https://example.org/a.gif",
             "licenca_declarada":"CC BY 4.0"},
            {"id":"g-2","titulo":"Minecraft piston 3D compressor",
             "midia":"modelo_3d","provedor":"Sketchfab","pagina":"https://example.org/m"},
            {"id":"g-3","titulo":"Generic piston model",
             "midia":"modelo_3d","provedor":"Sketchfab","pagina":"https://example.org/p"},
            {"id":"g-4","titulo":"Reciprocating compressor animated model",
             "midia":"modelo_3d","provedor":"Sketchfab","pagina":"https://example.org/s",
             "licenca_declarada":"CC BY-NC 4.0"},
        ]
    else:
        candidates=[
            {"id":"e-1","titulo":"Four stroke Otto combustion engine valves animation",
             "midia":"animacao_gif","provedor":"Commons","pagina":"https://example.org/e",
             "licenca_declarada":"CC BY-SA 3.0"},
            {"id":"e-2","titulo":"Diesel four stroke engine animation",
             "midia":"animacao_gif","provedor":"Commons","pagina":"https://example.org/d",
             "licenca_declarada":"CC BY-SA 3.0"},
            {"id":"e-3","titulo":"Motor electric engine car",
             "midia":"modelo_3d","provedor":"Sketchfab","pagina":"https://example.org/v"}
        ]
    return {"candidatos":candidates,"erros":[]}


def test_compressor_rejeita_minecraft_pistao_generico(monkeypatch):
    monkeypatch.setattr(G.SCOUT,"descobrir",fake_discover)
    r=G.procurar("compressor_alternativo")
    ids={x["id"] for x in r["candidatos"]}
    assert ids == {"g-1","g-4"}
    assert r["rejeitados_por_metadados"]==2
    assert not r["publicar"] and r["renderer"] is None
    assert all(x["estado"]=="CANDIDATO_NAO_INSPECIONADO" for x in r["candidatos"])


def test_modelo_nc_e_sem_rig_nunca_vira_renderizer(monkeypatch):
    monkeypatch.setattr(G.SCOUT,"descobrir",fake_discover)
    c={x["id"]:x for x in G.procurar("compressor_alternativo")["candidatos"]}["g-4"]
    assert "F-LICENCA-RESTRITIVA" in c["sinais_de_restricao"]
    assert "F-3D-MESH-RIG-NAO-BAIXADOS" in c["sinais_de_restricao"]
    assert c["pode_reproduzir"] is False


def test_otro_nao_seleciona_animacao_diesel_como_otto(monkeypatch):
    monkeypatch.setattr(G.SCOUT,"descobrir",fake_discover)
    r=G.procurar("motor_otto_4t")
    assert {x["id"] for x in r["candidatos"]}=={"e-1"}
    assert r["rejeitados_por_metadados"]==2


def test_busca_desligada_nao_chama_servicos(monkeypatch):
    def never(*a,**kw):
        raise AssertionError("Rede nao podia ter sido chamada")
    monkeypatch.setattr(G.SCOUT,"descobrir",never)
    for process in G.REGRAS:
        r=G.procurar(process,sem_rede=True)
        assert r["estado"]=="BUSCA_DESLIGADA_NESTA_EXECUCAO"
        assert not r["publicar"] and r["candidatos"]==[]


def test_ausencia_de_candidatos_nao_vira_figuracao(monkeypatch):
    monkeypatch.setattr(G.SCOUT,"descobrir",lambda *_a,**_kw:
                        {"candidatos":[{"id":"p","titulo":"Cool piston moving",
                                        "midia":"modelo_3d"}],"erros":["timeout"]})
    r=G.procurar("compressor_alternativo")
    assert r["estado"]=="SEM_REFERENCIAS_COMPATIVEIS_POR_TITULO"
    assert r["candidatos"]==[]
    assert "timeout" in r["erros_de_fonte"]


def test_titulo_pode_sugerir_mas_nunca_aprovar_uso(monkeypatch):
    monkeypatch.setattr(G.SCOUT,"descobrir",fake_discover)
    for p in G.REGRAS:
        r=G.procurar(p)
        assert all(c["pode_reproduzir"] is False for c in r["candidatos"])
        assert all(c["evidencia_movimento"] is None for c in r["candidatos"])
        assert r["analise_visual"]=="NAO_EXECUTADA"
