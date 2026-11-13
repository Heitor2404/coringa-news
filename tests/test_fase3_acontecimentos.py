"""Fase 3 (12/11/2026): imagem por ACONTECIMENTO — o que ficou depois da REVERSÃO seletiva das correções 2 e 3
(Torre Eiffel 4 ruim). Ficam: metadados (evento/acontecimento), diagnóstico de cobertura e busca dirigida. Saem: filtros
rígidos, cartões automáticos, mesma foto cobrindo várias ideias, câmera/transição fixas. Continua proibido: A-B-A e imagem
evidentemente desconectada. Sem vídeo, sem IA de verdade (a escolha do Gemini é simulada)."""
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


def test_casar_resposta_no_formato_antigo_segue_a_regra_de_antes(monkeypatch):
    v, _ = _casar(monkeypatch, [{'ideia': 1, 'foto': 'a1', 'exata': True}, {'ideia': 2, 'foto': 'a4', 'exata': False},
                                {'ideia': 3, 'foto': 'a3', 'exata': False}])
    c = v['cenas']
    assert c[1]['foto'] == 'a1' and c[1]['relacao'] == 'fato'
    assert c[2]['foto'] == 'a4' and 'relacao' not in c[2]                 # não exata, específica: aceita (como antes)
    assert c[3].get('foto') is None                                       # genérica e não exata: fora (como antes)


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


def test_roteiro_antigo_sem_evento_monta_como_antes(tmp_path):
    cenas_v = [{'tipo': 'gancho', 'fala': 'a', 'foto': 'a0'}, {'tipo': 'historia', 'fala': 'b'},
               {'tipo': 'historia', 'fala': 'c', 'foto': 'a1'}, {'tipo': 'fechamento', 'fala': 'd'}]
    cenas = _montar(tmp_path, cenas_v, [3.0, 3.0, 3.0, 2.0])
    assert cenas[1].get('img') and cenas[1].get('repetida')                # foto vizinha, como antes


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


# ───────── reversão seletiva (12/11, depois da Torre Eiffel 4) ─────────
def test_casar_volta_a_aceitar_foto_do_tema_e_so_tira_a_desconectada(monkeypatch):
    v, vistos = _casar(monkeypatch, [
        {'ideia': 0, 'foto': 'a0', 'exata': True, 'relacao': 'lugar'},
        {'ideia': 1, 'foto': 'a3', 'exata': False, 'relacao': None},           # genérica e sem ligação: sai
        {'ideia': 2, 'foto': 'a4', 'exata': True, 'relacao': 'lugar'},
        {'ideia': 3, 'foto': 'a1', 'exata': False, 'relacao': 'tema'},         # do tema, específica: VOLTA a valer
        {'ideia': 4, 'foto': 'a3', 'exata': False, 'relacao': 'ambiente'},     # genérica não exata: fora (regra de 11/11)
        {'ideia': 5, 'foto': 'a2', 'exata': True, 'relacao': 'documento'}])
    assert 'acontecimento: quem=Victor Lustig' in vistos[0]                   # o acontecimento continua indo no pedido
    c = v['cenas']
    assert [x.get('foto') for x in c[:6]] == ['a0', None, 'a4', 'a1', None, 'a2']
    assert c[3]['relacao'] == 'tema'


def test_casar_ambiente_em_frase_de_fato_volta_a_valer(monkeypatch):
    v, _ = _casar(monkeypatch, [{'ideia': 1, 'foto': 'a1', 'exata': True, 'relacao': 'ambiente'}])
    assert v['cenas'][1]['foto'] == 'a1'                                       # filtro rígido de ambiente saiu


def test_preencher_prefere_o_fato_aceita_o_tema_e_recusa_generica():
    v = _ideias()
    v['cenas'][0]['foto'] = 'a0'
    livres = copy.deepcopy(ACERVO)
    acervo.preencher(v, livres)
    c = v['cenas']
    assert c[1]['foto'] == 'a1' and c[1]['relacao'] == 'pessoa'               # ligada ao fato vem primeiro
    assert c[2]['foto'] == 'a4' and c[2]['relacao'] == 'lugar'
    assert c[3]['foto'] == 'a2' and c[3]['relacao'] == 'tema'                 # Poisson: reserva do tema (como antes)
    assert c[4]['foto'] == 'a3' and c[4]['relacao'] == 'ambiente'             # a genérica só na frase de ambiente
    assert c[5].get('foto') is None                                           # acabou: a genérica não tapa fato


def test_sem_foto_volta_a_cadeia_de_antes_ia_e_vizinha_sem_cartao():
    v = _sem_foto()
    roteiro._planos_sem_foto(v, 'Paris 1925')
    m = [c.get('midia') for c in v['cenas'][:6]]
    assert 'cartao' not in m and 'evento' not in m
    assert m[1] == 'ia' and m[3] == 'ia' and m[5] == 'ia'                     # cenário pedido → ilustração (como antes)
    assert 'Set in Paris 1925' in v['cenas'][1]['prompt_imagem']              # época travada continua
    assert not any('newspaper' in str(c.get('prompt_imagem') or '').lower() for c in v['cenas'])   # nada de documento inventado


def test_porteiro_de_tema_de_antes():
    v = {'cenas': [{'tipo': 'gancho', 'fala': 'g', 'foto': 'a0', 'grupo': 0}]
         + [{'tipo': 'historia', 'fala': f'f{k}', 'foto': 'a1' if k < 8 else None, 'grupo': k} for k in range(1, 14)]
         + [{'tipo': 'fechamento', 'fala': 's'}]}
    with pytest.raises(ValueError, match='frases sem imagem própria'):          # 6 sem cenário → 6 vizinhas > 2
        roteiro._planos_sem_foto(v, '')


def _img(c):
    return Path(str(c.get('img'))).name if c.get('img') else None


def _seq_sem_aba(cenas):
    vistas, ant = set(), None
    for c in cenas:
        k = _img(c)
        if not k or c['tipo'] == 'fechamento':
            continue
        assert not (k != ant and k in vistas), f'{k} voltou depois de sair da tela'
        vistas.add(k); ant = k


def test_montagem_sem_cartao_automatico_e_sem_a_b_a(tmp_path):
    v = _sem_foto()
    for c in v['cenas']:
        c.pop('cenario', None)                                                 # sem IA: só fotos reais e vizinhas
    v['cenas'][3]['foto'] = 'a1'
    roteiro._planos_sem_foto(v, '')
    cenas = _montar(tmp_path, v['cenas'], [3.0] * 6 + [2.0])
    ids = ac.ideias(cenas)
    assert all(c.get('img') for c in ids)                                     # nenhuma ideia vira cartão de texto
    assert not any(c.get('rotulo') for c in cenas) and not any(c.get('mesmo_evento') for c in cenas)
    assert len({_img(c) for c in ids}) >= 4                                   # variedade: cada foto real na sua ideia
    _seq_sem_aba(cenas)
    assert ac.aba(cenas) == 0


def test_plano_longo_sem_resolucao_fica_inteiro_e_nao_antecipa_a_proxima(tmp_path):
    """Plano-mestre G: foto 900×1200 em tela cheia não aguenta um detalhe de verdade → o plano fica inteiro (antes:
    A, A reenquadrada e a foto da PRÓXIMA ideia antes da hora)."""
    v = _sem_foto()
    for c in v['cenas']:
        c.pop('cenario', None)
    v['cenas'][1]['foto'], v['cenas'][3]['foto'], v['cenas'][5]['foto'] = 'a1', 'a2', 'a3'
    cenas = _montar(tmp_path, v['cenas'], [3.0, 3.0, 9.0, 3.0, 3.0, 3.0, 2.0])
    reuniao = [c for c in cenas if c.get('grupo') == 2]
    assert [_img(c) for c in reuniao] == ['a4.jpg'] and reuniao[0]['end'] - reuniao[0]['start'] == 9.0
    _seq_sem_aba(cenas)


def test_sem_camera_nem_transicao_forcadas(tmp_path):
    v = _sem_foto()
    for c in v['cenas']:
        c.pop('cenario', None)
    cenas = _montar(tmp_path, v['cenas'], [3.0] * 6 + [2.0])
    assert not any(c.get('camera') for c in cenas)                            # volta o rodízio do template
    assert not any(c.get('transicao') for c in cenas)                         # e as transições de sempre
    assert not hasattr(main, '_juntar_cartoes') and not hasattr(main, '_dar_movimento')


def test_cobertura_conta_foto_do_tema():
    cob = ac.cobertura([{'tipo': 'gancho', 'grupo': 0, 'evento': 'e0', 'img': 'A', 'relacao': 'tema'},
                        {'tipo': 'fechamento'}])
    assert cob['contagem']['tema'] == 1 and 'só do tema' in ac.linha_telegram(cob)
