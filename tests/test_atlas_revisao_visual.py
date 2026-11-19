"""Regressões da revisão visual, sem chamadas reais a Gemini."""
import json

from PIL import Image

from src.v4.formatos import revisao_visual


def _dados(tmp_path):
    q = tmp_path / 'quadros'
    q.mkdir()
    Image.new('RGB', (405, 720), '#333333').save(q / 'exemplo.png')
    (q / 'relatorio.json').write_text(json.dumps({
        'ok': True, 'quadros': [{'beat': 'b1', 'arquivo': 'exemplo.png', 't': 1.3}]
    }), encoding='utf-8')
    plano = {'narracao': {'texto': 'Esta fábrica produz semicondutores.'},
             'beats': [{'id': 'b1', 'composicao': 'atlas.prova',
                        'direcao_visual': {
                            'verbo': 'MOSTRAR',
                            'pergunta': 'Qual a fábrica desta história?',
                            'referente': 'Fábrica de semicondutores',
                            'aprendizado': 'Existe uma instalação industrial real',
                            'provas': ['fab18-real']}}]}
    (tmp_path / 'plano_resolvido.json').write_text(json.dumps(plano), encoding='utf-8')
    return tmp_path


def _visao_boa(prompt, imagens):
    assert 'nítida num celular' in prompt
    assert len(imagens) == 1 and imagens[0][:3] == b'\xff\xd8\xff'
    return {'referente_visivel': True, 'aprendizado_demonstrado': True,
            'enquadramento_adequado': True, 'imagem_celular_legivel': True,
            'mapa_informativo': False, 'acao_ou_relacao_visivel': False,
            'problemas': [], 'correcao': ''}


def test_quadro_fotografico_aprovado_pelo_crítico_independente(tmp_path):
    r = revisao_visual.revisar(_dados(tmp_path), _visao_boa)
    assert r['pronto'] and r['chamadas'] == 1


def test_rejeita_foto_fora_de_foco_apesar_de_qa_geometrico_verde(tmp_path):
    def ruim(p, i):
        return {**_visao_boa(p, i), 'referente_visivel': False,
                'problemas': ['o assunto ocupa pequena fração do quadro']}
    r = revisao_visual.revisar(_dados(tmp_path), ruim)
    assert r['pronto'] is False
    assert 'V-referente_visivel' in str(r['bloqueios'])


def test_falha_fechada_sem_modelo_ou_cota(tmp_path):
    def erro(*_):
        raise RuntimeError('sem cota Gemini')
    r = revisao_visual.revisar(_dados(tmp_path), erro)
    assert not r['pronto']
    assert 'SEM-REVISAO' in str(r['bloqueios'])


def test_diagrama_tecnico_nao_exige_mapa_no_critico(tmp_path):
    pasta = _dados(tmp_path)
    pl = json.loads((pasta / 'plano_resolvido.json').read_text())
    pl['beats'][0]['composicao'] = 'atlas.tecnica'
    pl['beats'][0]['direcao_visual']['verbo'] = 'DEMONSTRAR'
    (pasta / 'plano_resolvido.json').write_text(json.dumps(pl))
    def visao(p, imgs):
        return {**_visao_boa(p, imgs), 'acao_ou_relacao_visivel': True}
    assert revisao_visual.revisar(pasta, visao)['pronto']
