---
name: coringa-direcao
description: Use ao mexer no diretor automático do Coringa (storyboard, PROMPT, receitas de direção, contrato de plano, composições doc.*) ou ao diagnosticar um plano mal dirigido.
---
# Direção audiovisual do Coringa (V3.1)

1. O storyboard é escrito pelo MODELO (`src/v3/pipeline.py::storyboard_automatico`): 1 chamada + no máximo 1 correção
   dirigida pelos erros do validador. Nunca escreva storyboard à mão para produção; stub só em teste, rotulado.
2. Contexto do prompt é RECUPERADO, não a biblioteca inteira: receitas (`src/v3/receitas.py::recuperar`, só aprovadas e
   testadas), erros pertinentes (`memoria.erros_pertinentes`), regras aprovadas, composições viáveis por acontecimento
   (`contrato.viaveis`), acervo do vídeo + mídia de outros vídeos (`pipeline.acervo_diretor`).
3. Validação por código (sem IA): `pipeline.validar_storyboard` + `diretor.validar`. Erro que sobra derruba o plano;
   crítico sem plano válido bloqueia o vídeo (ERR-011).
4. Execução: `src/v2/diretor.py::montar` (enquadramento vertical, câmera com intenção, anotação só onde a visão
   localizou). Tempos SEMPRE da narração alinhada (`pipeline.aplicar_tempos`).
5. Receita nova: entra em `src/v3/receitas.json` como `proposto`, com objetivo, quando usar/não usar, composições,
   parâmetros obrigatórios e teste. Padrão, nunca fatos de um tema. `aprovado` exige exemplo aprovado + registro de aprovação humana.
6. Composição específica de um tema (ex.: `doc.eclusa`) é exceção; prefira composições gerais parametrizadas pelo contrato.

Testes: `python -m pytest -q tests/test_v3_diretor.py tests/test_v3_pipeline.py tests/test_v3_memoria.py`.
