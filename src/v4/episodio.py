"""Orquestrador V4: pedido → roteiro dirigido (IA) → contrato imposto/validado → acervo → narração real → tempos →
render por backend → camada de identidade/legendas → som → MP4 → métricas/engenharia reversa → estado.

Uma tentativa por cena (sem loops caros). Cena que falha no backend fica registrada como FALHA com o log; o episódio
continua (para a auditoria mostrar exatamente o que falhou) e o estado final vira BLOQUEADO. Nunca há aprovação aqui.
"""
from __future__ import annotations

import json
import shutil
import time
import traceback
from pathlib import Path

from src.v4 import acervo_v4, compositor, contrato, diretor, geo, metricas, som
from src.v4.backends import hyperframes as HF
from src.v4.backends import js, legado, rembg_camadas
from src.v4.componentes import COMPONENTES, SELO
from src.v4.util import IDENT, FalhaBackend, normalizar_clipe, sondar

PENDENTE = 'AGUARDANDO_APROVACAO_HUMANA'
BLOQUEADO = 'BLOQUEADO'


def _gravar(arq: Path, obj):
    arq.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding='utf-8')


def render_cena(c: dict, acv: dict, trab: Path, primeira: bool = False) -> tuple[Path, dict]:
    comp, p, dur = c['componente'], c.get('params') or {}, round(c['fim'] - c['ini'], 3)
    pasta = trab / c['id']
    pasta.mkdir(parents=True, exist_ok=True)
    bruto = pasta / 'bruto.mp4'
    a = acv.get(p.get('asset')) if p.get('asset') else None
    t0 = time.time()
    if comp == 'registro.foto':
        if not a:
            raise FalhaBackend('sem asset (acervo não encontrou mídia que mostre o pedido)')
        reg = legado.render_foto(Path(a['arq']), a['wh'], a.get('roi'), {**(c.get('camera') or {}), 'gancho': primeira},
                                 p.get('layout') if p.get('layout') in ('editorial', 'cobrir') else None, f"{a.get('titulo')} {a.get('desc')}",
                                 dur, pasta, bruto, critico=bool(c.get('acao_fisica')))
    elif comp == 'registro.video':
        if not a or not a.get('video'):
            raise FalhaBackend('sem vídeo no acervo')
        reg = legado.render_video(Path(a['arq']), a['wh'], a.get('roi'), float(p.get('inicio') or 0), dur, bruto, pasta)
    elif comp == 'mapa.rota':
        g = geo.preparar(p, pasta)
        props = {**p, 'duracao': dur, 'geo': g}
        if p.get('rota') and not g['meta'].get('rota_km'):
            props['rota'] = None                       # sem geometria real: NÃO se desenha rota (registrado)
        reg = {**js.remotion('MapaRota', props, bruto, pasta), 'geo_meta': g['meta'], 'rota_desenhada': bool(props.get('rota'))}
    elif comp == 'mecanismo.nivel_vasos':
        reg = js.revideo({**p, 'duracao': dur}, bruto, pasta)
    elif comp == 'tresd.camara':
        reg = js.remotion('Camara3D', {**p, 'duracao': dur}, bruto, pasta)
    elif comp == 'tipo.lottie':
        reg = js.remotion('TipoLottie', {'lottie': 'lottie/gota.json', **p, 'duracao': dur}, bruto, pasta)
    elif comp == 'dados.escala':
        reg = js.manim('EscalaAltura', {**p, 'duracao': dur}, bruto, pasta)
    elif comp == 'camadas.recorte':
        if not a:
            raise FalhaBackend('sem foto para recortar')
        rec = rembg_camadas.exigir(Path(a['arq']), pasta / 'recorte.png', pasta / 'rembg')
        reg = {**HF.render_coringa('camadas', p, {'foto': Path(a['arq']), 'recorte': pasta / 'recorte.png'}, dur, pasta, bruto), 'rembg': rec}
    elif comp == 'hf.registro':
        reg = HF.render_registro(p['item'], p.get('variaveis') or {}, dur, pasta, bruto)
    else:
        raise FalhaBackend(f'componente sem despacho: {comp}')
    clipe = normalizar_clipe(bruto, pasta / 'clipe.mp4', dur)
    return clipe, {**reg, 'estado': 'renderizado', 'segundos': round(time.time() - t0, 1), 'saida': sondar(clipe)}


def _camada_props(ep: dict, acv: dict, palavras: list[dict], falhas: set | None = None) -> dict:
    cenas = []
    for c in ep['cenas']:
        if c['id'] in (falhas or set()):
            cenas.append({'ini': c['ini'], 'fim': c['fim'], 'selo': None, 'credito': None})   # cena que falhou: nada a creditar
            continue
        a = acv.get((c.get('params') or {}).get('asset')) if (c.get('params') or {}).get('asset') else None
        selo = SELO.get(c['modalidade'])
        rot = IDENT['selo']['rotulos'].get(selo) if selo else None
        if rot and a and a.get('ano') and c['modalidade'] in ('registro_foto', 'registro_video', 'documento'):
            rot = f"{rot} · {a['ano']}"
        cenas.append({'ini': c['ini'], 'fim': c['fim'], 'selo': rot, 'credito': a.get('credito') if a else None})
    return {'duracao': ep['cenas'][-1]['fim'], 'palavras': palavras, 'cenas': cenas}


def produzir(pedido: dict, pasta: Path, trab: Path) -> dict:
    # ABSOLUTOS: os backends rodam com outro diretório de trabalho (Remotion, Revideo, geo) — execução 43956541084
    pasta, trab = Path(pasta).resolve(), Path(trab).resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    trab.mkdir(parents=True, exist_ok=True)
    res = {'video_id': pedido['video_id'], 'estado': BLOQUEADO, 'nao_publicado': True, 'etapas': {}, 'bloqueios': [], 'revisoes': []}
    t0 = time.time()
    # 1. direção (uma correção dirigida no máximo)
    rot = diretor.pedir(pedido)
    _gravar(pasta / 'roteiro_ia_1.json', rot)
    ep = diretor.esqueleto(rot, pedido)
    impostas = contrato.impor(ep)
    viol = [v for v in contrato.validar(ep) if v['gravidade'] == 'erro' and not v['regra'].startswith('R-ASSET')]
    if viol:
        rot = diretor.pedir(pedido, viol, rot)
        _gravar(pasta / 'roteiro_ia_2.json', rot)
        ep = diretor.esqueleto(rot, pedido)
        impostas += contrato.impor(ep)
    res['etapas']['direcao'] = {'correcao_dirigida': bool(viol), 'violacoes_1a': viol, 'correcoes_impostas': impostas}
    # 2. acervo
    acv, reg_acv = acervo_v4.montar(ep, trab / 'acervo')
    res['etapas']['acervo'] = reg_acv
    # 3. narração real e tempos
    from src import voz
    wav, tempos, caps, dur = voz.narrar([{'fala': c['fala']} for c in ep['cenas']], trab / 'voz')
    for c, (a, b) in zip(ep['cenas'], tempos):
        c['ini'], c['fim'] = round(a, 3), round(b, 3)
        c['params'] = diretor.segundos(c.get('params') or {}, c['fim'] - c['ini'])
    palavras = []
    for bl in caps:
        ws = bl['words']
        for k, w in enumerate(ws):
            fim = ws[k + 1]['s'] if k + 1 < len(ws) else bl['end']
            palavras.append({'w': w['w'], 's': w['s'], 'e': round(fim, 3), 'hl': bool(w.get('hl'))})
    res['etapas']['narracao'] = {'duracao': dur, 'palavras': len(palavras)}
    # 4. contrato final (com acervo)
    viol_final = contrato.validar(ep, acv)
    res['contrato'] = {'violacoes': viol_final, 'familias': contrato.familias(ep)}
    _gravar(pasta / 'episodio.json', ep)
    erro_cena = {v['cena'] for v in viol_final if v['gravidade'] == 'erro' and v['cena']}
    # 5. render por cena
    regs, clipes = [], []
    for i, c in enumerate(ep['cenas']):
        try:
            clipe, r = render_cena(c, acv, trab / 'cenas', primeira=i == 0)
        except Exception as e:
            r = {'backend': COMPONENTES.get(c['componente'], {}).get('backend'), 'estado': 'falhou', 'erro': str(e)[-1200:],
                 'trace': traceback.format_exc()[-800:]}
            clipe = trab / 'cenas' / c['id'] / 'falha.mp4'
            clipe.parent.mkdir(parents=True, exist_ok=True)
            # cena que falhou ocupa o tempo com quadro PRETO + aviso na auditoria (não é disfarçada de conteúdo)
            from src.v4.util import rodar
            rodar(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f"color=c=black:s=1080x1920:r=30:d={c['fim'] - c['ini']:.3f}", '-pix_fmt', 'yuv420p', clipe])
            res['bloqueios'].append(f"cena {c['id']} ({c['componente']}) falhou no backend: {str(e)[:200]}")
        if c['id'] in erro_cena:
            r['violacoes_contrato'] = [v for v in viol_final if v['cena'] == c['id']]
            res['bloqueios'].append(f"cena {c['id']}: " + '; '.join(v['regra'] for v in r['violacoes_contrato'] if v['gravidade'] == 'erro'))
        regs.append(r)
        clipes.append({'arq': clipe, 'dur': round(c['fim'] - c['ini'], 3), 'transicao': c.get('transicao')})
    lt = compositor.linha_do_tempo(ep, regs, pasta / 'linha_do_tempo.json')
    # 6. composição: vídeo, camada de identidade, som
    video = compositor.concatenar(clipes, trab, trab / 'video.mp4')
    camada = trab / 'camada.webm'
    try:
        reg_cam = js.remotion('Camada', _camada_props(ep, acv, palavras, {c['id'] for c, r in zip(ep['cenas'], regs) if r.get('estado') == 'falhou'}), camada, trab / 'camada', alfa=True)
    except Exception as e:
        camada, reg_cam = None, {'erro': str(e)[-600:]}
        res['bloqueios'].append('camada de identidade/legendas falhou: ' + str(e)[:160])
    sfx = []
    for c in ep['cenas']:
        for s in c.get('sfx') or []:
            if s.get('id') in som.SFX:
                sfx.append({'id': s['id'], 't': c['ini'] + float(s.get('em', 0)) * (c['fim'] - c['ini']), 'justificativa': s.get('justificativa'), 'cena': c['id']})
    musicas = sorted((Path(__file__).resolve().parents[2] / 'assets' / 'musica' / 'explica').glob('*.mp3'))
    musica = musicas[hash(pedido['video_id']) % len(musicas)] if musicas else None
    master = trab / 'master.wav'
    reg_som = som.mixar(Path(wav), ep['cenas'][-1]['fim'], sfx, musica, trab / 'som', master)
    mp4 = pasta / f"{pedido['video_id']}.mp4"
    info = compositor.final(video, camada, master, mp4, trab)
    res['etapas']['composicao'] = {'camada': reg_cam, 'som': reg_som, 'final': info}
    # 7. métricas + folha + revisão multimodal
    m = metricas.medir(mp4, lt)
    metricas.salvar(m, pasta / 'metricas.json')
    metricas.folha_de_contato(mp4, lt, pasta / 'folha_contato.jpg')
    res['metricas_resumo'] = m['resumo']
    res['audio'] = m['audio']
    res['revisao_multimodal'] = _revisao(mp4, ep, lt, pasta)
    m = metricas.combinar_revisao(m, res['revisao_multimodal'])
    metricas.salvar(m, pasta / 'metricas.json')
    res['metricas_resumo'] = m['resumo']
    a = m['audio']
    if a.get('lufs') is not None and abs(a['lufs'] - IDENT['som']['lufs']) > 1.0:
        res['revisoes'].append(f"áudio {a['lufs']} LUFS (alvo −14)")
    if a.get('pico') is not None and a['pico'] > IDENT['som']['true_peak'] + .3:
        res['revisoes'].append(f"pico {a['pico']} dBTP (> −1)")
    res['mp4'] = str(mp4)
    res['segundos'] = round(time.time() - t0, 1)
    res['estado'] = BLOQUEADO if res['bloqueios'] else PENDENTE
    _gravar(pasta / 'resultado.json', res)
    return res


def _revisao(mp4: Path, ep: dict, lt: list[dict], pasta: Path) -> dict:
    """revisão semântica por tira de quadros (Gemini, cota grátis). Falhou → PENDENTE (nunca aprovado por omissão)"""
    import os
    if not os.getenv('GEMINI_API_KEY'):
        return {'estado': 'PENDENTE', 'motivo': 'sem modelo de visão'}
    try:
        from src.gemini import json_visao
        from src.v3 import revisao_multimodal as RM
        dados = {'scenes': [{'start': c['ini'], 'end': c['fim'], 'fala': c['fala'], 'direcao': {'evento_id': c['id']}} for c in ep['cenas']]}
        fichas = [{'evento_id': c['id'], 'tipo': c['modalidade'], 'critico': bool(c.get('acao_fisica')),
                   'representacao_necessaria': c.get('o_que_precisa_aparecer'), 'criterio_visual': c.get('objetivo')} for c in ep['cenas']]
        def visao(pr, ims):                        # o Gemini às vezes devolve [ {...} ]: usa o 1º objeto; senão não revisado
            v = json_visao(pr, ims, leve=False)
            if isinstance(v, list):
                v = next((x for x in v if isinstance(x, dict)), {'_nao_revisado': 'resposta do modelo em lista vazia'})
            return v if isinstance(v, dict) else {'_nao_revisado': f'resposta do modelo não é objeto: {type(v).__name__}'}
        r = RM.revisar(mp4, dados, fichas, visao, pasta / 'revisao_multimodal')
        nao = [p for p in r['planos'] if '_nao_revisado' in (p['veredito'] or {})]
        return {'estado': 'PENDENTE' if nao else 'FEITA', 'chamadas': r['chamadas'], 'achados': r['achados'], 'nao_revisados': len(nao),
                'planos': r['planos']}
    except Exception as e:
        return {'estado': 'PENDENTE', 'motivo': f'{type(e).__name__}: {str(e)[:160]}'}
