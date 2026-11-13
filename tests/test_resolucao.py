"""Etapa 2 da auditoria (13/11/2026): resolução visual por cena. Cinco situações de assuntos diferentes + compatibilidade.
Nada de IA nem vídeo: o acervo e o casamento são simulados com os campos que o pipeline real produz."""
from pathlib import Path

import main
from src import aprovacao, fiscal, resolucao, storyboard as sbm

AC = lambda quem='', onde='', quando='', recurso='': {'quem': quem, 'onde': onde, 'quando': quando, 'recurso': recurso}


def _cena(k, fala, funcao, recurso='', **kw):
    return {'tipo': 'gancho' if k == 0 else 'historia', 'fala': fala, 'grupo': k, 'evento': f'e{k}',
            'bloco': {'funcao': funcao}, 'acontecimento': AC(recurso=recurso, quem=kw.pop('quem', ''), quando=kw.pop('quando', '')),
            'imagem': f'c{k}', **kw}


def _video(modo, cenas, acervo):
    v = {'plano': {'modos': [modo]}, 'cenas': cenas + [{'tipo': 'fechamento', 'fala': 'Segue.'}], 'acervo': acervo}
    return resolucao.resolver(sbm.construir(v))


def _r(v, k):
    return v['cenas'][k]['sb']['resolucao']


ACV = [{'id': 'p0', 'tipo_img': 'foto', 'mostra': 'polvo sobre rocha'},
       {'id': 'p1', 'tipo_img': 'foto', 'mostra': 'polvo dentro de concha'},
       {'id': 'd0', 'tipo_img': 'diagrama', 'mostra': 'diagrama de cromatóforo expandido e contraído', 'rotulado': True},
       {'id': 'v0', 'tipo_img': 'foto', 'mostra': 'vídeo de polvo mudando de cor', 'video': {'url': 'u'}},
       {'id': 'j0', 'tipo_img': 'jornal', 'mostra': 'jornal de 1925 sobre o golpe', 'ano': 1925},
       {'id': 'r0', 'tipo_img': 'foto', 'mostra': 'retrato de André Poisson'},
       {'id': 't0', 'tipo_img': 'foto', 'mostra': 'Torre Eiffel', 'lugar': 'Torre Eiffel'},
       {'id': 'rua', 'tipo_img': 'foto', 'mostra': 'rua de Paris', 'generica': True}]


# ───────── 1. polvo: cromatóforos ─────────
def test_polvo_mecanismo_vira_diagrama_real_ou_esquema_pendente_nunca_foto_de_contexto():
    v = _video('mecanismo', [
        _cena(0, 'Este polvo muda de cor em frações de segundo.', 'abertura', 'foto', foto='p0', relacao='tema'),
        _cena(1, 'A pele tem cromatóforos, sacos de pigmento.', 'mecanismo', 'foto', foto='p1', relacao='tema'),   # roteiro pediu "foto"
        _cena(2, 'Músculos esticam o saco e a cor aparece.', 'mecanismo', 'esquema', foto='d0', relacao='diagrama'),
        _cena(3, 'Os nervos ligam cada saco ao cérebro.', 'mecanismo', 'foto', midia='ia', prompt_imagem='x'),
        _cena(4, 'Por isso ele se camufla num piscar de olhos.', 'payoff', 'video', foto='v0', relacao='fato')], ACV)
    assert _r(v, 0)['tipo'] == 'contexto'
    r1 = _r(v, 1)
    assert v['cenas'][1]['sb']['midia_preferida'] == 'diagrama'                    # a necessidade venceu o "foto" do roteiro
    assert r1['tipo'] == 'esquema_pendente' and r1['pendente'] and r1['midia'] is None
    assert r1['rejeitadas'][0] == {'midia': 'p1', 'motivo': 'foto do assunto não mostra o processo'}
    assert v['cenas'][1].get('foto') is None and v['cenas'][1]['midia'] == 'pendente'      # a montagem não recebe a foto
    assert _r(v, 2)['tipo'] == 'reconstrucao_explicativa' and _r(v, 2)['midia'] == 'd0'   # diagrama rotulado do acervo
    r3 = _r(v, 3)
    assert r3['tipo'] == 'esquema_pendente' and 'IA não é esquema' in r3['rejeitadas'][0]['motivo']
    assert not v['cenas'][3].get('prompt_imagem')                                   # nenhuma imagem de IA será pedida
    assert _r(v, 4)['tipo'] == 'evidencia_real' and _r(v, 4)['nivel'] == 'direto'


# ───────── 2. acontecimento histórico que precisa ser mostrado ─────────
def test_golpe_historico_documento_real_reconstrucao_e_pendente():
    v = _video('historico_investigativo', [
        _cena(0, 'Em 1925, Lustig vendeu a Torre Eiffel.', 'abertura', 'lugar', foto='t0', relacao='lugar'),
        _cena(1, 'Os jornais contaram o golpe.', 'evidencia', 'jornal', foto='j0', relacao='documento'),
        _cena(2, 'Poisson pagou a propina na hora.', 'payoff', 'retrato', quem='André Poisson', foto='r0', relacao='pessoa'),
        _cena(3, 'Lustig entregou os papéis falsos.', 'evidencia', 'documento', midia='ia', prompt_imagem='x'),
        _cena(4, 'Poisson saiu feliz do hotel.', 'evidencia', '', midia='ia', prompt_imagem='y')], ACV)
    assert _r(v, 1)['tipo'] == 'evidencia_real' and 'documento' in _r(v, 1)['justificativa']
    r2 = _r(v, 2)
    assert r2['tipo'] == 'reconstrucao_pendente' and 'mostra quem ou onde' in r2['rejeitadas'][0]['motivo']
    assert _r(v, 3)['tipo'] == 'reconstrucao_pendente'                              # documento nunca vira IA
    assert 'documento não se fabrica' in _r(v, 3)['rejeitadas'][0]['motivo']
    assert _r(v, 4)['tipo'] == 'ilustracao_conceitual' and v['cenas'][4]['prompt_imagem'] == 'y'   # cena: IA sinalizada


# ───────── 3. cena documental: a foto real basta ─────────
def test_cena_documental_foto_real_e_evidencia_direta():
    v = _video('curiosidade_factual', [_cena(0, 'Abertura.', 'abertura', foto='t0', relacao='lugar'),
                                       _cena(1, 'A Torre Eiffel tem 330 metros.', '', 'lugar', foto='t0', relacao='lugar')], ACV)
    assert v['cenas'][1]['sb']['necessidade'] == 'documental'
    assert _r(v, 1)['tipo'] == 'evidencia_real' and _r(v, 1)['nivel'] == 'direto'


# ───────── 4. cena contextual: não precisa de esquema ─────────
def test_cena_contextual_aceita_foto_do_tema_sem_esquema():
    v = _video('historico_investigativo', [
        _cena(0, 'Paris vivia o pós-guerra.', 'contexto', 'ambiente', foto='rua', relacao='tema'),
        _cena(1, 'A cidade fervia de golpistas.', 'ligacao')], ACV)
    assert _r(v, 0)['tipo'] == 'contexto' and not _r(v, 0)['pendente']
    assert _r(v, 1)['tipo'] == 'contexto' and _r(v, 1)['midia'] == 'vizinha'      # a montagem continua a anterior
    assert not any(c.get('pendente') for c in v['cenas'])


# ───────── 5. mecanismo sem componente visual disponível ─────────
def _jpg(p: Path):
    from PIL import Image
    Image.new('RGB', (900, 1200), (60, 90, 120)).save(p)
    return p


def test_mecanismo_sem_recurso_fica_pendente_na_montagem_e_vira_p0(tmp_path):
    v = _video('mecanismo', [
        _cena(0, 'O céu fica laranja no fim da tarde.', 'abertura', 'foto', foto='p0', relacao='tema'),
        _cena(1, 'O ar espalha mais a luz azul.', 'mecanismo', 'foto'),                 # nada no acervo
        _cena(2, 'No fim da tarde a luz atravessa mais ar.', 'mecanismo', 'esquema')], ACV)
    assert [_r(v, k)['tipo'] for k in (1, 2)] == ['esquema_pendente'] * 2
    reais = {'c0': {'tipo': 'foto', 'arq': _jpg(tmp_path / 'p0.jpg')}}
    tempos = [(0, 3), (3, 6), (6, 9), (9, 11)]
    cenas = main._montar_cenas({'cenas': v['cenas'], 'titulo': 'Céu'}, reais, {}, tempos, tmp_path)
    pend = [c for c in cenas if c.get('pendente')]
    assert len(pend) == 2 and all(not c.get('img') and not c.get('repetida') for c in pend)   # nada emprestado
    assert aprovacao.midia_de(v['cenas'][1], {}, {})[0] == 'PENDENTE'               # a prévia mostra a pendência
    al = fiscal.alertas(dict(v, fatos='F'), cenas, [], [])
    assert sum(1 for a in al if a['nivel'] == 'P0' and 'esquema pendente' in a['motivo']) == 2
    assert 'ESQUEMA PENDENTE' in resolucao.linha_telegram(cenas)


# ───────── compatibilidade ─────────
def test_roteiro_antigo_sem_storyboard_nao_muda(tmp_path):
    cenas_v = [{'tipo': 'gancho', 'fala': 'a', 'foto': 'a0', 'imagem': 'c0'}, {'tipo': 'historia', 'fala': 'b', 'imagem': 'c1'},
               {'tipo': 'historia', 'fala': 'c', 'foto': 'a1', 'imagem': 'c2'}, {'tipo': 'fechamento', 'fala': 'd'}]
    v = resolucao.resolver({'cenas': cenas_v, 'acervo': []})
    assert not any(c.get('pendente') or c.get('sb') for c in v['cenas'])
    reais = {f'c{k}': {'tipo': 'foto', 'arq': _jpg(tmp_path / f'a{k}.jpg')} for k in (0, 2)}
    cenas = main._montar_cenas({'cenas': v['cenas'], 'titulo': 'T'}, reais, {}, [(0, 3), (3, 6), (6, 9), (9, 11)], tmp_path)
    assert cenas[1].get('img') and cenas[1].get('repetida')                          # vizinha, como sempre


def test_antes_e_depois_da_precedencia():
    """O caso que derrubou o polvo: recurso "foto" numa frase de processo. Antes: mídia preferida = foto; agora: diagrama."""
    c = _cena(1, 'A pele tem cromatóforos, sacos de pigmento.', 'mecanismo', 'foto')
    sbm.construir({'plano': {'modos': ['mecanismo']}, 'cenas': [c]})
    assert c['sb']['necessidade'] == 'processo' and c['sb']['midia_preferida'] == 'diagrama'
    assert sbm.POR_RECURSO['foto'] == 'foto_do_fato'                                 # o que ganhava antes
