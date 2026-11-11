"""Banco de temas do Coringa Explica.

1º a planilha do Google que vocês editam (variável TEMAS_PLANILHA = link "Publicar na web" em formato CSV);
2º se não houver planilha (ou ela acabar), a lista curada em assets/temas.txt.
O sistema pega o primeiro tema da fila que ainda não foi feito. Os já feitos ficam em data/historico_explica.json.

Planilha: 1ª linha com os nomes das colunas. Coluna obrigatória: "tema". Opcionais: "status" — linha com status
"feito", "pular" ou "não" é ignorada; "prioridade" — "sim" faz o tema sair antes de tudo. Outras colunas (ex.: "obs")
são só para vocês.
"""
import csv, io, json, os, re, unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HIST = RAIZ / 'data' / 'historico_explica.json'
LISTA = RAIZ / 'assets' / 'temas.txt'


def chave(t: str) -> str:
    t = unicodedata.normalize('NFKD', str(t)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


def usados() -> list[str]:
    try:
        return json.loads(HIST.read_text(encoding='utf-8'))
    except Exception:
        return []


def marcar_usado(tema: str):
    u = usados()
    u.append(tema)
    HIST.parent.mkdir(parents=True, exist_ok=True)
    HIST.write_text(json.dumps(u[-500:], ensure_ascii=False, indent=1), encoding='utf-8')


def _planilha() -> list[dict]:
    url = (os.getenv('TEMAS_PLANILHA') or '').strip()
    if not url:
        return []
    if '/edit' in url and 'output=csv' not in url:      # link normal da planilha: troca pelo de exportar CSV
        url = re.sub(r'/edit.*$', '/export?format=csv', url)
    try:
        import requests
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        r.encoding = 'utf-8'
        linhas = list(csv.DictReader(io.StringIO(r.text)))
    except Exception as e:
        print(f'  [temas] não consegui ler a planilha ({str(e)[:100]}); uso a lista interna')
        return []
    out = []
    for l in linhas:
        l = {chave(k): (v or '').strip() for k, v in l.items() if k}
        tema = l.get('tema') or l.get('temas') or ''
        if tema and chave(l.get('status', '')) not in ('feito', 'pular', 'nao', 'feita'):
            out.append({'tema': tema, 'prioridade': chave(l.get('prioridade', '')) in ('sim', 's', 'x', 'yes', '1')})
    print(f'  [temas] planilha: {len(out)} tema(s) na fila')
    return out


def _lista() -> list[str]:
    if not LISTA.exists():
        return []
    return [l.strip() for l in LISTA.read_text(encoding='utf-8').splitlines() if l.strip() and not l.strip().startswith('#')]


def fila_detalhada() -> list[dict]:
    """Temas ainda não feitos: planilha (com a marca de prioridade) e depois a lista interna."""
    feitos = {chave(u) for u in usados()}
    out, vistos = [], set()
    for t in _planilha() + [{'tema': x, 'prioridade': False, 'lista': True} for x in _lista()]:
        k = chave(t['tema'])
        if k and k not in feitos and k not in vistos:
            vistos.add(k)
            out.append({**t, 'planilha': not t.get('lista')})
    return out


def fila() -> list[str]:
    return [t['tema'] for t in fila_detalhada()]
