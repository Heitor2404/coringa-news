"""Revisão SEMÂNTICA audiovisual por plano (V3.1-resgate): uma tira de 4 quadros em ordem de tempo (início → fim do
plano) + a narração daquele trecho + a ficha do acontecimento (o que precisa aparecer, critério) → um modelo de visão
diz se a sequência DEMONSTRA o acontecimento e aponta o defeito concreto.

- Avalia movimento e mecanismo pela sequência, não por um quadro só.
- Usa a cota grátis do Gemini (`chamar_visao(prompt, [imagens]) → dict`); cache pelo sha da tira (não repete chamada).
- Resultado é DIAGNÓSTICO (o que está errado, em que segundo, como corrigir), classe `revisao` — julgamento de modelo não
  vira bloqueio sozinho. Sem chave/sem cota: registra que a revisão não rodou (nunca aprova por omissão).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

PROMPT = """Você revisa um documentário curto vertical. As imagens são 4 quadros EM ORDEM DE TEMPO de um único plano
({ini:.1f}s → {fim:.1f}s). Narração deste trecho: "{fala}".
Acontecimento: {evento} ({tipo}). Precisa mostrar: {precisa}. Critério: {criterio}.
Responda só JSON: {{"demonstra": "sim|parcial|nao", "midia_corresponde": true|false, "objeto_principal_visivel": true|false,
"mapa_ou_grafico_informativo": "sim|nao|nao_se_aplica", "texto_na_tela_legivel": true|false, "texto_interno_ou_tecnico_na_tela": true|false,
"problemas": ["defeito concreto, com o quadro (1–4) onde aparece"], "correcao": "a menor mudança que resolveria"}}"""


def tira(mp4: Path, ini: float, fim: float, destino: Path, n: int = 4) -> Path:
    d = max(.1, fim - ini)
    ts = [ini + d * f for f in ((.08, .38, .66, .94) if n == 4 else [k / (n - 1) for k in range(n)])]
    sel = '+'.join(f'between(t,{t:.3f},{t + .034:.3f})' for t in ts)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf', f"select='{sel}',scale=270:480,tile={n}x1:padding=6",
                    '-frames:v', '1', '-q:v', '4', str(destino)], check=True)
    return destino


def revisar(mp4: Path, dados: dict, fichas: list[dict], chamar_visao, pasta: Path, cache: dict | None = None) -> dict:
    pasta.mkdir(parents=True, exist_ok=True)
    cache = cache if cache is not None else {}
    por_ev = {f['evento_id']: f for f in fichas}
    planos, chamadas = [], 0
    for k, c in enumerate(dados['scenes']):
        d = c.get('direcao') or {}
        f = por_ev.get(d.get('evento_id')) or {}
        img = tira(mp4, c['start'], c['end'], pasta / f'tira_{k:02d}.jpg')
        h = hashlib.sha256(img.read_bytes() + str(c.get('fala')).encode()).hexdigest()
        if h in cache:
            r = cache[h]
        elif chamar_visao is None:
            r = {'_nao_revisado': 'sem modelo de visão disponível'}
        else:
            try:
                r = chamar_visao(PROMPT.format(ini=c['start'], fim=c['end'], fala=c.get('fala') or '', evento=d.get('evento_id'),
                                               tipo=f.get('tipo'), precisa=f.get('representacao_necessaria') or '—',
                                               criterio=f.get('criterio_visual') or '—'), [img])
                chamadas += 1
            except Exception as e:
                r = {'_nao_revisado': f'{type(e).__name__}: {str(e)[:120]}'}
            cache[h] = r
        planos.append({'plano': k, 'inicio': c['start'], 'fim': c['end'], 'evento_id': d.get('evento_id'), 'critico': bool(f.get('critico')),
                       'tira': img.name, 'veredito': r})
    return {'planos': planos, 'chamadas': chamadas, 'achados': achados(planos)}


def achados(planos: list[dict]) -> list[dict]:
    """Veredito → diagnóstico específico. Plano não revisado também aparece (nada é aprovado por omissão)."""
    out = []
    for p in planos:
        r = p['veredito'] or {}
        base = {'classe': 'revisao', 'dimensao': 'semantica', 'inicio': p['inicio'], 'fim': p['fim'], 'plano': p['plano']}
        if '_nao_revisado' in r:
            out.append({**base, 'codigo': 'M-NAO-REVISADO', 'problema': f"plano {p['plano']} sem revisão multimodal ({r['_nao_revisado']})", 'evidencia': p['tira']})
            continue
        probs = '; '.join(r.get('problemas') or [])
        cor = r.get('correcao') or ''
        if r.get('demonstra') in ('nao', 'parcial'):
            out.append({**base, 'codigo': 'M-NAO-DEMONSTRA' if r['demonstra'] == 'nao' else 'M-DEMONSTRA-PARCIAL',
                        'problema': f"{p['evento_id']}{' (crítico)' if p['critico'] else ''}: sequência {('não demonstra' if r['demonstra'] == 'nao' else 'demonstra em parte')} o acontecimento — {probs}",
                        'evidencia': p['tira'], 'correcao': cor})
        for chave, cod, txt in (('midia_corresponde', 'M-MIDIA-DIVERGE', 'a mídia não corresponde à narração'),
                                ('objeto_principal_visivel', 'M-OBJETO-INVISIVEL', 'objeto principal não visível'),
                                ('texto_na_tela_legivel', 'M-ILEGIVEL', 'texto na tela ilegível')):
            if r.get(chave) is False:
                out.append({**base, 'codigo': cod, 'problema': f"plano {p['plano']}: {txt} — {probs}", 'evidencia': p['tira'], 'correcao': cor})
        if r.get('texto_interno_ou_tecnico_na_tela') is True:
            out.append({**base, 'codigo': 'M-TEXTO-INTERNO', 'problema': f"plano {p['plano']}: descrição interna/técnica visível na tela — {probs}",
                        'evidencia': p['tira'], 'correcao': cor})
        if r.get('mapa_ou_grafico_informativo') == 'nao':
            out.append({**base, 'codigo': 'M-MAPA-DECORATIVO', 'problema': f"plano {p['plano']}: mapa/gráfico não acrescenta informação — {probs}",
                        'evidencia': p['tira'], 'correcao': cor})
    return out


def gravar(res: dict, destino: Path):
    destino.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
