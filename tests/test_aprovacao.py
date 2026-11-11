"""APROVAÇÃO NO TELEGRAM: nada é montado sem OK. Telegram falso (nenhuma mensagem de verdade é enviada)."""
import json
from pathlib import Path

import pytest

from src import aprovacao


def _jpg(arq: Path, cor=(120, 90, 60)) -> str:
    from PIL import Image
    Image.new('RGB', (800, 600), cor).save(arq, 'JPEG')
    return str(arq)


def _video(tmp_path: Path):
    """Roteiro com 5 frases, acervo com 7 itens (5 usados + 2 reservas: A e B)."""
    acervo = [{'id': f'a{k}', 'arq': _jpg(tmp_path / f'a{k}.jpg', (40 * k, 80, 120)), 'mostra': f'foto {k}', 'nota': 9 - k}
              for k in range(7)]
    acervo[6]['video'] = {'url': 'https://x/v.mp4', 'w': 1920, 'h': 1080}
    cenas = [{'tipo': 'gancho' if k == 0 else 'historia', 'fala': f'Frase *{k + 1}* com 1915', 'imagem': f'i{k}',
              'foto': f'a{k}', 'titulo': 'TÍTULO *TESTE*' if k == 0 else None} for k in range(5)]
    cenas.append({'tipo': 'fechamento', 'fala': 'Segue o Coringa', 'imagem': 'i9'})
    v = {'titulo': 'Teste', 'cenas': cenas, 'acervo': acervo, '_reserva': []}
    reais = {f'i{k}': {'tipo': 'foto', 'arq': acervo[k]['arq']} for k in range(5)}
    return v, reais, {}


class TelegramFalso:
    """Faz o papel do bot: guarda o que foi enviado e entrega as 'respostas' roteirizadas."""
    def __init__(self, respostas, erro_base=None):
        self.respostas, self.enviados, self.chave, self.erro_base, self.uid = list(respostas), [], None, erro_base, 100

    def __call__(self, metodo, arquivo=None, **d):
        if metodo == 'getUpdates':
            if d.get('offset') == -1:
                if self.erro_base:
                    raise RuntimeError(self.erro_base)
                return [{'update_id': 99}]
            if not self.respostas:
                return []
            r = self.respostas.pop(0)
            self.uid += 1
            if r.startswith('botao:'):
                acao, _, ch = r[6:].partition(':')
                return [{'update_id': self.uid, 'callback_query': {'id': 'x', 'data': f'{acao}:{ch or self.chave}',
                                                                   'message': {'chat': {'id': 123}}}}]
            return [{'update_id': self.uid, 'message': {'chat': {'id': 123}, 'text': r, 'message_id': 5}}]
        if metodo == 'sendMessage' and d.get('reply_markup'):
            self.chave = d['reply_markup']['inline_keyboard'][0][0]['callback_data'].split(':')[1]
        self.enviados.append((metodo, d.get('text') or d.get('caption') or '', arquivo))
        return {'message_id': len(self.enviados)}


@pytest.fixture
def bot(monkeypatch):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'x')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '123')
    def fazer(respostas, **kw):
        tg = TelegramFalso(respostas, **kw)
        monkeypatch.setattr(aprovacao, '_api', tg)
        return tg
    return fazer


@pytest.mark.parametrize('txt,esperado', [
    ('ok', ('ok', {})), ('OK!', ('ok', {})), ('/ok@coringa_bot', ('ok', {})), ('Sim', ('ok', {})), ('monta', ('ok', {})),
    ('outro tema', ('outro', {})), ('não', ('outro', {})),
    ('3=B', ('trocar', {3: 'B'})), ('3=b 7 = a', ('trocar', {3: 'B', 7: 'A'})), ('2:c', ('trocar', {2: 'C'})),
    ('trocar 3 7', ('trocar', {3: None, 7: None})), ('troca 4, 5 e 6', ('trocar', {4: None, 5: None, 6: None})),
    ('que vídeo legal', None), ('', None),
])
def test_interpretar(txt, esperado):
    assert aprovacao.interpretar(txt) == esperado


def test_previa_mostra_frases_e_reservas(tmp_path):
    from PIL import Image
    import io
    v, reais, imgs = _video(tmp_path)
    im = Image.open(io.BytesIO(aprovacao.desenhar(v, reais, imgs)))
    assert im.width == 1260 and im.height > 900
    assert [x['id'] for x in aprovacao.reservas(v)] == ['a6', 'a5']     # clipe (a6) vem primeiro
    assert '1. Frase 1 com 1915' in aprovacao.texto(v) and 'Segue o Coringa' not in aprovacao.texto(v) and 'FINAL: Segue o @coringa.explica' in aprovacao.texto(v)


def test_aviso_de_modelo_reserva_ia_e_repeticao(tmp_path):
    v, reais, imgs = _video(tmp_path)
    v['_reserva'] = ['Groq', 'Groq']
    del reais['i4']
    imgs['i3'] = reais.pop('i3')['arq']
    av = ' | '.join(aprovacao.avisos(v, reais, imgs))
    assert 'modelo reserva (Groq)' in av and '1 imagem(ns) de IA' in av and '🎨' not in av and '1 frase(s) sem imagem própria' in av


def test_botao_montar_aprova(bot, tmp_path):
    tg = bot(['botao:ok'])
    v, reais, imgs = _video(tmp_path)
    assert aprovacao.aprovar(v, reais, imgs, None, minutos=1) == 'ok'
    assert [m for m, _, _ in tg.enviados][:2] == ['sendPhoto', 'sendMessage']


def test_botao_de_previa_antiga_nao_vale(bot, tmp_path):
    bot(['botao:ok:123456', 'botao:outro'])            # 1º clique é de uma prévia de outro dia
    v, reais, imgs = _video(tmp_path)
    assert aprovacao.aprovar(v, reais, imgs, None, minutos=1) == 'outro'


def test_trocar_pela_reserva_e_depois_aprovar(bot, tmp_path):
    tg = bot(['3=A', 'ok'])                          # A = o clipe (reservas: clipes primeiro)
    v, reais, imgs = _video(tmp_path)
    usados = []
    def midia_de_item(x):
        usados.append(x['id'])
        return {'tipo': 'video', 'arq': '/tmp/v.mp4', 'thumb': x['arq'], 'w': 1920, 'h': 1080}
    assert aprovacao.aprovar(v, reais, imgs, midia_de_item, minutos=1) == 'ok'
    assert usados == ['a6'] and v['cenas'][2]['foto'] == 'a6' and reais['i2']['tipo'] == 'video'
    assert sum(1 for m, _, _ in tg.enviados if m == 'sendPhoto') == 2       # mandou a prévia nova depois da troca


def test_trocar_sem_letra_usa_a_melhor_reserva(bot, tmp_path):
    bot(['trocar 2', 'ok'])
    v, reais, imgs = _video(tmp_path)
    aprovacao.aprovar(v, reais, imgs, lambda x: {'tipo': 'foto', 'arq': x['arq']}, minutos=1)
    assert v['cenas'][1]['foto'] == 'a6'                # a melhor reserva é o clipe


def test_sem_resposta_nao_monta(bot, tmp_path):
    tg = bot([])
    v, reais, imgs = _video(tmp_path)
    assert aprovacao.aprovar(v, reais, imgs, None, minutos=0.02) == 'sem_resposta'
    assert 'NÃO montei' in tg.enviados[-1][1]


def test_telegram_fora_do_ar_segue_sem_aprovacao(bot, tmp_path):
    bot([], erro_base='getUpdates: 409 Conflict: webhook is active')
    v, reais, imgs = _video(tmp_path)
    assert aprovacao.aprovar(v, reais, imgs, None, minutos=1) == 'indisponivel'


def test_sem_telegram_configurado(monkeypatch, tmp_path):
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
    v, reais, imgs = _video(tmp_path)
    assert aprovacao.aprovar(v, reais, imgs, None, minutos=1) == 'indisponivel'


def test_roteiro_do_modelo_reserva_fica_registrado(monkeypatch):
    from src import gemini
    gemini.RESERVAS_USADAS.clear()
    def sem_cota(*a, **k):
        raise RuntimeError('503')
    monkeypatch.setattr(gemini, '_tentar', sem_cota)
    monkeypatch.setattr(gemini, '_groq', lambda p, j: json.dumps({'ok': 1}))
    assert gemini._em_cascata(lambda m: None, 'p', True, leve=False) == {'ok': 1}
    assert gemini.RESERVAS_USADAS == ['Groq']


def test_gancho_nunca_e_imagem_de_ia():
    from src import roteiro
    v = {'cenas': [{'tipo': 'gancho', 'fala': 'a', 'cenario': 'desert'}] +
                  [{'tipo': 'historia', 'fala': f'f{k}', 'foto': f'a{k}'} for k in range(6)]}
    roteiro._planos_sem_foto(v, '')
    assert v['cenas'][0]['midia'] == 'vizinha'


def test_montar_video_pede_aprovacao_antes_da_voz():
    import inspect
    import main
    fonte = inspect.getsource(main.montar_video)
    assert fonte.index('aprovacao.aprovar') < fonte.index('voz.narrar')
    assert "r == 'sem_resposta'" in fonte and "r == 'outro'" in fonte


def test_resposta_em_canal_tambem_vale(bot, tmp_path, monkeypatch):
    tg = bot([])
    v, reais, imgs = _video(tmp_path)
    original = tg.__call__
    entregue = []
    def com_canal(metodo, arquivo=None, **d):
        if metodo == 'getUpdates' and d.get('offset') != -1 and not entregue:
            entregue.append(1)
            return [{'update_id': 500, 'channel_post': {'chat': {'id': 123}, 'text': 'ok', 'message_id': 9}}]
        return original(metodo, arquivo, **d)
    monkeypatch.setattr(aprovacao, '_api', com_canal)
    assert aprovacao.aprovar(v, reais, imgs, None, minutos=1) == 'ok'
