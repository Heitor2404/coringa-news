"""FISCAL NOVO em MODO SOMBRA (Fase 0 da auditoria do Coringa, 12/11/2026).

Calcula a nota nova e mostra no Telegram, mas NÃO decide nada: o "pode postar" continua o de sempre (main._qualidade).
Pesos aprovados pelo Heitor (12/11): precisão factual 25 · imagem/narração 20 · ritmo 15 · acabamento 15 ·
narrativa/gancho 15 · recursos gráficos 5 · áudio 5.
- Recurso gráfico: a FALTA de mapa/gráfico não tira ponto sozinha; só quando ele era necessário para entender a frase.
- Erro factual grave é BLOQUEADOR: aparece separado, fora da média.
- O que não deu para medir fica "não medido" e a nota é calculada só com o que foi medido (sem chutar).
Custo: zero de Claude. Texto (fatos, narrativa, recursos) = 1 pedido ao Gemini DIRETO (sem passar pelo Claude);
imagem/narração = a nota do fiscal final que já existe; ritmo, acabamento e áudio = código.
"""
import json
import re
import subprocess
import threading
from pathlib import Path

from . import estaticos

LIMITE_TEXTO_S = 90          # o pedido ao Gemini roda em paralelo; passou disso, o fiscal segue sem ele (não segura o vídeo)
TEMPO_MIN_RODADA = 20        # minutos que precisam sobrar na rodada para o fiscal sombra rodar
PESOS = {'fatos': 25, 'imagem': 20, 'ritmo': 15, 'acabamento': 15, 'narrativa': 15, 'recursos': 5, 'audio': 5}
NOMES = {'fatos': 'fatos', 'imagem': 'imagem', 'ritmo': 'ritmo', 'acabamento': 'acabamento', 'narrativa': 'narrativa',
         'recursos': 'recursos', 'audio': 'áudio'}
INFOGRAFICOS = {'numero', 'cards', 'escala', 'lista', 'mapa', 'linha_tempo', 'comparacao', 'citacao', 'revelacao'}


def faixa(nota: float) -> str:
    if nota >= 9:
        return 'excelente'
    if nota >= 8:
        return 'bom'
    if nota >= 7:
        return 'aceitável (pode pedir correções)'
    return 'NÃO aprovado (só com decisão sua)'


# ───────────────────────── partes medidas por código ─────────────────────────
def nota_ritmo(cenas: list[dict]) -> tuple[float, dict, list[str]]:
    m = estaticos.medir_cenas(cenas)
    pontos = PESOS['ritmo'] * (1 - min(1.0, 1.5 * m['frac_estatica']))
    # mesma imagem voltando depois de outras (repetição percebida)
    vistas, voltas, ant = set(), 0, None
    for c in cenas:
        k = c.get('imagem') or c.get('img')
        if not k or c.get('tipo') == 'fechamento':
            continue
        if k != ant and k in vistas:
            voltas += 1
        vistas.add(k)
        ant = k
    pontos -= min(6, 2 * voltas)
    obs = [estaticos.resumo(m)] + ([f'{voltas} imagem(ns) voltando depois de outras'] if voltas else [])
    return round(max(0.0, pontos), 1), m, obs


def nota_acabamento(problemas_tela: list) -> tuple[float, list[str]]:
    """Por enquanto só o que o motor já mede: texto em cima de texto / saindo da tela (fiscal da tela).
    Margens seguras e tela final entram na Fase 3."""
    n = len(problemas_tela or [])
    obs = [f'texto sobre texto em {n} ponto(s)'] if n else []
    return round(max(0.0, PESOS['acabamento'] - 5 * n), 1), obs + ['(parcial: margens e tela final entram na Fase 3)']


def nota_audio(video: Path) -> tuple[float | None, list[str]]:
    """Volume integrado perto de −14 LUFS e pico abaixo de −1 dBTP (o padrão das redes)."""
    try:
        r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(video), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                           capture_output=True, text=True, timeout=60)
        txt = r.stderr[r.stderr.rfind('Summary:'):]
        lufs = float(re.search(r'I:\s*(-?[\d.]+) LUFS', txt).group(1))
        pico = float(re.search(r'Peak:\s*(-?[\d.]+) dBFS', txt).group(1))
    except Exception as e:
        return None, [f'áudio não medido ({str(e)[:60]})']
    pontos = PESOS['audio'] - max(0.0, abs(lufs + 14) - 1.5) - (1 if pico > -1 else 0)
    return round(max(0.0, pontos), 1), [f'volume {lufs:.1f} LUFS, pico {pico:.1f} dB']


# ───────────────────────── partes medidas pelo Gemini (texto) ─────────────────────────
def _frases(v: dict) -> list[dict]:
    """As ideias (frase inteira) com o recurso visual que cada uma ganhou."""
    out = []
    for c in v.get('cenas', []):
        if c.get('sub') or c.get('tipo') == 'fechamento':
            continue
        recurso = c['tipo'] if c['tipo'] in INFOGRAFICOS else ('etiqueta de lugar' if c.get('lugar') else 'imagem')
        out.append({'fala': str(c.get('fala_ideia') or c.get('fala') or '').replace('*', ''), 'recurso': recurso})
    return out


def _gemini_direto(prompt: str) -> dict:
    """Gemini SEM passar pelo Claude (a cascata normal tenta o Claude primeiro e gastaria crédito da assinatura)."""
    from google.genai import types
    from . import gemini

    def f(modelo):
        r = gemini.cliente().models.generate_content(
            model=modelo, contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.2))
        return gemini.extrair_json(r.text)
    return gemini._tentar(f, gemini.PRINCIPAIS or None)


def avaliar_texto(v: dict, prompt_base: str | None = None, pedir=None) -> dict:
    """Fatos (25), narrativa/gancho (15) e recursos (5) num pedido só. `pedir` só é trocado nos testes."""
    from . import cofre
    base = prompt_base if prompt_base is not None else cofre.prompt('PROMPT_FISCAL_SOMBRA')
    if base.startswith('['):                      # o texto ainda não está no cofre: não mede (não inventa)
        return {}
    frases = _frases(v)
    lista = '\n'.join(f"{k + 1}. {f['fala']}  [recurso na tela: {f['recurso']}]" for k, f in enumerate(frases))
    prompt = base.format(fatos=str(v.get('fatos') or '')[:12000], frases=lista, titulo=v.get('titulo', ''))
    caixa: dict = {}

    def rodar():
        try:
            caixa['r'] = (pedir or _gemini_direto)(prompt)
        except Exception as e:
            caixa['erro'] = e
    th = threading.Thread(target=rodar, daemon=True)     # daemon: se travar, não segura o fim da rodada
    th.start()
    th.join(LIMITE_TEXTO_S)
    if th.is_alive():
        raise TimeoutError(f'Gemini não respondeu em {LIMITE_TEXTO_S}s')
    if 'erro' in caixa:
        raise caixa['erro']
    r = caixa.get('r')
    if isinstance(r, list):
        r = r[0] if r else {}
    return r if isinstance(r, dict) else {}


def _num(x, maximo: float) -> float | None:
    try:
        return round(min(maximo, max(0.0, float(x))), 1)
    except (TypeError, ValueError):
        return None


# ───────────────────────── junta tudo ─────────────────────────
def sombra(v: dict, cenas: list[dict], video: Path | None, nota_imagem: float | None,
           problemas_tela: list | None = None, pedir=None, prompt_base: str | None = None) -> dict:
    partes, obs, bloqueadores = {}, {}, []
    try:
        from .orcamento import sobra
        if sobra() < TEMPO_MIN_RODADA:                  # rodada apertada: não gasta tempo com o fiscal de teste
            return {'nota': None, 'faixa': 'não rodou (pouco tempo na rodada)', 'partes': {}, 'nao_medido': list(PESOS),
                    'bloqueadores': [], 'obs': {}, 'ritmo': estaticos.medir_cenas([])}
    except Exception:
        pass
    partes['ritmo'], medida_ritmo, obs['ritmo'] = nota_ritmo(cenas)
    partes['acabamento'], obs['acabamento'] = nota_acabamento(problemas_tela or [])
    partes['imagem'] = round(min(10.0, max(0.0, float(nota_imagem))) * 2, 1) if nota_imagem is not None else None
    if video:
        partes['audio'], obs['audio'] = nota_audio(video)
    else:
        partes['audio'] = None
    try:
        t = avaliar_texto(v, prompt_base=prompt_base, pedir=pedir)
    except Exception as e:
        t, obs['texto'] = {}, [f'avaliação de texto falhou ({str(e)[:80]})']
    f = t.get('fatos') or {}
    partes['fatos'] = _num(f.get('nota'), PESOS['fatos']) if f else None
    for p in f.get('problemas') or []:
        item = f"frase {p.get('frase')}: {str(p.get('explicacao') or '')[:140]}"
        if str(p.get('tipo')) == 'erro_grave':
            bloqueadores.append(item)                     # fora da média: aparece separado
        else:
            obs.setdefault('fatos', []).append(f"{p.get('tipo')}: {item}")
    n = t.get('narrativa') or {}
    partes['narrativa'] = _num(n.get('nota'), PESOS['narrativa']) if n else None
    if n.get('comentario'):
        obs['narrativa'] = [str(n['comentario'])[:160]]
    rc = t.get('recursos') or {}
    if rc:
        faltou = [x for x in (rc.get('faltou') or []) if x.get('necessario', True)]   # só o que era necessário
        partes['recursos'] = round(max(0.0, PESOS['recursos'] - 1.5 * len(faltou)), 1)
        obs['recursos'] = [f"frase {x.get('frase')}: faltou {x.get('recurso')} ({str(x.get('por_que') or '')[:80]})" for x in faltou]
    else:
        partes['recursos'] = None
    medidos = {k: p for k, p in partes.items() if p is not None}
    peso = sum(PESOS[k] for k in medidos)
    nota = round(10 * sum(medidos.values()) / peso, 1) if peso else None
    return {'nota': nota, 'faixa': faixa(nota) if nota is not None else 'não medido', 'partes': partes,
            'nao_medido': [k for k, p in partes.items() if p is None], 'bloqueadores': bloqueadores, 'obs': obs,
            'ritmo': medida_ritmo}


def linhas_telegram(r: dict) -> list[str]:
    if not r or r.get('nota') is None:
        return []
    pts = ' · '.join(f"{NOMES[k]} {('%g' % p).replace('.', ',')}/{PESOS[k]}" for k, p in r['partes'].items() if p is not None)
    out = [f"🧪 Fiscal novo (TESTE, não decide nada): {str(r['nota']).replace('.', ',')}/10 — {r['faixa']}", f'   {pts}']
    if r['nao_medido']:
        out.append('   não medido: ' + ', '.join(NOMES[k] for k in r['nao_medido']))
    out.append('   ' + estaticos.resumo(r['ritmo']))
    for b in r['bloqueadores']:
        out.append(f'   ⛔ erro factual grave (bloqueador): {b}')
    for k in ('fatos', 'recursos'):
        for o in (r['obs'].get(k) or [])[:3]:
            out.append(f'   • {o}')
    return out


def salvar(r: dict, arq: Path):
    arq.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
