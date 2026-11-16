"""CLI reproduzível do motor V4 (`python -m src.v4 <comando>`):

  catalogo <checkout-hyperframes>   regenera o índice do catálogo HyperFrames inteiro
  sondar                             registro de capacidades (versões, estados, evidências)
  episodio <pedido.json> <saida>     produz o episódio (direção → acervo → voz → render por backend → composição → métricas)
  auditar <saida>                    refaz métricas/folha de contato sobre o MP4 e a linha do tempo (sem IA)
  relatorio <saida>                  engenharia reversa em Markdown (docs da execução)
  telegram <saida>                   prévia PRIVADA (chat autorizado), status visível, NÃO PUBLICADO
Cada etapa grava JSON reproduzível; nenhuma chamada de IA é necessária para refazer render/auditoria.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _telegram(saida: Path):
    from src.v3 import estado_final, previa_telegram
    res = json.loads((saida / 'resultado.json').read_text())
    est = estado_final.decidir(res)
    if res.get('revisao_multimodal', {}).get('estado') == 'PENDENTE':
        est.setdefault('pendencias', []).append('revisão multimodal PENDENTE: ' + str(res['revisao_multimodal'].get('motivo') or ''))
    r = res.get('metricas_resumo') or {}
    a = res.get('audio') or {}
    fam = (res.get('contrato') or {}).get('familias') or {}
    linhas = [f"EPISÓDIO V4 — PRÉVIA PRIVADA, NÃO PUBLICADO", f"STATUS: {est['estado']}",
              f"{r.get('duracao', 0):.1f}s · {r.get('cenas')} cenas · plano médio {r.get('plano_medio_s')}s · vazio médio {r.get('vazio_medio')} · "
              f"estático {r.get('pct_estatico')}% · áudio {a.get('lufs')} LUFS / pico {a.get('pico')}",
              'famílias: ' + ', '.join(f'{k}×{v}' for k, v in (fam.get('modalidades') or {}).items() if v) + (f" · faltam: {', '.join(fam.get('faltam'))}" if fam.get('faltam') else '')]
    for b in (res.get('bloqueios') or [])[:8]:
        linhas.append(f'- [bloqueio] {b[:180]}')
    for p in (est.get('pendencias') or [])[:6]:
        linhas.append(f'- [pendente] {str(p)[:160]}')
    cx = res.get('caixa') or {}
    linhas.append(f"custo: cobrado US$ {cx.get('cobrado_usd', 0) or 0:.2f} · assinatura US$ {cx.get('credito_usd', 0) or 0:.3f} · cota {cx.get('cota')} · provedores pagos desligados")
    linhas.append('Aprovação estética: só o Heitor.')
    mp4 = Path(res['mp4']) if res.get('mp4') and Path(res['mp4']).exists() else None
    if mp4:
        env = previa_telegram.enviar(mp4, est, 'Coringa V4 — Canal do Panamá', '\n'.join(linhas))
    else:
        chat, _ = previa_telegram.chat_autorizado()
        env = previa_telegram._api('sendMessage', {'chat_id': chat, 'text': ('PRÉVIA PRIVADA — sem MP4\n' + '\n'.join(linhas))[:3900]})
    (saida / 'telegram.json').write_text(json.dumps({'enviado': True, 'estado': est['estado']}, ensure_ascii=False))
    print('telegram', est['estado'])


def main(a: list[str]):
    cmd = a[0] if a else 'ajuda'
    if cmd == 'catalogo':
        subprocess.run([sys.executable, 'scripts/v4_catalogo_hyperframes.py', *a[1:]], check=True)
    elif cmd == 'sondar':
        subprocess.run([sys.executable, '-m', 'src.v4.capacidades', 'sondar'], check=True)
    elif cmd == 'episodio':
        from src import caixa
        from src.v4 import episodio
        pedido = json.loads(Path(a[1]).read_text(encoding='utf-8'))
        saida = Path(a[2])
        saida.mkdir(parents=True, exist_ok=True)
        with caixa.video(pedido['video_id'], saida):
            try:
                res = episodio.produzir(pedido, saida, saida / '_trabalho')
            finally:
                cx = caixa.resumo()
                (saida / 'caixa_resumo.json').write_text(json.dumps({**cx, 'operacoes': caixa._ATUAL['livro']['operacoes'][-120:]},
                                                                    ensure_ascii=False, indent=1, default=str), encoding='utf-8')
        res['caixa'] = cx
        (saida / 'resultado.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
        print(json.dumps({k: res.get(k) for k in ('estado', 'mp4', 'segundos')}, ensure_ascii=False))
    elif cmd == 'auditar':
        from src.v4 import metricas
        saida = Path(a[1])
        lt = json.loads((saida / 'linha_do_tempo.json').read_text())
        res = json.loads((saida / 'resultado.json').read_text())
        m = metricas.medir(Path(res['mp4']), lt)
        metricas.salvar(m, saida / 'metricas.json')
        metricas.folha_de_contato(Path(res['mp4']), lt, saida / 'folha_contato.jpg')
    elif cmd == 'relatorio':
        from src.v4 import reversa
        print(reversa.escrever(Path(a[1])))
    elif cmd == 'telegram':
        _telegram(Path(a[1]))
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
