# Bloqueio do visual LEGADO rejeitado pelo usuário — 22/11/2026

O estilo gráfico com máquinas pequenas na parte superior e grandes áreas azul-escuras vazias foi explicitamente recusado antes. A renderização `diretor_qa.mp4` de EUV + eclusa feita em 22/11 mostrava exatamente essa estética. **A nova gramática causal não produz visual novo por si só.**

## Código e escopo
- A decisão `F-VISUAL-LEGADO-DESCARTADO` interrompe novas prévias por `eventos_diretor` quando elas tentam cair silenciosamente no antigo `FilmeEditorial`. Não inventar fallback para cards/diagramas.
- `perfil_visual="LEGADO_REJEITADO_SOMENTE_QA"` permite executar **somente regressões históricas intencionais**, não significa aprovação de design. Retorno `visual_approval=REPROVADO_ESTILO_LEGADO`.
- QA do diretor com esse perfil compila mas **não renderiza MP4**. Outras regressões históricas mais antigas continuam isoladas; nunca apresentar seus arquivos como a nova direção.
- Testes e fontes já existentes recebem marcador explícito na branch experimental. Não mexer em `main`.

## Critério objetivo de próximo avanço
1. `plano_causal.eventos[].camera.alvos` deve ser **consumido realmente** no renderer por alvo conhecido e relação física.
2. Enquadramento 9:16 em alta ocupação, com bboxes validadas contra clips, legendas e UI, sem encolher toda a cena.
3. Ao menos duas famílias diferentes têm que usar a **mesma regra** sem coordenadas de assunto codificadas na lógica comum.
4. Testar MP4 real e inspecionar 8–16 frames, não só o grafo ou métricas RGB; rejeitar se o mecanismo continuar pequeno.
5. Não afirmar que a estética foi aprovada sem validação humana.

**Estado:** guard de regressão implementado; novo renderizador visual por eventos AINDA NÃO.
