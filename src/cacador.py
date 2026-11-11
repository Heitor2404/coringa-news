"""Caçador de pautas do Coringa Explica: escolhe o tema do dia com POTENCIAL DE VIRALIZAR, em qualquer área.

Junta candidatas de 4 lugares e um editor dá nota:
1. DATAS: o que vem nos próximos dias (Halloween, Natal, Dia dos Namorados, chuva de meteoros, sexta-feira 13...) e
   aniversários redondos de eventos famosos ("há 100 anos", lista "neste dia" da Wikipédia).
2. NOTÍCIAS DO MOMENTO: assuntos em alta no Brasil (Google Trends + Google News) → viram CURIOSIDADE, não jornal.
3. ESTUDOS NOVOS: divulgação científica (ScienceDaily, EurekAlert, Phys.org, NASA).
4. ATEMPORAIS: a planilha de vocês (coluna "prioridade" = sim força o tema) + a lista interna (todas as áreas).
O editor também decide se o tema merece série (2–3 partes) ou vídeo único (o padrão).
"""
import json, re, time, unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

from . import gemini, temas
from src import cofre

RAIZ = Path(__file__).resolve().parent.parent
REGISTRO = RAIZ / 'data' / 'pautas_explica.json'
BRT = timezone(timedelta(hours=-3))
UA = {'User-Agent': 'CoringaExplicaBot/1.0 (https://github.com/Heitor2404/coringa-news; educational short videos)'}


# ───────────────────────── 1. datas ─────────────────────────
def _pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def _enesimo_domingo(ano, mes, n):
    d = date(ano, mes, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _datas_do_ano(ano: int) -> list[tuple[date, str]]:
    p = _pascoa(ano)
    quinta_nov = date(ano, 11, 1) + timedelta(days=(3 - date(ano, 11, 1).weekday()) % 7) + timedelta(weeks=3)
    fixas = [((1, 1), 'Ano Novo'), ((2, 14), "Valentine's Day (namorados no mundo)"), ((3, 14), 'Dia do Pi'),
             ((3, 20), 'equinócio de outono no Brasil'), ((4, 1), 'Dia da Mentira'), ((4, 22), 'Dia da Terra / Descobrimento do Brasil'),
             ((5, 4), 'Dia de Star Wars'), ((5, 25), 'Dia do Orgulho Nerd'), ((6, 5), 'Dia do Meio Ambiente'),
             ((6, 12), 'Dia dos Namorados (Brasil)'), ((6, 21), 'solstício de inverno no Brasil (noite mais longa)'),
             ((6, 24), 'São João / festa junina'), ((7, 7), 'Dia Mundial do Chocolate'), ((7, 13), 'Dia do Rock'),
             ((7, 20), 'Dia do Amigo / chegada do homem à Lua (1969)'), ((8, 12), 'pico da chuva de meteoros Perseidas'),
             ((8, 22), 'Dia do Folclore'), ((9, 7), 'Independência do Brasil'), ((9, 22), 'equinócio de primavera no Brasil'),
             ((10, 12), 'Dia das Crianças'), ((10, 31), 'Halloween / Dia das Bruxas'), ((11, 2), 'Finados / Día de Muertos'),
             ((11, 17), 'pico da chuva de meteoros Leônidas'), ((12, 14), 'pico da chuva de meteoros Geminídeas'),
             ((12, 21), 'solstício de verão no Brasil (dia mais longo)'), ((12, 25), 'Natal'), ((12, 31), 'Réveillon')]
    out = [(date(ano, m, d), n) for (m, d), n in fixas]
    out += [(p - timedelta(days=47), 'Carnaval'), (p - timedelta(days=2), 'Sexta-feira Santa'), (p, 'Páscoa'),
            (_enesimo_domingo(ano, 5, 2), 'Dia das Mães'), (_enesimo_domingo(ano, 8, 2), 'Dia dos Pais (Brasil)'),
            (quinta_nov + timedelta(days=1), 'Black Friday')]
    for mes in range(1, 13):                      # sexta-feira 13
        if date(ano, mes, 13).weekday() == 4:
            out.append((date(ano, mes, 13), 'Sexta-feira 13'))
    return out


def datas(hoje: date) -> list[dict]:
    out = []
    for d, nome in _datas_do_ano(hoje.year) + _datas_do_ano(hoje.year + 1):
        falta = (d - hoje).days
        if 0 <= falta <= 7:
            quando = 'HOJE' if falta == 0 else ('amanhã' if falta == 1 else f'em {falta} dias')
            out.append({'origem': 'data', 'titulo': f'{nome} ({quando})', 'urgencia': max(0, 10 - falta)})
    try:                                              # aniversários redondos ("há 100 anos") nos próximos 3 dias
        redondos = {10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100, 125, 150, 200, 250, 300, 400, 500}
        for k in range(0, 4):
            d = hoje + timedelta(days=k)
            r = requests.get(f'https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{d.month:02d}/{d.day:02d}',
                             headers=UA, timeout=30)
            r.raise_for_status()
            for ev in r.json().get('events', []):
                anos = d.year - int(ev.get('year') or 0)
                if anos in redondos:
                    out.append({'origem': 'data', 'urgencia': 8 - k,
                                'titulo': f"há {anos} anos ({d.strftime('%d/%m')}/{ev.get('year')}): {ev.get('text', '')[:180]}"})
    except Exception as e:
        print(f'  [pautas] "neste dia" indisponível: {str(e)[:80]}')
    return out


# ───────────────────────── 2. notícias em alta ─────────────────────────
def noticias() -> list[dict]:
    out = []
    for url in ('https://trends.google.com/trending/rss?geo=BR', 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=BR'):
        try:
            f = feedparser.parse(requests.get(url, headers=UA, timeout=30).content)
            for e in f.entries[:15]:
                out.append({'origem': 'noticia', 'titulo': f'em alta no Brasil: {e.title}', 'urgencia': 8})
            if f.entries:
                break
        except Exception:
            continue
    try:
        from . import pautas
        for p in pautas.buscar(por_topico=4)[:20]:
            out.append({'origem': 'noticia', 'titulo': f"notícia: {p['titulo']}", 'urgencia': 7})
    except Exception as e:
        print(f'  [pautas] Google News falhou: {str(e)[:80]}')
    return out


# ───────────────────────── 3. estudos novos ─────────────────────────
FEEDS_CIENCIA = ['https://www.sciencedaily.com/rss/strange_offbeat.xml', 'https://www.sciencedaily.com/rss/top/science.xml',
                 'https://www.eurekalert.org/rss.xml', 'https://phys.org/rss-feed/', 'https://www.nasa.gov/feed/']


def estudos() -> list[dict]:
    out = []
    for url in FEEDS_CIENCIA:
        try:
            f = feedparser.parse(requests.get(url, headers=UA, timeout=30).content)
            for e in f.entries[:8]:
                resumo = re.sub(r'<[^>]+>', '', e.get('summary', ''))[:160]
                out.append({'origem': 'estudo', 'titulo': f'estudo/descoberta: {e.title} — {resumo}', 'urgencia': 6})
        except Exception:
            continue
    return out


# ───────────────────────── 4. atemporais ─────────────────────────
def atemporais(n: int = 30) -> list[dict]:
    """Até 30 temas: os da planilha primeiro (em ordem sorteada a cada dia, para os do fim também terem chance);
    a lista interna só completa se a planilha tiver menos que isso. Prioridade = sim sempre entra."""
    import random
    fila = temas.fila_detalhada()
    prio = [t for t in fila if t.get('prioridade')]
    plan = [t for t in fila if t['planilha'] and not t.get('prioridade')]
    lista = [t for t in fila if not t['planilha']]
    sorteio = random.Random(datetime.now(BRT).strftime('%Y%m%d'))
    sorteio.shuffle(plan)
    sorteio.shuffle(lista)
    escolhidos = (prio + plan + lista)[:max(n, len(prio))]
    return [{'origem': 'planilha' if t['planilha'] else 'lista', 'titulo': t['tema'], 'urgencia': 0,
             'prioridade': t.get('prioridade', False), 'tema_original': t['tema']} for t in escolhidos]


# ───────────────────────── registro (variedade de áreas) ─────────────────────────
def recentes(n: int = 10) -> list[dict]:
    try:
        return json.loads(REGISTRO.read_text(encoding='utf-8'))[-n:]
    except Exception:
        return []


def registrar(escolha: dict):
    r = recentes(200)
    r.append({'data': datetime.now(BRT).strftime('%Y-%m-%d'), 'tema': escolha.get('tema'), 'area': escolha.get('area'),
              'origem': escolha.get('origem')})
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(json.dumps(r[-200:], ensure_ascii=False, indent=1), encoding='utf-8')


# ───────────────────────── o editor escolhe ─────────────────────────
PROMPT_PAUTA = cofre.prompt('PROMPT_PAUTA')


COTA = {'datas': 15, 'notícias': 12, 'estudos': 12, 'atemporais': 30}   # cada fonte tem vaga garantida no editor


def cacar() -> list[dict]:
    """Devolve as pautas do dia em ordem (a melhor primeiro). Tema da planilha com prioridade = sim vai na frente."""
    hoje = datetime.now(BRT).date()
    cands = []
    for nome, fn in (('datas', lambda: datas(hoje)), ('notícias', noticias), ('estudos', estudos), ('atemporais', atemporais)):
        try:
            r = fn()
            print(f'  [pautas] {nome}: {len(r)} (vão para o editor: {min(len(r), COTA[nome])})')
            cands += r[:COTA[nome]]
        except Exception as e:
            print(f'  [pautas] {nome} falhou: {str(e)[:80]}')
    prioridade = [c for c in cands if c.get('prioridade')]
    feitos = {temas.chave(t) for t in temas.usados()}
    rec = recentes()
    lista = '\n'.join(f"{c['origem']} · {c['titulo']}" for c in cands)
    txt_rec = '\n'.join(f"{r['data']} · {r.get('area', '?')} · {r.get('tema', '')}" for r in rec) or '(nenhum)'
    pautas = []
    try:
        r = gemini.json_(PROMPT_PAUTA.format(hoje=hoje.strftime('%A, %d/%m/%Y'), candidatas=lista, recentes=txt_rec))
        if isinstance(r, list):
            r = {'pautas': r}
        for p in r.get('pautas') or []:
            if isinstance(p, dict) and p.get('tema') and temas.chave(p['tema']) not in feitos:
                try:
                    p['partes'] = max(1, min(3, int(p.get('partes') or 1)))
                except (TypeError, ValueError):
                    p['partes'] = 1
                if p.get('origem') in ('data', 'noticia', 'estudo'):
                    p['partes'] = 1                    # perde a graça se for em partes
                cand = next((c for c in cands if c['titulo'] == p.get('candidata')), None)
                if cand and cand.get('tema_original'):
                    p['tema_original'] = cand['tema_original']   # para marcar como feito na planilha/lista
                pautas.append(p)
    except Exception as e:
        print(f'  [pautas] editor de pauta indisponível ({str(e)[:80]}); sigo a fila de temas')
    # planilha com prioridade = sim: sai primeiro, do jeito que vocês escreveram
    frente = [{'tema': c['tema_original'], 'tema_original': c['tema_original'], 'origem': 'planilha', 'area': '',
               'partes': 0, 'motivo': 'prioridade marcada na planilha', 'contexto': ''} for c in prioridade
              if temas.chave(c['tema_original']) not in feitos]
    if not pautas:                                   # sem editor: a fila de sempre
        pautas = [{'tema': c['tema_original'], 'tema_original': c['tema_original'], 'origem': c['origem'], 'area': '',
                   'partes': 0, 'motivo': 'próximo da fila', 'contexto': ''} for c in cands if c.get('tema_original')]
    # tema com pouca imagem real vai para o fim da fila (o vídeo dele costuma ser barrado por falta de material)
    pautas = [p for p in pautas if float(p.get('visual') or 10) >= 7] + [p for p in pautas if float(p.get('visual') or 10) < 7]
    final = frente + pautas
    for k, p in enumerate(final[:5]):
        print(f"  [pautas] {k + 1}. [{p.get('origem')}/{p.get('area') or '?'}] {p['tema'][:80]}"
              + (f" · viral {p.get('viral')} momento {p.get('momento')} visual {p.get('visual')} · partes {p.get('partes')}"
                 if p.get('viral') is not None else ''))
    return final
