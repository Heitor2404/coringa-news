# ATLAS — Inspeção de referência animada baseada em quadros reais

Data: 21/11/2026. Branch experimental `atlas-direcao-visual-20261118`. **Não é motor gerador de animações pronto**.

## O que foi implementado

- `src/v4/formatos/inspecionar_referencia.py`: valida arquivo original e hash SHA-256, amostra até 8 quadros de GIF animado ou verifica JPGs extraídos de vídeo com hash de arquivo e quadro. Usa `src.gemini.json_visao` existente APENAS quando solicitado e há fonte acessível.
- O modelo deve indicar `RELEVANTE`, `PARCIAL`, `IRRELEVANTE` ou `INCERTO`, atores e fases observados, e a ação com pares de quadros `antes/depois` e descrição concreta. Sem evidência por ação, bloqueia.
- `src/v4/formatos/referencias_mecanismos.py::planejar`: agora rejeita observações com hashes ausentes, índices inválidos, sequência errada ou falta de ligação entre ação e evidência. Continua consultando `catalogo_mecanismos.py` e não inventa nova física.
- `src/v4/formatos/referencias_mecanismos.py::extrair_quadros`: inclui referência, arquivo de origem, hash do MP4 e hashes de cada um dos 5 JPGs.
- `.github/workflows/qa-referencias-animadas.yml`: testes offline nos pushes, extração de clipe local real; download remoto e análise Gemini somente no disparo manual (`workflow_dispatch`), mediante existência de mídia e chave.

## Provas efetuadas neste ciclo

- CI de desenvolvimento no commit `7ab5e655faa6f7323f4f667faee66537713dbd07`: **25 testes automatizados aprovados** e extração de 5 JPGs reais a partir do clipe original de navio de `tests/midia/video_horizontal_navio.mp4` (6,006 s, 1280×720).
- Os quadros locais mostram a proa de embarcação e mudanças de paisagem/água. **Não mostram um ciclo de eclusa**, portanto não devem entrar como demonstração dessa física.
- Artifact da coleta: `14722965494`, run `44943262619`, expira em 24/11/2026. O vídeo original não integra o artifact; a verificação de origem é feita com o arquivo local presente no runner.
- Testes de visão são com respostas SIMULADAS e GIF de teste fabricado; não equivalem a avaliação Gemini de uma animação externa.
- Última tentativa de baixar GIFs Commons via GitHub Actions retornou HTTP 429. Não houve revisão multimodal real dos GIFs de pistão ou coração; nenhum foi aprovado.

## Operação privada após conseguir GIF de origem

```bash
python -m src.v4.formatos.inspecionar_referencia \
  docs/v4/formatos/briefs_referencia/motor_pistao.json \
  saida_ref/live_pistao/referencias.json \
  saida_ref/live_pistao/quadros \
  saida_ref/live_pistao/revisao \
  --usar-gemini
```

Em formato 3D não há operador de rigging ou render nesta etapa: um thumbnail ou um nome de modelo Sketchfab não prova movimento. Seria preciso modelo editável ou arquivo de vídeo da animação, inspecionar seus estados e construir capacidade específica reutilizável.

## Próximo gate

1. Adquirir pelo menos uma animação técnica de fato acessível, com procedência; deixar de depender da hospedagem Wikimedia com 429.
2. Executar visão real e comparar a interpretação do modelo com inspeção independente dos quadros. Registrar rejeições corretas e falsos positivos, inclusive resultados decorativos/irrelevantes.
3. Traduzir estados e conexões comprovados em dados de cena causal; montar com atores/operadores reusáveis sem codificação de episódio.
4. Provar reconstrução em dois temas novos e avaliar visualmente; NÃO publicar nem promover `FilmeEditorial` antes disso.

**Status:** infraestrutura de pesquisa + evidência de quadros funcional, interpretação por VLM conectada de modo opcional, reconstrução automática multitema ainda não demonstrada.
