# Reference-first — Compressor alternativo 2D (ciclo P–V com válvulas)

**22/11/2026.** Laboratório isolado na branch `atlas-direcao-visual-20261118`, sem Claude, sem publicação e sem promoção ao `FilmeEditorial`.

## Motivação e decisão

O 3D antigo reutilizava quase a mesma animação de pistão para motor e compressor. A demonstração estava errada: insuficiente para explicar admissão e descarga. Neste trabalho implementou-se um **operador físico específico de compressor** em vez de trocar o título do motor Otto.

## Fontes e limites da pesquisa

- EFRC — [Tutorial: Reciprocating compressors](https://www.recip.org/tutorial-reciprocating-compressors/): gás entra e sai por válvulas, deslocamento do pistão e volume de folga.
- [How a reciprocating piston compressor works](https://reddycompressors.com/compressors/reciprocating/how-it-works/): quatro fases físicas, reexpansão residual, admissão, compressão e descarga; válvulas autoatuadas por diferencial de pressão.
- Wikimedia Commons — [Piston.gif](https://commons.wikimedia.org/wiki/File:Piston.gif), R. Castelnuovo/Jahobr, 24 quadros documentados na página, sob licenças CC BY-SA/GFDL, **somente referência mecânica genérica**. Download tentado no Actions [45065403117](https://github.com/Heitor2404/coringa-news/actions/runs/45065403117), mas serviço retornou **HTTP 429**. Não houve medição desta animação. Nunca classificar como fonte de compressor.
- Modelo 3D encontrado no engx3d (2026) indica CC BY-NC (uso não comercial), logo não utilizar no canal comercial. Listing em Fab de compressor animado não possui uso/aprovação de licença verificada. Não comprados/baixados/integrados.

**A parte de física veio de fontes técnicas; não houve RECONSTRUÇÃO automática de vídeo de compressor da internet.** Esta etapa é uma simulação autoral de física P–V que não compartilha as fases Otto. O processo de reconhecimento automático da referência permanece pendente.

## Implementação

`src/v4/formatos/compressor_pv_core.py`: pure state machine com ciclo de 1 volta por repetição:
1. `REEXPANSAO_RESIDUAL` — pistão começa a descer com gás da folga ainda acima de pressão de sucção; as duas válvulas fechadas.
2. `ADMISSAO_AR` — quando pressão da câmara cai até 1× entrada, válvula de sucção abre (entrada azul).
3. `COMPRESSAO_AR` — na subida, as válvulas fecham, o volume cai e pressão cresce.
4. `DESCARGA_PRESSURIZADA` — quando pressão da câmara chega ao valor definido de linha (nesta prova 5× entrada), válvula de descarga abre (fluxo laranja).

O pistão, a biela e o pino do virabrequim partilham a mesma cinemática. Posição, volume, pressão e válvula derivam do ângulo do eixo e do modelo politrópico didático, não de um cronograma de cores com posições desencontradas. A posição da biela é conservada matematicamente por toda a volta.

`src/v4/formatos/render_compressor_pv_2d.py`: cutaway SVG autoral (CairoSVG + FFmpeg) 540×960, 24fps, 8 segundos sem áudio. Mostra gás da câmara, válvulas, ar azul entrando, pressão subindo, descarga laranja saindo e **tubo fisicamente conectado ao tanque**. Textos principais y155–233 num frame de 540×960; fundo e parte do mecanismo podem atravessar margens periféricas de UI sem diminuir todo o conjunto.

`src/v4/formatos/reference_first.py`: renderer `CompressorPV2D` aparece no laboratório como capaz de representar visualmente o ciclo mas **NÃO APROVADO** para reconstrução por referência, porque não foi observada animação real do compressor. O 3D antigo continua reprovado por capacidades ausentes. Isso impede a aprovação enganosa.

## Provas e QA

- [GitHub Actions run 45066104183](https://github.com/Heitor2404/coringa-news/actions/runs/45066104183) **SUCCESS**, após corrigir um teste desatualizado de texto e deslocar o cabeçalho para área mais segura. Run predecessor 45065733372 também tinha renderizado MP4, mas sua versão continha defeito: tubo de saída terminava sem ligação ao tanque.
- Arquivos do artifact **14771212692**, nome `compressor-2d-pressao-valvulas-privado` (expira 27/11/2026 20:23 UTC):
  - `COMPRESSOR_AR_FISICO_2D_PRIVADO.mp4` — 8s 24fps 540×960, sem som nem publicação.
  - `contato_8_fases_compressor_PV.jpg` — oito tempos reais do MP4 para auditoria.
  - `qa_estados.json`: boundaries do ciclo e declara que referência animada do compressor ainda não foi obtida.
- `tests/test_compressor_pv_causal.py` validou estados P–V amostrados em 241 quadros, invariantes de biela, válvulas mutuamente exclusivas, estados fisicamente coerentes, SVG e render real.
- Estado de fase em `qa_estados.json`: reexpansão progress 0–0,115; admissão 0,1155–0,5; compressão 0,5005–0,857; descarga 0,8575–1,0. Os valores dependem dos parâmetros didáticos escolhidos (folga=0,06 do deslocamento, Pdescarga/Padmissão=5 e n=1,25); **não são medição de um compressor comercial específico**.
- Uma execução inicial de workflow falhou por erro de YAML (colon sem aspas); corrigido. Em outra tentativa, teste verificava texto antigo RESER- depois da melhoria para TANQUE; corrigido. No run final os testes e MP4 passaram.

## Limitações e próximo passo

1. Não afirmar qualidade estética aprovada: mesmo mais limpo que o antigo 3D, é um modelo gráfico didático 2D, sem narração.
2. Não afirmar análise/reconstrução de fonte audiovisual de compressor; há referência física descritiva, e fonte animada de pistão que não baixou. Não há rig 3D extraído, objetos automaticamente identificados ou cálculo de pressão CFD.
3. É física paramétrica genérica, não plano individual por assunto. Adaptar esse operador requer um PROCESSO com ciclo P–V, válvulas autoatuadas e fonte de detalhes. O modelo não substitui um renderizador de engrenagem, eclusa ou motor Otto.
4. A próxima etapa difícil continua sendo obter mídia de compressor animado com licença/reuso claros, identificar atores e tempos com confiabilidade, calibrar posições/pressões com evidência, e comparar automaticamente uma reconstrução vetorial com a referência. Se não houver mídia, manter classificação de **simulação**, não de reconstrução.

**Nenhum vídeo publicado, nenhuma mudança em `main`, NTC, DOSSIÊ, `FilmeEditorial` nem uso do Claude.**
