"""Receitas de direção (src/v3/receitas.json): padrões por FUNÇÃO NARRATIVA e TIPO DE ACONTECIMENTO, consultados pelo
diretor automático. Só entram no prompt as receitas aprovadas (boa prática) e testadas (opção); propostas, reprovadas e
obsoletas ficam fora. Nenhum fato de tema vai junto: a receita descreve o padrão."""
from __future__ import annotations

import json
from pathlib import Path

ARQ = Path(__file__).with_name('receitas.json')
CAMPOS = ('id', 'estado', 'objetivo', 'funcoes_narrativas', 'tipos_acontecimento', 'adequado', 'inadequado', 'midia',
          'requisitos_factuais', 'composicoes', 'enquadramento', 'movimento', 'anotacoes', 'transicao',
          'parametros_obrigatorios', 'exemplo_aprovado', 'exemplo_reprovado', 'motivo', 'testes')
NO_PROMPT = {'aprovado', 'testado'}


def todas(arq: Path | None = None) -> list[dict]:
    return json.loads(Path(arq or ARQ).read_text(encoding='utf-8'))['receitas']


def problemas(arq: Path | None = None) -> list[str]:
    from src.v3.memoria import ESTADOS
    out, ids = [], set()
    for r in todas(arq):
        for c in CAMPOS:
            if c not in r:
                out.append(f"{r.get('id')}: falta {c}")
        if r.get('estado') not in ESTADOS:
            out.append(f"{r.get('id')}: estado inválido {r.get('estado')}")
        if r.get('estado') == 'aprovado' and not (r.get('exemplo_aprovado') and r.get('aprovacao')):
            out.append(f"{r['id']}: aprovada sem exemplo aprovado e registro de aprovação")
        if r['id'] in ids:
            out.append(f"{r['id']}: repetida")
        ids.add(r['id'])
    return out


def recuperar(tipos: set[str], funcoes: set[str], composicoes: set[str] | None = None, limite: int = 8, arq: Path | None = None) -> list[dict]:
    """Receitas pertinentes ao vídeo, aprovadas primeiro. Pontuação: tipo de acontecimento em comum (2), função narrativa
    em comum (1); composição exigida indisponível tira a receita."""
    out = []
    for r in todas(arq):
        if r['estado'] not in NO_PROMPT:
            continue
        ti = set(r['tipos_acontecimento'])
        pt = 2 * len(ti & tipos) + (1 if '*' in ti else 0) + len(set(r['funcoes_narrativas']) & funcoes)
        if not pt:
            continue
        if composicoes is not None and not (set(r['composicoes']) & composicoes):
            continue
        out.append((r['estado'] == 'aprovado', pt, r))
    out.sort(key=lambda x: (-x[0], -x[1], x[2]['id']))
    return [r for _, _, r in out[:limite]]


def texto_prompt(rs: list[dict]) -> str:
    linhas = []
    for r in rs:
        rot = 'BOA PRÁTICA APROVADA' if r['estado'] == 'aprovado' else 'opção testada'
        enq = r.get('enquadramento') or {}
        an = '; '.join(f"{a['tipo']} {a['quando']}" for a in r.get('anotacoes') or [])
        linhas.append(f"[{r['id']} · {rot}] {r['objetivo']} Usar quando: {'; '.join(r['adequado'])}. Não usar: {'; '.join(r['inadequado'])}. "
                      f"Composições: {', '.join(r['composicoes'])}. Câmera: {r['movimento']}"
                      + (f" ({enq.get('inicial')}→{enq.get('final')})" if enq.get('inicial') else '')
                      + (f". Anotação: {an}" if an else '') + f". Transição: {r['transicao']}. Obrigatório: {'; '.join(r['parametros_obrigatorios'])}."
                      + (f" Exemplo aprovado (padrão, não copie fatos): {r['exemplo_aprovado']}" if r.get('exemplo_aprovado') else '')
                      + (f" Exemplo reprovado: {r['exemplo_reprovado']}" if r.get('exemplo_reprovado') else ''))
    return '\n'.join(linhas)
