---
name: coringa-auditoria
description: Use para auditar um vídeo/execução do Coringa (fiscal técnico e editorial, folha de contato, feedback por timestamp, regressões, custo) ou registrar um erro corrigido.
---
# Auditoria do Coringa

1. Resultado de execução real: ramo `v3-validacao-resultado` (cifrado). Decifrar com a chave do piloto da máquina de análise.
2. Leia nesta ordem: `resultado.json` → `fiscal_v3.md` → `folha_contato.jpg` → `storyboard_ia.json` (prompt, resposta
   original, correções, consumo) → só então o MP4.
3. Classes: **bloqueio** (objetivo) · **revisão** (olho humano) · **estética** (preferência). Id no storyboard não comprova cobertura.
4. Feedback humano: `python -m src.v3.memoria feedback <video> <mm:ss> <categoria> "texto" --gravidade revisao --direcao <direcao.json>`.
   Cada feedback liga timestamp → plano → receita. Correção generalizável vira teste e/ou regra (`proposto`).
5. Erro corrigido → `docs/memoria/erros.json` com teste de regressão; `python -m src.v3.memoria conferir` precisa passar.
6. Custo: `storyboard_ia.json.consumo` (diretor), `*-custos.json` (livro-caixa), tempos em `resultado.json`.
7. Não declarar sucesso por testes unitários ou JSON válido: MP4 + folha de contato + avaliação humana.
