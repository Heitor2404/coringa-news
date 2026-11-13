"""Plano-mestre, etapa D (12/11/2026): storyboard semântico — uma estrutura por cena, do roteiro à montagem.
Fixtures: (i) golpe histórico com documento, pagamento e fuga; (ii) processo biológico invisível a olho nu;
(iii) curiosidade científica com comparação. Sem IA, sem vídeo."""
import copy
import json
from pathlib import Path

import main
from src import editorial as ed, storyboard as sb

RAIZ = Path(__file__).resolve().parent.parent
CASOS = json.loads((RAIZ / 'tests/editorial_casos.json').read_text(encoding='utf-8'))
AC = lambda quem='', onde='', quando='', recurso='': {'quem': quem, 'onde': onde, 'quando': quando, 'recurso': recurso}


def _v(nome):
    v = copy.deepcopy(CASOS[nome]['roteiro'])
    v['categoria'] = CASOS[nome]['categoria']
    for k, c in enumerate(v['cenas']):
        c['grupo'] = k
        c['evento'] = f'e{k}'
    return ed.preparar(v)


def _golpe():
    v = _v('historia')
    c = v['cenas']
    c[0].update(acontecimento=AC(onde='Torre Eiffel', quando='1925', recurso='lugar'), foto='a0', relacao='lugar')
    c[1].update(acontecimento=AC('Victor Lustig', 'Paris', '1925', 'documento'), mostrar='documentos falsos do ministério',
                foto='a9', relacao='tema')                                        # foto de Paris numa frase de falsificação
    c[2].update(acontecimento=AC('Victor Lustig', 'Hôtel de Crillon', '1925', 'lugar'), foto='a4', relacao='lugar')
    c[3].update(acontecimento=AC('Victor Lustig', quando='1925', recurso='jornal'), foto='a2', relacao='documento')
    c[4].update(acontecimento=AC('André Poisson', '', '1925', 'retrato'), mostrar='Poisson entregando o dinheiro',
                foto='a5', relacao='pessoa')                                      # pagamento: o retrato não mostra a ação
    c[5].update(acontecimento=AC('André Poisson', quando='1925'), midia='ia', ia=True)
    c[6].update(acontecimento=AC('Victor Lustig', 'Viena', '1925', 'lugar'), foto='a6', relacao='lugar')   # fuga
    return v


def test_cada_cena_tem_proposito_intencao_e_alternativa_plausivel():
    for nome in CASOS:
        v = sb.construir(_v(nome))
        for c in v['cenas'][:-1]:
            s = c['sb']
            assert s['proposito'] != 'sem_funcao' and s['narracao'] and s['midia_preferida']
            assert s['alternativas'] and s['fallback'] and s['requisitos']
            assert 'cartao' not in [s['midia_preferida']] + s['alternativas']        # nunca cartão automático
        assert 'sb' not in v['cenas'][-1]


def test_golpe_historico_distingue_documento_retrato_e_contexto():
    v = sb.atualizar_midia(sb.construir(_golpe()))
    s = [c['sb'] for c in v['cenas'][:-1]]
    assert s[1]['midia_preferida'] == 'documento' and s[1]['evidencia'] == 'contextual'
    assert 'contextualiza, não demonstra' in s[1]['limitacoes'][0]
    assert s[3]['evidencia'] == 'direto' and s[3]['explica']                       # o jornal da época mostra o fato
    assert s[4]['evidencia'] == 'contextual' and 'mostra quem, não o que fez' in s[4]['limitacoes'][0]
    assert 'acao' in s[4]['requisitos']
    assert s[5]['evidencia'] == 'ilustrativo' and 'não é registro real' in s[5]['limitacoes'][0]
    assert s[6]['evidencia'] == 'contextual' and 'mostra onde' in s[6]['limitacoes'][0]     # Viena não mostra a fuga
    assert s[0]['explica']                                                          # abertura: o lugar basta
    assert s[2]['evidencia'] == 'contextual' and 'mostra onde' in s[2]['limitacoes'][0]     # o hotel não mostra a reunião
    r = sb.resumo(v['cenas'])
    assert set(r['centrais_sem_explicacao']) == {2, 4, 5, 6} and 1 not in r['centrais_sem_explicacao']   # 1 = contexto
    assert 'replanejar' in sb.linha_telegram(v['cenas'])


def test_biologia_prefere_esquema_correto_ao_que_e_invisivel():
    v = sb.construir(_v('biologia'))
    mec = [c['sb'] for c in v['cenas'][:-1] if c['sb']['proposito'] == 'mecanismo']
    assert mec and all(s['midia_preferida'] == 'diagrama' and 'processo' in s['requisitos'] for s in mec)
    assert all('foto_cientifica' in s['alternativas'] for s in mec)
    assert all(s['movimento'].startswith('parado') for s in mec)                  # esquema: leitura, sem Ken Burns
    sem = sb.atualizar_midia(v)
    assert sem['cenas'][1]['sb']['evidencia'] == 'sem_midia' and not sem['cenas'][1]['sb']['explica']


def test_ciencia_com_comparacao_usa_grafico_e_mapa_so_quando_pedido():
    v = _v('ciencia')
    v['cenas'][5].update(tipo='comparacao', itens=[{'rotulo': 'Terra', 'valor': 1}, {'rotulo': 'Marte', 'valor': 2}])
    v = sb.atualizar_midia(sb.construir(v))
    s = v['cenas'][5]['sb']
    assert s['midia_preferida'] == 'grafico' and s['evidencia'] == 'explicativo' and s['composicao']['foco'] == 'dado'
    assert not any(c['sb']['midia_preferida'] == 'mapa' for c in v['cenas'][:-1])


def test_pedacos_compartilham_o_storyboard_e_montagem_registra_tempo_e_transicao():
    v = _golpe()
    sub = dict(v['cenas'][2], sub=1, fala='continua.')
    v['cenas'].insert(3, sub)
    v['cenas'][4]['evento'] = v['cenas'][2]['evento']                             # mesmo acontecimento
    v = sb.construir(v)
    assert v['cenas'][3]['sb'] is v['cenas'][2]['sb']
    t = 0.0
    for c in v['cenas']:
        c['start'], c['end'] = t, t + 2.0
        t += 2.0
    sb.registrar_tempos(v['cenas'])
    assert v['cenas'][2]['sb']['span'] == (4.0, 8.0)                               # a ideia inteira, com o pedaço
    assert v['cenas'][4]['sb']['transicao'] == 'continuidade'
    assert v['cenas'][1]['sb']['transicao'] in ('novo_bloco', 'contraste', 'mudanca_de_lugar_ou_tempo')


def test_roteiro_antigo_sem_plano_nem_bloco_nao_quebra():
    v = {'cenas': [{'tipo': 'gancho', 'fala': 'a', 'grupo': 0}, {'tipo': 'historia', 'fala': 'b', 'grupo': 1},
                   {'tipo': 'fechamento', 'fala': 'c'}]}
    v = sb.atualizar_midia(sb.construir(v))
    assert v['cenas'][0]['sb']['proposito'] == 'abertura' and v['cenas'][1]['sb']['proposito'] == 'sem_funcao'
    assert sb.resumo(v['cenas'])['sem_funcao'] == 1


def _jpg(p: Path, cor):
    from PIL import Image
    Image.new('RGB', (900, 1200), cor).save(p)
    return p


def test_storyboard_atravessa_a_montagem_real(tmp_path):
    v = sb.atualizar_midia(sb.construir(_golpe()))
    reais = {}
    for k, c in enumerate(v['cenas']):
        if c.get('foto'):
            reais[c['foto']] = {'tipo': 'foto', 'arq': _jpg(tmp_path / f"{c['foto']}.jpg", (30 * k % 255, 80, 120)), 'ano': 1925}
            c['imagem'] = c['foto']
    tempos = [(2.0 * k, 2.0 * k + 2.0) for k in range(len(v['cenas']))]
    cenas = main._montar_cenas({'cenas': v['cenas'], 'titulo': 'Torre'}, reais, {}, tempos, tmp_path)
    ideias = list({id(c['sb']): c for c in cenas if c.get('sb')}.values())
    assert len(ideias) == len(v['cenas']) - 1
    assert all(c['sb']['span'] for c in ideias)
    assert ideias[0]['sb'] is v['cenas'][0]['sb']                                 # a MESMA estrutura, não uma cópia
