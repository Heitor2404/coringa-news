"""Diretor V4: a IA (Claude Code por assinatura; Gemini só se o Claude faltar) escreve o roteiro e ESCOLHE, por cena,
modalidade → componente → parâmetros. Regras que dependem de verificação ficam no código (contrato.validar/impor);
o prompt só informa. Uma correção dirigida com as violações; o que sobrar fica registrado (nunca aprovado por omissão).

Tempos internos dos componentes vêm como FRAÇÃO da cena (0–1) e viram segundos depois da narração real.
"""
from __future__ import annotations

import json
import re

from src.v4 import componentes, contrato

REGRAS = """IDENTIDADE: Coringa Explica — documental moderno, factual, sem apresentador. Reconstruções sempre rotuladas.
REFERÊNCIAS (técnica, não estilo copiado): Zack D. Films = gancho em 0–2 s, curiosidade crescente, cada corte acrescenta
uma revelação, payoff sem enrolar; Vox = arquivo bem escolhido, MAPA QUE ENSINA, hierarquia limpa; Primal Space =
mecanismo de verdade em 2D/2.5D (partes, estado inicial, ação, estado final, causa→efeito); Kurzgesagt = animação
vetorial PONTUAL só onde o registro real não mostra a ação.
NARRATIVA: gancho ~0–2 s; contexto ~2–8 s; progressão natural até o payoff. Nada de slides; não repetir a mesma imagem
com reenquadramento. Frases curtas, faladas, português do Brasil correto. Só fatos da lista (com fonte).
CÂMERA: FIXA por padrão. 'revelar' só com "revela" (o que entra no quadro) + justificativa; nunca no gancho. Sem zoom
para dar movimento. TRANSIÇÃO: corte. 'dissolve' só com justificativa (tempo/espaço/narrativa). Proibidos whip, iris, flash.
DEMONSTRAÇÃO: se a fala descreve ação física (sobe, enche, flui, abre, atravessa), a modalidade TEM de mostrar a ação
(esquema_2d, cena_3d, composicao_25d, registro_video ou mapa animado) — nunca foto parada ou só texto.
MAPA: localização correta, rota só com geometria real (rota_osm), nomes legíveis; nada de mapa decorativo.
SOM: efeito só ligado a um acontecimento visível (água entrando, comporta fechando), com justificativa."""

SAIDA = """Responda SÓ com JSON:
{"titulo": "...", "cenas": [{
  "id": "c1", "fala": "texto narrado desta cena (8–30 palavras)", "objetivo": "o que a cena acrescenta",
  "o_que_precisa_aparecer": "o que o espectador precisa VER", "acao_fisica": true|false,
  "modalidade": "<modalidade>", "componente": "<componente>", "params": {...},
  "busca": {"tipo": "foto|video", "consultas_en": ["termos para Wikimedia Commons"], "deve_mostrar": "..."} | null,
  "camera": {"tipo": "fixa", "enquadramento": "objeto|contexto|geral"} ou {"tipo":"revelar","revela":[...],"justificativa":"..."},
  "transicao": {"tipo": "corte"} ou {"tipo":"dissolve","justificativa":"..."},
  "sfx": [{"id": "agua_fluxo|comporta|valvula|impacto|sopro", "em": 0.0-1.0, "justificativa": "acontecimento"}],
  "fatos": ["f1"]
}]}
Tempos DENTRO de params (t, de, ate, rotulo_t, encher.de/ate, tempos.*, camera[].t) são FRAÇÕES da cena (0–1).
Componentes com acervo (registro.foto, registro.video, camadas.recorte) usam params.asset = "auto" e o bloco "busca"."""


def prompt(pedido: dict, correcoes: list[dict] | None = None, anterior: dict | None = None) -> str:
    fatos = '\n'.join(f"- {f['id']}: {f['texto']} [fonte: {f['fonte']}]" for f in pedido['fatos'])
    cat = []
    for q in pedido.get('consultas_catalogo', ['title kinetic text', 'number counter chart', 'diagram flow', 'map route']):
        r = componentes.buscar_registro(q, 5)
        if r:
            cat.append(f"  '{q}': " + '; '.join(f"{x['item']} ({x['orientacao']}, vars={x['variaveis'][:6]})" for x in r))
    fam = ', '.join(pedido.get('familias_obrigatorias') or [])
    base = f"""Você é o DIRETOR do Coringa Explica. Escreva e dirija UM episódio vertical 9:16 de {pedido['alvo_duracao'][0]}–{pedido['alvo_duracao'][1]} s
(≈ {int(pedido['alvo_duracao'][0] * 2.6)}–{int(pedido['alvo_duracao'][1] * 2.6)} palavras narradas no total), como UMA história coerente.

PERGUNTA: {pedido['pergunta']}

FATOS VERIFICADOS (use só estes; cite os ids em "fatos"):
{fatos}

{REGRAS}

MODALIDADES: {json.dumps(componentes.MODALIDADES, ensure_ascii=False)}

{componentes.resumo_prompt()}
Itens do catálogo HyperFrames relevantes (busca local):
{chr(10).join(cat) or '  (nenhum em retrato/responsivo)'}

{('FAMÍLIAS QUE O EPISÓDIO PRECISA COBRIR (cada uma onde a NARRATIVA pedir, sem catálogo de efeitos): ' + fam) if fam else ''}
{pedido.get('notas_diretor', '')}

{SAIDA}"""
    if correcoes:
        base += '\n\nSEU ROTEIRO ANTERIOR violou regras verificadas em código. Corrija SÓ o necessário e devolva o JSON inteiro:\n' + \
                '\n'.join(f"- cena {v['cena']}: [{v['regra']}] {v['texto']}" for v in correcoes) + '\n\nANTERIOR:\n' + json.dumps(anterior, ensure_ascii=False)[:24000]
    return base


def pedir(pedido: dict, correcoes=None, anterior=None) -> dict:
    from src import claude
    from src.gemini import extrair_json
    txt = None
    if claude.disponivel():
        txt = claude.pedir(prompt(pedido, correcoes, anterior))
    else:                                           # sem Claude Code: Gemini na cota grátis (registrado pelo caixa)
        from src import gemini
        txt = gemini.texto(prompt(pedido, correcoes, anterior))
    if not txt:
        raise RuntimeError('nenhum modelo de direção disponível (Claude Code/Gemini)')
    return extrair_json(txt)


CHAVES_TEMPO = {'t', 'de', 'ate', 'rotulo_t'}


def segundos(obj, dur: float, chave: str | None = None):
    """frações da cena → segundos (recursivo). 'tempos' (durações de fases) também são frações da cena."""
    if isinstance(obj, dict):
        return {k: (round(float(v) * dur, 3) if (k in CHAVES_TEMPO or chave == 'tempos') and isinstance(v, (int, float)) and 0 <= v <= 1.0001
                    else segundos(v, dur, k)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [segundos(x, dur, chave) for x in obj]
    return obj


def esqueleto(roteiro: dict, pedido: dict) -> dict:
    """roteiro da IA → episódio no contrato 4.0 (tempos provisórios por número de palavras; a narração real os substitui)"""
    cenas, t = [], 0.0
    for i, c in enumerate(roteiro.get('cenas') or []):
        d = max(1.5, len(re.findall(r'\w+', c.get('fala', ''))) / 2.6)
        cenas.append({**c, 'id': c.get('id') or f'c{i + 1}', 'ini': round(t, 3), 'fim': round(t + d, 3)})
        t += d
    return {'versao_contrato': contrato.VERSAO, 'video_id': pedido['video_id'], 'titulo': roteiro.get('titulo') or pedido['pergunta'],
            'pergunta': pedido['pergunta'], 'alvo_duracao': pedido['alvo_duracao'], 'fatos': pedido['fatos'], 'cenas': cenas}
