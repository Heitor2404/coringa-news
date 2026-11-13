"""Plano-mestre, etapa I (12/11/2026): custos, falhas, repetições e métricas. Nenhuma chamada paga (tudo simulado).
Confere que o plano-mestre NÃO aumentou o número de pedidos ao Claude no caminho do Explica e registra o tamanho dos
prompts; que falha do Gemini entra no livro-caixa; e que o orçamento continua só monitorando."""
import copy
import os
from pathlib import Path

import pytest

from src import cofre, custo, gemini, metricas, orcamento, orcamento_video, roteiro, storyboard as sbm

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def limpo(monkeypatch):
    custo.zerar()
    monkeypatch.setattr(orcamento, 'MARCAS', [])
    yield
    custo.zerar()


def test_falha_do_gemini_entra_no_livro_caixa(monkeypatch):
    monkeypatch.setattr(gemini, 'CHAVES', ['k'])
    monkeypatch.setattr(gemini, '_esgotado', set())
    monkeypatch.setattr(gemini.time, 'sleep', lambda s: None)

    def nunca(modelo):
        raise RuntimeError('500 INTERNAL')
    with pytest.raises(RuntimeError, match='indisponível'):
        gemini._tentar(nunca, ['m1'])
    assert [(x['ia'], x['ok']) for x in custo.LIVRO] == [('gemini', False)]


def _cenas_com_escolhas():
    v = {'plano': {'modos': ['historico_investigativo']}, 'cenas': [
        {'tipo': 'gancho', 'fala': 'a', 'grupo': 0, 'foto': 'a0', 'relacao': 'fato', 'bloco': {'funcao': 'abertura'},
         '_escolha': {'foto': 'a0', 'motivos': ['escolhida pelo casamento'], 'rejeitadas': [{'foto': 'a3', 'motivo': 'genérica e não mostra o que a frase diz'}]}},
        {'tipo': 'historia', 'fala': 'b', 'grupo': 1, 'foto': 'a1', 'relacao': 'tema', 'bloco': {'funcao': 'evidencia'},
         '_escolha': {'foto': 'a1', 'motivos': ['o Gemini disse "fato", mas a imagem é de 2012 e o fato de 1925'],
                      'rejeitadas': [{'foto': 'a6', 'motivo': 'já usada em outra ideia'}]}},
        {'tipo': 'historia', 'fala': 'c', 'grupo': 2, 'foto': 'a2', 'relacao': 'pessoa', 'bloco': {'funcao': 'contexto'},
         '_escolha': {'foto': 'a2', 'motivos': ['reserva com 3.5 pontos', 'mesma pessoa do fato']}},
        {'tipo': 'historia', 'fala': 'd', 'grupo': 3, 'bloco': {'funcao': 'payoff'}},
        {'tipo': 'fechamento', 'fala': 'e'}]}
    return sbm.atualizar_midia(sbm.construir(v))


def test_metricas_juntam_custo_falhas_repeticoes_acervo_e_representacao(monkeypatch):
    for etapa, ok, saida in (('roteiro', False, 0), ('roteiro', True, 7000), ('crítica', True, 4000), ('ganchos', True, 500)):
        custo.registrar('claude', 'sonnet', 0.05, {'output_tokens': saida}, 10, ok=ok, etapa_=etapa)
    custo.registrar('gemini', 'flash', etapa_='casar')
    custo.registrar('gemini', 'indisponível', ok=False, etapa_='fiscal sombra')
    orcamento.MARCAS += [('roteiro pronto', 9.5), ('narração pronta', 14.0)]
    v = _cenas_com_escolhas()
    m = metricas.coletar(v, v['cenas'])
    assert m['claude'] == {'chamadas': 4, 'falhas': 1, 'repetidas': 1, 'usd_estimado': 0.2, 'teto_garantido': False}
    assert m['gemini'] == {'chamadas': 2, 'falhas': 1}
    assert m['fases']['claude:roteiro']['tokens_saida'] == 7000 and m['tempo_min']['roteiro pronto'] == 9.5
    assert m['acervo'] == {'ideias': 4, 'com_foto': 3, 'do_casamento': 2, 'reservas': 1, 'sem_foto': 1, 'relacao_rebaixada': 1,
                           'recusas': {'genérica e não mostra o que a frase diz': 1, 'já usada em outra ideia': 1}}
    assert m['representacao']['cenas'] == 4 and m['representacao']['centrais_sem_explicacao'] == [1, 3]
    linha = metricas.linha_telegram(m)
    assert linha.startswith('📈 Métricas: Claude 4 chamada(s) (1 falha(s)) · 1 repetida(s)') and 'representação' in linha


# ───────── nenhum pedido novo ao Claude no caminho do Explica ─────────
FATOS = '- ★ Em 1925, Victor Lustig vendeu a Torre Eiffel (Wikipédia)\n- Reuniu seis sucateiros (Wikipédia)'


def test_explica_continua_com_os_mesmos_pedidos_ao_claude(monkeypatch):
    from src import acervo as acv, fontes
    monkeypatch.setattr(orcamento, 'sobra', lambda: 999)
    monkeypatch.setattr(orcamento, 'marca', lambda *a, **k: None)
    monkeypatch.setattr(fontes, 'coletar', lambda *a, **k: (FATOS, ['Wikipédia'], 'https://x', {'epoca': '1925'}))
    monkeypatch.setattr(acv, 'coletar', lambda *a, **k: [{'id': 'a0', 'mostra': 'torre', 'mini': b'', 'util': True, 'nota': 7}])
    monkeypatch.setattr(acv, 'complementar', lambda v, acervo, *a, **k: acervo)
    monkeypatch.setattr(roteiro, 'geocodificar', lambda v: v)
    monkeypatch.setattr(roteiro.viabilidade, 'avaliar', lambda *a, **k: {'ok': True, 'especificas': 9, 'uteis': 9, 'videos': 0})
    monkeypatch.setattr(roteiro, '_planos_sem_foto', lambda v, *a, **k: v)          # porteiro de acervo: fora deste teste
    monkeypatch.setattr(gemini, 'json_visao', lambda *a, **k: {'escolhas': []})
    cenas = [{'tipo': 'gancho', 'fala': f'Em 1925 ele vendeu a torre {k}.', 'cenario': 'x', 'bloco': {'funcao': 'abertura'}}
             if k == 0 else {'tipo': 'historia', 'fala': f'Lustig reuniu sucateiros na cena {k}.', 'cenario': 'x',
                             'bloco': {'funcao': 'payoff' if k == 12 else 'contexto'}} for k in range(13)]
    roteiro_falso = {'titulo': 'Torre', 'plano': {'promessa': 'como vendeu a torre', 'angulo': {'tipo': 'misterio', 'pergunta': 'como?'},
                                                  'modos': ['historico_investigativo']},
                     'cenas': cenas + [{'tipo': 'fechamento', 'fala': 'Segue.'}]}
    pedidos = []

    def json_(prompt, *a, **k):
        pedidos.append(prompt[:40])
        if 'roteiro' in prompt[:200].lower() or len(pedidos) == 1:
            return copy.deepcopy(roteiro_falso)
        return {'aprovado': True, 'notas': {}} if len(pedidos) == 2 else {'ganchos': []}
    monkeypatch.setattr(gemini, 'json_', json_)
    monkeypatch.setattr(roteiro, 'PROMPT_ROTEIRO_EXPLICA', 'roteiro {pergunta}{formato}{noticia}{fatos}{partes}{categoria}{acervo}')
    monkeypatch.setattr(roteiro, 'PROMPT_CRITICA', 'critica {escopo}{fatos}{roteiro}{problemas}')
    v = roteiro.escrever_explica({'pergunta': 'Como vendeu a torre?', 'termos': ['Lustig'], 'partes': 1})
    assert len(pedidos) == 3                                                       # roteiro + crítica + ganchos (como antes)
    assert v['plano']['origem'] == 'roteirista' and all(c.get('sb') for c in v['cenas'] if c['tipo'] != 'fechamento')


@pytest.mark.skipif(not (Path(os.environ.get('COFRE_DIR') or RAIZ / 'cofre') / 'prompts').exists(), reason='sem o cofre')
def test_tamanho_dos_prompts_registrado():
    """Antes do plano-mestre: roteiro 10.562 e crítica 2.711 caracteres. O crescimento fica registrado aqui."""
    r, c = len(cofre.prompt('PROMPT_ROTEIRO_EXPLICA')), len(cofre.prompt('PROMPT_CRITICA'))
    assert r <= 13500 and c <= 3800
    assert (r - 10562) / 10562 < 0.30                                              # ≈ +20% no roteiro (≈ +700 tokens escritos no cache)


def test_orcamento_continua_so_monitorando(monkeypatch):
    monkeypatch.setenv('ORCAMENTO_MODO', 'aplicar')
    assert orcamento_video.modo() == 'monitorar'
