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

from src.v4 import acervo_v4, compositor, contrato, diretor, geo, metricas, portoes, prerender, som, viabilidade
from src.v4.backends import hyperframes as HF
from src.v4.backends import js, legado, rembg_camadas
from src.v4.componentes import ALTERNATIVAS, COMPONENTES, DEMONSTRAM_ACAO, SELO
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
            # a cena PROMETE uma rota e não há geometria real: mapa sem rota é decorativo (auditoria 16/11, c2) → não pronta
            raise FalhaBackend('rota pedida sem geometria real (OSM): ' + str(g['meta'].get('rota_motivo_ausente')))
        reg = {**js.remotion('MapaRota', props, bruto, pasta), 'geo_meta': g['meta'], 'rota_desenhada': bool(props.get('rota'))}
    elif comp == 'mecanismo.eclusa':
        q = dict(p)
        if q.get('tempos') and all(isinstance(x, (int, float)) and 0 <= x <= 1.0001 for x in q['tempos']):
            q['tempos'] = [round(x * dur, 2) for x in q['tempos']]          # frações da cena → segundos (lista)
        q['v4'] = True                                  # identidade V4: sem cabeçalho próprio, nota fora da legenda
        reg = legado.render_v2('mecanismo.eclusa', q, dur, pasta / 'v2', bruto, c.get('fala', ''))
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


def render_validado(c: dict, acv: dict, trab: Path, primeira: bool = False) -> tuple[Path | None, dict]:
    """componente pedido → alternativas pré-validadas. Cada clipe passa pelos portões (tamanho, duração, não preto,
    mudança visual quando a cena promete ação). Devolve (clipe, registro) ou (None, registro com os motivos)."""
    exige = c['modalidade'] in DEMONSTRAM_ACAO or bool(c.get('acao_fisica'))
    dur = round(c['fim'] - c['ini'], 3)
    cadeia = [(c['componente'], None)] + ALTERNATIVAS.get(c['componente'], [])
    tentativas = []
    for k, (comp, traduz) in enumerate(cadeia):
        cc = dict(c, id=c['id'] if not k else f"{c['id']}_alt{k}", componente=comp,
                  params=traduz({**(c.get('params') or {}), 'duracao': dur}) if traduz else c.get('params'))
        try:
            clipe, r = render_cena(cc, acv, trab, primeira=primeira)
        except Exception as e:
            tentativas.append({'componente': comp, 'estado': 'falhou', 'erro': str(e)[-900:], 'trace': traceback.format_exc()[-600:]})
            continue
        v = portoes.validar_clipe(clipe, dur, exige)
        tentativas.append({'componente': comp, 'estado': 'renderizado' if v['ok'] else 'reprovado_portao', 'motivos': v['motivos'],
                           'backend': r.get('backend')})
        if v['ok']:
            if k:
                c['componente_usado'] = comp
                c['params_usados'] = cc['params']
            return clipe, {**r, 'componente_usado': comp, 'alternativa': bool(k), 'tentativas': tentativas}
    motivos = [f"{t['componente']}: " + ('; '.join(t.get('motivos') or []) or str(t.get('erro', ''))[-240:]) for t in tentativas]
    return None, {'backend': COMPONENTES.get(c['componente'], {}).get('backend'), 'estado': 'nao_pronta', 'motivos': motivos, 'tentativas': tentativas}


def clipe_diagnostico(c: dict, motivo: str, trab: Path) -> Path:
    """cena NÃO pronta: placa explícita de diagnóstico (nunca tela preta disfarçada de conteúdo). O MP4 inteiro vira
    material de DIAGNÓSTICO, não episódio."""
    from src.v4.util import rodar
    pasta = trab / 'cenas' / c['id']
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / 'diagnostico.mp4'
    dur = c['fim'] - c['ini']
    fonte = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    txt = f"CENA {c['id']} NAO RENDERIZADA\nDIAGNOSTICO - NAO E EPISODIO\n{c['componente']}"
    vf = f"drawtext=fontfile={fonte}:text='{txt}':fontcolor=white:fontsize=46:x=(w-text_w)/2:y=700:line_spacing=18" if Path(fonte).exists() else 'null'
    rodar(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f"color=c=0x5a1010:s=1080x1920:r=30:d={dur:.3f}", '-vf', vf,
           '-pix_fmt', 'yuv420p', arq])
    (pasta / 'motivo.txt').write_text(motivo, encoding='utf-8')
    return arq


def texto_repete_fala(c: dict, limite: float = .7) -> bool:
    """o componente já ESCREVE a fala na tela (tipografia/linhas): legenda por cima = a mesma frase duas vezes
    (auditoria 16/11, c9). A legenda some só nessa cena; o texto do componente é a leitura."""
    import re
    p = c.get('params_usados') or c.get('params') or {}
    na_tela = ' '.join(str(x.get('texto', '')) for x in p.get('linhas') or [] if isinstance(x, dict))
    if not na_tela:
        return False
    fala = set(re.findall(r'\w+', str(c.get('fala', '')).lower()))
    tela = set(re.findall(r'\w+', na_tela.lower()))
    # medido sobre o TEXTO DA TELA: se quase tudo que está escrito é dito no mesmo momento, a legenda duplica a leitura
    return bool(tela) and len(fala & tela) / len(tela) >= limite


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
        cenas.append({'ini': c['ini'], 'fim': c['fim'], 'selo': rot, 'credito': a.get('credito') if a else None,
                      'legenda': not texto_repete_fala(c)})
    return {'duracao': ep['cenas'][-1]['fim'], 'palavras': palavras, 'cenas': cenas}


def carregar_narracao(pedido: dict, ep: dict) -> dict | None:
    """narração já gravada (cifrada no repositório) — só se as falas forem EXATAMENTE as mesmas"""
    if not pedido.get('narracao_cifrada'):
        return None
    from src.v3 import material
    arq = Path(__file__).resolve().parents[2] / pedido['narracao_cifrada']
    try:
        n = json.loads(material.decifrar(material._segredo(), arq.read_bytes()))
    except Exception as e:
        print(f'  [narração] pacote não decifrou ({str(e)[:80]}): TTS normal', flush=True)
        return None
    if n.get('falas_hash') != prerender.hash_falas(ep['cenas']) or len(n.get('tempos') or []) != len(ep['cenas']):
        print('  [narração] falas diferentes do pacote: TTS normal', flush=True)
        return None
    return n


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
    # 1b. VIABILIDADE do acervo ANTES de fechar o storyboard (17/11): registro sem mídia comprovada troca de forma por regra
    ep, viab = viabilidade.resolver(ep, pedido)
    viol = [v for v in contrato.validar(ep) if v['gravidade'] == 'erro' and not v['regra'].startswith('R-ASSET')]
    if viol:
        rot = diretor.pedir(pedido, viol, rot)
        _gravar(pasta / 'roteiro_ia_2.json', rot)
        ep = diretor.esqueleto(rot, pedido)
        impostas += contrato.impor(ep)
        ep, viab = viabilidade.resolver(ep, pedido)
    res['etapas']['direcao'] = {'correcao_dirigida': bool(viol), 'violacoes_1a': viol, 'correcoes_impostas': impostas}
    res['etapas']['viabilidade'] = viab
    # 2. narração (reutilizada quando as falas são as mesmas) e tempos
    narr = carregar_narracao(pedido, ep)
    if narr:
        wav = trab / 'voz' / 'voz.wav'
        wav.parent.mkdir(parents=True, exist_ok=True)
        import base64
        flac = wav.with_suffix('.flac')
        flac.write_bytes(base64.b64decode(narr['flac_b64']))
        from src.v4.util import rodar
        rodar(['ffmpeg', '-v', 'error', '-y', '-i', flac, '-ar', '48000', wav])
        tempos, palavras, dur = narr['tempos'], narr['palavras'], narr['duracao']
    else:
        from src import voz
        wav, tempos, caps, dur = voz.narrar([{'fala': c['fala']} for c in ep['cenas']], trab / 'voz')
        palavras = []
        for bl in caps:
            ws = bl['words']
            for k, w in enumerate(ws):
                fim = ws[k + 1]['s'] if k + 1 < len(ws) else bl['end']
                palavras.append({'w': w['w'], 's': w['s'], 'e': round(fim, 3), 'hl': bool(w.get('hl'))})
    for c, (a, b) in zip(ep['cenas'], tempos):
        c['ini'], c['fim'] = round(a, 3), round(b, 3)
        c['params'] = diretor.segundos(c.get('params') or {}, c['fim'] - c['ini'])
    res['etapas']['narracao'] = {'duracao': dur, 'palavras': len(palavras), 'reutilizada': (narr or {}).get('origem')}
    # 3. PRÉ-RENDER obrigatório: nenhuma cena pode estar destinada a virar placa de diagnóstico
    pre = prerender.verificar(ep, pedido, narr, trab / 'prerender')
    res['prerender'] = pre
    _gravar(pasta / 'prerender.json', pre)
    if not pre['pronto']:
        res['bloqueios'].append('PRÉ-RENDER não pronto: ' + '; '.join(pre['gerais'] + [f"{x['cena']}: {x['problemas'][0]}" for x in pre['cenas'] if x['problemas']])[:900])
        res['estado'] = 'BLOQUEADO_PRE_RENDER'
        _gravar(pasta / 'episodio.json', ep)
        _gravar(pasta / 'resultado.json', res)
        return res
    # 4. acervo: itens comprovados da biblioteca (+ busca nova, com falha fechada, só se o pedido permitir)
    acv = viabilidade.acervo_da_biblioteca(ep, trab / 'acervo')
    reg_acv = [{'cena': r['cena'], 'estado': 'biblioteca', 'asset': r.get('asset')} for r in viab if r.get('asset')]
    if pedido.get('buscar_novas'):
        mais, reg2 = acervo_v4.montar(ep, trab / 'acervo')
        acv.update(mais)
        reg_acv += reg2
    res['etapas']['acervo'] = reg_acv
    # 5. contrato final (com acervo)
    viol_final = contrato.validar(ep, acv)
    res['contrato'] = {'violacoes': viol_final, 'familias': contrato.familias(ep)}
    _gravar(pasta / 'episodio.json', ep)
    erro_cena = {v['cena'] for v in viol_final if v['gravidade'] == 'erro' and v['cena']}
    # 5. render por cena
    regs, clipes = [], []
    for i, c in enumerate(ep['cenas']):
        erros = [v for v in viol_final if v['cena'] == c['id'] and v['gravidade'] == 'erro']
        if any(v['regra'].startswith('R-ASSET') for v in erros):
            # mídia sem licença/ausente NÃO vai ao render (auditoria 16/11: c5 foi renderizada antes do bloqueio)
            r = {'backend': COMPONENTES.get(c['componente'], {}).get('backend'), 'estado': 'nao_pronta',
                 'motivos': [f"{v['regra']}: {v['texto']}" for v in erros]}
            clipe = None
        else:
            clipe, r = render_validado(c, acv, trab / 'cenas', primeira=i == 0)
        if erros:
            r['violacoes_contrato'] = erros
            res['bloqueios'].append(f"cena {c['id']}: " + '; '.join(v['regra'] for v in erros))
        if clipe is None:
            clipe = clipe_diagnostico(c, '; '.join(r.get('motivos') or []), trab)
        regs.append(r)
        clipes.append({'arq': clipe, 'dur': round(c['fim'] - c['ini'], 3), 'transicao': c.get('transicao')})
        # resumo no LOG do Actions (sem segredos): a execução 43986419846 virou diagnóstico e o log não dizia qual cena
        print(f"  [cena {c['id']}] {c['modalidade']} → {r.get('componente_usado') or c['componente']}: {r.get('estado')}"
              + (f" | {' || '.join(r.get('motivos') or [])[:600]}" if r.get('estado') != 'renderizado' else ''), flush=True)
    lt = compositor.linha_do_tempo(ep, regs, pasta / 'linha_do_tempo.json')
    # 6. composição: vídeo, camada de identidade, som
    video = compositor.concatenar(clipes, trab, trab / 'video.mp4')
    camada = trab / 'camada.webm'
    try:
        reg_cam = js.remotion('Camada', _camada_props(ep, acv, palavras, {c['id'] for c, r in zip(ep['cenas'], regs) if r.get('estado') != 'renderizado'}), camada, trab / 'camada', alfa=True)
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
    g = portoes.decidir(ep['cenas'], regs, res['revisao_multimodal'], m['por_cena'])
    res['portoes'] = g
    res['bloqueios'] += g['bloqueios']
    res['revisoes'] += g['revisoes']
    if g['estado'] == portoes.DIAGNOSTICO:
        diag = mp4.with_name(mp4.stem + '_DIAGNOSTICO.mp4')
        mp4.replace(diag)
        mp4 = diag
    res['mp4'] = str(mp4)
    res['segundos'] = round(time.time() - t0, 1)
    res['estado'] = g['estado'] if g['estado'] == portoes.DIAGNOSTICO else (BLOQUEADO if res['bloqueios'] else PENDENTE)
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
