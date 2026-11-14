"""Avaliação V2.2 do contrato de acontecimentos — de ponta a ponta (seletor → montagem → fiscal), com paráfrases e
construções inéditas em 8 categorias. Casos escritos ANTES de rodar; critérios de aceitação objetivos:

  C1  contrato declarado COM dados → composição capaz do tipo em 100% dos casos;
  C2  contrato crítico declarado SEM dados → limitação com os dados que faltam, e o fiscal BLOQUEIA uma vez, com o que
      falta na evidência (100%);
  C3  tipo declarado desconhecido → limitação e bloqueio (100%);
  C4  formato antigo (sem contrato), paráfrase crítica → NUNCA aprovação automática com representação inadequada
      (aceito: composição capaz OU bloqueio OU revisão humana obrigatória) — 100%;
  C5  conjunto de reserva da V2.1 (só padrões) → não pode cair abaixo de 10/16 (resultado anterior).

Uso: python -m src.v2.avaliacao_contrato [saida.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.v2 import avaliacao_selecao, contrato, fiscal_v2, montagem

RAIZ = Path(__file__).resolve().parents[2]
IMG = str(RAIZ / 'tests' / 'img' / 'fundo_c.jpg')
P = lambda *a: [{'nome': n, 'lon': lo, 'lat': la} for n, lo, la in a]

# (id, categoria, fala (paráfrase), contrato com dados, comps aceitáveis)
CASOS = [
    ('q1', 'ferrugem/química', 'Deixado na chuva, o portão foi ganhando aquela crosta alaranjada.',
     {'tipo': 'transformacao', 'sujeito': 'ferro', 'acao': 'oxida', 'estado_inicial': 'ferro', 'estado_final': 'óxido de ferro (ferrugem)', 'mostrar': 'ferro virando ferrugem',
      'dados': {'etapas': ['Ferro exposto', 'Água e oxigênio', 'Óxido de ferro']}, 'fonte': 'Wikipédia'}, {'processo.etapas'}),
    ('q2', 'ferrugem/química', 'Uma gota de vinagre no bicarbonato e a mistura espuma na hora.',
     {'tipo': 'transformacao', 'sujeito': 'bicarbonato', 'acao': 'libera gás carbônico', 'dados': {'etapas': ['Ácido + base', 'Gás carbônico', 'Espuma']}}, {'processo.etapas'}),
    ('m1', 'movimento físico', 'Solta da mão, a maçã acelera rumo ao chão.',
     {'tipo': 'movimento', 'sujeito': 'maçã', 'acao': 'cai', 'dados': {'forcas': [{'nome': 'Peso', 'angulo': -90, 'intensidade': .8}]}}, {'forcas.vetores'}),
    ('m2', 'movimento físico', 'O patinador recolhe os braços e passa a girar mais depressa.',
     {'tipo': 'movimento', 'sujeito': 'patinador', 'acao': 'gira mais rápido', 'dados': {'cena': 'rotacao'}}, {'animacao.quadros'}),
    ('k1', 'máquina', 'Cada pedalada vira giro na roda traseira graças à corrente.',
     {'tipo': 'mecanismo', 'sujeito': 'bicicleta', 'acao': 'transmite força', 'dados': {'etapas': ['Pedal', 'Coroa e corrente', 'Catraca', 'Roda']}}, {'processo.etapas', 'diagrama.explicativo'}),
    ('k2', 'máquina', 'O vapor empurra o êmbolo, e o êmbolo faz a roda andar.',
     {'tipo': 'mecanismo', 'dados': {'nos': [{'id': 'v', 'rotulo': 'Vapor'}, {'id': 'e', 'rotulo': 'Êmbolo'}, {'id': 'r', 'rotulo': 'Roda'}]}}, {'diagrama.explicativo'}),
    ('d1', 'deslocamento', 'As andorinhas trocam a Europa pela África quando o frio chega.',
     {'tipo': 'deslocamento', 'dados': {'pontos': P(('Europa', 10, 50), ('África', 20, 0))}}, {'mapa.rota'}),
    ('d2', 'deslocamento', 'Magalhães saiu de Sevilha e, anos depois, a expedição voltou dando a volta ao mundo.',
     {'tipo': 'deslocamento', 'dados': {'pontos': P(('Sevilha', -6, 37.4), ('Filipinas', 124, 11))}}, {'mapa.rota'}),
    ('p1', 'evolução de processo', 'Do grão moído à xícara, o café passa por quatro estágios.',
     {'tipo': 'processo', 'dados': {'etapas': ['Moagem', 'Água quente', 'Extração', 'Filtragem']}}, {'processo.etapas'}),
    ('p2', 'evolução de processo', 'A população da cidade não parou de crescer em cem anos.',
     {'tipo': 'evolucao_temporal', 'dados': {'serie': [{'ano': 1920, 'valor': 1}, {'ano': 1950, 'valor': 2}, {'ano': 1980, 'valor': 5}, {'ano': 2020, 'valor': 9}]}}, {'grafico.temporal'}),
    ('n1', 'fenômeno natural', 'Quando a lua cheia passa, a água avança sobre a praia.',
     {'tipo': 'nivel', 'sujeito': 'mar', 'acao': 'sobe', 'dados': {'de': 0, 'ate': 3}}, {'mecanismo.nivel', 'mecanismo.eclusa'}),
    ('n2', 'fenômeno natural', 'O meteorito derrubou árvores num raio de dezenas de quilômetros.',
     {'tipo': 'impacto', 'dados': {'aneis': [{'raio_km': 26}]}}, {'evento.impacto'}),
    ('b1', 'transformação biológica', 'O girino perde a cauda e ganha pernas.',
     {'tipo': 'transformacao', 'dados': {'etapas': ['Girino', 'Pernas traseiras', 'Sapo']}}, {'processo.etapas'}),
    ('b2', 'transformação biológica', 'O sangue leva oxigênio dos pulmões até as células.',
     {'tipo': 'processo', 'dados': {'etapas': ['Pulmões', 'Hemácias', 'Células']}}, {'processo.etapas'}),
    ('h1', 'evento histórico', 'Roma foi fundada em 753 a.C. e o império do Ocidente terminou em 476.',
     {'tipo': 'sequencia_historica', 'dados': {'eventos': [{'ano': -753, 'texto': 'Fundação'}, {'ano': 476, 'texto': 'Queda do Ocidente'}]}}, {'linha_tempo.historica'}),
    ('h2', 'evento histórico', 'Naquele dia de 1914 o primeiro navio cruzou de um oceano ao outro.',
     {'tipo': 'evento_historico', 'dados': {'img': IMG}}, {'foto.historica'}),
]


def _uma(fala: str, ac: dict | None) -> tuple[dict, list[dict], dict]:
    s = {'tipo': 'historia', 'fala': fala, 'start': 0.0, 'end': 4.0, 'img': IMG, 'grupo': 'g0'}
    if ac is not None:
        s['acontecimento'] = ac
    d1 = {'duration': 4.0, 'meta': {'titulo': 'teste', 'fontes': ['Wikipédia']}, 'scenes': [s], 'captions': []}
    v2, direcao = montagem.converter(d1)
    r = fiscal_v2.avaliar(v2, direcao, [], d1)
    return v2, direcao, r


def _res(v2, direcao, r):
    sc = v2['scenes'][0]
    cods = sorted({a['codigo'] for a in r['achados'] if a['gravidade'] in ('bloqueio', 'revisao')})
    return {'comp': sc['comp'], 'bloqueios_revisoes': cods, 'aprovacao_automatica': r['aprovacao_automatica'],
            'limitacao': direcao[0].get('limitacao'), 'faltam': direcao[0].get('faltam'),
            'evidencia_s5': ' '.join(a['evidencia'] for a in r['achados'] if a['codigo'] == 'S5' and a['gravidade'] == 'bloqueio'),
            'n_bloqueios': sum(1 for a in r['achados'] if a['gravidade'] == 'bloqueio')}


def rodar() -> dict:
    out = {'C1': [], 'C2': [], 'C3': [], 'C4': []}
    for cid, cat, fala, ac, ok in CASOS:
        x = _res(*_uma(fala, ac))
        out['C1'].append({'id': cid, 'categoria': cat, 'fala': fala, **x, 'aceitaveis': sorted(ok),
                          'passou': x['comp'] in ok and x['aprovacao_automatica']})
        sem = {k: v for k, v in ac.items() if k != 'dados'}
        sem['obrigatoria'] = True
        y = _res(*_uma(fala, sem))
        out['C2'].append({'id': cid + '-sem-dados', 'categoria': cat, 'fala': fala, **y,
                          # correção do piloto: S1 e S5 eram a MESMA causa contada duas vezes; o critério exige o bloqueio
                          # (S5), a lista do que falta E essa lista na evidência do próprio bloqueio, numa causa só
                          'passou': (not y['aprovacao_automatica']) and 'S5' in y['bloqueios_revisoes'] and bool(y['faltam'])
                                    and 'falta:' in y['evidencia_s5'] and y['n_bloqueios'] == 1})
        z = _res(*_uma(fala, None))
        cap = z['comp'] in ok
        out['C4'].append({'id': cid + '-formato-antigo', 'categoria': cat, 'fala': fala, **z, 'aceitaveis': sorted(ok),
                          'passou': cap or not z['aprovacao_automatica'],
                          'como': 'composição capaz' if cap else ('bloqueio' if any(c.startswith(('S1', 'S5', 'D')) for c in z['bloqueios_revisoes']) else
                                                                  'revisão humana (S6)' if 'S6' in z['bloqueios_revisoes'] else 'APROVADA SEM REPRESENTAÇÃO')})
    for fala, tipo in [('A fusão nuclear acende a estrela.', 'fusao_estelar'), ('O vírus sequestra a célula.', 'replicacao_viral')]:
        y = _res(*_uma(fala, {'tipo': tipo, 'mostrar': fala, 'importancia': 'critica'}))
        out['C3'].append({'id': tipo, 'fala': fala, **y, 'passou': not y['aprovacao_automatica'] and 'S5' in y['bloqueios_revisoes']})
    sel = avaliacao_selecao.rodar()
    out['C5'] = {'reserva_passaram': sel['reserva_passaram'], 'reserva_total': sel['reserva_total'], 'passou': sel['reserva_passaram'] >= 10,
                 'positivos': f"{sel['positivos_passaram']}/{sel['positivos_total']}", 'negativos': f"{sel['negativos_passaram']}/{sel['negativos_total']}"}
    out['resumo'] = {k: f"{sum(x['passou'] for x in out[k])}/{len(out[k])}" for k in ('C1', 'C2', 'C3', 'C4')}
    out['resumo']['C5'] = f"{sel['reserva_passaram']}/{sel['reserva_total']} (≥ 10)"
    out['C4_como'] = {}
    for x in out['C4']:
        out['C4_como'][x['como']] = out['C4_como'].get(x['como'], 0) + 1
    return out


if __name__ == '__main__':
    r = rodar()
    for k in ('C1', 'C2', 'C3', 'C4'):
        for x in r[k]:
            print(('ok ' if x['passou'] else 'XX '), k, x['id'].ljust(22), str(x['comp']).ljust(22), x['bloqueios_revisoes'], 'auto' if x['aprovacao_automatica'] else '', x.get('como', ''))
    print(r['resumo'], r['C4_como'])
    if len(sys.argv) > 1:
        json.dump(r, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1, default=str)
