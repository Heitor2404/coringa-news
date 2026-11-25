"""Acervo do V4: para cada cena com `busca`, procura no Commons (fotos) ou em fontes de vídeo livres (Commons/Archive/
Pixabay se houver chave), baixa, escolhe a mídia que MOSTRA o pedido e localiza o objeto principal (ROI).

- Licença e crédito saem do PRÓPRIO arquivo (metadados da fonte); o crédito exibido é sempre o do asset da cena.
- Mídia não reutilizada entre cenas (regra de repetição); vídeo curto demais para a cena é descartado.
- Escolha por visão (Gemini, cota grátis) quando disponível; senão a maior resolução vertical útil (registrado).
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
from pathlib import Path

import requests

LIC = re.compile(r'\b(?:CC[ -]?(?:BY|0|PDM)|CC0|GFDL|FAL|OGL|Public domain|PD\b|PD-|domínio público|No restrictions|Attribution|Creative Commons|ShareAlike)', re.I)
UA = {'User-Agent': 'CoringaExplica/4.0 (contato via GitHub heitor2404/coringa-news)'}


def _licenca(credito: str) -> str | None:
    """a licença está no ÚLTIMO parêntese do crédito montado pelo acervo ('… — autor (LICENÇA), via …'); só a lista
    fixa de padrões deixava sem licença um vídeo do Commons com outra grafia (execução 43956541084)"""
    grupos = [g.strip() for g in re.findall(r'\(([^()]{2,60})\)', credito or '') if LIC.search(g)]
    return grupos[-1] if grupos else None      # só parêntese com cara de licença: "(1913)" não é licença


def _miniatura(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers=UA, timeout=40)
        r.raise_for_status()
        from PIL import Image
        im = Image.open(io.BytesIO(r.content)).convert('RGB')
        im.thumbnail((512, 512))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=82)
        return b.getvalue()
    except Exception:
        return None


def candidatos(busca: dict) -> list[dict]:
    from src import acervo
    q = [x for x in busca.get('consultas_en') or [] if x][:4]
    if busca.get('tipo') == 'video':                    # acervo._seguro chama a fonte SEM argumentos: lambda
        return [c for c in acervo._seguro(lambda: acervo.f_videos(q)) if c.get('video')]
    return acervo._seguro(lambda: acervo.f_commons(q))


GENERICOS = {'canal', 'canals', 'lock', 'locks', 'ship', 'ships', 'video', 'videos', 'transit', 'construction', 'the', 'of', 'and',
             'river', 'sea', 'ocean', 'port', 'boat', 'water', 'aerial', 'view', 'old', 'history', 'historic'}


def _sem_acento(t: str) -> str:
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFD', str(t or '').lower()) if unicodedata.category(ch) != 'Mn')


def nomes_proprios(consultas: list[str]) -> set[str]:
    """nomes próprios das consultas (Panama, Miraflores, Gatun): o que identifica o LUGAR, não o tipo de coisa"""
    return {_sem_acento(w) for q in consultas or [] for w in re.findall(r'\b[A-ZÁÉÍÓÚ][\wÀ-ÿ]{2,}', q) if _sem_acento(w) not in GENERICOS}


def mesmo_lugar(c: dict, nomes: set[str]) -> bool:
    """o nome do lugar aparece nos metadados? É PISTA de ordenação, não prova: sem o nome o candidato fica INCERTO (vai à
    visão com exigência de lugar+objeto); com o nome ainda precisa da confirmação visual."""
    if not nomes:
        return True
    texto = _sem_acento(f"{c.get('titulo', '')} {c.get('desc', '')} {c.get('descricao', '')} {c.get('url', '')}")
    return any(n in texto for n in nomes)


def _roi_valida(roi) -> list | None:
    """o modelo às vezes devolve pixels; ROI só vale normalizada em [0, 1]"""
    try:
        r = [float(v) for v in roi]
        return r if len(r) == 4 and all(0 <= v <= 1 for v in r) and r[2] > 0 and r[3] > 0 else None
    except Exception:
        return None


def escolher(cands: list[dict], deve_mostrar: str, usados: set[str], consultas: list[str] | None = None) -> tuple[dict | None, dict]:
    cands = [c for c in cands if c.get('url') not in usados and (_licenca(c.get('credito')) or c.get('video'))]
    nomes = nomes_proprios(consultas or [])
    # 17/11 (Heitor): tag SEM o nome do lugar não prova que a mídia é de outro lugar — o candidato fica INCERTO e só vira
    # prova se a visão confirmar lugar e objeto (abaixo). Os com o nome nas tags vêm primeiro.
    for c in cands:
        c['_lugar_nas_tags'] = mesmo_lugar(c, nomes)
    if not cands:
        return None, {'prova': 'INCERTO', 'motivo': 'sem candidato com licença'}
    cands = sorted(cands, key=lambda c: (not c['_lugar_nas_tags'], -(min(c.get('w') or 0, c.get('h') or 0))))[:6]
    if not os.getenv('GEMINI_API_KEY'):
        # auditoria 16/11: sem visão a 1ª opção NÃO vira prova — nada entra como REGISTRO
        return None, {'metodo': 'nenhum', 'prova': 'INCERTO', 'motivo': 'visão indisponível: sem prova do que a mídia mostra'}
    lugar = ', '.join(sorted(nomes)) or 'o lugar do pedido'
    try:
        from src.gemini import json_visao
        imgs = [_miniatura(c['url']) for c in cands]
        ok = [(c, b) for c, b in zip(cands, imgs) if b]
        if not ok:
            return None, {'metodo': 'visao_gemini', 'prova': 'INCERTO', 'motivo': 'nenhuma miniatura legível'}
        r = json_visao(f"""Escolha a imagem que MELHOR mostra: "{deve_mostrar}" (lugar: {lugar}). Rejeite as que mostram outra
coisa, OUTRO LUGAR, ou só texto. Seja estrito: na dúvida, -1. Responda JSON {{"escolha": índice ou -1, "motivo": "...",
"local_confere": true|false (o lugar visível é compatível com {lugar}), "objeto_confere": true|false (o objeto/ação pedido aparece),
"roi": [x, y, w, h] normalizado 0–1 do objeto principal}}. Imagens: 0..{len(ok) - 1}.""", [b for _, b in ok], leve=False)
        if isinstance(r, list):
            r = next((x for x in r if isinstance(x, dict)), {})
        k = int(r.get('escolha', -1))
        info = {'metodo': 'visao_gemini', 'motivo': r.get('motivo'), 'local_confere': r.get('local_confere'), 'objeto_confere': r.get('objeto_confere')}
        if not 0 <= k < len(ok):
            return None, {**info, 'prova': 'REPROVADO', 'motivo': 'nenhuma mostra o pedido: ' + str(r.get('motivo'))[:160]}
        if r.get('local_confere') is not True or r.get('objeto_confere') is not True:
            return None, {**info, 'prova': 'INCERTO', 'motivo': 'escolha sem confirmação de lugar e objeto: ' + str(r.get('motivo'))[:160]}
        roi = _roi_valida(r.get('roi'))
        return ok[k][0], {**info, 'prova': 'PROVADO', 'roi': roi, **({'roi_descartada': r.get('roi')} if r.get('roi') and not roi else {})}
    except Exception as e:
        return None, {'metodo': 'visao_gemini', 'prova': 'INCERTO', 'motivo': f'visão falhou: {str(e)[:160]}'}


def baixar(c: dict, pasta: Path, aid: str) -> dict:
    from src import acervo
    pasta.mkdir(parents=True, exist_ok=True)
    if c.get('video'):
        bruto = pasta / f'{aid}_bruto'
        r = requests.get(c['video']['url'], headers=UA, timeout=300)
        r.raise_for_status()
        bruto.write_bytes(r.content)
        arq = pasta / f'{aid}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(bruto), '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', str(arq)], check=True)
        bruto.unlink(missing_ok=True)
        x = dict(c, arq=str(arq))
    else:
        x = acervo._baixar_item(dict(c), pasta / f'{aid}.jpg')
        if not x.get('arq'):
            raise RuntimeError(f'download falhou: {c.get("url")}')
        x['arq'] = str(x['arq'])
        x.pop('mini', None)
    from PIL import Image
    if not c.get('video'):
        x['w'], x['h'] = Image.open(x['arq']).size
    return x


def montar(ep: dict, pasta: Path) -> tuple[dict, list[dict]]:
    """preenche params.asset das cenas com busca; devolve (acervo{id: item}, registro)"""
    acv, reg, usados = {}, [], set()
    pasta.mkdir(parents=True, exist_ok=True)
    for c in ep['cenas']:
        b = c.get('busca')
        if not b or (c.get('params') or {}).get('asset') not in (None, 'auto'):
            continue
        aid = f"{'v' if b.get('tipo') == 'video' else 'a'}{len(acv) + 1}"
        try:
            cands = candidatos(b)
            esc, info = escolher(cands, b.get('deve_mostrar') or c.get('o_que_precisa_aparecer', ''), usados, b.get('consultas_en'))
            if not esc:
                reg.append({'cena': c['id'], 'estado': 'sem_midia', 'candidatos': len(cands), **info})
                c['params']['asset'] = None
                continue
            x = baixar(esc, pasta, aid)
            usados.add(esc['url'])
            pix = 'pixabay' in str(x.get('url')) or 'pixabay' in str((x.get('video') or {}).get('url'))
            cred = x.get('credito') or (f"{x.get('titulo') or 'vídeo'} (Pixabay Content License), via Pixabay" if pix else '')
            acv[aid] = {'id': aid, 'arq': x['arq'], 'wh': [x.get('w'), x.get('h')], 'titulo': x.get('titulo'), 'desc': x.get('desc'),
                        'ano': x.get('ano'), 'credito': cred, 'licenca': _licenca(cred) or ('Pixabay Content License' if pix else None),
                        'fonte_url': x.get('url'), 'video': x.get('video'), 'roi': info.get('roi'), 'escolha': info}
            c['params']['asset'] = aid
            reg.append({'cena': c['id'], 'estado': 'ok', 'asset': aid, 'candidatos': len(cands), **info})
        except Exception as e:
            reg.append({'cena': c['id'], 'estado': 'erro', 'erro': str(e)[:200]})
            c['params']['asset'] = None
    (pasta / 'acervo.json').write_text(json.dumps(acv, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return acv, reg


# E246: discovery for the documentary director. No legacy selection fallback.
def fontes_documentais(tipo):
    from src import acervo, midia
    if tipo=='video':
        return [('commons_video',lambda q:midia.candidatos_arquivo(q)),
                ('nasa_video',lambda q:midia.candidatos_nasa_video(q)),
                ('archive_video',lambda q:midia.candidatos_archive(q))]
    if tipo=='foto':
        return [('commons',lambda q:acervo.f_commons([q])),
                ('nasa',lambda q:acervo.f_nasa([q])),
                ('loc',lambda q:acervo.f_loc([q])),
                ('met',lambda q:acervo.f_met([q]))]
    raise ValueError('E246-TIPO')


def _candidato_documental(c,fonte,tipo):
    from urllib.parse import urlsplit
    from src.v3.biblioteca import classificar_licenca
    if not isinstance(c,dict):return None
    url=c.get('url_original') or c.get('url')
    if not isinstance(url,str):return None
    u=urlsplit(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password:return None
    page=c.get('pagina')
    credit=c.get('credito') or ''
    # Legacy source labels/guesses are NOT individual license receipts.
    lic=c.get('licenca') or ''
    parsed=classificar_licenca({'licenca':lic,'credito':credit})
    rights='REVISAR_PAGINA_INDIVIDUAL'
    if fonte in ('commons','commons_video') and lic and credit and isinstance(page,str):
        p=urlsplit(page)
        if p.scheme=='https' and p.hostname=='commons.wikimedia.org' and p.path.startswith('/wiki/File:') and parsed['uso_comercial']=='sim':
            rights='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA'
    if parsed['uso_comercial']=='nao':return None
    return {'fonte':fonte,'tipo':tipo,'titulo':str(c.get('titulo') or c.get('descricao') or '')[:240],
            'descricao':str(c.get('desc') or c.get('descricao') or '')[:400],
            'url':url,'pagina':page,'credito':credit,'licenca':lic,'direitos':rights,
            'largura_declarada':c.get('w'),'altura_declarada':c.get('h'),
            'duracao_declarada':c.get('dur'),'tamanho_declarado':c.get('tamanho_original'),
            'derivado':c.get('derivado',False),'url_master':c.get('url_master'),
            'estado':'CANDIDATO_NAO_INSPECIONADO','publicar':False}


def pesquisar_cobertura(necessidade, *, biblioteca=None, fontes=None, inspecionar=None,
                       max_buscas=6, max_candidatos=12):
    """Bounded discovery from director needs, not a list of media by topic.
    A search result or textual match never constitutes verified coverage.
    Optional inspector receives candidates for this exact obligation; its
    positive response still means private review only.
    """
    if type(max_buscas) is not int or not 1<=max_buscas<=8 or type(max_candidatos) is not int or not 1<=max_candidatos<=20:
        raise ValueError('E246-ORCAMENTO')
    if necessidade.get('necessidade')=='territorio':
        return {'id':necessidade['id'],'estado':'DELEGAR_ATLAS','buscas':[],
                'candidatos':[],'pronto_para_render':False,'publicar':False}
    if necessidade.get('necessidade') not in ('registro','lacuna_explicativa'):
        raise ValueError('E246-NECESSIDADE')
    ev=necessidade.get('evidencia_visual') or 'indefinida'
    if ev not in ('movimento','estatica','contexto','indefinida'):raise ValueError('E246-EVIDENCIA')
    tipos={'movimento':('video',),'estatica':('foto','video'),
           'contexto':('foto','video'),'indefinida':('video','foto')}[ev]
    q=necessidade.get('pesquisa',{})
    consultas=[]
    for x in (q.get('consultas_en') or [])+(q.get('consultas') or []):
        if isinstance(x,str) and 2<=len(x.strip())<=180 and x.strip() not in consultas:consultas.append(x.strip())
    consultas=consultas[:2]
    if not consultas:raise ValueError('E246-CONSULTA')
    report={'id':necessidade['id'],'evidencia_visual':ev,'buscas':[],'candidatos':[],
            'biblioteca':[],'pronto_para_render':False,'publicar':False}
    vistos=set()
    # Reuse existing curated catalogue matches first; they are not approvals
    # for this new event. The global V3 search is optional and read-only.
    for item in necessidade.get('candidatos') or []:
        if item.get('natureza') not in tipos:continue
        report['biblioteca'].append({'origem':'catalogo_comprovado','asset_id':item['asset_id'],
            'tipo':item['natureza'],'sha256':item.get('sha_catalogo'),'estado':'REIDRATAR_E_INSPECIONAR'})
    if biblioteca is not None:
        for tipo in tipos:
            for item in biblioteca.buscar(consultas[0],tipo=tipo,limite=4):
                sha=item.get('sha256')
                if not sha or sha in vistos:continue
                vistos.add(sha)
                report['biblioteca'].append({'origem':'biblioteca_v3','asset_id':item['id'],'tipo':tipo,
                    'sha256':sha,'estado':'REIDRATAR_E_INSPECIONAR'})
    def analisar(c):
        if inspecionar is None:return False
        # A callback can decline; do not treat its opinion as production proof.
        try:r=inspecionar(c,necessidade)
        except Exception as e:r={'estado':'FALHA','tipo':type(e).__name__}
        c['inspecao']=r
        return isinstance(r,dict) and r.get('estado')=='PERTINENTE_PRIVADO' and r.get('necessidade_id')==necessidade['id']
    for item in report['biblioteca']:
        if analisar(item):
            return {**report,'estado':'CANDIDATO_PRIVADO_REVISADO'}
    if fontes is None:fontes=fontes_documentais
    # Interleave evidence types and sources. The second query reformulates
    # the search only if nothing reviewed has satisfied the obligation.
    rotas=[(tipo,nome,fn) for tipo in tipos for nome,fn in fontes(tipo)]
    # Take one source per type before considering a second source.
    groups=[[x for x in rotas if x[0]==tipo] for tipo in tipos]
    rotas=[g[i] for i in range(max(map(len,groups),default=0)) for g in groups if i<len(g)]
    # Reserve a round for the alternative query instead of exhausting budget
    # on the first query. Without inspection, continue looking for options.
    por_rodada=max(1,max_buscas//len(consultas))
    for ri,consulta in enumerate(consultas):
        for tipo,nome,fn in rotas[:por_rodada]:
            if len(report['buscas'])>=max_buscas:return {**report,'estado':'LACUNA_NAO_VERIFICADA'}
            row={'consulta':consulta,'tipo':tipo,'fonte':nome}
            try:raw=fn(consulta) or []
            except Exception as e:
                report['buscas'].append({**row,'estado':'FALHA','tipo_erro':type(e).__name__});continue
            added=0
            for item in raw[:12]:
                c=_candidato_documental(item,nome,tipo)
                if not c or c['url'] in vistos:continue
                if len(report['candidatos'])>=max_candidatos:break
                vistos.add(c['url']);report['candidatos'].append(c);added+=1
                if analisar(c):
                    report['buscas'].append({**row,'estado':'OK','novos':added})
                    return {**report,'estado':'CANDIDATO_PRIVADO_REVISADO'}
                if added>=2:break
            report['buscas'].append({**row,'estado':'OK' if added else 'SEM_NOVOS_CANDIDATOS','novos':added})
    return {**report,'estado':'REVISAR_CANDIDATOS' if report['candidatos'] or report['biblioteca'] else 'LACUNA_NAO_VERIFICADA'}
