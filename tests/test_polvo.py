"""O teste real do polvo (12/11/2026, execução 43350473725) refeito offline com os dados do registro: o acervo de 27
imagens, a pergunta, o roteiro de mecanismo e o casamento que voltou 0/13. Gastou ≈ US$ 0,49 e não saiu vídeo.
Aqui: a viabilidade é decidida ANTES do roteiro; o teto de palavras não pede roteiro de novo; o casamento registra por
que cada ideia ficou sem foto; frase de mecanismo vira esquema explicativo; o porteiro é adaptativo (sem afrouxar
história); e a chamada opcional não sai com o teto estourado. Nenhuma chamada paga."""
import copy

import pytest

from src import acervo, custo, gemini, orcamento, orcamento_video as ov, roteiro, storyboard as sbm, viabilidade

PERGUNTA = 'Como o polvo muda de cor em menos de um segundo?'
FATOS = ('- ★ A pele do polvo tem cromatóforos: sacos elásticos de pigmento (Wikipédia)\n'
         '- Músculos radiais esticam o cromatóforo em menos de um segundo (Wikipédia)\n'
         '- Os músculos são ligados direto a nervos do cérebro (Wikipédia)\n'
         '- Leucóforos refletem a luz do ambiente; iridóforos fazem brilho metálico (Wikipédia)\n'
         '- O polvo não enxerga cores como nós (reportagem)\n- O choco também muda de cor (Wikipédia)')
# as 27 imagens úteis do registro (a0–a26), com o que o catálogo disse; sem a marca "genérica" (não ficou registrada):
# as de espécie identificada são específicas, as outras ("um polvo", "um cefalópode") ficam como genéricas — o pior caso
REG = ['polvo comum (Octopus vulgaris) no fundo do mar (2007)', 'polvo (Octopus bimaculoides) sobre superfície escura',
       'polvo (Octopus tetricus) camuflado na areia', 'polvo ocelado (Amphioctopus fangsiao) em concha (2005)',
       'polvo (Octopus rubescens) em poça de maré', 'polvo (Octopus vulgaris) camuflado na areia (2009)',
       'poça de maré com algas e rochas', 'estrela-do-mar azul num recife (2004)', 'um polvo camuflado numa rocha',
       'praia com recifes vista do alto (2007)', 'polvo (Octopus vulgaris) na Espanha', 'um polvo rosa camuflado no coral',
       'um polvo camuflado entre rochas', 'um polvo numa fenda', 'cabeça e tentáculos de um polvo rosa',
       'cabeça de um polvo com luz azul', 'um polvo sob luz azul', 'choco flambeu (Metasepia pfefferi) colorido',
       'choco flambeu nas Filipinas', 'um polvo no fundo rochoso', 'um cefalópode colorido entre algas',
       'polvo comum (Octopus vulgaris) no parque natural', 'polvo comum (Octopus vulgaris) camuflado entre algas',
       'polvo comum (Octopus vulgaris) sobre cascalho', 'olho de um polvo camuflado', 'polvo-diurno no Atol Pearl e Hermes',
       'um polvo no leito arenoso']


def _acervo():
    out = []
    for k, m in enumerate(REG):
        out.append({'id': f'a{k}', 'mostra': m, 'titulo': m, 'mini': b'', 'util': True, 'nota': 6, 'fonte': 'commons',
                    'credito': 'Wikimedia', 'w': 1600, 'h': 1200, 'generica': '(' not in m and 'choco flambeu' not in m})
    return out


AC = lambda quem='', onde='', quando='', recurso='': {'quem': quem, 'onde': onde, 'quando': quando, 'recurso': recurso}
IDEIAS = [('abertura', 'Este polvo não enxerga verde nem vermelho, mas pinta a própria pele.'),
          ('contexto', 'O polvo-comum vive no fundo do Mediterrâneo e do Atlântico.'),
          ('mecanismo', 'A pele dele tem milhares de cromatóforos, sacos elásticos de pigmento.'),
          ('mecanismo', 'Músculos em volta de cada saco o esticam como um balão.'),
          ('evidencia', 'Isso acontece em menos de um segundo.'),
          ('mecanismo', 'Os músculos são ligados direto a nervos que saem do cérebro.'),
          ('mecanismo', 'Embaixo, os leucóforos refletem a luz do ambiente.'),
          ('mecanismo', 'Os iridóforos fazem o brilho metálico, como uma bolha de sabão.'),
          ('contexto', 'O choco, primo do polvo, faz o mesmo truque.'),
          ('virada', 'Mas o polvo não enxerga as cores como nós.'),
          ('mecanismo', 'Uma hipótese é que a própria pele perceba a luz.'),
          ('payoff', 'Por isso ele se camufla em menos de um segundo.'),
          ('consequencia', 'É assim que ele some na frente de um predador.')]


def _roteiro():
    cenas = [{'tipo': 'gancho' if k == 0 else 'historia', 'fala': f, 'grupo': k, 'evento': f'e{k}', 'bloco': {'funcao': fn},
              'cenario': 'octopus skin closeup', 'busca': 'octopus', 'acontecimento': AC(recurso='')}
             for k, (fn, f) in enumerate(IDEIAS)] + [{'tipo': 'fechamento', 'fala': 'Segue o Coringa Explica.'}]
    v = {'titulo': 'POLVO', 'tipo_conteudo': 'mecanismo', 'plano': {'modos': ['mecanismo'], 'duracao_alvo_s': 45},
         'estilo_visual': 'photorealistic', 'cenas': cenas}
    return sbm.construir(v)


@pytest.fixture(autouse=True)
def limpo(monkeypatch):
    custo.zerar()
    monkeypatch.setattr(orcamento, 'sobra', lambda: 999)
    yield
    custo.zerar()
    ov.fechar()


# ───────── 1. viabilidade antes das chamadas caras ─────────
def test_polvo_e_mecanismo_e_o_acervo_basta_antes_do_roteiro():
    assert viabilidade.classificar({'pergunta': PERGUNTA}, FATOS) == 'mecanismo'
    assert viabilidade.classificar({'pergunta': 'Como Victor Lustig vendeu a Torre Eiffel em 1925?'}) == 'historico'
    r = viabilidade.avaliar(_acervo(), 'mecanismo')
    assert r['ok'] and r['uteis'] == 27


def test_sem_material_o_tema_cai_antes_de_qualquer_pedido_ao_claude(monkeypatch):
    from src import fontes
    monkeypatch.setattr(orcamento, 'marca', lambda *a, **k: None)
    monkeypatch.setattr(fontes, 'coletar', lambda *a, **k: (FATOS, ['Wikipédia'], 'u', {'epoca': ''}))
    monkeypatch.setattr(acervo, 'coletar', lambda *a, **k: _acervo()[6:8])         # só a poça e a estrela-do-mar
    pedidos = []
    monkeypatch.setattr(gemini, 'json_', lambda *a, **k: pedidos.append(1) or {})
    with pytest.raises(ValueError, match='ANTES do roteiro'):
        roteiro.escrever_explica({'pergunta': PERGUNTA, 'termos': ['polvo'], 'partes': 1})
    assert pedidos == []                                                            # nenhum roteiro, crítica ou gancho


# ───────── 4 e 5. casamento 0/13 registrado; mecanismo vira esquema; porteiro adaptativo ─────────
def _casar_como_na_rodada(monkeypatch, capsys):
    """O que a rodada viu: o Gemini não escolheu foto para nenhuma ideia (0/13)."""
    pedidos = []
    monkeypatch.setattr(gemini, 'json_visao', lambda p, m, leve=False: pedidos.append(p) or
                        {'escolhas': [{'ideia': k, 'foto': None} for k in range(13)]})
    v = acervo.casar(_roteiro(), _acervo())
    return v, pedidos[0], capsys.readouterr().out


def test_casamento_registra_o_porque_e_diz_ao_gemini_o_que_cada_frase_precisa(monkeypatch, capsys):
    v, pedido, log = _casar_como_na_rodada(monkeypatch, capsys)
    assert '0 de 13 ideias' in log and 'o Gemini respondeu 13 ideia(s), 13 sem foto (null)' in log
    assert log.count('sem foto — o Gemini não escolheu nenhuma') == 13
    assert '[mecanismo: foto só se MOSTRAR o processo' in pedido and '[contexto: uma boa foto do próprio assunto serve]' in pedido


def test_rodada_do_polvo_agora_monta_com_contexto_e_esquemas_pendentes(monkeypatch, capsys):
    v, _, _ = _casar_como_na_rodada(monkeypatch, capsys)
    v = acervo.preencher(v, _acervo())
    ideias = [c for c in v['cenas'] if c['tipo'] != 'fechamento']
    com_foto = [k for k, c in enumerate(ideias) if c.get('foto')]
    assert set(com_foto) >= {0, 1, 8}                                              # abertura e contexto: fotos do assunto
    assert all(not ideias[k].get('foto') for k in (2, 3, 5, 6, 7, 10))              # mecanismo: fica para o esquema
    v = roteiro._planos_sem_foto(v, '')                                            # antes: ValueError (4 de 13)
    esq = [c for c in v['cenas'] if c.get('midia') == 'pendente']
    assert len(esq) >= 6 and not any(c.get('prompt_imagem') for c in esq)       # Etapa 2: esquema PENDENTE, sem IA inventando
    from src import resolucao
    resolucao.resolver(v)
    tipos = {c['sb']['resolucao']['tipo'] for c in v['cenas'] if c.get('sb') and c['sb']['proposito'] == 'mecanismo'}
    assert tipos == {'esquema_pendente'}


def test_mecanismo_sem_foto_real_nenhuma_continua_barrado(monkeypatch, capsys):
    v, _, _ = _casar_como_na_rodada(monkeypatch, capsys)                            # e nenhuma reserva
    with pytest.raises(ValueError, match='pouco material visual'):
        roteiro._planos_sem_foto(v, '')


def test_historia_continua_com_a_regra_de_sempre():
    v = _roteiro()
    v.update(tipo_conteudo='historico', plano={'modos': ['historico_investigativo']})
    for c in v['cenas'][:4]:
        c['foto'] = 'a0'
    with pytest.raises(ValueError, match='só 4 de 13 frases'):
        roteiro._planos_sem_foto(v, '')


# ───────── 6. opcional não sai com o teto estourado ─────────
def _gasto(usd_lista):
    ov.abrir('polvo')
    custo.tentativa('polvo')
    for etapa, usd in usd_lista:
        custo.registrar('claude', 'sonnet', usd, None, 1, etapa_=etapa)


def test_sem_bloqueio_por_orcamento_e_a_regra_de_opcional_fica_desligada(monkeypatch):
    _gasto([('roteiro', 0.30), ('crítica', 0.25)])                                 # 0,55: acima do teto de referência
    pedidos = []
    monkeypatch.setattr(gemini, 'json_', lambda *a, **k: pedidos.append(1) or {'opcoes': []})
    roteiro.escolher_gancho(_roteiro(), FATOS)
    assert pedidos == [1] and not ov.opcional_excedida('ganchos')                  # política de 12/11: só monitora


def test_ganchos_pulados_se_a_regra_for_religada(monkeypatch):
    monkeypatch.setattr(ov, 'PULAR_OPCIONAL_ACIMA_DO_TETO', True)
    _gasto([('tema', 0.0015), ('garimpo', 0.0657), ('roteiro', 0.2387), ('crítica', 0.2158)])        # 0,52
    pedidos = []
    monkeypatch.setattr(gemini, 'json_', lambda *a, **k: pedidos.append(1) or {})
    v = roteiro.escolher_gancho(_roteiro(), FATOS)
    assert pedidos == [] and ov.opcional_excedida('ganchos') and not ov.opcional_excedida('roteiro')


def test_ganchos_saem_normalmente_abaixo_do_teto(monkeypatch):
    _gasto([('garimpo', 0.0657), ('roteiro', 0.1217)])
    pedidos = []
    monkeypatch.setattr(gemini, 'json_', lambda *a, **k: pedidos.append(1) or {'opcoes': []})
    roteiro.escolher_gancho(_roteiro(), FATOS)
    assert pedidos == [1]


def test_mecanismo_com_uma_foto_so_nao_passa_com_esquemas_e_ilustracoes():
    v = _roteiro()
    v['cenas'][0]['foto'] = 'a0'
    with pytest.raises(ValueError, match=r'mecanismo\): 1 foto\(s\) real\(is\) do assunto \(mínimo 2\)'):
        roteiro._planos_sem_foto(v, '')
