"""Acesso ao Gemini com troca automática de modelo quando a cota acaba."""
import json, os, re, time

MODELOS_TEXTO = [m.strip() for m in os.getenv('GEMINI_MODELOS', 'gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite').split(',') if m.strip()]
# tarefas simples (escolher pauta, checar fatos) usam primeiro os modelos "lite", que têm mais cota grátis
MODELOS_LEVES = [m.strip() for m in os.getenv('GEMINI_MODELOS_LEVES', 'gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.6-flash,gemini-3.8-flash').split(',') if m.strip()]
# modelos "de verdade" (qualidade) e os "lite" (mais cota, menos qualidade)
PRINCIPAIS = [m for m in MODELOS_TEXTO if 'lite' not in m]
LITES = [m for m in MODELOS_TEXTO if 'lite' in m]
# 2ª chave (opcional, de outra conta Google): quando a cota grátis da 1ª acaba, o sistema continua com a 2ª
CHAVES = [k for k in (os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2')) if k]
_clientes: dict = {}
_chave = 0
_esgotado: set = set()     # (chave, modelo) com a cota do dia acabada: não perde tempo tentando de novo
_busca_off = os.getenv('GEMINI_BUSCA_WEB', '1') == '0'


def cliente():
    if not CHAVES:
        raise RuntimeError('sem GEMINI_API_KEY')
    if _chave not in _clientes:
        from google import genai
        from google.genai import types
        # sem limite de tempo, uma chamada travada no Google deixava o vídeo parado por horas
        _clientes[_chave] = genai.Client(api_key=CHAVES[_chave], http_options=types.HttpOptions(timeout=240_000))
    return _clientes[_chave]


def _cota_do_dia(msg: str) -> bool:
    """A mensagem "You exceeded your current quota" vem IGUAL para o limite por minuto e para o do dia; o que muda é o
    quotaId (…PerMinute… ou …PerDay…). Antes qualquer 429 era tratado como "acabou o dia" e a chave era descartada à toa."""
    m = msg.lower()
    if 'perminute' in m or 'per minute' in m:
        return False
    return 'limit: 0' in m or 'perday' in m or 'per day' in m


_lento: dict = {}   # modelo → até quando fica de lado (sobrecarga/travamento)


def _tentar(fn, modelos=None):
    """Tenta cada chave e cada modelo; em sobrecarga (503) ou limite por minuto (429) espera e tenta de novo antes de trocar.
    Cota do dia acabada: troca na hora (de modelo e, se tiver, de chave)."""
    global _chave
    erro = None
    principal = modelos is None or modelos == PRINCIPAIS
    from .orcamento import sobra
    # sobrecarga: espera pouco e passa para o próximo modelo/chave/serviço (esperar 15+30+60 s em cada modelo comia
    # 15 minutos da execução de 10/11 e o tema ficou sem tempo para ser trocado)
    esperas = [8]
    ordem = list(range(_chave, len(CHAVES))) + list(range(0, _chave))
    for ch in ordem:
        _chave = ch
        for modelo in (modelos or MODELOS_TEXTO):
            if (ch, modelo) in _esgotado or _lento.get(modelo, 0) > time.time():
                continue
            for tentativa in range(len(esperas) + 1):
                try:
                    r = fn(modelo)
                    from . import custo
                    custo.registrar('gemini', modelo)        # grátis: só conta o pedido (separado do Claude)
                    time.sleep(4)   # respeita o limite de pedidos por minuto do plano grátis
                    return r
                except Exception as e:  # cota, sobrecarga, etc.
                    erro = e
                    msg = str(e)
                    if '429' in msg or 'RESOURCE_EXHAUSTED' in msg:
                        tipo = 'do DIA' if _cota_do_dia(msg) else 'por MINUTO'
                        print(f'  [gemini] {modelo} (chave {ch + 1}): limite {tipo} atingido')
                        if tipo == 'do DIA':
                            _esgotado.add((ch, modelo))
                            break          # cota do dia desse modelo acabou: tenta o próximo
                        if tentativa >= 1:
                            break
                        espera = re.search(r'retry in ([0-9.]+)s|retrydelay["\': ]+([0-9.]+)s', msg, re.I)
                        time.sleep(min(60.0, float(next(g for g in espera.groups() if g)) + 1) if espera else 30)
                    elif '504' in msg or 'DEADLINE' in msg:
                        _lento[modelo] = time.time() + 600     # travando: deixa esse modelo de lado por 10 minutos
                        break
                    elif ('503' in msg or 'UNAVAILABLE' in msg or '500' in msg or 'overloaded' in msg.lower()) and tentativa < len(esperas):
                        print(f'  [gemini] {modelo} sobrecarregado; espero {esperas[tentativa]}s e tento de novo')
                        time.sleep(esperas[tentativa])
                    else:
                        break
            if '503' in str(erro) or 'UNAVAILABLE' in str(erro):
                _lento[modelo] = time.time() + 300         # sobrecarregado: 5 minutos sem tentar esse modelo
            print(f'  [gemini] {modelo}' + (f' (chave {ch + 1})' if len(CHAVES) > 1 else '') + f' falhou: {str(erro)[:120]}')
    try:                                     # plano-mestre I: a falha também entra no livro-caixa (ok=False, grátis)
        from . import custo
        custo.registrar('gemini', 'indisponível', ok=False)
    except Exception:
        pass
    raise RuntimeError(f'Gemini indisponível: {erro}')


def pesquisar(prompt: str) -> str:
    """Texto livre, com busca no Google para checar fatos.
    No plano grátis a busca pode não estar liberada: aí levanta erro rápido e quem chamou usa a reserva."""
    global _busca_off
    if _busca_off:
        raise RuntimeError('busca na web desligada nesta execução')
    from google.genai import types
    erro = None
    for modelo in MODELOS_TEXTO[:1]:
        try:
            r = cliente().models.generate_content(
                model=modelo, contents=prompt,
                config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0.3))
            time.sleep(4)
            if r.text and len(r.text) > 200:
                return r.text
        except Exception as e:
            erro = e
    _busca_off = True   # não insiste: no plano grátis ela costuma não estar liberada e só gastaria cota
    raise RuntimeError(f'busca indisponível: {str(erro)[:160]}')


def texto(prompt: str, leve: bool = False) -> str:
    """Texto livre, sem busca."""
    from google.genai import types
    def f(modelo):
        r = cliente().models.generate_content(model=modelo, contents=prompt,
                                              config=types.GenerateContentConfig(temperature=0.3))
        return r.text or ''
    return _em_cascata(f, prompt, False, leve)


def json_(prompt: str, leve: bool = False):
    """Resposta em JSON."""
    from google.genai import types
    def f(modelo):
        r = cliente().models.generate_content(
            model=modelo, contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.6))
        return extrair_json(r.text)
    return _em_cascata(f, prompt, True, leve)


RESERVAS_USADAS: list[str] = []      # tarefa de qualidade (roteiro, revisão, gancho) que saiu de modelo reserva


def _em_cascata(f, prompt: str, json_mode: bool, leve: bool):
    """Ordem de qualidade: CLAUDE (assinatura Pro; Sonnet, ou Haiku nas tarefas simples) → Gemini principal (todas as
    chaves) → Groq GPT-OSS 120B → Gemini lite → Cloudflare. Assim o Gemini sobrecarregado não estraga mais o roteiro."""
    from . import claude
    if claude.disponivel():
        try:
            txt = claude.pedir(prompt, leve)
            return extrair_json(txt) if json_mode else txt
        except Exception as e:            # sem crédito, fora do ar, JSON quebrado: segue para o Gemini
            print(f'  [claude] falhou ({str(e)[:160]}); sigo com o Gemini')
    if leve:
        try:
            return _tentar(f, MODELOS_LEVES)
        except RuntimeError as e:
            return _reserva(prompt, json_mode, e)
    try:
        return _tentar(f, PRINCIPAIS)
    except RuntimeError as e:
        erro = e
    try:
        txt = _groq(prompt, json_mode)
        print('  [ia] Gemini principal sem cota; usei o Groq (GPT-OSS 120B)')
        RESERVAS_USADAS.append('Groq')
        return extrair_json(txt) if json_mode else txt
    except Exception as e:
        print(f'  [ia] reserva groq falhou: {str(e)[:120]}')
    try:
        r = _tentar(f, LITES)
        RESERVAS_USADAS.append('Gemini lite')
        return r
    except RuntimeError as e:
        RESERVAS_USADAS.append('Cloudflare')
        return _reserva(prompt, json_mode, e, so_cloudflare=True)


def extrair_json(txt: str):
    txt = (txt or '').strip()
    txt = re.sub(r'^```(?:json)?|```$', '', txt, flags=re.M).strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        m = re.search(r'[\[{].*[\]}]', txt, re.S)
        return json.loads(m.group(0))


# ───────────── reservas gratuitas quando o Gemini falhar (Groq → Cloudflare) ─────────────
def _groq(prompt: str, json_mode: bool) -> str:
    import requests
    chave = os.getenv('GROQ_API_KEY')
    if not chave:
        raise RuntimeError('sem GROQ_API_KEY')
    erro = None
    for modelo in [os.getenv('GROQ_MODELO', 'openai/gpt-oss-120b'), 'openai/gpt-oss-20b']:   # o llama-3.3 foi desativado (404)
        corpo = {'model': modelo, 'temperature': 0.6, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 8000}
        if json_mode:
            corpo['response_format'] = {'type': 'json_object'}
        r = requests.post('https://api.groq.com/openai/v1/chat/completions', json=corpo, timeout=180,
                          headers={'Authorization': f'Bearer {chave}'})
        if r.ok:
            return r.json()['choices'][0]['message']['content']
        erro = f'{modelo}: {r.status_code} {r.text[:120]}'
    raise RuntimeError(erro)


def _cloudflare_txt(prompt: str, json_mode: bool) -> str:
    import requests
    conta, token = os.getenv('CF_ACCOUNT_ID'), os.getenv('CF_API_TOKEN')
    if not (conta and token):
        raise RuntimeError('sem chaves da Cloudflare')
    modelo = os.getenv('CF_MODELO_TEXTO', '@cf/meta/llama-3.3-70b-instruct-fp8-fast')
    r = requests.post(f'https://api.cloudflare.com/client/v4/accounts/{conta}/ai/run/{modelo}', timeout=120,
                      headers={'Authorization': f'Bearer {token}'},
                      json={'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 4000})
    r.raise_for_status()
    resp = r.json()['result']['response']
    return resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)


def _reserva(prompt: str, json_mode: bool, erro_gemini, so_cloudflare: bool = False):
    for nome, fn in ((('cloudflare', _cloudflare_txt),) if so_cloudflare else (('groq', _groq), ('cloudflare', _cloudflare_txt))):
        try:
            txt = fn(prompt, json_mode)
            print(f'  [ia] Gemini indisponível; usei a reserva: {nome}')
            return extrair_json(txt) if json_mode else txt
        except Exception as e:
            print(f'  [ia] reserva {nome} falhou: {str(e)[:120]}')
    raise RuntimeError(f'nenhuma IA disponível (Gemini: {str(erro_gemini)[:120]})')


def json_visao(prompt: str, imagens: list[bytes], leve: bool = True):
    """Mostra imagens ao Gemini (que enxerga) e pede uma resposta em JSON. Sem reserva: se falhar, quem chamou decide."""
    from google.genai import types
    partes = []
    for k, img in enumerate(imagens):
        partes += [f'IMAGEM {k}:', types.Part.from_bytes(data=img, mime_type='image/jpeg')]
    partes.append(prompt)

    def f(modelo):
        r = cliente().models.generate_content(
            model=modelo, contents=partes,
            config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.2))
        return extrair_json(r.text)
    if leve:
        return _tentar(f, MODELOS_LEVES)
    try:                                   # olhar imagens: principal (todas as chaves) → lite (todas as chaves)
        return _tentar(f, PRINCIPAIS)
    except RuntimeError:
        print('  [ia] visão: Gemini principal sem cota; uso o modelo lite')
        return _tentar(f, LITES)
