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

LIMITE_TEXTO_S = 150         # o pedido ao Gemini roda em paralelo; passou disso, o fiscal segue sem ele (não segura o vídeo)
# 12/11 (Torre Eiffel 4): fatos, narrativa e recursos saíram "não medido" SEM motivo. O pedido de texto ao Gemini não foi
# respondido (o livro-caixa registra 8 chamadas do Gemini na rodada e nenhuma é do fiscal sombra) e o erro ficava só no
# .json criptografado. O fiscal sombra só tentava os modelos PRINCIPAIS do plano grátis, os mesmos que o casamento de
# imagens tinha acabado de usar; com o limite por minuto (espera de até 60 s por modelo) os 90 s estouravam. Agora:
# principais → lite (grátis também) dentro de 150 s; o motivo aparece no Telegram e no registro; avaliação do lite é marcada.
TEMPO_MIN_RODADA = 20        # minutos que precisam sobrar na rodada para o fiscal sombra rodar
PESOS = {'fatos': 25, 'imagem': 20, 'ritmo': 15, 'acabamento': 15, 'narrativa': 15, 'recursos': 5, 'audio': 5}
NOMES = {'fatos': 'fatos', 'imagem': 'imagem', 'ritmo': 'ritmo', 'acabamento': 'acabamento', 'narrativa': 'narrativa',
         'recursos': 'recursos', 'audio': 'áudio'}
INFOGRAFICOS = {'numero', 'cards', 'escala', 'lista', 'mapa', 'linha_tempo', 'comparacao', 'citacao', 'revelacao'}
# 12/11 (vídeo da Torre Eiffel): cada frase recebe UM status. "incorreta" (contradiz os fatos) é diferente de "não
# conferível" (os fatos não falam disso: pode estar certo, mas não há evidência). Não conferível NÃO é erro e NÃO ganha
# ponto: só frase CONFERIDA nos fatos soma. Com menos da metade das afirmações conferíveis, fatos = NÃO MEDIDO.
STATUS_FATO = ('confere', 'impreciso', 'erro_grave', 'nao_conferivel', 'sem_afirmacao')
ROTULO_FATO = {'confere': 'conferem', 'impreciso': 'imprecisas', 'erro_grave': 'incorretas',
               'nao_conferivel': 'não conferíveis', 'sem_afirmacao': 'sem afirmação'}
COBERTURA_MIN = 0.5


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
    m = estaticos.medir_movimento(cenas)      # 12/11: imagem imóvel × movimento de câmera que de fato muda a vista
    pontos = PESOS['ritmo'] * (1 - min(1.0, 1.5 * m['frac_estatica']))
    # mesma imagem voltando depois de outras (repetição percebida). 12/11: pela imagem NA TELA (arquivo + assinatura
    # visual), não pelo id da ideia — a foto reaproveitada da vizinha tem o id de outra ideia e não era contada
    vistas, voltas, ant = set(), 0, None
    for c, k in zip(cenas, estaticos.chaves_visuais(cenas)):
        if not c.get('img') or c.get('tipo') == 'fechamento':
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


def medir_audio(video: Path) -> dict:
    """Volume integrado (LUFS), pico real (dBTP), taxa de amostragem e canais. Só mede (não muda nada)."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(video), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True, timeout=60)
    txt = r.stderr[r.stderr.rfind('Summary:'):]
    out = {'lufs': float(re.search(r'I:\s*(-?[\d.]+) LUFS', txt).group(1)),
           'pico': float(re.search(r'Peak:\s*(-?[\d.]+) dBFS', txt).group(1))}
    try:
        p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=sample_rate,channels',
                            '-of', 'json', str(video)], capture_output=True, text=True, timeout=30)
        st = (json.loads(p.stdout or '{}').get('streams') or [{}])[0]
        out['taxa_hz'] = int(st['sample_rate']) if st.get('sample_rate') else None
        out['canais'] = int(st['channels']) if st.get('channels') else None
    except Exception:
        out['taxa_hz'] = out['canais'] = None
    return out


def texto_audio(a: dict) -> str:
    canais = {1: 'mono', 2: 'estéreo'}.get(a.get('canais'), f"{a.get('canais')} canais" if a.get('canais') else 'canais ?')
    taxa = f"{a['taxa_hz'] / 1000:g} kHz" if a.get('taxa_hz') else 'taxa ?'
    return f"volume {a['lufs']:.1f} LUFS, pico {a['pico']:.1f} dBTP, {taxa}, {canais}"


def nota_audio(video: Path) -> tuple[float | None, list[str]]:
    """Volume integrado perto de −14 LUFS e pico abaixo de −1 dBTP (o padrão das redes)."""
    try:
        a = medir_audio(video)
    except Exception as e:
        return None, [f'áudio não medido ({str(e)[:60]})']
    pontos = PESOS['audio'] - max(0.0, abs(a['lufs'] + 14) - 1.5) - (1 if a['pico'] > -1 else 0)
    return round(max(0.0, pontos), 1), [texto_audio(a)]


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
    """Gemini SEM passar pelo Claude (a cascata normal tenta o Claude primeiro e gastaria crédito da assinatura).
    Principais primeiro; sem resposta deles, os lite (grátis também). O modelo que respondeu vai em '_modelo'."""
    from google.genai import types
    from . import gemini

    def f(modelo):
        r = gemini.cliente().models.generate_content(
            model=modelo, contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.2))
        out = gemini.extrair_json(r.text)
        if isinstance(out, list):
            out = out[0] if out else {}
        if isinstance(out, dict):
            out['_modelo'] = modelo
        return out
    return gemini._tentar(f, (gemini.PRINCIPAIS + gemini.LITES) or None)


def tem_fatos(v: dict) -> bool:
    return bool(str(v.get('fatos') or '').strip())


SEM_FATOS = '(SEM FATOS PESQUISADOS: não avalie os fatos; devolva "fatos": {"frases": []})'


def avaliar_texto(v: dict, prompt_base: str | None = None, pedir=None) -> dict:
    """Fatos (25), narrativa/gancho (15) e recursos (5) num pedido só. `pedir` só é trocado nos testes."""
    from . import cofre
    base = prompt_base if prompt_base is not None else cofre.prompt('PROMPT_FISCAL_SOMBRA')
    if base.startswith('['):                      # o texto ainda não está no cofre: não mede (não inventa)
        return {}
    frases = _frases(v)
    lista = '\n'.join(f"{k + 1}. {f['fala']}  [recurso na tela: {f['recurso']}]" for k, f in enumerate(frases))
    fatos = str(v.get('fatos') or '').strip()[:12000] or SEM_FATOS
    prompt = base.format(fatos=fatos, frases=lista, titulo=v.get('titulo', ''))
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
    if not isinstance(r, dict) or not any(k in r for k in ('fatos', 'narrativa', 'recursos')):
        raise ValueError('a resposta veio sem fatos/narrativa/recursos')
    return r


def nota_fatos(f: dict, n_frases: int) -> dict:
    """Nota de fatos calculada AQUI (não pela IA), frase a frase:
    confere = 1 · impreciso = 0,5 · incorreta (erro_grave) = 0 e vira bloqueador · não conferível = 0 (sem evidência não
    ganha ponto, mas não é erro) · sem afirmação = fora da conta. Nota = 25 × pontos ÷ frases com afirmação.
    Sem lista frase a frase, ou com menos de COBERTURA_MIN das afirmações conferíveis nos fatos: NÃO MEDIDO."""
    por_frase = {}
    for x in (f or {}).get('frases') or []:
        try:
            k = int(x.get('frase'))
        except (TypeError, ValueError, AttributeError):
            continue
        st = str(x.get('status') or '').strip().lower().replace('ã', 'a').replace('í', 'i').replace('-', '_').replace(' ', '_')
        st = {'sem_fonte': 'nao_conferivel', 'incorreta': 'erro_grave', 'incorreto': 'erro_grave'}.get(st, st)
        if 1 <= k <= max(n_frases, 1) and st in STATUS_FATO:
            por_frase[k] = (st, str(x.get('explicacao') or '')[:140])
    cont = {s: sum(1 for st, _ in por_frase.values() if st == s) for s in STATUS_FATO}
    afirm = sum(cont[s] for s in ('confere', 'impreciso', 'erro_grave', 'nao_conferivel'))
    conferiveis = afirm - cont['nao_conferivel']
    itens = {s: [f'frase {k}: {e}' for k, (st, e) in sorted(por_frase.items()) if st == s]
             for s in ('impreciso', 'erro_grave', 'nao_conferivel')}
    r = {'nota': None, 'contagem': cont, 'afirmacoes': afirm, 'conferiveis': conferiveis, 'motivo': '',
         'bloqueadores': itens['erro_grave'], 'imprecisas': itens['impreciso'], 'nao_conferiveis': itens['nao_conferivel']}
    if not por_frase:
        r['motivo'] = 'a avaliação não trouxe a conferência frase a frase'
    elif not afirm:
        r['motivo'] = 'nenhuma frase com afirmação'
    elif conferiveis / afirm < COBERTURA_MIN:
        r['motivo'] = f'evidência insuficiente: só {conferiveis} de {afirm} afirmações dá para conferir nos fatos'
    else:
        r['nota'] = round(PESOS['fatos'] * (cont['confere'] + 0.5 * cont['impreciso']) / afirm, 1)
    return r


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
    motivo_texto = ''
    try:
        t = avaliar_texto(v, prompt_base=prompt_base, pedir=pedir)
        if not t:
            motivo_texto = 'o texto do fiscal sombra não está no cofre'
    except Exception as e:
        t = {}
        motivo_texto = f'o Gemini não respondeu ({type(e).__name__}: {str(e)[:90]})'
    if motivo_texto:
        obs['texto'] = [motivo_texto]
        print(f'  [fiscal sombra] fatos/narrativa/recursos não medidos: {motivo_texto}')
    else:
        modelo = str(t.get('_modelo') or '')
        obs['texto_modelo'] = [modelo] if modelo else []
        if 'lite' in modelo:
            print(f'  [fiscal sombra] texto avaliado pelo modelo lite ({modelo}): os principais não responderam')
    fatos_r = None
    if not tem_fatos(v):
        partes['fatos'] = None                            # sem fatos pesquisados não há como conferir: NÃO MEDIDO
        obs['fatos_motivo'] = ['o fiscal não recebeu os fatos pesquisados']
    elif t:
        fatos_r = nota_fatos(t.get('fatos') or {}, len(_frases(v)))
        partes['fatos'] = fatos_r['nota']
        bloqueadores += fatos_r['bloqueadores']           # incorreta: fora da média, aparece separado
        obs['fatos'] = [f'impreciso: {x}' for x in fatos_r['imprecisas']] + \
                       [f'não conferível: {x}' for x in fatos_r['nao_conferiveis']]
        if fatos_r['motivo']:
            obs['fatos_motivo'] = [fatos_r['motivo']]
    else:
        partes['fatos'] = None
        obs['fatos_motivo'] = [motivo_texto or 'sem avaliação de texto']
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
            'ritmo': medida_ritmo, 'fatos': fatos_r, 'recebeu_fatos': tem_fatos(v),
            'alertas': alertas(v, cenas, problemas_tela or [], bloqueadores), 'por_cena': por_cena(cenas)}


# ───────────────────────── plano-mestre H: alertas graves e evidência por cena ─────────────────────────
# A nota total NÃO esconde falha grave: os alertas ficam separados (P0 = não pode ir ao ar; P1 = vídeo fraco), cada um
# com a evidência. Só observação: não muda a nota, o fiscal antigo nem a publicação. Falsos positivos conhecidos:
#  - "cena central sem mídia que explique": depende da relação dada pelo Gemini e conferida por metadados (E); foto boa
#    sem ano ou sem nome no catálogo cai como contextual;
#  - "promessa não retomada": comparação por palavras (sinônimos escapam);
#  - "dado fora dos fatos": por dígitos ("três mil" escrito por extenso nos fatos não casa com 3000).
def alertas(v: dict, cenas: list[dict], problemas_tela: list, bloqueadores: list) -> list[dict]:
    from . import editorial, recursos, storyboard
    out = [{'nivel': 'P0', 'motivo': 'informação incorreta', 'evidencia': b} for b in bloqueadores]
    out += [{'nivel': 'P0', 'motivo': 'texto em cima de texto', 'evidencia': str(t)} for t in problemas_tela]
    fatos = str(v.get('fatos') or '')
    try:
        for pb in recursos.conferir(v, fatos) if fatos else []:
            if pb['inventado']:
                out.append({'nivel': 'P0', 'motivo': 'gráfico com dado fora dos fatos', 'evidencia': f"cena {pb['cena'] + 1}: {pb['problema']}"})
        for c in v.get('cenas', []):
            if c.get('_rebaixado'):
                out.append({'nivel': 'P1', 'motivo': 'gráfico rebaixado (dado fora dos fatos)', 'evidencia': c['_rebaixado']})
        from . import resolucao
        for pd in resolucao.resumo(cenas)['pendentes']:     # Etapa 2: decisão do Heitor — cena central sem representação = P0 editorial
            out.append({'nivel': 'P0' if pd['central'] else 'P1', 'motivo': f"cena sem representação ({pd['tipo'].replace('_', ' ')})",
                        'evidencia': f"cena {pd['cena']}: {pd['sugestao']}"})
        r = storyboard.resumo(cenas)
        if r['centrais_sem_explicacao']:
            out.append({'nivel': 'P1', 'motivo': 'cena central sem mídia que explique',
                        'evidencia': 'cenas ' + ', '.join(str(k + 1) for k in r['centrais_sem_explicacao'][:6])})
        p = v.get('plano') or {}
        if p and p.get('origem') != 'derivado':
            for pb in editorial.validar_plano(p, fatos) + editorial.avaliar_roteiro(v, fatos)['problemas']:
                if any(x in pb for x in ('promessa', 'payoff', 'não fecha', 'não é viável', 'suspense', 'desvio')):
                    out.append({'nivel': 'P1', 'motivo': 'roteiro', 'evidencia': pb})
    except Exception as e:                                # instrumento: nunca derruba a rodada
        out.append({'nivel': '?', 'motivo': 'alertas não medidos', 'evidencia': str(e)[:80]})
    return out


def por_cena(cenas: list[dict]) -> list[dict]:
    vistos, out = set(), []
    for c in cenas:
        sb = c.get('sb')
        if sb and id(sb) not in vistos:
            vistos.add(id(sb))
            out.append({'cena': sb['cena'] + 1, 'proposito': sb['proposito'], 'evidencia': sb['evidencia'],
                        'explica': sb['explica'], 'limitacoes': sb['limitacoes'][:3]})
    return out


def linhas_telegram(r: dict) -> list[str]:
    """Vai numa mensagem SEPARADA do resumo do vídeo (sem corte): pode listar tudo."""
    if not r or r.get('nota') is None:
        return []
    pts = ' · '.join(f"{NOMES[k]} {('%g' % p).replace('.', ',')}/{PESOS[k]}" for k, p in r['partes'].items() if p is not None)
    out = [f"🧪 Fiscal novo (TESTE, não decide nada): {str(r['nota']).replace('.', ',')}/10 — {r['faixa']}", f'   {pts}']
    if r['nao_medido']:
        motivo = (r['obs'].get('fatos_motivo') or [''])[0]
        texto = (r['obs'].get('texto') or [''])[0]
        out.append('   não medido: ' + ', '.join(NOMES[k] + (f' ({motivo})' if k == 'fatos' and motivo else '')
                                                for k in r['nao_medido'])
                   + (f' — narrativa/recursos: {texto}' if texto and texto != motivo else ''))
    modelo = (r['obs'].get('texto_modelo') or [''])[0]
    if 'lite' in modelo:
        out.append(f'   (fatos/narrativa/recursos avaliados pelo modelo lite {modelo}: os principais não responderam)')
    f = r.get('fatos')
    if f and f.get('contagem'):
        c = f['contagem']
        out.append('   📚 fatos frase a frase: ' + ' · '.join(f"{c[s]} {ROTULO_FATO[s]}" for s in STATUS_FATO)
                   + ' (não conferível = sem fonte nos fatos; não é erro e não soma ponto)')
    out += ['   ' + x for x in estaticos.resumo(r['ritmo']).split('\n')]
    out += ['   ' + x for x in (r['obs'].get('ritmo') or [])[1:]]          # imagens voltando depois de outras
    for b in r['bloqueadores']:
        out.append(f'   ⛔ informação INCORRETA (contradiz os fatos; bloqueador só no teste): {b}')
    for k in ('fatos', 'recursos'):
        for o in r['obs'].get(k) or []:
            out.append(f'   • {o}')
    al = r.get('alertas') or []
    if al:
        out.append(f"   🚩 alertas (fora da nota, não decidem): " + ' · '.join(f"{a['nivel']} {a['motivo']}" for a in al[:5]))
        for a in al[:5]:
            out.append(f"      - {a['nivel']}: {a['evidencia'][:120]}")
    ex = [c for c in r.get('por_cena') or []]
    if ex:
        n = sum(1 for c in ex if c['explica'])
        out.append(f'   🖼 representação: {n} de {len(ex)} cenas com mídia que explica a frase (storyboard)')
    return out


def salvar(r: dict, arq: Path):
    arq.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
