"""TESTE (Evidência V1, experimental): casamento cego via OpenRouter, nvidia/nemotron-3.5-super-vl:free.
Mesmo prompt cego do cofre (ramo evidencia-v1), mesmas 4 imagens do Ever Given e acontecimentos i6 (positivo) e i2 (negativo)
do teste com o Gemini. NO MÁXIMO 2 chamadas, sem nova tentativa; sem chave → nenhuma chamada. Saída cifrada pelo workflow."""
import base64, json, os, sys, time
from pathlib import Path
import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
OUT = RAIZ / 'saida_teste_openrouter'
MODELO = 'nvidia/nemotron-3.5-super-vl:free'
IMAGENS = [('a6_commons', 'a11-g.jpg'), ('a10_outro_navio', 'a23-g.jpg'), ('a12_2020', 'a27-g.jpg'), ('a1_roterda', 'a1-g.jpg')]
EVENTOS = ('i6', 'i2')
MAX = 2


def main():
    from src import cofre
    OUT.mkdir(exist_ok=True)
    res = {'modelo': MODELO, 'ordem_das_imagens': [k for k, _ in IMAGENS], 'acontecimentos': list(EVENTOS), 'chamadas': []}
    chave = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not chave:
        res['erro'] = 'sem OPENROUTER_API_KEY no repositório: nenhuma chamada feita'
    else:
        fix = json.loads((RAIZ / 'tests/evidencia/desenvolvimento.json').read_text(encoding='utf-8'))['dominios']['naval']
        acs = '\n'.join(f"{k}: elemento={a['bruto'].get('sujeito')}; ação={a['bruto'].get('acao')}; antes={a['bruto'].get('estado_inicial') or '-'}; "
                        f"depois={a['bruto'].get('estado_final') or '-'}" for k, a in fix['acontecimentos'].items() if k in EVENTOS)
        prompt = cofre.prompt('PROMPT_CASAR_EVIDENCIA').format(n=len(IMAGENS), primeiro='0', acontecimentos=acs)
        conteudo = []
        for k, (_, f) in enumerate(IMAGENS):
            b64 = base64.b64encode((RAIZ / 'tests/piloto_ever_given/img' / f).read_bytes()).decode()
            conteudo += [{'type': 'text', 'text': f'IMAGEM {k}:'}, {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}]
        conteudo.append({'type': 'text', 'text': prompt})
        corpo = {'model': MODELO, 'temperature': 0.2, 'messages': [{'role': 'user', 'content': conteudo}]}
        # chamada 1 com response_format JSON; a 2ª só acontece se a 1ª for recusada POR CAUSA desse parâmetro (400)
        for k, extra in enumerate(({'response_format': {'type': 'json_object'}}, {})):
            if k >= MAX:
                break
            t = time.time()
            try:
                r = requests.post('https://openrouter.ai/api/v1/chat/completions', timeout=240,
                                  headers={'Authorization': f'Bearer {chave}', 'Content-Type': 'application/json',
                                           'X-Title': 'coringa-evidencia-teste'}, json={**corpo, **extra})
                c = {'n': k + 1, 'status': r.status_code, 'segundos': round(time.time() - t, 1), 'json_format': bool(extra)}
                try:
                    j = r.json()
                except Exception:
                    j = {'bruto': r.text[:2000]}
                c['resposta'] = j
                res['chamadas'].append(c)
                if r.status_code == 400 and extra and 'response_format' in r.text:
                    continue
                break
            except Exception as e:
                res['chamadas'].append({'n': k + 1, 'erro': str(e)[:300], 'segundos': round(time.time() - t, 1)})
                break
    (OUT / 'casamento.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('[openrouter]', res.get('erro') or [(c.get('status'), c.get('segundos')) for c in res['chamadas']])


if __name__ == '__main__':
    main()
