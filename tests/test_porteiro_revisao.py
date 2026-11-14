"""Porteiro final × fiscal V2 (integração): o caminho REAL de main._fazer_curiosidade decide se o vídeo segue para o
envio (telegram) ou fica retido. Só as etapas de geração (roteiro, mídia, voz, render) são trocadas por um vídeo
pronto; o porteiro (_aplicar_porteiro) e a decisão de envio são os de produção."""
import pytest

import main


def _q():
    return {'erros': [], 'motivos': [], 'nota': 10, 'cont': {}, 'ideias': 8, 'dur': 50, 'palavras': 120, 'ia': False}


@pytest.fixture
def fluxo(monkeypatch, tmp_path):
    """Roda _fazer_curiosidade com um resultado do fiscal V2 escolhido pelo teste; devolve o que foi enviado."""
    from src import roteiro
    enviados, avisos = [], []

    def rodar(piloto, dur=50.0, problemas_tela=None):
        tema = {'pergunta': 'Por que o navio encalhou?'}
        monkeypatch.setattr(roteiro, 'tema_livre', lambda pedido: dict(tema))
        monkeypatch.setattr(roteiro, 'escrever_explica', lambda t, parte, serie: {'titulo': 'Teste', 'resumo': 'r', 'arco': [], 'parte': 0})
        monkeypatch.setattr(main, '_arquivo_serie', lambda pedido, parte: tmp_path / 'serie.json')

        def montar_video(v, pasta, nome, teste=False):
            # o vídeo "ficou pronto"; o porteiro de produção decide o que acontece com ele
            arq = pasta / f'{nome}.mp4'
            arq.write_bytes(b'mp4')
            (pasta / f'{nome}.txt').write_text('legenda', encoding='utf-8')
            main._aplicar_porteiro(v, _q(), {'problemas_tela': problemas_tela or []}, dur, piloto, teste)
            return arq
        monkeypatch.setattr(main, 'montar_video', montar_video)
        monkeypatch.setattr(main, 'telegram', lambda arq, legenda, v=None: enviados.append(arq.name))
        monkeypatch.setattr(main, '_tg', lambda metodo, dados, *a, **k: avisos.append(dados.get('text', '')))
        r = main._fazer_curiosidade('o navio Ever Given', 1, tmp_path, unico=True)
        return r, list(enviados), list(avisos)
    return rodar


def test_zero_bloqueios_e_uma_revisao_pendente_nao_publica(fluxo):
    r, enviados, avisos = fluxo({'bloqueios': [], 'revisoes': ['S7 cena 2: capacidade apresentada como carga transportada'],
                                 'aprovacao_automatica': False})
    assert enviados == []                                            # nada vai ao ar sem aprovação humana explícita
    assert r == 'pular'
    assert any('revisão humana pendente' in a and 'capacidade' in a for a in avisos), avisos


def test_resposta_do_fiscal_sem_aprovacao_explicita_tambem_retem(fluxo):
    r, enviados, _ = fluxo({'bloqueios': [], 'aprovacao_automatica': None})
    assert enviados == []


def test_um_bloqueio_nao_publica(fluxo):
    r, enviados, avisos = fluxo({'bloqueios': ['S5 cena 10: acontecimento crítico sem representação adequada'],
                                 'revisoes': [], 'aprovacao_automatica': False})
    assert enviados == [] and r == 'pular'
    assert any('fiscal V2.2: S5' in a for a in avisos), avisos


def test_zero_bloqueios_e_zero_revisoes_prossegue(fluxo):
    r, enviados, avisos = fluxo({'bloqueios': [], 'revisoes': [], 'aprovacao_automatica': True})
    assert r is True and enviados == ['explica-o-navio-ever-given.mp4']
    assert not any('barrado' in a for a in avisos)


def test_aprovado_pelo_fiscal_v2_ainda_respeita_os_demais_controles(fluxo):
    ok = {'bloqueios': [], 'revisoes': [], 'aprovacao_automatica': True}
    for kw in ({'dur': 95.0}, {'problemas_tela': ['legenda sobre título em 3.2 s']}):
        r, enviados, avisos = fluxo(ok, **kw)
        assert enviados == [] and r == 'pular', kw                  # vídeo longo / texto sobre texto continuam barrando


def test_sem_fiscal_v2_o_motor_atual_segue_como_antes(fluxo):
    r, enviados, _ = fluxo(None)                                     # MOTOR_VISUAL ausente: comportamento de produção intacto
    assert r is True and enviados
