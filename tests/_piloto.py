"""Reprodução OFFLINE do piloto real Ever Given (tests/piloto_ever_given): mesmas cenas, mesma voz (tempos), mesmo
acervo. Nenhuma chamada de IA. Usado pelos testes de regressão da correção do piloto."""
import copy
import json
from pathlib import Path

F = Path(__file__).parent / 'piloto_ever_given'


def ler(nome):
    return json.loads((F / nome).read_text(encoding='utf-8'))


def _local(p):
    return str(F / 'img' / Path(str(p)).name) if p else p


def roteiro() -> dict:
    v = ler('roteiro.json')
    ac = ler('acervo.json')
    for x in ac:
        if x.get('arquivo'):
            x['arq'] = str(F / 'img' / x['arquivo'])
    v['acervo'] = ac
    return v


def cenas_v1(v: dict | None = None) -> dict:
    """Cenas V1 do piloto (tempos reais). Com `v` (roteiro depois do preparo), aplica nas cenas o que o fluxo real
    aplicaria em _montar_cenas: acontecimento, foto escolhida (→ arquivo), fonte e crédito."""
    d = ler('v1_cenas_original.json')
    d = copy.deepcopy(d)
    d.setdefault('meta', {})['fontes'] = list((v or ler('roteiro.json')).get('fontes') or [])
    for s in d['scenes']:
        for k in ('img',):
            if s.get(k):
                s[k] = _local(s[k])
    if v is not None:
        por_id = {x['id']: x for x in v['acervo']}
        for s, c in zip(d['scenes'], v['cenas']):
            for k in ('acontecimento', 'fonte', 'valor', 'credito', 'acervo_id', 'tipo'):
                if k in c:
                    s[k] = c[k]
            x = por_id.get(c.get('foto'))
            if x and x.get('arq') and s.get('tipo') != 'revelacao':
                s['img'] = x['arq']; s['real'] = True; s['tipo_img'] = x.get('tipo_img', 'foto')
            elif c.get('foto') is None and c.get('_sem_imagem'):
                s['img'] = None
    return d
