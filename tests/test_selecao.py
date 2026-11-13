"""Plano-mestre, etapa E (12/11/2026): acervo e seleção com evidência. Candidatos corretos, contextuais, enganosos e
duplicados; o Gemini é simulado e tratado como hipótese. Nenhum documento fabricado; motivo de cada escolha/recusa."""
import copy

from src import acervo, gemini, roteiro, selecao, storyboard as sbm

AC = lambda quem='', onde='', quando='', recurso='': {'quem': quem, 'onde': onde, 'quando': quando, 'recurso': recurso}
ACERVO = [
    {'id': 'a0', 'titulo': 'Eiffel Tower 1925', 'mostra': 'Torre Eiffel', 'ano': 1925, 'lugar': 'Torre Eiffel, Paris',
     'fonte': 'commons', 'credito': 'Wikimedia', 'w': 1600, 'h': 1200, 'nota': 8, 'mini': b''},
    {'id': 'a1', 'titulo': 'Victor Lustig mugshot', 'mostra': 'retrato de homem', 'ano': 1935, 'pessoas': ['Victor Lustig'],
     'fonte': 'loc', 'credito': 'LOC', 'w': 900, 'h': 1200, 'nota': 7, 'mini': b''},
    {'id': 'a2', 'titulo': 'Le Petit Journal 1925', 'mostra': 'página de jornal', 'ano': 1925, 'tipo_img': 'jornal',
     'fonte': 'commons', 'credito': 'BnF', 'w': 1200, 'h': 1700, 'nota': 7, 'mini': b''},
    {'id': 'a3', 'titulo': 'Paris street', 'mostra': 'rua de Paris', 'ano': 2012, 'generica': True,
     'fonte': 'openverse', 'credito': 'Flickr', 'w': 2000, 'h': 1300, 'nota': 6, 'mini': b''},
    {'id': 'a4', 'titulo': 'Hôtel de Crillon facade', 'mostra': 'fachada do hotel', 'ano': 2015, 'lugar': 'Hôtel de Crillon',
     'fonte': 'commons', 'credito': 'Wikimedia', 'w': 1800, 'h': 1200, 'nota': 6, 'mini': b''},
    {'id': 'a5', 'titulo': 'Old banknotes', 'mostra': 'cédulas antigas', 'ano': None, 'fonte': '', 'credito': '',
     'w': 400, 'h': 300, 'nota': 4, 'mini': b''},
    {'id': 'a6', 'titulo': 'Steel scrap yard 1920s', 'mostra': 'ferro velho', 'ano': 1924, 'fonte': 'loc', 'credito': 'LOC',
     'w': 1400, 'h': 1000, 'nota': 7, 'mini': b''},
]


def _cenas():
    return {'cenas': [
        {'tipo': 'gancho', 'fala': 'Em 1925, ele vendeu a *Torre Eiffel*.', 'grupo': 0, 'evento': 'e0', 'bloco': {'funcao': 'abertura'},
         'acontecimento': AC(onde='Torre Eiffel', quando='1925', recurso='lugar')},
        {'tipo': 'historia', 'fala': 'Lustig *forjou* papéis do ministério.', 'grupo': 1, 'evento': 'e1', 'bloco': {'funcao': 'evidencia'},
         'acontecimento': AC('Victor Lustig', 'Paris', '1925', 'documento'), 'mostrar': 'papéis falsos do ministério'},
        {'tipo': 'historia', 'fala': 'Reuniu sucateiros no *Crillon*.', 'grupo': 2, 'evento': 'e2', 'bloco': {'funcao': 'contexto'},
         'acontecimento': AC('Victor Lustig', 'Hôtel de Crillon', '1925', 'lugar')},
        {'tipo': 'historia', 'fala': 'Os jornais *contaram* o golpe.', 'grupo': 3, 'evento': 'e3', 'bloco': {'funcao': 'consequencia'},
         'acontecimento': AC('Victor Lustig', quando='1925', recurso='jornal')},
        {'tipo': 'historia', 'fala': 'A torre virou *sucata* no papel.', 'grupo': 4, 'evento': 'e4', 'bloco': {'funcao': 'mecanismo'},
         'acontecimento': AC(quando='1925', recurso='objeto'), 'mostrar': 'ferro velho', 'busca': 'scrap yard'},
        {'tipo': 'fechamento', 'fala': 'Segue.'}], 'plano': {'modos': ['historico_investigativo']}}


def _casar(monkeypatch, escolhas, acv=None):
    chamadas = []
    monkeypatch.setattr(gemini, 'json_visao', lambda p, m, leve=False: chamadas.append(p) or {'escolhas': escolhas})
    v = sbm.construir(_cenas())
    v = acervo.casar(v, copy.deepcopy(acv or ACERVO))
    return v, chamadas


# ───────── conferência da hipótese do Gemini ─────────
def test_fato_com_ano_incompativel_vira_tema_com_motivo():
    c = _cenas()['cenas'][0]
    rel, mot, ok = selecao.verificar(ACERVO[3], c, 'fato')                         # rua de 2012 "mostrando" 1925
    assert rel == 'tema' and '2012' in mot[0] and '1925' in mot[0]


def test_documento_so_se_for_papel_de_verdade_e_da_epoca():
    c = _cenas()['cenas'][3]
    assert selecao.verificar(ACERVO[2], c, 'documento')[0] == 'documento'           # jornal de 1925
    rel, mot, _ = selecao.verificar(ACERVO[6], c, 'documento')                      # ferro-velho não é papel
    assert rel == 'tema' and 'papel' in mot[0]


def test_pessoa_e_lugar_precisam_do_nome_no_catalogo():
    c = _cenas()['cenas'][1]
    assert selecao.verificar(ACERVO[1], c, 'pessoa')[0] == 'pessoa'
    rel, mot, _ = selecao.verificar(ACERVO[6], c, 'pessoa')
    assert rel == 'tema' and 'Victor Lustig' in mot[0]


def test_fato_sem_ano_na_imagem_fica_nao_verificado():
    rel, mot, ok = selecao.verificar(ACERVO[5], _cenas()['cenas'][4], 'fato')
    assert rel == 'fato' and ok is False and 'não verificada' in mot[0]


# ───────── casamento: uma chamada, recusas registradas ─────────
def test_casar_registra_escolhas_rebaixamentos_e_recusas(monkeypatch):
    v, chamadas = _casar(monkeypatch, [
        {'ideia': 0, 'foto': 'a0', 'exata': True, 'relacao': 'lugar'},
        {'ideia': 1, 'foto': 'a3', 'exata': False, 'relacao': 'tema'},             # genérica: recusada
        {'ideia': 2, 'foto': 'a4', 'exata': True, 'relacao': 'lugar'},
        {'ideia': 3, 'foto': 'a6', 'exata': True, 'relacao': 'documento'},         # enganosa: não é papel
        {'ideia': 4, 'foto': 'a6', 'exata': True, 'relacao': 'objeto'}])           # duplicada: já usada
    assert len(chamadas) == 1
    c = v['cenas']
    assert c[0]['_escolha']['relacao'] == 'lugar'
    assert c[1].get('foto') is None and c[1]['_escolha']['rejeitadas'][0]['motivo'].startswith('genérica')
    assert c[3]['foto'] == 'a6' and c[3]['relacao'] == 'tema' and 'papel' in c[3]['_escolha']['motivos'][0]
    assert c[4].get('foto') is None and c[4]['_escolha']['rejeitadas'][0]['motivo'] == 'já usada em outra ideia'


# ───────── reservas: ranqueamento e recusa ─────────
def test_preencher_escolhe_pela_frase_e_recusa_o_que_nao_serve():
    v = sbm.construir(_cenas())
    v['cenas'][0]['foto'] = 'a0'
    acv = copy.deepcopy(ACERVO)
    acervo.preencher(v, acv)
    c = v['cenas']
    assert c[1].get('foto') is None and 'acontecimento' in c[1]['_escolha']['motivos'][0]   # Etapa 2: fato central
    assert c[2]['foto'] == 'a1' and 'mesma pessoa do fato' in c[2]['_escolha']['motivos']   # contexto: Lustig > qualquer
    assert c[4].get('foto') is None and 'processo' in c[4]['_escolha']['motivos'][0]   # Etapa 2: processo não leva reserva
    assert all(x.get('foto') != 'a3' for x in c)                                    # genérica fora de frase de ambiente
    ruim = sbm.construir({'cenas': [dict(_cenas()['cenas'][4], foto=None, bloco={'funcao': 'contexto'})]})
    acervo.preencher(ruim, [copy.deepcopy(ACERVO[5])])                              # sem proveniência, 400 px
    assert ruim['cenas'][0].get('foto') is None and 'nenhuma reserva serve' in ruim['cenas'][0]['_escolha']['motivos'][0]


# ───────── fallback condicional, sem documento fabricado ─────────
def _sem_foto(modo, recurso, funcao):
    v = {'estilo_visual': '', 'plano': {'modos': [modo]}, 'cenas': [
        {'tipo': 'gancho', 'fala': 'g', 'grupo': 0, 'foto': 'a0', 'cenario': 'x', 'bloco': {'funcao': 'abertura'}}]
        + [{'tipo': 'historia', 'fala': f'frase {k}', 'grupo': k, 'foto': 'a0', 'cenario': 'x'} for k in range(1, 4)]
        + [{'tipo': 'historia', 'fala': 'a frase sem foto', 'grupo': 4, 'cenario': 'Lustig forging ministry papers',
            'acontecimento': AC('Victor Lustig', 'Paris', '1925', recurso), 'bloco': {'funcao': funcao}},
           {'tipo': 'fechamento', 'fala': 's'}]}
    return roteiro._planos_sem_foto(sbm.construir(v), 'Paris 1925')


def test_documento_que_faltou_nao_vira_documento_falso():
    c = _sem_foto('historico_investigativo', 'documento', 'evidencia')['cenas'][4]
    assert c['midia'] == 'ia' and 'Do not depict any document' in c['prompt_imagem']
    assert 'nenhum documento é fabricado' in c['_fallback']


def test_mecanismo_sem_foto_fica_esquema_pendente_sem_ia():
    v = _sem_foto('mecanismo', '', 'mecanismo')
    c = v['cenas'][4]
    assert c['midia'] == 'pendente' and not c.get('prompt_imagem') and 'esquema pendente' in c['_fallback']


def test_storyboard_recebe_escolha_e_rebaixa_o_nao_verificado(monkeypatch):
    acv = copy.deepcopy(ACERVO)
    v, _ = _casar(monkeypatch, [{'ideia': 4, 'foto': 'a5', 'exata': True, 'relacao': 'fato'},
                                {'ideia': 3, 'foto': 'a2', 'exata': True, 'relacao': 'documento'}], acv)
    sbm.atualizar_midia(v)
    s4, s3 = v['cenas'][4]['sb'], v['cenas'][3]['sb']
    assert s4['evidencia'] == 'contextual' and any('não verificada' in x for x in s4['limitacoes'])
    assert s3['evidencia'] == 'direto' and s3['escolha']['foto'] == 'a2'
