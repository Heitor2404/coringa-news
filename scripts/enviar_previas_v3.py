"""Prévias PRIVADAS das execuções V3 (validação no Actions) ao Telegram: MP4, status, decisões de forma/composição,
fiscal (incluindo as decisões ruins F-*) e custos do caixa. Enviar prévia NÃO é publicar.

uso: python scripts/enviar_previas_v3.py saida_v3/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.v3 import estado_final, previa_telegram   # noqa: E402


def _ler(p: Path):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return None


def relatorio(caso: str, pasta_v3: Path, raiz_caso: Path) -> tuple[str, dict, Path | None]:
    res = _ler(pasta_v3 / 'resultado.json') or {}
    est = _ler(pasta_v3 / 'estado_final.json') or estado_final.decidir(res)
    mc = next((_ler(p) for p in raiz_caso.rglob('microcena.json')), None) or {}
    cx = next((_ler(p) for p in raiz_caso.rglob('caixa_resumo.json')), None) or {}
    fis = _ler(pasta_v3 / 'fiscal_v3.json') or {}
    dire = _ler(pasta_v3 / 'direcao.json') or {}
    dados = _ler(pasta_v3 / 'v2_dados.json') or {}
    L = [f"MICROCENA {mc.get('perfil', caso).upper()} — PRÉVIA PRIVADA, NÃO PUBLICADA", f"STATUS: {est.get('estado')}"]
    if mc:
        L.append(f"prova pedida: {mc.get('prova')} · acontecimento {mc.get('evento')} ({mc.get('tipo')}), {mc.get('palavras')} palavras")
    L += ['', 'DECISÕES DO DIRETOR (automático)']
    for k, pl in enumerate((dire.get('storyboard_usado') or {}).get('planos') or []):
        sc = (dados.get('scenes') or [{}] * 99)[k] if k < len(dados.get('scenes') or []) else {}
        p = sc.get('params') or {}
        L.append(f"- plano {k}: forma {pl.get('forma_visual') or '?'} · {pl.get('composicao')} · layout {p.get('layout', '-')} · "
                 f"mídia {p.get('natureza', '-')} · câmera {pl.get('movimento_camera') or 'fixo'}" + (f" · revela {pl['revela']}" if pl.get('revela') else ''))
    for k, r in enumerate(dire.get('registro') or []):
        for d in r.get('degradacoes') or []:
            if d.get('impacto') != 'aceitavel' or d.get('codigo') in ('COMPOSICAO-EDITORIAL', 'RECUO-RECUSADO', 'ENQUADRAMENTO-VERTICAL', 'MIDIA-ALTERNATIVA'):
                L.append(f"  · plano {k} [{d.get('impacto')}] {d.get('codigo')}: {str(d.get('texto'))[:140]}")
    r = fis.get('resumo') or {}
    L += ['', f"FISCAL: bloqueios {r.get('bloqueios', len(res.get('bloqueios') or []))} · revisões {r.get('revisoes', len(res.get('revisoes') or []))} · "
              f"áudio {(r.get('audio') or {}).get('lufs')} LUFS · {(r.get('video') or {}).get('duracao', 0) or 0:.1f}s"]
    for a in (fis.get('achados') or []):
        if a.get('classe') in ('bloqueio', 'revisao'):
            L.append(f"- [{a['classe']}] {a.get('codigo')}: {str(a.get('problema'))[:150]}")
    for b in (res.get('bloqueios') or [])[:6]:
        if not fis:
            L.append(f'- [bloqueio] {str(b)[:180]}')
    ops = cx.get('operacoes') or []
    modelos = sorted({f"{o.get('provedor')}:{o.get('modelo') or '-'}" for o in ops})
    L += ['', 'CUSTOS', f"cobrança efetiva US$ {cx.get('cobrado_usd', 0) or 0:.2f} · crédito de assinatura US$ {cx.get('credito_usd', 0) or 0:.3f} · "
                         f"cota grátis {cx.get('cota') or {}} · chamadas {cx.get('chamadas', len(ops))} · negadas {cx.get('negadas', 0)}",
          f"modelos: {', '.join(modelos) or '—'}", 'provedores pagos desabilitados (teto provisório US$ 0,80; alerta 0,60)']
    mp4 = None
    if res.get('mp4'):                         # o workflow move saida/ para saida_v3/<caso>/saida: procura pelo nome
        mp4 = Path(res['mp4']) if Path(res['mp4']).exists() else next(iter(sorted(raiz_caso.rglob(Path(res['mp4']).name))), None)
    return '\n'.join(L), est, mp4


def main():
    base = Path(sys.argv[1])
    for caso in sorted(p for p in base.iterdir() if p.is_dir()):
        pastas = sorted(caso.rglob('resultado.json'))
        if not pastas:
            texto, est, mp4 = (f"MICROCENA {caso.name}: sem resultado (ver registro)\n" + ((caso / 'registro.txt').read_text(errors='ignore')[-1500:]
                                                                                         if (caso / 'registro.txt').exists() else ''),
                               {'estado': estado_final.BLOQUEADO, 'motivos': ['execução sem resultado']}, None)
        else:
            texto, est, mp4 = relatorio(caso.name, pastas[-1].parent, caso)
        (caso / 'previa_relatorio.txt').write_text(texto, encoding='utf-8')
        try:
            if mp4:
                env = previa_telegram.enviar(mp4, est, f'Microcena {caso.name}', texto)
            else:
                chat, _ = previa_telegram.chat_autorizado()
                previa_telegram._api('sendMessage', {'chat_id': chat, 'text': ('PRÉVIA PRIVADA — sem MP4\n' + texto)[:3900]})
                env = {'mensagens': 1, 'sem_mp4': True}
            print(caso.name, 'telegram', env)
            (caso / 'telegram.json').write_text(json.dumps({'enviado': True, **env}, ensure_ascii=False), encoding='utf-8')
        except previa_telegram.EnvioRecusado as e:
            print(caso.name, 'telegram NÃO enviado:', e)
            (caso / 'telegram.json').write_text(json.dumps({'enviado': False, 'motivo': str(e)}, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
