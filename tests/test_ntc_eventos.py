"""NTC Fase 4 · CP2 — verificador de acontecimentos (src/ntc_eventos.py).

Cobre: compatibilidade com roteiros antigos, eventos centrais que não podem ser
escondidos trocando o papel da cena, alertas próprios para evento central
impossível, generalização (mesmo verbo em classes diferentes, nada específico
de barata/cupim/Valdirene) e as quatro histórias de teste.
"""
import copy
import json
import unittest
from pathlib import Path

from src import fabula, ntc_eventos as E
from tests import ntc_geometria as G

AQUI = Path(__file__).parent
HIST = AQUI / 'ntc_historias'


def _carregar(p: Path) -> dict:
    return json.loads(p.read_text(encoding='utf-8'))


def _cena(narr, objs=(), papel=None, evento=None, cenario='rua'):
    c = {'cenario': cenario, 'cor': 100, 'pose': 'neutra', 'balao': '', 'narracao': narr, 'sfx': None,
         'objetos': [dict(tipo=t, quantidade=q, acao=a, lugar='meio') for t, q, a in objs]}
    if papel:
        c['papel'] = papel
    if evento:
        c['evento'] = evento
    return c


def _roteiro(cenas, tema='E se algo acontecesse?'):
    enchimento = [_cena('Isso é curioso.', papel='contexto') for _ in range(max(0, 8 - len(cenas)))]
    return {'tema': tema, 'titulo_tela': tema.upper(), 'cenas': cenas + enchimento}


class Compatibilidade(unittest.TestCase):
    """Roteiro antigo (sem acontecimentos/papel/evento) → dados de montagem idênticos aos de antes da Fase 4."""

    def test_dados_template_igual_ao_retrato(self):
        casos = dict(G.casos())
        retratos = sorted((AQUI / 'retratos').glob('ntc_dados_*.json'))
        self.assertGreaterEqual(len(retratos), 4)
        for p in retratos:
            nome = p.stem.removeprefix('ntc_dados_')
            with self.subTest(nome):
                atual = json.loads(json.dumps(G.dados_do_roteiro(casos[nome]), sort_keys=True))
                self.assertEqual(atual, _carregar(p))

    def test_campos_novos_nao_mudam_a_montagem(self):
        """Os campos novos são só para o verificador: a montagem do vídeo não muda por causa deles."""
        r = _carregar(AQUI / 'ntc_roteiro_baratas.json')
        novo = copy.deepcopy(r)
        novo['acontecimentos'] = [{'id': 'e1', 'verbo': 'some', 'alvo': 'barata', 'importancia': 'central'}]
        for c in novo['cenas']:
            c.update(papel='acao', mostra='e1', evento={'verbo': 'some', 'alvo': 'barata'})
        self.assertEqual(json.dumps(G.dados_do_roteiro(r), sort_keys=True),
                         json.dumps(G.dados_do_roteiro(novo), sort_keys=True))

    def test_roteiro_antigo_e_avaliado_sem_erro(self):
        for p in [AQUI / 'ntc_roteiro_baratas.json', AQUI / 'ntc_roteiro_baratas_parte2.json']:
            rel = E.avaliar(fabula.validar(_carregar(p)))
            self.assertTrue(rel['eventos'])
            self.assertTrue(all(l['papel'] == '(sem papel)' for l in rel['eventos']))


class NaoDaPraEsconder(unittest.TestCase):
    """Ajuste 1: trocar o papel para reação/contexto não esconde o acontecimento central."""

    def _central_impossivel(self, papel):
        r = _roteiro([_cena('E se a porta da casa caísse sozinha?', papel=papel, evento={'verbo': 'cai', 'alvo': 'porta'}),
                      _cena('A porta caiu de novo.', papel=papel),
                      _cena('Ninguém conseguia fechar a porta.', papel=papel)],
                     tema='E se as portas caíssem?')
        return E.avaliar(fabula.validar(r))

    def test_central_impossivel_alerta_em_qualquer_papel(self):
        for papel in ('acao', 'reacao', 'contexto', None):
            with self.subTest(papel=papel):
                rel = self._central_impossivel(papel)
                self.assertTrue(any(a.startswith('⛔ evento CENTRAL impossível') and 'porta' in a for a in rel['alertas']),
                                rel['alertas'])

    def test_pct_nao_cai_ao_marcar_como_reacao(self):
        self.assertEqual(self._central_impossivel('acao')['pct_D_acao'], self._central_impossivel('reacao')['pct_D_acao'])

    def test_importancia_declarada_nao_rebaixa(self):
        r = _roteiro([_cena('A porta caiu.', papel='reacao', evento={'verbo': 'cai', 'alvo': 'porta', 'importancia': 'detalhe'})] +
                     [_cena('A porta da casa estava velha.', papel='contexto') for _ in range(3)],
                     tema='E se as portas caíssem?')
        rel = E.avaliar(fabula.validar(r))
        self.assertTrue(any(l['importancia'] == 'central' for l in rel['eventos'] if l['verbo'] == 'cai'))

    def test_central_possivel_nunca_mostrado(self):
        """O alvo existe na biblioteca, mas o roteiro só o cita em cenas de reação, sem colocar o objeto."""
        r = _roteiro([_cena('E se o pão sumisse do mundo?', papel='reacao'),
                      _cena('O pão sumiu da padaria.', papel='reacao'),
                      _cena('Sem pão no café.', papel='contexto')], tema='E se o pão sumisse?')
        rel = E.avaliar(fabula.validar(r))
        al = [a for a in rel['alertas'] if a.startswith('⚠️ evento CENTRAL possível mas nunca mostrado')]
        self.assertTrue(al and 'reação/contexto' in al[0], rel['alertas'])


class Generalizacao(unittest.TestCase):
    """Mesmo verbo, classes diferentes; nenhuma regra é de um tema só."""

    def test_some_em_tres_classes(self):
        for obj, palavra in (('pao', 'pão'), ('dinheiro', 'dinheiro'), ('passaro', 'pássaro')):
            with self.subTest(obj):
                r = _roteiro([_cena(f'O {palavra} sumiu.', [(obj, 1, 'some')], 'acao')])
                l = [x for x in E.avaliar(fabula.validar(r))['eventos'] if x['verbo'] == 'some'][0]
                self.assertEqual((l['nivel'], l['status']), ('A', 'mostrado'))

    def test_invade_respeita_classe(self):
        ok = [x for x in E.avaliar(fabula.validar(_roteiro([_cena('Os ratos invadiram a rua.', [('rato', 3, 'corre')], 'acao')])))['eventos']
              if x['verbo'] == 'invade']
        self.assertEqual(ok[0]['nivel'], 'A')
        nao = [x for x in E.avaliar(fabula.validar(_roteiro([_cena('O dinheiro invadiu a rua.', [('dinheiro', 3, 'cai')], 'acao')])))['eventos']
               if x['verbo'] == 'invade']
        self.assertEqual(nao[0]['nivel'], 'D')

    def test_inseto_generico_nao_vira_barata(self):
        for bicho in ('formigas', 'abelhas', 'cupins'):
            with self.subTest(bicho):
                r = _roteiro([_cena(f'As {bicho} apareceram.', [('barata', 3, 'aparece')], 'acao')])
                l = [x for x in E.avaliar(fabula.validar(r))['eventos'] if x['verbo'] == 'aparece'][0]
                self.assertEqual(l['nivel'], 'D')

    def test_quantidade_vira_painel(self):
        r = _roteiro([dict(_cena('O preço subiu.', papel='acao'), painel={'rotulo': 'PREÇO', 'valor': 10})])
        l = [x for x in E.avaliar(fabula.validar(r))['eventos'] if x['verbo'] == 'cresce'][0]
        self.assertEqual((l['nivel'], l['status']), ('C', 'mostrado'))

    def test_expressao_idiomatica_ignorada(self):
        evs = E.eventos_narrados('Aí ela caiu na real e a notícia correu.')
        self.assertFalse([e for e in evs if e['verbo'] in ('cai', 'foge')])

    def test_personagem_como_sujeito_nao_e_acontecimento(self):
        self.assertFalse(E.eventos_narrados('A Valdirene saiu correndo.'))

    def test_agente_nao_e_alvo(self):
        evs = E.eventos_narrados('O fogo queimou as folhas.')
        self.assertEqual([e['alvo']['chave'] for e in evs if e['verbo'] == 'queima'], ['folhas'])

    def test_catalogo_sem_regra_de_tema(self):
        """O verificador lê só o catálogo; o código não tem nome de bicho nem de personagem."""
        codigo = (AQUI.parent / 'src' / 'ntc_eventos.py').read_text(encoding='utf-8').lower()
        for palavra in ('barata', 'cupim', 'valdirene'):
            self.assertNotIn(palavra, codigo)


class Historias(unittest.TestCase):
    """As quatro histórias de teste (assuntos diferentes, formato novo)."""

    def _rel(self, nome):
        return E.avaliar(fabula.validar(_carregar(HIST / f'{nome}.json')))

    def test_quatro_assuntos(self):
        self.assertEqual(len(list(HIST.glob('*.json'))), 4)

    def test_ratos_tudo_mostrado(self):
        rel = self._rel('animais_ratos')
        self.assertEqual(rel['contagem']['D'], 0)
        self.assertEqual(rel['mostrados'], rel['total'])
        self.assertFalse(rel['alertas'])

    def test_dinheiro_sem_impossivel(self):
        rel = self._rel('economia_dinheiro')
        self.assertEqual(rel['contagem']['D'], 0)
        self.assertFalse(rel['alertas'])

    def test_fogo_casa_destruida_tem_alerta_proprio(self):
        rel = self._rel('desastre_fogo')
        self.assertTrue(any(a.startswith('⛔') and 'casa' in a for a in rel['alertas']))
        self.assertFalse(any(a.startswith('NÃO RECOMENDO') for a in rel['alertas']))

    def test_madeira_nao_recomendada(self):
        rel = self._rel('lacunas_madeira')
        self.assertTrue(rel['alertas'][0].startswith('NÃO RECOMENDO'))
        self.assertEqual(rel['mostrados'], 0)

    def test_parte2_baratas(self):
        rel = E.avaliar(fabula.validar(_carregar(AQUI / 'ntc_roteiro_baratas_parte2.json')))
        self.assertGreater(rel['pct_D'], 50)
        self.assertTrue(any('cupins' in a and a.startswith('⛔') for a in rel['alertas']))

    def test_resumo_telegram_curto(self):
        for p in HIST.glob('*.json'):
            s = E.resumo_telegram(E.avaliar(fabula.validar(_carregar(p))))
            self.assertTrue(s.startswith('🎯'))
            self.assertLess(len(s), 1500)


if __name__ == '__main__':
    unittest.main()
