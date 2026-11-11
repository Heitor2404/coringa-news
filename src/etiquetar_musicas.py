"""Etiqueta as músicas de assets/musica/ com o Gemini e salva em assets/musica/musicas.json.

    python -m src.etiquetar_musicas            # só as músicas que ainda não têm etiqueta
    python -m src.etiquetar_musicas --refazer  # refaz todas (apaga ajustes manuais)

Precisa de GEMINI_API_KEY. Revise o resultado: o "clima" de uma música é uma opinião,
e você pode corrigir o musicas.json na mão (as etiquetas existentes não são sobrescritas).
"""
import argparse, json, unicodedata
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1] / 'assets' / 'musica'
ARQ = PASTA / 'musicas.json'
CLIMAS = ['tenso', 'sério', 'neutro', 'leve', 'esperançoso', 'curioso']
ENERGIAS = ['baixa', 'média', 'alta']

PROMPT = f"""Você é curador musical de vídeos curtos de notícia e curiosidade.
Ouça esta música de fundo e classifique-a para escolher em qual tipo de vídeo ela combina.
Responda só em JSON, neste formato:
{{"clima": "<um de: {', '.join(CLIMAS)}>", "energia": "<uma de: {', '.join(ENERGIAS)}>", "descricao": "<até 15 palavras>"}}
Use "tenso" para suspense/alerta, "sério" para tom de telejornal, "leve" para descontraído, "curioso" para curiosidades."""


def _sem_acento(s: str) -> str:
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().strip()


def _escolher(valor, opcoes: list[str], padrao: str) -> str:
    """Casa o valor com uma das opções (ignorando maiúsculas e acentos). Se não casar, usa o padrão."""
    mapa = {_sem_acento(o): o for o in opcoes}
    return mapa.get(_sem_acento(str(valor)), padrao)


def validar(tag: dict) -> dict:
    """Rede de segurança: o schema já obriga os valores certos, mas se algo escapar a música NÃO é descartada.
    Cai em 'neutro'/'média' e fica marcada com a descrição 'revisar' para você conferir."""
    clima = _escolher(tag.get('clima'), CLIMAS, 'neutro')
    energia = _escolher(tag.get('energia'), ENERGIAS, 'média')
    descricao = str(tag.get('descricao', '')).strip()[:120]
    if _sem_acento(str(tag.get('clima'))) not in map(_sem_acento, CLIMAS) or _sem_acento(str(tag.get('energia'))) not in map(_sem_acento, ENERGIAS):
        descricao = ('revisar: ' + descricao).strip()
    return {'clima': clima, 'energia': energia, 'descricao': descricao}


def _schema():
    """Obriga o Gemini a responder só com os valores definidos em CLIMAS e ENERGIAS."""
    from google.genai import types
    S, T = types.Schema, types.Type
    return S(type=T.OBJECT, required=['clima', 'energia', 'descricao'], properties={
        'clima': S(type=T.STRING, enum=CLIMAS),
        'energia': S(type=T.STRING, enum=ENERGIAS),
        'descricao': S(type=T.STRING)})


def etiquetar(arq: Path) -> dict:
    from google.genai import types
    from . import gemini
    audio = types.Part.from_bytes(data=arq.read_bytes(), mime_type='audio/mpeg')

    def f(modelo):
        r = gemini.cliente().models.generate_content(
            model=modelo, contents=[PROMPT, audio],
            config=types.GenerateContentConfig(response_mime_type='application/json', response_schema=_schema(), temperature=0.2))
        return validar(gemini.extrair_json(r.text))
    return gemini._tentar(f, gemini.MODELOS_LEVES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refazer', action='store_true', help='refaz todas as etiquetas')
    a = ap.parse_args()
    atuais = {} if a.refazer or not ARQ.exists() else json.loads(ARQ.read_text(encoding='utf-8'))
    musicas = sorted(PASTA.glob('*.mp3'))
    resultado = {m.name: atuais[m.name] for m in musicas if m.name in atuais}   # some o que foi apagado da pasta
    for m in musicas:
        if m.name in resultado:
            print(f'= {m.name}: já etiquetada')
            continue
        try:
            resultado[m.name] = etiquetar(m)
            print(f'+ {m.name}: {resultado[m.name]}')
        except Exception as e:
            print(f'✘ {m.name}: {str(e)[:200]}')
    ARQ.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{len(resultado)}/{len(musicas)} etiquetadas em {ARQ}')


if __name__ == '__main__':
    main()
