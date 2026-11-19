"""Ciclo de autocorreção visual — mocks apenas para o diretor e o render."""
import json

from src.v4.formatos.autocorrecao import preparar_candidato, executar


def _base():
    return {'formato': 'atlas', 'canal': 'coringa', 'video_id': 'visual-1',
            'duracao': 12.0,
            'narracao': {'texto': 'Esta fábrica constrói semicondutores.',
                         'fatos': [{'id': 'f1', 'fontes': ['https://example.org'], 'texto': 'Fato'}]},
            'beats': [{'id': 'b1', 'fatos': ['f1'], 'composicao': 'atlas.prova',
                       'camadas': [{'id': 'p1', 'componente': 'atlas.provaVisual',
                                    'p': {'asset': 'imagem:real'}}],
                       'direcao_visual': {'verbo': 'MOSTRAR', 'provas': ['p1'],
                                          'pergunta': 'Que instalação será apresentada?',
                                          'referente': 'Fábrica de semicondutores real',
                                          'aprendizado': 'O espectador identifica uma fábrica real'}}]}


def _catalogo():
    return {'itens': [{'id': 'imagem:real', 'sha256_origem': 'a' * 64, 'licenca': 'CC BY 4.0',
                       'prova': {'midia_corresponde': True}}]}


def _critico():
    return {'pronto': False,
            'bloqueios': [{'beat': 'b1', 'problemas': ['V-enquadramento_adequado: máquina muito pequena'],
                           'veredito': {'correcao': 'enquadramento físico dominante'}}]}


def test_nao_permite_mudar_narracao_para_enganar_fiscal():
    proposta = _base()
    proposta['narracao'] = {'texto': 'A narração mudou.', 'fatos': proposta['narracao']['fatos']}
    cand, r = preparar_candidato(_base(), _critico(), lambda _: proposta, _catalogo())
    assert cand is None and 'narracao' in r['motivo']


def test_respeita_bloqueio_de_material_insuficiente():
    cand, r = preparar_candidato(_base(), _critico(),
                                 lambda _: {'bloqueado': 'MÍDIA INSUFICIENTE', 'faltam': ['EUV']},
                                 _catalogo())
    assert cand is None and r['faltam'] == ['EUV']


def test_nao_inventa_solucao_com_modelo_de_visao_indisponivel():
    cand, r = preparar_candidato(_base(), {
        'pronto': False, 'bloqueios': [{'beat': 'b1', 'problemas': ['SEM-REVISAO: sem cota']}]},
        lambda _: (_ for _ in ()).throw(AssertionError('não deveria chamar IA')),
        _catalogo())
    assert cand is None and 'modelo de visão indisponível' in r['motivo']


def test_uma_tentativa_revisada_aprovada_com_midia_comprovada(monkeypatch, tmp_path):
    from src.v4.formatos import ponte_biblioteca
    monkeypatch.setattr(ponte_biblioteca, 'catalogo', _catalogo)
    arq = tmp_path / 'plano.json'
    arq.write_text(json.dumps(_base()), encoding='utf-8')
    (tmp_path / 'revisao_visual.json').write_text(json.dumps(_critico()), encoding='utf-8')
    calls = []
    def revisar(pl):
        calls.append(pl['video_id'])
        return {'pronto': True, 'bloqueios': [], 'chamadas': 1}
    r = executar(arq, tmp_path, chamar=lambda _: _base(), reavaliar=revisar)
    assert r['decisao'] == 'candidato_revalidado_visual'
    assert r['tentativas'] == 1 and calls == ['visual-1']


def test_revisao_ruim_reverte_plano_e_bloqueia(monkeypatch, tmp_path):
    from src.v4.formatos import ponte_biblioteca
    monkeypatch.setattr(ponte_biblioteca, 'catalogo', _catalogo)
    arq = tmp_path / 'plano.json'
    arq.write_text(json.dumps(_base()), encoding='utf-8')
    anterior = arq.read_text()
    (tmp_path / 'revisao_visual.json').write_text(json.dumps(_critico()), encoding='utf-8')
    def ruim(_):
        return {'pronto': False, 'bloqueios': [{'problemas': ['continua distante']}]}
    r = executar(arq, tmp_path, chamar=lambda _: _base(), reavaliar=ruim)
    assert r['decisao'] == 'bloqueado'
    assert arq.read_text() == anterior
    assert r['tentativas'] == 1
