"""Fase 3, correção 2 (12/11/2026): imagem por ACONTECIMENTO. Sem vídeo, sem IA de verdade (a escolha do Gemini é
simulada). O espectador precisa ver o fato narrado; foto só do tema, empréstimo entre acontecimentos e A-B-A saem."""
import copy
import json
from pathlib import Path

import pytest

import main
from src import acervo, acontecimentos as ac, fiscal, gemini, roteiro

AC = lambda quem='', onde='', quando='', recurso='': {'quem': quem, 'onde': onde, 'quando': quando, 'recurso': recurso}


# ───────── roteiro: acontecimento e evento ─────────
def test_normalizar_acontecimento_e_evento():
    v = {'cenas': [{'tipo': 'gancho', 'fala': 'a', 'grupo': 0, 'evento': 'e1',
                    'acontecimento': {'quem': 'Victor Lustig', 'recurso': 'Linha do tempo'}},
                   {'tipo': 'historia', 'fala': 'b', 'grupo': 1, 'acontecimento': {'recurso': 'pintura a óleo'}},
                   {'tipo': 'historia', 'fala': 'b2', 'grupo': 1, 'sub': 1},
                   {'tipo': 'historia', 'fala': 'c', 'grupo': 2, 'acontecimento': 'texto solto'},
                   {'tipo': 'fechamento', 'fala': 'segue'}]}
    ac.normalizar(v)
    c = v['cenas']
    assert c[0]['acontecimento'] == AC('Victor Lustig', recurso='linha_tempo') and c[0]['evento'] == 'e1'
    assert c[1]['acontecimento']['recurso'] == '' and c[1]['evento'] == 'i1'      # recurso inválido fica em branco
    assert c[2]['evento'] == 'i1' and c[2]['acontecimento'] == c[1]['acontecimento']   # pedaço herda da ideia
    assert c[3]['acontecimento'] == AC() and 'acontecimento' not in c[4]


def test_critica_que_esquece_o_acontecimento_herda_da_versao_anterior(monkeypatch):
    cenas = [{'tipo': 'gancho', 'fala': 'Lustig vendeu a torre', 'evento': 'e1', 'acontecimento': AC('Victor Lustig')}] + \
            [{'tipo': 'historia', 'fala': f'Frase {k} sobre Paris em 1925', 'evento': f'e{k}', 'acontecimento': AC(onde='Paris')}
             for k in range(2, 14)] + [{'tipo': 'fechamento', 'fala': 'Segue'}]
    v = {'titulo': 'T', 'cenas': cenas}
    sem = {'roteiro': {'titulo': 'T', 'cenas': [{k: x for k, x in c.items() if k not in ('evento', 'acontecimento')}
                                               for c in cenas]}, 'aprovado': False, 'notas': {}}
    monkeypatch.setattr(gemini, 'json_', lambda *a, **k: copy.deepcopy(sem))
    novo = roteiro.revisar(v, 'FATOS')
    assert [c.get('evento') for c in novo['cenas']] == [c.get('evento') for c in cenas]


# ───────── escolha da imagem (casar), com o Gemini simulado ─────────
ACERVO = [{'id': 'a0', 'mostra': 'Torre Eiffel em 1925', 'mini': b'', 'lugar': 'Torre Eiffel, Paris'},
          {'id': 'a1', 'mostra': 'retrato de Victor Lustig', 'mini': b'', 'pessoas': ['Victor Lustig']},
          {'id': 'a2', 'mostra': 'jornal de 1925 sobre o golpe', 'mini': b'', 'tipo_img': 'jornal'},
          {'id': 'a3', 'mostra': 'rua de Paris', 'mini': b'', 'generica': True},
          {'id': 'a4', 'mostra': 'Hôtel de Crillon, Paris', 'mini': b'', 'lugar': 'Hôtel de Crillon'}]


def _ideias():
    return {'cenas': [
        {'tipo': 'gancho', 'fala': 'Ele vendeu a *Torre Eiffel*', 'grupo': 0, 'evento': 'e0', 'acontecimento': AC(onde='Torre Eiffel', recurso='lugar')},
        {'tipo': 'historia', 'fala': 'Lustig *forjou* documentos', 'grupo': 1, 'evento': 'e1', 'acontecimento': AC('Victor Lustig', 'Paris', '1925', 'documento')},
        {'tipo': 'historia', 'fala': 'Reuniu sucateiros no *Crillon*', 'grupo': 2, 'evento': 'e2', 'acontecimento': AC('Victor Lustig', 'Hôtel de Crillon', '1925', 'lugar')},
        {'tipo': 'historia', 'fala': 'Poisson *pagou* a propina', 'grupo': 3, 'evento': 'e3', 'acontecimento': AC('André Poisson', '', '1925', 'retrato')},
        {'tipo': 'historia', 'fala': 'Paris vivia o *pós-guerra*', 'grupo': 4, 'evento': 'e4', 'acontecimento': AC(recurso='ambiente')},
        {'tipo': 'historia', 'fala': 'Os jornais *contaram* tudo', 'grupo': 5, 'evento': 'e5', 'acontecimento': AC('Victor Lustig', quando='1925', recurso='jornal')},
        {'tipo': 'fechamento', 'fala': 'Segue'}]}


def _casar(monkeypatch, escolhas):
    vistos = []
    monkeypatch.setattr(gemini, 'json_visao', lambda prompt, minis, leve=False: vistos.append(prompt) or {'escolhas': escolhas})
    v = acervo.casar(_ideias(), copy.deepcopy(ACERVO))
    return v, vistos


def test_casar_manda_o_acontecimento_e_exige_ligacao_com_o_fato(monkeypatch):
    v, vistos = _casar(monkeypatch, [
        {'ideia': 0, 'foto': 'a0', 'exata': True, 'relacao': 'lugar'},
        {'ideia': 1, 'foto': 'a3', 'exata': False, 'relacao': None},           # só do tema: sai
        {'ideia': 2, 'foto': 'a4', 'exata': True, 'relacao': 'lugar'},
        {'ideia': 3, 'foto': 'a1', 'exata': False, 'relacao': 'tema'},         # Lustig numa frase sobre Poisson: sai
        {'ideia': 4, 'foto': 'a3', 'exata': False, 'relacao': 'ambiente'},     # genérica, mas a frase é de ambiente
        {'ideia': 5, 'foto': 'a2', 'exata': True, 'relacao': 'documento'}])
    assert len(vistos) == 1 and 'acontecimento: quem=Victor Lustig, onde=Paris, quando=1925, recurso=documento' in vistos[0]
    c = v['cenas']
    assert [x.get('foto') for x in c[:6]] == ['a0', None, 'a4', None, None, 'a2']
    assert [x.get('relacao') for x in c[:6]] == ['lugar', None, 'lugar', None, None, 'documento']


def test_casar_ambiente_so_em_frase_de_ambiente(monkeypatch):
    v, _ = _casar(monkeypatch, [{'ideia': 4, 'foto': 'a0', 'exata': True, 'relacao': 'ambiente'},
                                {'ideia': 1, 'foto': 'a1', 'exata': True, 'relacao': 'ambiente'}])
    assert v['cenas'][4]['foto'] == 'a0' and v['cenas'][4]['relacao'] == 'ambiente'
    assert v['cenas'][1].get('foto') is None                             # frase de fato não aceita "ambiente"


def test_casar_resposta_no_formato_antigo_segue_a_regra_de_antes(monkeypatch):
    v, _ = _casar(monkeypatch, [{'ideia': 1, 'foto': 'a1', 'exata': True}, {'ideia': 2, 'foto': 'a4', 'exata': False},
                                {'ideia': 3, 'foto': 'a3', 'exata': False}])
    c = v['cenas']
    assert c[1]['foto'] == 'a1' and c[1]['relacao'] == 'fato'
    assert c[2]['foto'] == 'a4' and 'relacao' not in c[2]                 # não exata, específica: aceita (como antes)
    assert c[3].get('foto') is None                                       # genérica e não exata: fora (como antes)


def test_preencher_so_pessoa_ou_lugar_do_fato_ou_ambiente():
    v = _ideias()
    v['cenas'][0]['foto'] = 'a0'
    livres = copy.deepcopy(ACERVO)
    acervo.preencher(v, livres)
    c = v['cenas']
    assert c[1]['foto'] == 'a1' and c[1]['relacao'] == 'pessoa'           # retrato do Lustig: pessoa do fato
    assert c[2]['foto'] == 'a4' and c[2]['relacao'] == 'lugar'            # o Crillon: lugar do fato
    assert c[3].get('foto') is None                                       # nada do Poisson: fica sem
    assert c[4]['relacao'] == 'ambiente'                                  # ambiente pega a reserva que sobrar
    assert c[5].get('foto') in (None, 'a2')


def test_segunda_busca_dirigida_pelo_acontecimento(monkeypatch):
    from src import orcamento
    monkeypatch.setattr(orcamento, 'sobra', lambda: 100)
    qs = []
    for f in ('_categoria_commons', '_busca_commons'):
        monkeypatch.setattr(acervo, f, lambda q, n=0: qs.append(q) or [])
    for f in ('f_wikidata', 'f_smithsonian', 'f_openverse', 'f_videos'):
        monkeypatch.setattr(acervo, f, lambda qq: [])
    monkeypatch.setattr(acervo, '_commons_infos', lambda t, f: [])
    v = {'cenas': [{'tipo': 'historia', 'fala': 'a', 'busca': 'Victor Lustig arrest', 'acontecimento': AC(recurso='jornal')},
                   {'tipo': 'historia', 'fala': 'b', 'busca': '', 'acontecimento': AC('André Poisson', 'Paris', '1925', 'documento')},
                   {'tipo': 'historia', 'fala': 'c', 'busca': 'Eiffel Tower 1925', 'acontecimento': AC(recurso='lugar')}]}
    acervo.complementar(v, [], Path('/tmp'))
    assert {'Victor Lustig arrest newspaper', 'André Poisson Paris 1925 document', 'Eiffel Tower 1925'} <= set(qs)


# ───────── ideias sem foto: nada inventado ─────────
def _sem_foto(**extra):
    v = _ideias()
    ac.normalizar(v)
    v['cenas'][0]['foto'] = 'a0'
    v['cenas'][2]['foto'] = 'a4'
    v['cenas'][2]['evento'] = 'e1'                                        # a reunião e a falsificação: o MESMO golpe
    v['cenas'][4]['foto'], v['cenas'][4]['relacao'] = 'a3', 'ambiente'      # frase de ambiente com a rua de Paris
    for c in v['cenas']:
        c.setdefault('cenario', 'Paris 1925 street')
    v.update(extra)
    return v


def test_ideia_sem_foto_vira_mesmo_evento_ou_cartao_e_ia_so_se_pedida():
    v = _sem_foto()
    v['cenas'][5]['visual'] = 'ia'                                        # o roteiro pediu ilustração
    roteiro._planos_sem_foto(v, 'Paris 1925')
    m = [c.get('midia') for c in v['cenas'][:6]]
    assert m == [None, 'evento', None, 'cartao', None, 'ia']
    assert not any(c.get('prompt_imagem') for c in v['cenas'][:5])        # nenhuma IA para tapar fato histórico


def test_porteiro_de_tema_continua_com_os_mesmos_limites():
    v = {'cenas': [{'tipo': 'gancho', 'fala': 'g', 'foto': 'a0', 'grupo': 0}]
         + [{'tipo': 'historia', 'fala': f'f{k}', 'foto': 'a1' if k < 6 else None, 'grupo': k, 'evento': f'e{k}',
             'acontecimento': AC()} for k in range(1, 14)] + [{'tipo': 'fechamento', 'fala': 's'}]}
    with pytest.raises(ValueError, match='frases sem imagem própria'):          # 8 cartões > 2 + 4
        roteiro._planos_sem_foto(v, '')
    v['cenas'][7]['foto'] = v['cenas'][8]['foto'] = 'a1'
    roteiro._planos_sem_foto(v, '')                                             # 6 cartões: passa, como antes passava


# ───────── montagem: sem empréstimo entre acontecimentos, sem A-B-A ─────────
def _jpg(p: Path, cor):
    from PIL import Image
    Image.new('RGB', (900, 1200), cor).save(p)
    return p


def _montar(tmp, cenas_v, duracoes):
    reais = {}
    for k, c in enumerate(cenas_v):
        if c.get('foto'):
            reais[c['foto']] = {'tipo': 'foto', 'arq': _jpg(tmp / f"{c['foto']}.jpg", (40 * k % 255, 90, 120)), 'ano': 1925}
            c['imagem'] = c['foto']
    t, tempos = 0.0, []
    for d in duracoes:
        tempos.append((t, t + d)); t += d
    return main._montar_cenas({'cenas': cenas_v, 'titulo': 'Torre'}, reais, {}, tempos, tmp)


def test_montagem_reaproveita_so_o_mesmo_evento_e_deixa_cartao_no_resto(tmp_path):
    v = _sem_foto()
    roteiro._planos_sem_foto(v, '')
    cenas = _montar(tmp_path, v['cenas'], [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 2.0])
    ids = ac.ideias(cenas)
    img = lambda c: Path(str(c.get('img'))).name if c.get('img') else None
    assert img(ids[1]) == 'a4.jpg' and ids[1].get('mesmo_evento')        # forjou ← reunião (mesmo golpe)
    assert img(ids[3]) is None and ids[3].get('rotulo') is None           # Poisson: cartão com *pagou*
    assert img(ids[4]) == 'a3.jpg' and img(ids[5]) is None                # ilustração pedida não veio aqui: cartão
    assert not any(c.get('repetida') for c in cenas if c['tipo'] != 'gancho')
    cob = ac.cobertura(cenas)
    assert cob['contagem']['emprestada'] == 0 and cob['aba'] == 0
    assert cob['contagem']['mesmo_acontecimento'] == 1 and cob['contagem']['cartao'] == 2
    assert cob['contagem']['ambiente'] == 1 and cob['contagem']['ligada_ao_fato'] == 0


def test_plano_longo_reenquadra_a_mesma_imagem_sem_trazer_outra(tmp_path):
    v = _sem_foto()
    roteiro._planos_sem_foto(v, '')
    cenas = _montar(tmp_path, v['cenas'], [3.0, 3.0, 9.0, 3.0, 3.0, 3.0, 2.0])
    reuniao = [c for c in cenas if c.get('grupo') == 2]
    assert len(reuniao) == 3 and {Path(c['img']).name for c in reuniao} == {'a4.jpg'}
    assert [c.get('sub') or 0 for c in reuniao] == [0, 1, 2]              # detalhe/outro canto da MESMA foto
    assert ac.aba(cenas) == 0


def test_roteiro_antigo_sem_evento_monta_como_antes(tmp_path):
    cenas_v = [{'tipo': 'gancho', 'fala': 'a', 'foto': 'a0'}, {'tipo': 'historia', 'fala': 'b'},
               {'tipo': 'historia', 'fala': 'c', 'foto': 'a1'}, {'tipo': 'fechamento', 'fala': 'd'}]
    cenas = _montar(tmp_path, cenas_v, [3.0, 3.0, 3.0, 2.0])
    assert cenas[1].get('img') and cenas[1].get('repetida')                # foto vizinha, como antes


def test_cartao_sem_asteriscos_usa_nomes_da_propria_fala(tmp_path):
    v = _sem_foto()
    v['cenas'][3]['fala'] = 'André Poisson pagou em 1925'
    roteiro._planos_sem_foto(v, '')
    cenas = _montar(tmp_path, v['cenas'], [3.0] * 6 + [2.0])
    assert ac.ideias(cenas)[3]['rotulo'] == 'Poisson 1925'                 # palavras ditas na narração, nada inventado


# ───────── cobertura: só registro ─────────
def test_cobertura_classes_e_aba():
    cenas = [{'tipo': 'gancho', 'grupo': 0, 'evento': 'e0', 'img': 'A', 'relacao': 'lugar'},
             {'tipo': 'historia', 'grupo': 1, 'evento': 'e1', 'img': 'B', 'relacao': 'fato'},
             {'tipo': 'historia', 'grupo': 2, 'evento': 'e2', 'img': 'A', 'repetida': True},
             {'tipo': 'linha_tempo', 'grupo': 3, 'evento': 'e3'},
             {'tipo': 'historia', 'grupo': 4, 'evento': 'e4'},
             {'tipo': 'historia', 'grupo': 5, 'evento': 'e1', 'img': 'B', 'mesmo_evento': True},
             {'tipo': 'historia', 'grupo': 6, 'evento': 'e6', 'img': 'C', 'ia': True},
             {'tipo': 'fechamento'}]
    cob = ac.cobertura(cenas)
    assert [p['classe'] for p in cob['por_ideia']] == ['ligada_ao_fato', 'mostra_o_fato', 'emprestada', 'grafico',
                                                      'cartao', 'mesmo_acontecimento', 'ilustracao_ia']
    assert cob['aba'] == 1 and '🎬 Cobertura visual (só registro, não muda nota): 7 ideias' in ac.linha_telegram(cob)


def test_montar_video_registra_cobertura_sem_mudar_notas_nem_decisao(monkeypatch, tmp_path):
    SOMBRA = fiscal.sombra
    def rodar(pasta, quebrar):
        cenas = [{'tipo': 'gancho', 'fala': 'a', 'grupo': 0, 'evento': 'e0', 'img': 'a.jpg', 'start': 0, 'end': 3},
                 {'tipo': 'historia', 'fala': 'b', 'grupo': 1, 'evento': 'e1', 'start': 3, 'end': 58},
                 {'tipo': 'fechamento', 'fala': 'c', 'start': 58, 'end': 60}]
        monkeypatch.setattr(main.voz, 'narrar', lambda *a, **k: (pasta / 'a.wav', [], [], 60.0))
        monkeypatch.setattr(main, 'escolher_musica', lambda *a, **k: None)
        monkeypatch.setattr(main, '_montar_cenas', lambda *a, **k: copy.deepcopy(cenas))
        monkeypatch.setattr(main, 'renderizar', lambda dados, audio, saida, trab, musica=None: saida.write_bytes(b''))
        monkeypatch.setattr(main, 'renderizar_capa', lambda *a, **k: None)
        monkeypatch.setattr(main, 'fiscal_final', lambda *a, **k: (6.0, []))
        monkeypatch.setattr(main, 'pacote_diagnostico', lambda *a, **k: None)
        monkeypatch.setattr(main, 'erros_basicos', lambda *a, **k: [])
        monkeypatch.setattr(fiscal, 'sombra', lambda v, c, s, n, t: SOMBRA(v, c, None, n, t, pedir=lambda p: {},
                                                                          prompt_base='{fatos}{frases}{titulo}'))
        if quebrar:
            monkeypatch.setattr(ac, 'cobertura', lambda c: 1 / 0)
        v = {'titulo': 'T', 'fatos': 'F', 'cenas': [{'tipo': 'gancho', 'fala': 'a'}, {'tipo': 'historia', 'fala': 'b'},
                                                    {'tipo': 'fechamento', 'fala': 'c'}]}
        pasta.mkdir()
        main.montar_video(v, pasta, 'v')
        return v
    com = rodar(tmp_path / 'com', False)
    sem = rodar(tmp_path / 'sem', True)
    assert com['_telegram']['resumo'] == sem['_telegram']['resumo'] and com['_bloqueado'] == sem['_bloqueado']
    assert '🎬 Cobertura visual' in com['_telegram']['diagnostico'] and '🎬' not in sem['_telegram']['diagnostico']
    assert json.loads((tmp_path / 'com' / 'v-cobertura.json').read_text())['contagem']['cartao'] == 1
    assert (json.loads((tmp_path / 'com' / 'v-fiscal-sombra.json').read_text())['nota']
            == json.loads((tmp_path / 'sem' / 'v-fiscal-sombra.json').read_text())['nota'])


def test_ntc_nao_usa_acontecimentos():
    raiz = Path(__file__).resolve().parent.parent / 'src'
    for p in raiz.glob('*.py'):
        if p.name.startswith(('fabula', 'ntc')):
            t = p.read_text(encoding='utf-8')
            assert 'import acontecimentos' not in t and 'acontecimentos.' not in t.replace('acontecimentos (src', ''), p.name


# ───────── o cartão na tela ─────────
from tests.test_tela import precisa_navegador   # noqa: E402


@precisa_navegador
def test_cartao_na_tela_sem_texto_em_cima(tmp_path):
    """Ideia sem imagem do fato: o template escreve as palavras da narração; nada encosta em nada."""
    from src.render.render import fiscal_tela, preparar
    from tests.caso_tela import _foto, _legendas
    f = _foto(tmp_path, 'torre', 1200, 1600, (120, 100, 80))
    cenas = [{'tipo': 'historia', 'start': 0.0, 'end': 3.0, 'img': f, 'real': True, 'foto_wh': [1200, 1600],
              'fala': 'Ele vendeu a *Torre Eiffel*'},
             {'tipo': 'historia', 'start': 3.0, 'end': 6.0, 'fala': 'Poisson *pagou* a propina'},
             {'tipo': 'historia', 'start': 6.0, 'end': 9.0, 'fala': 'André Poisson pagou em 1925', 'rotulo': 'Poisson 1925',
              'lugar': 'PARIS · 1925'},
             {'tipo': 'imagem', 'start': 9.0, 'end': 12.0, 'fala': 'Os *jornais* contaram', 'rotulo': 'O GOLPE'}]
    d = preparar({'meta': {'titulo': 'Torre', 'marca': '@coringa.explica'}, 'scenes': cenas, 'duration': 12.0,
                  'captions': _legendas([(c['start'] + 0.1, c['end'] - 0.1, c['fala']) for c in cenas])})
    assert fiscal_tela(d, tmp_path) == []


def test_previa_mostra_cartao_e_mesmo_fato():
    from src import aprovacao
    v = {'cenas': [{'tipo': 'gancho', 'fala': 'a', 'imagem': 'a0'}, {'tipo': 'historia', 'fala': 'b', 'midia': 'cartao'},
                   {'tipo': 'historia', 'fala': 'c', 'midia': 'evento'}, {'tipo': 'historia', 'fala': 'd', 'midia': 'vizinha'},
                   {'tipo': 'fechamento', 'fala': 'e'}]}
    reais = {'a0': {'tipo': 'foto', 'arq': '/tmp/a0.jpg'}}
    assert [aprovacao.midia_de(c, reais, {})[0] for c in v['cenas'][:4]] == ['FOTO', 'CARTÃO', 'MESMO FATO', 'REPETE']
    av = '\n'.join(aprovacao.avisos(v, reais, {}))
    assert 'cartão com as palavras da narração' in av and 'mesmo acontecimento' in av and 'repete a foto vizinha' in av
