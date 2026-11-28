# Taiwan — investigação de filmagens reais por acontecimento (19/11/2026)

**Estado:** fontes CANDIDATAS, não mídia curada ou liberada ao render. Nenhum MP4 baixado/inspecionado neste trabalho, nenhum SHA de conteúdo verificado e nenhuma narração gerada. Trabalho exclusivo na branch experimental.

## Critério
A imagem precisa mostrar aquilo que o roteiro diz. Mídia de laboratório NIST, agência DARPA ou placa eletrônica genérica **NÃO** pode ser chamada de TSMC/Taiwan/ASML. Vídeo real com mero pan sobre uma placa não comprova ação fabril. Exigir fonte original, arquivo local, SHA256, inspeção de quadros, licença/exceções e identidade explícita.

## Candidatos priorizados

1. **NIST — Inside an instrument at the NIST Center for Nanoscale Science**
   - Página oficial: https://www.nist.gov/video/inside-instrument-nist-center-nanoscale-science
   - A própria página descreve maquinaria **girando dentro de um instrumento de deposição de metal vaporizado em wafer**, um processo físico relevante para semicondutores; publicação em 08/05/2023. Publicação de vídeo dentro de Kaltura, ainda SEM MP4 no projeto.
   - Uso potencial: demonstrar uma etapa real de fabricação **em laboratório NIST**, se o movimento descrito estiver visível na amostra. Não alegar que é fábrica Taiwan/TSMC, nem confundir deposição com EUV.
   - Direitos: https://www.nist.gov/copyrights-disclaimers informa que material NIST não marcado com copyright geralmente pode ser copiado/distribuído com crédito recomendado; conferir direitos **do item e eventuais terceiros** no próprio arquivo antes de atribuir domínio público.
   - Status: **CANDIDATO, SEM INSPEÇÃO, SEM SHA, SEM ATESTADO INDIVIDUAL DE LICENÇA**.

2. **NIST — A Visit to the E-Beam Machine**
   - Página oficial: https://www.nist.gov/video/visit-e-beam-machine
   - Vídeo atribuído a Jennifer Lauren Lee/NIST e animação a Sean Kelley/NIST, 31/08/2017. Visita a sala limpa e máquina de litografia por feixe de elétrons. Kaltura, sem MP4 ingerido.
   - Uso potencial: mostrar a máquina/laboratório real; a função do e-beam pode ser explicada sob identificação correta. **E-beam não é sistema EUV da ASML**, e laboratório não equivale a fab industrial de Taiwan.
   - Direitos: política geral NIST acima; checar a licença específica dos trechos/áudio/animação e condições do conteúdo recuperado.
   - Status: **CANDIDATO, SEM INSPEÇÃO, SEM SHA**.

3. **DARPA/DVIDS — NGMM: Next Generation Microelectronics Manufacturing**
   - Página oficial: https://www.dvidshub.net/video/995636/ngmm-next-generation-microelectronics-manufacturing
   - Vídeo de 1m49, publicado 09/02/2026, produção DARPA/Tom Shortridge; a própria página marca **PUBLIC DOMAIN** e remete a https://www.dvidshub.net/about/copyright. Página de download apresenta variantes 1920×1080 e 1024×576, mas o arquivo não foi recuperado aqui (a URL direta de uma variante recusou consulta web com 403).
   - Uso potencial: contexto verificável de fabricação avançada e encapsulamento/integração heterogênea de chips **nos EUA**, NÃO operação de TSMC. Pode não conter ação física suficiente: revisar quadros antes de escrever cenas.
   - Status: **CANDIDATO PUBLIC DOMAIN INDICADO, SEM BYTES/INSPEÇÃO/SHA**.

4. **Mixkit — Microchip technology close up**
   - Página: https://mixkit.co/free-stock-video/microchip-technology-close-up-1140/
   - Licença deste item: https://mixkit.co/license/modal/videoFree/ (uso comercial permitido). Item 11s, placa/chip em macro com movimento de câmera; não mostra produção nem litografia.
   - Uso potencial: **representação de objeto físico pronto**, não vídeo de fabricação.
   - Status: **CANDIDATO COM LICENÇA EXPLÍCITA NA PÁGINA, SEM BYTES/INSPEÇÃO/SHA**.

## Não usar como fonte de fabricação sem resolver direitos
- https://commons.wikimedia.org/wiki/File:How_ST_designs_and_manufactures_semiconductor_devices.webm — Commons reporta **License review needed**; além disso ST não é TSMC.
- https://commons.wikimedia.org/wiki/File:How_EUV_lithography_works.webm — Commons reporta **License review needed**. Não tratar como seguro só porque mostra o fenômeno.

## Próximo lote operacional
- Tentar recuperar e inspecionar **primeiro o processo NIST de deposição**, depois a máquina e-beam, e registrar para cada mídia local: arquivo, SHA, dimensões, duração, licença específica, identidade, intervalo com ação real e quadros de controle.
- Não colocar em `ponte_biblioteca.catalogo()` antes dessa inspeção. Se o vídeo não mostrar fisicamente o que a fala exige, corrigir a fala ANTES de TTS.
- Reusar o mapa ATLAS Taiwan provado no artifact 14564100281, sem rerenderizar por hábito; o portão exige que o MP4 e o sidecar estejam no mesmo runner.
- Atenção: mesmo que dois clipes NIST sejam aprovados, isso NÃO demonstra a relação Taiwan-Holanda-EUA ou o payoff factual; roteiro e evidências dessas cenas seguem faltando.

**Não houve render, TTS, Telegram nem publicação.**
