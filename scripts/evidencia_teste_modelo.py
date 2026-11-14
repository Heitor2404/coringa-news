"""TESTE MÍNIMO (Evidência V1, experimental): casamento cego com modelo ALTERNATIVO, uma única chamada, sem nova tentativa.

Diagnóstico sem geração: lista os modelos visíveis para a chave e consulta o 3.8-flash e o alternativo (models.get).
Casamento: 4 imagens já guardadas do Ever Given (no repositório) × 2 acontecimentos do gabarito de desenvolvimento:
  i6 (evidência direta: a6 mostra o navio atravessado) e i2 (imagem enganosa: a10 é outro navio homônimo navegando em 2011).
Saída: saida_teste_modelo/ (cifrada pelo workflow).
"""
import json, os, sys, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
OUT = RAIZ / 'saida_teste_modelo'
ALTERNATIVO = os.environ.get('MODELO_ALTERNATIVO', 'gemini-3.6-flash')
IMAGENS = [('a6_commons', 'a11-g.jpg'), ('a10_outro_navio', 'a23-g.jpg'), ('a12_2020', 'a27-g.jpg'), ('a1_roterda', 'a1-g.jpg')]
EVENTOS = ('i6', 'i2')


def main():
    from google import genai
    from google.genai import types
    from src import cofre
    OUT.mkdir(exist_ok=True)
    cli = genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options=types.HttpOptions(timeout=240_000))
    diag = {}
    try:
        diag['modelos_visiveis'] = sorted(m.name for m in cli.models.list() if 'gemini' in m.name)
    except Exception as e:
        diag['modelos_visiveis_erro'] = str(e)[:300]
    for m in ('gemini-3.8-flash', ALTERNATIVO):
        try:
            x = cli.models.get(model=m)
            diag[m] = {k: getattr(x, k, None) for k in ('name', 'version', 'input_token_limit', 'output_token_limit')}
        except Exception as e:
            diag[m] = {'erro': str(e)[:300]}
    fix = json.loads((RAIZ / 'tests/evidencia/desenvolvimento.json').read_text(encoding='utf-8'))['dominios']['naval']
    acs = '\n'.join(f"{k}: elemento={a['bruto'].get('sujeito')}; ação={a['bruto'].get('acao')}; antes={a['bruto'].get('estado_inicial') or '-'}; "
                    f"depois={a['bruto'].get('estado_final') or '-'}" for k, a in fix['acontecimentos'].items() if k in EVENTOS)
    imgs = [(RAIZ / 'tests/piloto_ever_given/img' / f).read_bytes() for _, f in IMAGENS]
    partes = []
    for k, b in enumerate(imgs):
        partes += [f'IMAGEM {k}:', types.Part.from_bytes(data=b, mime_type='image/jpeg')]
    partes.append(cofre.prompt('PROMPT_CASAR_EVIDENCIA').format(n=len(imgs), primeiro='0', acontecimentos=acs))
    t = time.time()
    res = {'modelo': ALTERNATIVO, 'ordem_das_imagens': [k for k, _ in IMAGENS], 'acontecimentos': list(EVENTOS)}
    try:
        r = cli.models.generate_content(model=ALTERNATIVO, contents=partes,
                                        config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.2))
        res.update(texto=r.text, segundos=round(time.time() - t, 1))
        u = getattr(r, 'usage_metadata', None)
        if u:
            res['uso'] = {k: getattr(u, k, None) for k in ('prompt_token_count', 'candidates_token_count', 'thoughts_token_count', 'total_token_count')}
    except Exception as e:
        res.update(erro=str(e)[:400], segundos=round(time.time() - t, 1))
    (OUT / 'diagnostico.json').write_text(json.dumps(diag, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    (OUT / 'casamento.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('[teste]', ALTERNATIVO, 'ok' if 'texto' in res else res.get('erro', '')[:150], res.get('segundos'), 's')


if __name__ == '__main__':
    main()
