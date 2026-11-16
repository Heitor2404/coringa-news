"""Render completo do episódio de referência (Londres 1666) no GitHub Actions — SEM nenhuma IA.

Usa só o que já existe: storyboard supervisionado, imagens do checkpoint e do Commons, narração já gravada (entregue
cifrada), música do repositório; render pelo palco V2 + FFmpeg; fiscal técnico/editorial; estado final explícito;
prévia PRIVADA ao Telegram. O caixa fica aberto com TODOS os provedores de IA declarados 'desconhecido': qualquer
chamada de IA seria negada e apareceria no livro (prova de que o render não usou IA).

uso: python scripts/render_londres.py STORYBOARD MATERIAL/ SAIDA/ [--telegram]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ['CAIXA_PROVEDORES'] = json.dumps({p: {'faturamento': 'desconhecido'} for p in
                                             ('claude_code', 'gemini', 'groq', 'pollinations', 'gemini_imagem', 'cloudflare')})
os.environ.pop('CAIXA_RATIFICADO', None)

from src import caixa                                   # noqa: E402
from src.v3 import estado_final, supervisionado as S    # noqa: E402

TITULO = 'Grande Incêndio de Londres, 1666 — episódio de referência (render completo)'


def relatorio(est: dict, fis: dict, cx: dict, render_s: float, mp4: Path, achados: list) -> str:
    r = fis or {}
    linhas = [f'STATUS: {est["estado"]} (prévia privada; não publicado)', '',
              f'Arquivo: {mp4.name} · {mp4.stat().st_size / 1048576:.1f} MB · render {render_s:.0f}s', '',
              'FISCAL', f"bloqueios {r.get('bloqueios', 0)} · revisões {r.get('revisoes', 0)} · estéticos {r.get('esteticas', 0)}",
              f"áudio {(r.get('audio') or {}).get('lufs')} LUFS · pico {(r.get('audio') or {}).get('pico_dbtp')} dBTP · {(r.get('video') or {}).get('duracao', 0):.1f}s"]
    for a in achados:
        if a.get('classe') in ('bloqueio', 'revisao'):
            linhas.append(f"- [{a['classe']}] {a.get('inicio', '')}s {a['codigo']}: {str(a.get('problema'))[:160]}")
    if est.get('pendencias'):
        linhas += ['', 'PENDÊNCIAS'] + [f'- {p[:180]}' for p in est['pendencias'][:12]]
    linhas += ['', 'CUSTOS DESTA EXECUÇÃO',
               f"cobrança efetiva: US$ {cx.get('cobrado_usd', 0):.2f} · chamadas de IA: {cx.get('chamadas', 0)} · negadas: {cx.get('negadas', 0)}",
               'crédito de assinatura: 0 · cota grátis: 0 · GitHub Actions: minutos do runner público (sem cobrança)',
               f"teto provisório US$ {cx.get('teto', 0.8):.2f} / alerta {cx.get('alerta', 0.6):.2f}; provedores pagos desabilitados"]
    return '\n'.join(linhas)


def main():
    sb, mat, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with caixa.video('londres-1666-render-referencia', out):
        p = S.preparar(sb, mat, out)
        res = S.completo(p, out, 'londres_1666_referencia')
        cx = caixa.resumo()
    fis = json.loads((out / 'fiscal.json').read_text(encoding='utf-8'))
    achados = fis.get('achados') or []
    res_estado = {'mp4': res['mp4'], 'bloqueios': [f"{a['codigo']}: {a['problema']}" for a in achados if a.get('classe') == 'bloqueio'],
                  'revisoes': [f"{a.get('inicio')}s {a['codigo']}: {a['problema']}" for a in achados if a.get('classe') == 'revisao'],
                  'revisao_multimodal': {'chamadas': 0}}
    est = estado_final.decidir(res_estado)
    estado_final.gravar(est, out / 'estado_final.json')
    texto = relatorio(est, fis.get('resumo') or {}, cx, res['render_s'], Path(res['mp4']), achados)
    (out / 'relatorio_render.txt').write_text(texto, encoding='utf-8')
    (out / 'custos.json').write_text(json.dumps({**cx, 'segundos_total': round(time.time() - t0, 1)}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(texto)
    if '--telegram' in sys.argv:
        from src.v3 import previa_telegram
        try:
            env = previa_telegram.enviar(Path(res['mp4']), est, TITULO, texto)
            print('telegram:', env)
            (out / 'telegram.json').write_text(json.dumps({'enviado': True, **env}, ensure_ascii=False), encoding='utf-8')
        except previa_telegram.EnvioRecusado as e:
            print('telegram NÃO enviado:', e)
            (out / 'telegram.json').write_text(json.dumps({'enviado': False, 'motivo': str(e)}, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
