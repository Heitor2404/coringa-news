"""RECUPERAÇÃO ÚNICA (Evidência V1, experimental) — só o que falhou na coleta 43631002615.

- Metadados/imagens: SÓ as entradas que falharam por HTTP 429. Títulos exatos numa consulta em LOTE; buscas uma a uma com
  pausa. Uma tentativa por caso: falhou de novo → registra e encerra aquele caso.
- Gemini (prompts cegos do cofre, ramo evidencia-v1), limite absoluto de 6 chamadas, sem nova tentativa:
  1 catálogo só das imagens RECUPERADAS (os catálogos que responderam são reaproveitados, não refeitos) +
  os 5 casamentos que falharam por 503/504 (naval, espaco_apollo11, historia_muro_berlim, engenharia_tacoma,
  biologia_metamorfose). A ordem das imagens no casamento = ordem do catálogo antigo + recuperadas no fim.
- Imagens já baixadas vêm do cofre privado (evidencia_imagens/) ou do repositório (Ever Given): nada é baixado de novo.
Saída: saida_recuperacao/ (cifrada pelo workflow).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import evidencia_coleta as C   # noqa: E402  (mesmas funções de consulta, sem repetir código)

ANT = RAIZ / 'tests' / 'evidencia' / 'coleta_real'
OUT = RAIZ / 'saida_recuperacao'
IMG_ANT = RAIZ / 'cofre' / 'evidencia_imagens'
MAX_NOVAS = 6
CASAR = ['naval', 'espaco_apollo11', 'historia_muro_berlim', 'engenharia_tacoma', 'biologia_metamorfose']
PAUSA = 3.0
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.append(s)


def falhou_429(r: dict) -> bool:
    return not r.get('arquivo') and any('429' in str(t.get('erro', '')) for t in r.get('tentativas') or [])


def recuperar(regs: dict) -> dict:
    alvo = {k: r for k, r in regs.items() if falhou_429(r)}
    log(f'[recuperação] {len(alvo)} entradas falharam por 429')
    novos = {}
    exatos, buscas = {}, {}
    for k, r in alvo.items():
        dom, chave = k.split('/', 1)
        for tipo, q in C.ALVOS[dom][chave]:
            if tipo == 'commons':
                exatos[k] = q; break
            if tipo == 'busca':
                buscas[k] = q; break
    for k, q in buscas.items():                                  # buscas: uma a uma, com pausa; 1 tentativa
        time.sleep(PAUSA)
        try:
            t = C.commons_busca(q)
            novos[k] = {'consulta': q, 'titulo_achado': t}
            if t:
                exatos[k] = t
            else:
                novos[k]['erro'] = 'busca sem resultado'
        except Exception as e:
            novos[k] = {'consulta': q, 'erro': str(e)[:200]}
    paginas = {}
    tit = list(dict.fromkeys(exatos.values()))
    for i in range(0, len(tit), 40):                            # títulos exatos: em LOTE
        time.sleep(PAUSA)
        try:
            j = C._get(C.COMMONS, action='query', titles='|'.join(tit[i:i + 40]), prop='imageinfo|categories',
                       iiprop='url|size|mime|extmetadata|timestamp', iiurlwidth=1024, cllimit='max', format='json', formatversion=2).json()
            norm = {n['from']: n['to'] for n in j.get('query', {}).get('normalized', [])}
            for p in j.get('query', {}).get('pages', []):
                paginas[p['title']] = p
            for a, b in norm.items():
                paginas.setdefault(a, paginas.get(b))
        except Exception as e:
            log(f'[recuperação] lote {i}: {str(e)[:150]}')
    (OUT / 'imagens').mkdir(parents=True, exist_ok=True)
    for k in alvo:
        dom, chave = k.split('/', 1)
        r = novos.setdefault(k, {})
        t = exatos.get(k)
        p = paginas.get(t) if t else None
        if t and (not p or p.get('missing') or not p.get('imageinfo')):
            r.setdefault('erro', 'título não encontrado no lote' if t in paginas or not paginas else 'lote falhou')
        if p and p.get('imageinfo'):
            r['bruto'] = {'fonte': 'Commons', 'pagina': p}
            time.sleep(PAUSA)
            dest = OUT / 'imagens' / f'{dom}__{chave}.jpg'
            try:
                info = p['imageinfo'][0]
                C.baixar(info.get('thumburl') or info['url'], dest)
                r['arquivo'] = dest.name
            except Exception as e:
                r['erro_download'] = str(e)[:200]
        log(f"[recuperação] {k}: registro={'sim' if r.get('bruto') else 'não'} arquivo={r.get('arquivo')} {r.get('erro', '')}")
    return novos


CH = 0


def chamar(prompt, imgs, modelo):
    global CH
    if CH >= MAX_NOVAS:
        return {'erro': f'limite de {MAX_NOVAS} chamadas atingido: não chamei'}
    CH += 1
    C.CHAMADAS = 0                      # o limite que vale aqui é MAX_NOVAS (contado acima)
    return C.gemini_uma_vez(prompt, imgs, modelo)


def visao(regs: dict, novos: dict):
    from src import cofre, gemini
    p_cat, p_cas = cofre.prompt('PROMPT_CATALOGO_EVIDENCIA'), cofre.prompt('PROMPT_CASAR_EVIDENCIA')
    leve, principal = gemini.MODELOS_LEVES[0], gemini.MODELOS_TEXTO[0]
    fix = {}
    for arq in ('desenvolvimento.json', 'reservado.json'):
        fix.update(json.loads((RAIZ / 'tests' / 'evidencia' / arq).read_text(encoding='utf-8'))['dominios'])
    (OUT / 'gemini').mkdir(exist_ok=True)
    # imagens recuperadas dos domínios que terão casamento: 1 catálogo único para elas
    rec = [(k, v['arquivo']) for k, v in novos.items() if v.get('arquivo') and k.split('/')[0] in CASAR]
    cat_rec = {'ordem': [k for k, _ in rec]}
    if rec:
        cat_rec['resposta'] = chamar(p_cat.format(n=len(rec)), [(OUT / 'imagens' / a).read_bytes() for _, a in rec], leve)
    (OUT / 'gemini' / '_catalogo_recuperadas.json').write_text(json.dumps(cat_rec, ensure_ascii=False, indent=1), encoding='utf-8')
    log(f"[gemini] catálogo das recuperadas: {len(rec)} imagens · {'ok' if 'texto' in cat_rec.get('resposta', {}) else cat_rec.get('resposta', {}).get('erro', 'sem chamada')}")
    for dom in CASAR:
        ant = json.loads((ANT / 'gemini' / f'{dom}.json').read_text(encoding='utf-8'))
        ordem = list(ant['ordem_das_imagens'])
        imgs = []
        for chave in ordem:
            local = IMG_ANT / f'{dom}__{chave}.jpg'
            imgs.append(local.read_bytes())
        for k, a in rec:
            if k.startswith(dom + '/'):
                ordem.append(k.split('/', 1)[1]); imgs.append((OUT / 'imagens' / a).read_bytes())
        acs = '\n'.join(f"{k}: elemento={a['bruto'].get('sujeito')}; ação={a['bruto'].get('acao')}; antes={a['bruto'].get('estado_inicial') or '-'}; "
                        f"depois={a['bruto'].get('estado_final') or '-'}" for k, a in fix[dom]['acontecimentos'].items())
        cas = chamar(p_cas.format(n=len(imgs), primeiro='0', acontecimentos=acs), imgs, principal)
        saida = {'ordem_das_imagens': ordem, 'catalogo_reaproveitado_de': f'coleta 43631002615 ({len(ant["ordem_das_imagens"])} imagens)',
                 'catalogo': ant['catalogo'], 'casamento': cas}
        (OUT / 'gemini' / f'{dom}.json').write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding='utf-8')
        log(f"[gemini] {dom}: casamento com {len(imgs)} imagens · {'ok' if 'texto' in cas else cas.get('erro')}")
        time.sleep(8)
    log(f'[gemini] chamadas novas: {CH} de no máximo {MAX_NOVAS}')


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    regs = json.loads((ANT / 'registros.json').read_text(encoding='utf-8'))
    novos = recuperar(regs)
    (OUT / 'registros_recuperados.json').write_text(json.dumps(novos, ensure_ascii=False, indent=1), encoding='utf-8')
    visao(regs, novos)
    (OUT / 'log.txt').write_text('\n'.join(LOG), encoding='utf-8')
