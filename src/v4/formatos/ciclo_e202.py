"""E202 — ciclo completo e reprodutível por caso: direção → narração → render → quadros → revisão → 1 correção.

Usado igual no Actions (com provedores do projeto) e localmente (só cache e duração medida gravada). Cada etapa
registra o que aconteceu; nada vira "aprovado": o MP4 privado espera o Heitor.

  python -m src.v4.formatos.ciclo_e202 <entrada.json> <saida/> [--caso id] [--sem-ia] [--sem-voz] [--sem-visao]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from src.v4.formatos import cena_declarativa_e202 as CD
from src.v4.formatos import diretor_visual_e202 as D

RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / 'motor4'
NARRACOES = RAIZ / 'benchmarks/e202/narracao'


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _falas(plano: dict) -> list[str]:
    cena = next(c for c in plano['cenas'] if c.get('modalidade') == 'cena_declarativa')
    return [str(b['fala']) for b in cena['beats']]


def narrar(plano: dict, caso_id: str, pasta: Path, usar_voz: bool) -> dict:
    """Voz do projeto (src.voz: Gemini TTS configurado → Edge se faltar). Tempos por beat e palavras medidas.
    Os TEMPOS (não o áudio) são gravados por hash das falas, para a reprodução local ter os mesmos quadros."""
    falas = _falas(plano)
    chave = hashlib.sha256('\n'.join(falas).encode()).hexdigest()[:16]
    salvo = NARRACOES / f'{caso_id}-{chave}.json'
    if not usar_voz:
        if salvo.exists():
            n = json.loads(salvo.read_text(encoding='utf8'))
            return {**n, 'audio': None, 'origem': 'tempos_medidos_gravados_sem_audio_local'}
        cena = next(c for c in plano['cenas'] if c.get('modalidade') == 'cena_declarativa')
        return {'duracoes': D.estimar_duracoes(cena), 'palavras': None, 'audio': None, 'origem': 'ESTIMADA_SEM_VOZ'}
    from src import voz
    pasta.mkdir(parents=True, exist_ok=True)
    wav, tempos, caps, dur = voz.narrar([{'fala': f} for f in falas], pasta)
    motor = 'gemini_tts' if list(pasta.glob('gemini*.wav')) else 'edge_tts'
    duracoes = [round(tempos[0][1], 4)] + [round(b - a, 4) for a, b in tempos[1:]]
    pal = D.palavras_de_caps(caps)
    pub = MOTOR / 'remotion/public/e202'
    pub.mkdir(parents=True, exist_ok=True)
    final = pasta / 'narracao48k.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-ar', '48000', '-ac', '1', str(final)], check=True)
    h = _sha(final)
    shutil.copyfile(final, pub / f'{h}.wav')
    n = {'caso': caso_id, 'falas_sha16': chave, 'duracoes': duracoes, 'palavras': pal, 'duracao_audio': round(float(dur), 3),
         'motor_voz': motor, 'audio_sha256': h}
    NARRACOES.mkdir(parents=True, exist_ok=True)
    salvo.write_text(json.dumps(n, ensure_ascii=False) + '\n', encoding='utf8')
    return {**n, 'audio': f'e202/{h}.wav', 'origem': motor}


def renderizar(props: dict, mp4: Path) -> None:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    pj = mp4.with_suffix('.props.json')
    pj.write_text(json.dumps(props, ensure_ascii=False), encoding='utf8')
    cmd = ['npx', '--no-install', 'remotion', 'render', 'remotion/src/index.ts', 'FilmeEditorial', str(mp4.resolve()),
           f'--props={pj.resolve()}', '--codec=h264', '--crf=20', '--concurrency=2', '--public-dir=remotion/public', '--log=error']
    if os.getenv('CORINGA_CHROME_HEADLESS'):
        cmd.append(f"--browser-executable={os.environ['CORINGA_CHROME_HEADLESS']}")
    subprocess.run(cmd, cwd=MOTOR, check=True)


def sondar(mp4: Path) -> dict:
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(mp4)],
                         capture_output=True, text=True, check=True).stdout
    p = json.loads(out)
    v = next(s for s in p['streams'] if s['codec_type'] == 'video')
    a = [s for s in p['streams'] if s['codec_type'] == 'audio']
    return {'largura': v['width'], 'altura': v['height'], 'quadros': int(v.get('nb_frames') or 0),
            'fps': v['r_frame_rate'], 'duracao': float(p['format']['duration']), 'audio': bool(a), 'sha256': _sha(mp4)}


def _rgb(mp4: Path, escala: int = 4):
    import numpy as np
    w, h = 1080 // escala, 1920 // escala
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3), escala


def movimento_no_foco(mp4: Path, sg: dict, fps: int = 30) -> tuple[list[dict], str]:
    """Pixels que mudam DENTRO da caixa de tela dos atores em foco, durante cada beat. Medida de presença de
    movimento no referente — NÃO prova que a ação é compreensível (isso é revisão visual/humana)."""
    import numpy as np
    a, esc = _rgb(mp4)
    sha_rgb = hashlib.sha256(a.tobytes()).hexdigest()
    ts = [b['t'] for b in sg['beats']] + [sg['camera'][-1]['t']]
    out = []
    for k in range(len(sg['beats'])):
        i0, i1 = int(ts[k] * fps), min(len(a) - 1, int(ts[k + 1] * fps))
        t = ts[k] + (ts[k + 1] - ts[k]) * .6
        cam = D._interp(sg['camera'], t, ('x', 'y', 'zoom'))
        xs, ys = [], []
        for at in sg['actors']:
            if at['id'] in (sg['beats'][k].get('foco_ids') or []):
                st = D._interp(at['states'], t, ('x', 'y', 'scale', 'sx', 'sy', 'opacity'))
                x0, y0, x1, y1 = D._tela(at, st, cam)
                xs += [x0, x1]; ys += [y0, y1]
        if not xs or i1 <= i0 + 1:
            out.append({'beat': k + 1, 'pixels': 0, 'caixa': None}); continue
        x0, x1 = max(0, int(min(xs) / esc)), min(a.shape[2], int(max(xs) / esc) + 1)
        y0, y1 = max(0, int(min(ys) / esc)), min(a.shape[1], int(max(ys) / esc) + 1)
        b = a[i0:i1, y0:y1, x0:x1].astype(np.int16)
        n = int((np.abs(b[1:] - b[:-1]).max(axis=3) > 12).any(axis=0).sum()) if b.shape[1] and b.shape[2] else 0
        out.append({'beat': k + 1, 'pixels': n, 'caixa': [x0 * esc, y0 * esc, x1 * esc, y1 * esc]})
    return out, sha_rgb


def quadros_jpg(mp4: Path, tempos: list[float], pasta: Path) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    out = []
    for k, t in enumerate(tempos):
        p = pasta / f'q{k + 1}.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1', '-vf', 'scale=540:960', '-q:v', '3', str(p)], check=True)
        out.append(p)
    return out


def folha(mp4: Path, saida: Path) -> None:
    dur = sondar(mp4)['duracao']          # 8 quadros espalhados pela duração inteira
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf', f'fps=8/{dur:.3f},scale=360:640,tile=4x2', '-frames:v', '1', str(saida)], check=True)


def ciclo(caso: dict, saida: Path, usar_ia: bool, usar_voz: bool, usar_visao: bool) -> dict:
    pasta = saida / caso['id']
    pasta.mkdir(parents=True, exist_ok=True)
    reg = {'caso': caso['id'], 'etapas': {}, 'publicar': False, 'aprovacao_humana': 'PENDENTE'}
    r = D.dirigir(caso, permitir_chamada=usar_ia)
    comp = r.pop('compilado', None) or {}
    reg['direcao'] = {k: r[k] for k in ('estado', 'violacoes_finais', 'alertas_geometria', 'historico', 'chamadas_ia', 'disponibilidade')}
    reg['plano'] = r['plano']
    if r['estado'] != 'PLANO_COMPILADO':
        reg['estado'] = 'BLOQUEADO_DIRECAO'
        return reg
    for rodada in (1, 2):
        n = narrar(r['plano'], caso['id'], pasta / f'voz{rodada}', usar_voz)
        reg['etapas'][f'narracao{rodada}'] = {k: v for k, v in n.items() if k != 'palavras'}
        f = D.filme(r, caso, n['duracoes'], n.get('palavras'), n.get('audio'))
        sg = f['props']['shots'][0]['scene_graph']
        geo = D.geometria(sg)
        mp4 = pasta / f"{caso['id']}_r{rodada}.mp4"
        renderizar(f['props'], mp4)
        info = sondar(mp4)
        mov, sha_rgb = movimento_no_foco(mp4, sg)
        folha(mp4, pasta / f"{caso['id']}_r{rodada}_folha.jpg")
        meios = [b['t'] + (t1 - b['t']) * .6 for b, t1 in zip(sg['beats'], [x['t'] for x in sg['beats'][1:]] + [sg['camera'][-1]['t']])]
        jpgs = quadros_jpg(mp4, meios, pasta / f'quadros_r{rodada}')
        etapa = {'mp4': mp4.name, 'sonda': info, 'sha256_quadros_rgb': sha_rgb, 'movimento_no_foco': mov,
                 'geometria': geo, 'proveniencia': f['proveniencia'], 'contrato_comum': D.auditoria_contrato(f['props'])}
        falhas_auto = [g for g in geo] + [{'regra': 'M-SEM-MOVIMENTO-NO-FOCO', 'texto': f"beat {m['beat']}: {m['pixels']} px"} for m in mov if m['pixels'] < 150]
        if info['duracao'] < 8:
            falhas_auto.append({'regra': 'M-CURTO', 'texto': f"{info['duracao']:.2f}s < 8s"})
        visao = None
        if usar_visao:
            try:
                visao = D.revisao_visual([p.read_bytes() for p in jpgs], caso, r['plano'])
            except Exception as e:
                visao = {'erro': f'{type(e).__name__}: {str(e)[:200]}'}
        etapa['visao_automatica'] = visao
        etapa['falhas_automaticas'] = falhas_auto
        reg['etapas'][f'render{rodada}'] = etapa
        print('E202-RENDER', json.dumps({'caso': caso['id'], 'rodada': rodada, 'sonda': info, 'rgb': sha_rgb,
                                        'mov': [m['pixels'] for m in mov], 'falhas': falhas_auto,
                                        'visao': (visao or {}).get('falhas') if isinstance(visao, dict) else None}, ensure_ascii=False))
        problemas = list(falhas_auto)
        if isinstance(visao, dict) and visao.get('falhas'):
            resp = visao.get('resposta') or {}
            problemas += [{'regra': 'V-REVISAO', 'texto': str(p)[:240]} for p in (resp.get('problemas') or [])[:4]]
            problemas += [{'regra': 'V-CORRECAO', 'texto': json.dumps(c, ensure_ascii=False)[:240]} for c in (resp.get('correcoes') or [])[:4]]
        if rodada == 2 or not problemas:
            reg['estado'] = 'MP4_PRIVADO_GERADO' if not problemas else 'MP4_PRIVADO_COM_DEFEITOS_REGISTRADOS'
            reg['mp4_final'] = mp4.name
            break
        # UMA correção dirigida pelo que foi MEDIDO/VISTO no MP4 real
        disp = D.disponibilidade(caso)
        regs = []
        try:
            plano2 = D.pedir_ia(D.prompt(caso, disp, problemas, r['plano']), regs, permitir_chamada=usar_ia)
        except RuntimeError as e:
            reg['etapas']['correcao'] = {'erro': str(e)[:200], 'problemas': problemas}
            reg['estado'] = 'MP4_PRIVADO_COM_DEFEITOS_REGISTRADOS'; reg['mp4_final'] = mp4.name
            break
        v2, _ = D.verificar(plano2, caso, disp)
        reg['etapas']['correcao'] = {'problemas_enviados': problemas, 'chamadas_ia': regs, 'violacoes_pos': v2}
        if v2:
            reg['estado'] = 'MP4_PRIVADO_COM_DEFEITOS_REGISTRADOS'; reg['mp4_final'] = mp4.name
            break
        r = {**r, 'plano': plano2}
        reg['plano_corrigido'] = plano2
    return reg


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('entrada'); ap.add_argument('saida')
    ap.add_argument('--caso', action='append'); ap.add_argument('--sem-ia', action='store_true')
    ap.add_argument('--sem-voz', action='store_true'); ap.add_argument('--sem-visao', action='store_true')
    a = ap.parse_args(argv)
    ent = json.loads(Path(a.entrada).read_text(encoding='utf8'))
    saida = Path(a.saida)
    resumo = []
    for caso in ent['cases']:
        if a.caso and caso['id'] not in a.caso:
            continue
        try:
            reg = ciclo(caso, saida, not a.sem_ia, not a.sem_voz, not a.sem_visao)
        except Exception as e:
            reg = {'caso': caso['id'], 'estado': 'ERRO', 'erro': f'{type(e).__name__}: {str(e)[:400]}'}
        (saida / f"{caso['id']}_registro.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
        resumo.append({'caso': caso['id'], 'estado': reg.get('estado'), 'mp4': reg.get('mp4_final')})
        print('E202-CASO', json.dumps(resumo[-1], ensure_ascii=False))
    (saida / 'RESUMO.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
    return 0 if all(x['estado'] and x['estado'].startswith('MP4') for x in resumo) else 2


if __name__ == '__main__':
    sys.exit(main())
