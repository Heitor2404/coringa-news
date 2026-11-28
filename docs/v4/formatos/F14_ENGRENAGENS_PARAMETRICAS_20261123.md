# F14 — nova família mecânica: redução por engrenagens cilíndricas externas

**Data:** 23/11/2026 ~10h48 BRT. **Estado:** F14b VALIDADA TECNICAMENTE, estética / fabricação / identidade industrial **PENDENTES**. Branch experimental `atlas-direcao-visual-20261118`; **NÃO** em `main` nem produção.

## O que esta fase entrega

Abandonou-se a repetição da mesma biela e pistão para provar uma segunda **topologia mecânica rotativa**: dois eixos com engrenagens externas de dentes retos em caixa aberta ilustrativa. Há um **kernel de engrenagens**, duas configurações JSON diferentes e um **único compositor SVG/FFmpeg**. O motor é 2D vetorial calculado; não é pipeline universal de reconhecimento de maquinário, nem CAD fabricável.

- `src/v4/formatos/engrenagens_parametricas_f14.py`: desenho original das silhuetas dos dentes com flancos involutos 20°, raios primitivo/base/ponta/raiz, cubos de eixos, cinemática ideal da relação angular `theta_saida = fase_saida - theta_entrada * z_entrada/z_saida`. Distância entre centros `a = modulo*(z1+z2)/2`; duas rodas rodam em sentidos opostos. **Risco técnico declarado:** raiz radial simplificada, sem filete trocoidal, folga de fabricação, flexão, carga ou análise de contato 3D.
- `src/v4/formatos/compositor_engrenagens_f14.py`: compositor ÚNICO de redutores por cena JSON; suporte a alteração dos dentes/módulo, relação, acabamento e rpm didático, com estágio/câmera FIXA e texto legível. Nenhuma parte industrial foi copiada de terceiros.
- `src/v4/formatos/cenas_parametricas/redutor_engrenagens_18x36.json`: **18 e 36 dentes, 2:1**, módulo didático 6,2 px, distância entre centros 167,4 px, duas voltas de entrada por clip.
- `src/v4/formatos/cenas_parametricas/redutor_engrenagens_24x36.json`: **24 e 36 dentes, 1,5:1**, módulo 5,4 px, distância entre centros 162 px, duas voltas de entrada por clip.
- `tests/test_engrenagens_f14.py`: ângulos inversos exatos, razão e centros, formas SVG reais, **40 poses amostradas por preset com detector raster de sobreposição de silhuetas de dentes** (limite de ruído 30 pixels), geometria não finita rejeitada, ausência de identidades/CAD falsos, título essencial comparado às zonas UI hipotéticas, regressão F7.
- `.github/workflows/qa-engrenagens-f14.yml`: executa QA e produz dois MP4s de 9s/540×960/24fps, folhas reais, hashes, riscos de UI com perfis da F13; sem Claude, API paga, Telegram ou publicação.

## Fundamentação (principio técnico, não direito de imagem)

Referência para cálculo modular e dentes involutos: KHK Gears, `https://khkgears.net/new/gear_knowledge/gear_technical_reference/calculation_gear_dimensions.html`; visão complementar `https://roymech.org/Useful_Tables/Drive/Gears`.

**Os sites são fonte de equações e terminologia, NÃO licença para copiar fotografias/diagramas/CAD e NÃO certificam nossa qualidade ou fidelidade industrial.** Nenhum pixel alheio foi incorporado.

## Sequência e evidência REAL

1. **Primeiro run F14** https://github.com/Heitor2404/coringa-news/actions/runs/45186035140 — SUCCESS, 37 testes, 2 MP4s. Inspeção da prancha `COMPARATIVO_F14_2_REDUCOES_8_QUADROS.jpg` observou rodas pequenas no palco em relação ao espaço disponível, títulos acima da área de interface conservadora, movimento discreto. Isso motivou correção, não promoção.
2. **F14b** ampliou as rodas por módulo/dados, dobrou o número de voltas de entrada no clip, transferiu textos ESSENCIAIS para abaixo da faixa superior e acrescentou teste raster de engrenamento em 40 poses por preset. Não houve pan ou zoom, e as juntas/polias não foram reescritas.
3. **Run FINAL** https://github.com/Heitor2404/coringa-news/actions/runs/45187162677 — **SUCCESS, 41 testes aprovados**, render e QA de pixels completos.
4. **Artifact** `lab-f14-redutores-2-configs-8-quadros-privados`, ID **14824256968**, expira **28/11/2026 ~13h47 UTC**. ZIP baixado, extraído e arquivos conferidos no container:
   - `REDUTOR_F14_18X36.mp4` — 9s, 540×960, 24fps, sem áudio, SHA256 `f55438c5aceb3cf2a4dee1c50715c1b48617e4e7bffc36513514a005060238a2`.
   - `REDUTOR_F14_24X36.mp4` — mesmas specs, SHA256 `8504e459ac70f19adaadeb13042bd9010561058f900594549519633e8aa67c9e`.
   - `COMPARATIVO_F14_2_REDUCOES_8_QUADROS.jpg`: folha de 8 frames reais, aberta e inspecionada. As engrenagens apresentam dentes separados, contatos visuais plausíveis, rotação coordenada e caixa com dois eixos. O acabamento é didático/estilizado e NÃO replica um redutor de fabricante.
   - `QA_F14.json`, frames PNG e relatórios `REDUTOR_F14_*.json`: cinemática, ator, vídeo e captura de riscos com SHA verificáveis.
5. **QA de UI conservadora/observada da F13** nas 3 fases de teste: sobreposição de pixels das próprias rodas = 0% nos quatro perfis orgânicos aproximados de Reels/TikTok/Shorts, com até **0,24% na roda de saída no perfil conservador de ANÚNCIOS Meta**. A posição da marca/título tem teste de máscara mas **não foi homologada no dispositivo real**. Não confundir 0% estimado com interface efetiva do usuário.

## O que foi ganho de verdade, e o que não foi

**Comprovado:** outro núcleo físico diferente de biela/hidráulica; duas relações mecânicas reais com dentes e módulos variáveis, mesmo compositor, duas prévias privadas, câmera estável, testes de colisão raster, fonte técnica e conteúdo original.

**NÃO comprovado:** capacidade de pesquisar novo assunto automaticamente e reconhecer/segmentar máquina por foto/vídeo/3D; licenciamento de componentes industriais; qualidade visual fotorealista; parâmetros de torque/eficiência/força; validação de fabricação, de resistência, ou a fidelidade de um modelo de redutor específico. O motor ainda precisa de kernels físicos e direção visual previamente programados por **família**.

**Importante:** F14 NÃO foi cadastrada como renderer do `catalogo_mecanismos.py` PRODUTIVO e não destravou publicação; esse catálogo exige ações e identificação visual verificadas, algo que a prova laboratorial ainda não entrega. F7–F13 continuam intactas.

## Próximo gate de valor (F15)

Melhorar a arquitetura de **seleção/ montagem baseada em descrição estruturada de mecanismo e fonte técnica rastreável**, capaz de escolher entre F7 biela/F14 engrenagens e devolver erro explicado para mecanismo fora do catálogo, antes de desperdiçar recursos com render. Separar:
- grafo de relações físicas e famílias parametrizadas;
- reconhecimento de tipos de ligação pela estrutura (eixos, dentes, biela, fluido), não só palavra solta no título;
- identidade visual comprovável por referência rastreável e licença de imagem **independente**;
- coordenação editorial/referência sem escolher cena pronta do mesmo tema.

Depois homologar uma segunda família visualmente mais difícil com referência industrial/3D licenciada (direção futura). Evitar disfarçar templates pré-cadastrados como inteligência capaz de copiar qualquer máquina.

**Sem alterações na `main`, NTC, DOSSIÊ, Telegram ou produção. Publicação BLOQUEADA.**
