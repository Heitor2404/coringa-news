# ATLAS — plano de recuperação P0, baseado em evidência (19/11/2026)

**Decisão:** vídeo Chips de 32,1 s reprovado pelo responsável; NÃO publicar. O problema não é "a velocidade do Gemini", nem "a fonte pequena": é a falta de prova visual, direção e verificação editorial no processo que cria os beats. Esta versão não é referência de estilo.

## Evidência material

1. `docs/memoria/erros.json`: 84 registros de engenharia (vários com testes verdes). 
2. `docs/memoria/feedback.jsonl`: 8 avaliações antigas abertas do Panamá, sem fechamento; adicionado o episódio Chips com 5 registros (um da reprovação explícita do responsável, os demais auditoria independente por trecho).
3. `docs/memoria/regras_editoriais.json`: 0 regras antes desta intervenção; 3 regras agora **propostas**, não automaticamente aprovadas.
4. `src/v3/revisao_multimodal.py`: revisão audiovisual por plano já existia na V3; **NÃO era executada no workflow ATLAS `atlas-chips-v2-privado.yml`**.
5. `src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json`: exatamente 2 fotografias e 6 beats, majoritariamente mapa/etiqueta. `atlas.prova` usa mapa de fundo em fotos; `atlas.protagonista` não tem representação de máquinas, projeto e fabricação.
6. Workflow exigia `len(usados)==2`, `len(beats)==6`, `not p["clipes"]`; limites de piloto indevidamente travados antes da direção. Removidos limites arbitrários sobre nº de fotos/ordem de cenas.

## Ações implantadas na branch experimental

- `src/v4/formatos/triagem_editorial.py` + teste: preflight de evidência **antes de sintetizar voz**. Diretor/roteiro deve declarar por beat verbo visual, pergunta, referente, aprendizado e IDs de provas efetivamente presentes, ligados a fatos com fontes. Um título, cartão, etiqueta ou mapa genérico não é prova de ação/indústria/cadeia. O piloto rejeitado agora falha **sem gastar TTS**.
- `.github/workflows/atlas-chips-v2-privado.yml`: chama esse gate logo após checkout; não roda voz/render quando contrato insuficiente. Piloto antigo permanece rejeitado, sem liberar produção.
- `src/v4/formatos/revisao_visual.py` + testes: crítico visual independente usando Gemini visão e imagens renderizadas (amostras de cada beat) **depois do QA geométrico e antes do MP4**; tenta detectar objeto ausente, mídia ruim/ilegível, mapa decorativo, aprendizado não demonstrado, enquadramento ruim. Falha bloqueia; ausência de Gemini também bloqueia, sem substituir por falsa aprovação. Registra `revisao_visual.json` e envia motivo no Telegram.
- `src/v4/formatos/produzir.py::render` exige revisão visual aprovada quando `formato=atlas`; não altera DOSSIÊ/NTC. Revisor estático não substitui inspeção de movimento, nem aprovação humana.
- `src/v4/formatos/diretor.py`: novo contrato explícito no prompt e memória V3 de **reprovações humanas como contraexemplos** + **regras apenas se aprovadas**. Memória não é fine-tuning.
- `docs/memoria/feedback.jsonl` / `regras_editoriais.json`: 5 feedbacks, 3 regras propostas. Nenhuma regra promovida sem avaliação em episódios distintos.
- CI `44456958676` passou 144 testes Python + TypeScript com estes novos gates; exceção: mudanças subsequentes no prompt de memória devem ser submetidas ao CI complementar.

## Lacunas restantes — não declarar cura completa

1. **Visual plan ANTES da voz**: gerar amostras/animatic de baixa resolução sem TTS final; isso reduz custo e evita gastar minutos e chamadas de IA com algo visualmente condenado. Render atual de frames ainda requer um plano resolvido com áudio. Requer desacoplar `quadros` dos timestamps de áudio por uma agenda provisória.
2. **Biblioteca visual suficiente e curada**: priorizar conteúdo factual claro e licenciado do objeto em questão. Pipeline deve pesquisar/selecionar mídia para a ação ANTES de fechar a história; usar `src/v3/biblioteca.py`, `src/v4/viabilidade.py`, `src/v4/formatos/ponte_biblioteca.py`. Não fingir EUV nem alterar procedência. Se não houver mídia, adaptar a pauta ou parar.
3. **Revisão do movimento em MP4**: `src/v3/revisao_multimodal.py` revisa 4 quadros ordenados do vídeo e critério visual por evento; adaptar para ATLAS e unir diagnóstico do estilo ao de movimento depois de MP4. Revisor de styleframes não comprova ação.
4. **Laço de autocorreção controlada**: revisor → JSON de defeitos classificados por beat → diretor propõe NO MÁXIMO 1 correção de storyboard/composição usando mídia comprovada → nova triagem e styleframes → novo julgamento. Não alterar código, modelos, fontes ou regras silenciosamente; se persistir, bloquear com diagnóstico. Medir custo/latência por tentativa e manter orçamento Claude total ≤ US$0,30, caso aplicável.
5. **Calibração comparativa às 2 referências**: legibilidade, ocupação do assunto, tipos de provas concretas, clareza, densidade e sentido do movimento. Não imitar nem importar fotogramas sem licença. `A` e `B` são gramáticas diferentes; a execução ATLAS não pode virar dossiê nem NTC.

## Próxima prova pequena (sem MP4 completo)

**Tema piloto Chips, 20–25 s — storyboard auditável:** objeto real (chip/wafer legível) → fábrica/Taiwan com mapa regional apertado → equipamento de fabricação real identificado/licenciado ou esquema tecnicamente aprovado → conexão documental entre projeto, equipamento e fabricação → consequência concreta. Esta é apenas a sequência a ser avaliada; não significa haver assets para todas as cenas. Buscar/acrescentar imagens com provas de licença/hash e avaliação de qualidade antes de fechar roteiro. Sem material ou mecanismo suficiente: `BLOQUEIO_EDITORIAL_SEM_PROVA`, não títulos em mapa.

Critérios de aceite (sem substituir julgamento humano):
- 100% dos fatos centrais têm **objeto/relação visível** apropriado; não apenas textos descrevendo aquilo.
- Quadros de evidência e ações passam pelo revisor multimodal. Mapa só quando esclarece local/relação real, sem área irrelevante dominar a cena.
- Sem lettering ilegível, mídia obviamente escura ou mal enquadrada, flashes genéricos, imagens repetidas sem nova informação.
- Não promover regra por acertar 1 tema: validar em **pelo menos 2 assuntos diferentes**; se não generalizar, permanecer hipótese.
- Feedback humano recolhido por cena, vinculado a commit/asset/receita; só depois de aprovado vira padrão recuperado pelo diretor.
- Aprovação humana **explícita** e autorização de publicar separada.

**Proibição operacional:** nenhum workflow novo de produção completa sem este contrato; nunca enfraquecer fiscal técnico para buscar luz verde; não tocar `main`, `motor-integral-v4`, DOSSIÊ ou NTC. Este documento não promete resultado "definitivo" sem aprovação real de vídeo; registra o caminho verificável.
