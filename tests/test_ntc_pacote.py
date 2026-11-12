"""NTC Fase 4 · CP1 — pacote de reprodução (src/ntc_pacote.py) e gancho no fabula.fazer."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import fabula, ntc_eventos, ntc_pacote as P
from tests import ntc_geometria as G

AQUI = Path(__file__).parent


def _pacote(pasta):
    r = fabula.validar(json.loads((AQUI / 'ntc_roteiro_baratas_parte2.json').read_text(encoding='utf-8')))
    t = G._tempos(r); caps = G._legendas(r, t)
    d = fabula.dados_template(r, t, caps, t[-1][1] + 2.5)
    pac = P.montar(r, d, t, caps, ntc_eventos.avaliar(r), Path('ntc-x.mp4'))
    return pac, P.salvar(pac, Path(pasta))


class Pacote(unittest.TestCase):
    def test_conteudo_completo(self):
        with tempfile.TemporaryDirectory() as tmp:
            pac, arq = _pacote(tmp)
            lido = P.ler(arq)
            for campo in ('roteiro', 'dados_montagem', 'tempos', 'legendas', 'motor', 'eventos', 'tema', 'criado_em', 'personagem'):
                self.assertIn(campo, lido)
            self.assertTrue(lido['motor']['commit'])
            self.assertTrue(any(k.endswith('kit_objetos.js') for k in lido['motor']['arquivos']))
            self.assertIn('capacidades.json', ' '.join(lido['motor']['arquivos']))

    def test_mesmo_motor_e_remontagem_identica(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, arq = _pacote(tmp)
            pac = P.ler(arq)
            self.assertEqual(P.conferir_motor(pac), [])
            refeito = fabula.dados_template(fabula.validar(pac['roteiro']), pac['tempos'], pac['legendas'], pac['dados_montagem']['duration'])
            self.assertEqual(json.dumps(refeito, sort_keys=True), json.dumps(pac['dados_montagem'], sort_keys=True))

    def test_motor_alterado_e_detectado(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, arq = _pacote(tmp)
            pac = P.ler(arq)
            pac['motor']['arquivos']['canais/ntc/vetor/kit_objetos.js'] = 'outro'
            self.assertEqual(P.conferir_motor(pac), ['canais/ntc/vetor/kit_objetos.js'])

    def test_resumo_telegram(self):
        with tempfile.TemporaryDirectory() as tmp:
            pac, arq = _pacote(tmp)
            self.assertTrue(P.resumo_telegram(pac, arq).startswith('📦'))


class GanchoNaoDerrubaVideo(unittest.TestCase):
    def test_falha_no_pacote_vira_aviso(self):
        with mock.patch.object(P, 'salvar', side_effect=OSError('disco cheio')):
            msg = fabula._pacote({'tema': 't', 'cenas': []}, {'cenas': []}, [], [], None, Path('x.mp4'))
        self.assertIn('Pacote não salvo', msg)

    def test_falha_nos_eventos_vira_none(self):
        with mock.patch.object(ntc_eventos, 'avaliar', side_effect=RuntimeError('x')):
            self.assertIsNone(fabula._eventos({'cenas': []}))

    def test_workflow_arquiva_no_cofre(self):
        wf = (AQUI.parent / '.github' / 'workflows' / 'gerar-videos.yml').read_text(encoding='utf-8')
        self.assertIn('sparse-checkout add arquivo_ntc', wf)
        self.assertIn('saida/pacotes_ntc', wf)


if __name__ == '__main__':
    unittest.main()
