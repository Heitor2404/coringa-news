"""RESOLUÇÃO VISUAL POR CENA (auditoria estrutural, Etapa 2 — 13/11/2026).

O storyboard passa a DECIDIR a mídia de cada ideia. O resolvedor olha o que a cena precisa mostrar (`sb.necessidade`) e o
que o acervo/casamento/planos sem foto ofereceram, e grava em `sb.resolucao`:
  tipo         evidencia_real · reconstrucao_explicativa · ilustracao_conceitual · contexto
               (ou pendente: esquema_pendente · reconstrucao_pendente)
  midia        id do acervo, "ia", "video_clima", "vizinha", "infografico" ou None
  nivel        direto · explicativo · ilustrativo · contextual · sem_midia
  justificativa, rejeitadas [{midia, motivo}], pendente (bool), sugestao (o que falta fazer)
Depois `aplicar` escreve os campos antigos (foto/midia/prompt_imagem) A PARTIR da resolução — a montagem continua lendo
os mesmos campos (migração gradual), mas agora derivados de uma fonte só. Cena pendente NÃO recebe foto emprestada nem
imagem de IA: a montagem a mostra sem mídia e marcada `pendente` (nunca como se estivesse resolvida).

Regras (sem afrouxar nem inventar):
  processo   → registro real do próprio processo (relação "fato" conferida) ou diagrama real do acervo; foto do assunto,
               foto vizinha ou imagem de IA "estilo diagrama" NÃO resolvem (IA pode inventar ciência) → esquema_pendente
  acontecimento (evidência/payoff) → registro real do fato ou documento; ilustração de IA sinalizada (nunca de documento);
               retrato/lugar/foto do tema sozinhos não mostram o fato → reconstrucao_pendente
  acontecimento_flex → aceita pessoa/lugar/objeto do próprio fato como contexto
  contexto / documental / grafico → como antes (contexto rotulado como contexto)
Etapa 3 (13/11): o critério é se a mídia REPRESENTA o acontecimento, não o rótulo "genérica" do catálogo — mídia real
cujo conteúdo mostra o que a cena precisa vale como evidência real (selecao.mostra_o_fato); em processo, vídeo do
fenômeno vale, foto estática não demonstra o funcionamento. Evidência real, reconstrução explicativa e ilustração
conceitual continuam distintas.
Roteiro sem storyboard (antigo): nada muda.
"""
from . import selecao, storyboard

INFOGRAFICOS = storyboard.INFOGRAFICOS
REAIS = ('fato', 'documento')
LIGADAS = ('pessoa', 'lugar', 'objeto')
PAPEL = ('documento', 'jornal', 'manuscrito', 'carta', 'cartaz')


def _candidato(c: dict, por_id: dict) -> tuple[str | None, dict]:
    """O que as etapas anteriores puseram nesta ideia."""
    x = por_id.get(c.get('foto')) if c.get('foto') else None
    if x is not None:
        return c['foto'], x
    if c.get('midia') in ('ia', 'video', 'vizinha'):
        return {'ia': 'ia', 'video': 'video_clima', 'vizinha': 'vizinha'}[c['midia']], {}
    return None, {}


def _classe(c: dict, mid: str | None, x: dict) -> tuple[str, str]:
    """(tipo de evidência que a mídia candidata É, nível)."""
    if c.get('tipo') in INFOGRAFICOS:
        return 'reconstrucao_explicativa', 'explicativo'
    if mid is None:
        return 'nenhuma', 'sem_midia'
    if mid == 'ia':
        return 'ilustracao_conceitual', 'ilustrativo'
    if mid in ('vizinha', 'video_clima'):
        return 'contexto', 'contextual'
    rel = c.get('relacao')
    esc = c.get('_escolha') or {}
    if str(x.get('tipo_img') or '').lower() == 'diagrama' or rel == 'diagrama':
        return 'reconstrucao_explicativa', 'explicativo'
    if rel in REAIS and esc.get('verificada', True) is not False:
        return 'evidencia_real', 'direto'
    if rel in LIGADAS:
        return 'ligada', 'contextual'
    return 'contexto', 'contextual'


def _real_que_mostra(c: dict, nec: str, mid, x: dict, classe: str, excluir) -> tuple[str | None, str, list[str]]:
    """Etapa 3: mídia REAL do acervo (foto/vídeo) que mostra o que a cena precisa vale como evidência, mesmo marcada
    "genérica" ou com relação "tema". Devolve (classe nova ou None, justificativa/motivo de recusa, raízes em comum).
      acontecimento/flex/documental/contexto: mostra → evidência real (polvo camuflado na frase da camuflagem)
      processo: VÍDEO que mostra → evidência real (o fenômeno acontecendo); foto estática só se o casamento, que VIU a
                imagem, disse "fato" — senão ela mostra o resultado, não o mecanismo (fica esquema)"""
    if not x or mid in (None, 'ia', 'vizinha', 'video_clima') or classe not in ('ligada', 'contexto', 'evidencia_real'):
        return None, '', []
    ok, comum = selecao.mostra_o_fato(x, c, excluir)
    if not ok:
        return None, '', []
    if nec == 'processo' and not x.get('video'):
        if classe == 'evidencia_real':
            return 'evidencia_real', 'registro real (casamento disse "fato") com o que a cena mostra: ' + ', '.join(comum[:3]), comum
        return None, 'foto estática mostra o resultado, não o funcionamento (' + ', '.join(comum[:3]) + ')', comum
    oque = 'vídeo real mostra o fenômeno acontecendo' if x.get('video') else 'mídia real mostra o próprio acontecimento'
    return 'evidencia_real', f"{oque}: {', '.join(comum[:3])}", comum


def resolver_cena(c: dict, por_id: dict, excluir=frozenset()) -> dict:
    sb = c['sb']
    nec = sb.get('necessidade') or 'documental'
    mid, x = _candidato(c, por_id)
    if x.get('tipo_img'):
        c['_tipo_img'] = str(x['tipo_img']).lower()        # para o storyboard saber que é diagrama/documento
    classe, nivel = _classe(c, mid, x)
    rej = []
    tipo, just, pend, sug = None, '', False, ''
    papel = str(x.get('tipo_img') or '').lower() in PAPEL
    nova, porque, comum = _real_que_mostra(c, nec, mid, x, classe, excluir)
    if nova:
        if classe != 'evidencia_real' or nec == 'processo':
            classe, nivel = 'evidencia_real', 'direto'
            c['_mostra_fato'] = porque
    elif nec == 'processo' and classe == 'evidencia_real' and mid and not x.get('video'):
        classe = 'contexto'                               # "fato" de foto estática sem o que a cena mostra: não é mecanismo
    if porque and not nova:
        rej.append({'midia': mid, 'motivo': porque})
    if nec == 'grafico' or classe == 'reconstrucao_explicativa':
        tipo, just = 'reconstrucao_explicativa', ('infográfico com dado dos fatos' if c.get('tipo') in INFOGRAFICOS
                                                  else 'diagrama real do acervo explica o processo')
    elif classe == 'evidencia_real':
        tipo, just = 'evidencia_real', (c.pop('_mostra_fato', None)
                                        or f"registro real do próprio fato ({c.get('relacao')}{', documento' if papel else ''})")
    elif nec == 'processo':
        if mid and not porque:
            rej.append({'midia': mid, 'motivo': {'ia': 'imagem de IA não é esquema confiável (pode inventar ciência)',
                                                 'vizinha': 'foto emprestada não mostra o processo'}.get(mid, 'foto do assunto não mostra o processo')})
        tipo, pend, nivel = 'esquema_pendente', True, 'sem_midia'
        just = 'processo sem registro real nem diagrama no acervo'
        sug = 'ESQUEMA: ' + (sb.get('intencao_visual') or sb.get('narracao', ''))[:100]
    elif nec == 'acontecimento':
        if classe == 'ilustracao_conceitual' and sb.get('midia_preferida') != 'documento':
            tipo, just = 'ilustracao_conceitual', 'reconstrução ilustrada do fato (sinalizada como IA)'
        else:
            if mid:
                rej.append({'midia': mid, 'motivo': {'ligada': 'retrato/lugar mostra quem ou onde, não o fato',
                                                     'contexto': 'foto do tema não mostra o fato',
                                                     'ilustracao_conceitual': 'documento não se fabrica com IA'}.get(classe, 'não mostra o fato')})
            tipo, pend, nivel = 'reconstrucao_pendente', True, 'sem_midia'
            just = 'fato central sem registro real nem reconstrução'
            sug = 'RECONSTRUÇÃO ou REPLANEJAR: ' + (sb.get('intencao_visual') or sb.get('narracao', ''))[:100]
    elif classe == 'ilustracao_conceitual':
        tipo, just = 'ilustracao_conceitual', 'ilustração sinalizada (não há registro real)'
    elif classe in ('ligada', 'contexto'):
        tipo = 'contexto'
        just = ('pessoa/lugar/objeto do próprio fato' if classe == 'ligada' else
                'foto emprestada da cena vizinha' if mid == 'vizinha' else 'foto do assunto, como contexto')
        if nec == 'documental' and classe == 'ligada':
            tipo, nivel, just = 'evidencia_real', 'direto', 'a frase é sobre esta pessoa/lugar/objeto'
    else:                                                # sem mídia e sem necessidade estrita: a montagem empresta
        tipo, nivel, just = 'contexto', 'contextual', 'sem mídia própria: a montagem continua a imagem anterior'
        mid = 'vizinha'
    for r in (c.get('_escolha') or {}).get('rejeitadas') or []:
        rej.append({'midia': r.get('foto'), 'motivo': r.get('motivo')})
    return {'tipo': tipo, 'midia': None if pend else mid, 'nivel': nivel, 'justificativa': just, 'rejeitadas': rej[:6],
            'pendente': pend, 'sugestao': sug, 'necessidade': nec, 'mostra': comum[:4]}


def resolver(v: dict) -> dict:
    """Uma vez, depois do acervo e dos planos sem foto. Grava sb.resolucao e alinha os campos antigos (aplicar)."""
    por_id = {x['id']: x for x in v.get('acervo') or []}
    excluir = selecao.assunto(v)
    for c in v.get('cenas', []):
        if c.get('sub') or c.get('tipo') == 'fechamento' or not c.get('sb'):
            continue
        c['sb']['resolucao'] = resolver_cena(c, por_id, excluir)
        aplicar(c)
    for c in v.get('cenas', []):                         # pedaços da mesma ideia seguem a ideia
        if c.get('sub') and c.get('sb') and c['sb'].get('resolucao'):
            aplicar(c)
    pend = [c['sb']['cena'] + 1 for c in v.get('cenas', []) if not c.get('sub') and (c.get('sb') or {}).get('resolucao', {}) and c['sb']['resolucao']['pendente']]
    if pend:
        print(f"  [resolução] {len(pend)} cena(s) pendente(s) (sem mídia que represente): {', '.join(map(str, pend))}")
    return v


def aplicar(c: dict):
    """Os campos que a montagem lê saem da resolução (fonte única)."""
    r = c['sb']['resolucao']
    if r['pendente']:
        c.pop('foto', None)
        c.pop('relacao', None)
        c.pop('prompt_imagem', None)
        c['midia'] = 'pendente'
        c['pendente'] = r['tipo']
    else:
        c.pop('pendente', None)


def resumo(cenas: list[dict]) -> dict:
    vistos, cont, pend = set(), {}, []
    for c in cenas:
        sb = c.get('sb')
        if not sb or id(sb) in vistos or not sb.get('resolucao'):
            continue
        vistos.add(id(sb))
        t = sb['resolucao']['tipo']
        cont[t] = cont.get(t, 0) + 1
        if sb['resolucao']['pendente']:
            pend.append({'cena': sb['cena'] + 1, 'tipo': t, 'sugestao': sb['resolucao']['sugestao'],
                         'central': sb['necessidade'] in storyboard.ESTRITAS})
    return {'contagem': cont, 'pendentes': pend}


def linha_telegram(cenas: list[dict]) -> str:
    r = resumo(cenas)
    if not r['contagem']:
        return ''
    nomes = {'evidencia_real': 'evidência real', 'reconstrucao_explicativa': 'reconstrução explicativa',
             'ilustracao_conceitual': 'ilustração conceitual', 'contexto': 'contexto',
             'esquema_pendente': 'ESQUEMA PENDENTE', 'reconstrucao_pendente': 'RECONSTRUÇÃO PENDENTE'}
    return '🧩 Resolução visual: ' + ' · '.join(f'{n} {nomes.get(t, t)}' for t, n in r['contagem'].items())
