"""V2.5 — ENSAIO INTEGRADO do fluxo real, offline (sem IA paga, sem rede): checkpoint → edição auditada → retomada
→ pré-validação → plano visual → preparo → prévia → cobertura → mídia do acervo (main._midia_do_acervo) → cenas
(main._montar_cenas) → montagem V2 → palco/render (piloto.renderizar) → fiscal → limpeza → checkpoint novo.
Só a voz é simulada (tempos por caracteres; áudio de arquivo). Cada falha sai com UMA causa objetiva (`diagnostico`).

Cenários (src/v2/ensaio.py rodar):
  ok          checkpoint íntegro + edição → MP4 sem bloqueio, composição do preparo = composição renderizada
  sem_imagem  uma imagem do acervo apagada do checkpoint → para ANTES da narração (ArquivoCheckpoint), sem MP4
  ia_fora     provedor de IA indisponível com contrato pendente → nada quebra; bloqueio com o que falta
  retomadas   A → B → limpeza pós-vídeo → C: as imagens continuam (o defeito de 43740293581)
Uso: python -m src.v2.ensaio <checkpoint_com_imagens> <edicao.json> <pasta_saida> [cenario]
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _sem_ia(prompt):
    raise RuntimeError('provedor de IA indisponível (simulado)')


def _diag(etapa: str, causa: str, **extra) -> dict:
    return {'ok': False, 'etapa': etapa, 'diagnostico': f'{etapa}: {causa}', **extra}


def executar(origem: Path, edicao: dict | None, saida: Path, render: bool = True, apagar_imagem: str | None = None,
             chamar=_sem_ia, audio: Path | None = None) -> dict:
    import main
    from src.v2 import checkpoint, cobertura, piloto, planejamento, preparo, prevalidacao, previa
    saida = Path(saida)
    shutil.rmtree(saida, ignore_errors=True)
    saida.mkdir(parents=True)
    orig = saida / 'checkpoint_origem'
    shutil.copytree(origem, orig)
    if apagar_imagem:
        next((orig / 'arquivos').glob(f'{apagar_imagem}_*')).unlink()
    v_erros = checkpoint.verificar_arquivos(orig)['erros']
    if v_erros:
        return _diag('verificação do checkpoint', '; '.join(v_erros[:3]))
    if edicao:
        checkpoint.editar(orig, edicao)
    try:
        ck = checkpoint.Checkpoint(saida / 'checkpoint', orig, 'roteiro')
        v = ck.carregar('roteiro')['v']
    except checkpoint.ArquivoCheckpoint as e:
        return _diag('retomada', str(e))
    try:
        rc = prevalidacao.reparar(v, chamar=chamar)
    except Exception as e:
        return _diag('pré-validação', f'falha não tratada do provedor: {e}')
    try:
        planejamento.planejar(v, chamar=chamar)
    except Exception as e:
        return _diag('plano visual', f'falha não tratada do provedor: {e}')
    from src.v2 import plano_exec
    try:                                        # V2.5: plano VINCULANTE (1 ajuste; retirada segura; ou recusa)
        pl = plano_exec.vincular(v, '', chamar=chamar)
    except ValueError as e:
        return _diag('plano visual executável', str(e)[:500], plano=(v.get('_plano_visual_exec') or {}).get('acontecimentos'))
    rel = preparo.preparar(v)
    if rel['bloqueios']:
        return _diag('preparo', ' | '.join(f"{b['evento']}: {'; '.join(map(str, b['faltam']))[:120]}" for b in rel['bloqueios']),
                     pendentes=rc.get('pendentes_depois'))
    pv = previa.validar(v, saida / 'previa')
    if pv['bloqueios']:
        return _diag('prévia', ' | '.join(f"{b['evento']}: {'; '.join(b['faltam'])[:120]}" for b in pv['bloqueios']))
    cb = cobertura.avaliar(v, pv, saida / 'previa')
    if cb['bloqueios']:
        return _diag('cobertura', ' | '.join(f"{b['evento']}: {'; '.join(b['faltam'])[:120]}" for b in cb['bloqueios']))
    trab = saida / 'trab'
    trab.mkdir()
    reais, imgs, _, ia_ids = main._midia_do_acervo(v, trab)
    sem_midia = [c.get('foto') for c in v['cenas'] if c.get('foto') and c.get('imagem') not in reais]
    if sem_midia:
        return _diag('mídia', f'foto(s) do acervo sem arquivo utilizável: {sem_midia}')
    t, tempos = 0.05, []
    for c in v['cenas']:
        d = max(1.6, len(re.sub(r'\*', '', c['fala'])) / 14.6)
        tempos.append((t, t + d)); t += d + .12
    cenas = main._montar_cenas(v, reais, imgs, tempos, trab, ia_ids)
    caps = []
    for c, (a, b) in zip(v['cenas'], tempos):
        ws = re.sub(r'\*', '', c['fala']).split()
        for i0 in range(0, len(ws), 5):
            caps.append({'start': round(a + (b - a) * i0 / len(ws), 3), 'end': round(a + (b - a) * min(len(ws), i0 + 5) / len(ws), 3),
                         'words': [{'w': w.upper().strip('.,:'), 'hl': False, 's': round(a + (b - a) * (i0 + j) / len(ws), 3)} for j, w in enumerate(ws[i0:i0 + 5])]})
    d1 = {'duration': round(t, 2), 'meta': {'titulo': v.get('titulo') or '', 'categoria': 'CIÊNCIA', 'marca': '@coringa.explica',
                                           'pergunta': next((c.get('pergunta') for c in v['cenas'] if c.get('pergunta')), ''),
                                           'fontes': list(v.get('fontes') or []), 'preparo': rel}, 'scenes': cenas, 'captions': caps}
    out = {'ok': True, 'etapa': 'fim', 'plano': plano_exec.resumo(pl), 'plano_json': pl.get('acontecimentos'), 'preparo': preparo.resumo(rel), 'previa': previa.resumo(pv), 'cobertura': cobertura.resumo(cb)}
    if render:
        aud = saida / 'voz.wav'
        fonte = ['-f', 'lavfi', '-i', 'sine=f=180:d=1,volume=0.25'] if not audio else ['-i', str(audio)]
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', *fonte, '-t', f"{d1['duration']:.2f}", '-ar', '48000', str(aud)], check=True)
        r = piloto.renderizar(d1, aud, saida / 'ensaio.mp4', saida / 'trab2', None, saida, 'ensaio')
        v2 = json.loads((saida / 'ensaio-piloto' / 'v2_dados.json').read_text(encoding='utf-8'))
        # paridade: a composição decidida no preparo é a renderizada (nenhuma troca silenciosa entre as etapas)
        dec = {e['id']: e['representacao'] for e in rel['eventos']}
        div = []
        for sc in v2['scenes']:
            for i1 in sc.get('origem') or []:
                if cenas[i1].get('tipo') in ('gancho', 'revelacao', 'fechamento'):
                    continue                     # cena estrutural é editorial por definição
                eid = ((cenas[i1].get('acontecimento') or {}).get('id'))
                rep = dec.get(eid) or {}
                if rep.get('modo') == 'composicao' and sc['comp'] != rep.get('comp'):
                    div.append(f"{eid}: preparo {rep.get('comp')} × render {sc['comp']}")
        out.update(fiscal_bloqueios=r['bloqueios'], fiscal_revisoes=r['revisoes'], audio=r['relatorio']['audio'],
                   divergencias=sorted(set(div)), mp4=str(saida / 'ensaio.mp4'))
        if r['bloqueios'] or div:
            out.update(ok=False, etapa='fiscal', diagnostico='fiscal: ' + '; '.join(r['bloqueios'] + sorted(set(div)))[:400])
    main._limpar_acervo(v)
    out['checkpoint_novo'] = checkpoint.verificar_arquivos(saida / 'checkpoint')
    if out['checkpoint_novo']['erros']:
        out.update(ok=False, diagnostico='checkpoint novo incompleto: ' + '; '.join(out['checkpoint_novo']['erros'][:3]))
    return out


if __name__ == '__main__':
    o, e, s = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')), Path(sys.argv[3])
    print(json.dumps(executar(o, e, s), ensure_ascii=False, indent=1, default=str))
