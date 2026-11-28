# ATLAS V2 — Guerra dos Chips: plano de prova privada curta
**19/11/2026 • Branch `atlas-direcao-visual-20261118` • NÃO PUBLICÁVEL**

## Objetivo do experimento
Verificar se as capacidades P0/P1 — foto documental protagonista, abertura física verificável, cartografia que mostra dependência, crédito no rodapé, voz Gemini/Charon, sequência de conteúdo com progressão semântica — conseguem gerar uma prévia realmente melhor que o piloto flat/cartão da Guerra dos Chips. Isso é um **teste editorial supervisionado**, NÃO um novo formato customizado para chips.

## Material real reaproveitado, não duplicado
As duas entradas foram *copiadas literalmente* do ramo de teste `atlas-piloto-chips-20261118` para a biblioteca comprovada do ramo `atlas-direcao-visual-20261118`, sem novos downloads, sem forjar hashes ou direitos:
- `commons:TSMC_Fab_18_May_2025.jpg`: exterior real da **TSMC Fab 18 em Tainan/Taiwan** (autor **4300streetcar**, Wikimedia Commons **CC BY 4.0**), versão exata de miniatura 960×640 com SHA-256 `3cfbaf153fd3f4d1e3a26f16ba9058baa37f9c63d7fee0c42d7c18cd57330ca0`. É o exterior, **NÃO representa fabricação, EUV, processo interno ou participação de mercado**. Fonte: https://commons.wikimedia.org/wiki/File:TSMC_Fab_18_May_2025.jpg
- `commons:Silicon_wafer_close_view.jpg`: wafer genérico real, sem fornecedor identificado (autor **Le hollandais volant**, Wikimedia Commons **CC BY 4.0**), versão exata 960×720 SHA-256 `f6514745cd41b4bce8a6a7c1be824f3391c92897e84d7982b2470050dd5adbe1`. Serve para explicar o **objeto**, NÃO comprova produto da TSMC. Fonte: https://commons.wikimedia.org/wiki/File:Silicon_wafer_close_view.jpg
- O vídeo Commons da IBM sobre EUV consta com `License review needed`: **não utilizado**.
- O catálogo conserva `confirmacao_humana: null` dessas fotos. Elas entram só na **prévia experimental privada**, sem liberar publicação e sem dizer que houve revisão humana final.

## Sequência editorial (~25 s, a duração real depende do Gemini)
Plano fonte: `src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json`.
1. **Foto da Fab18 desde o primeiro quadro**: observação física e identificação rápida do local, com arquivo real grande em 9:16, sem pin/mini-card.
2. **Mapa Taiwan**: a pergunta *por que uma fábrica nessa ilha importa?* torna geografia pertinente.
3. **Foto do wafer**: primeira revelação mostra o objeto e seu caráter ilustrativo; segunda revelação `rotulo2` sincronizada à fala explica que é a base de circuitos, mantendo a mesma foto em evolução (sem corte forçado).
4. **Mapa EUA–Taiwan/Pacífico**: projetos de empresas americanas, com país destacado e rótulo compacto, não rotas falsas.
5. **Mapa Holanda–Taiwan**: equipamentos e fabricação em elos separados; rótulos sequenciais respeitam dissolves e áreas seguras, sem pins fora do quadro.
6. **Payoff**: efeito potencial de falhas em um elo, sem presumir impossibilidade geral de fabricação fora de Taiwan.

Nota editorial: O vídeo NÃO ensina como opera EUV nem simula ação de máquinas; sem prova licenciada e mecanismo aprovado, não há animação inventada. Falas de TSMC/Nvidia/ASML/BIS futuras precisam checagem de escopo temporal. Este curta deliberadamente omite o percentual controverso `90%`.

## Engenharia e isolamento
- `src/v4/formatos/plano.py`: `abertura_tipo: "mapa"` preserva a regra antiga. `"prova_real"` libera apenas foto protagonista ou MP4 comprovado desde 0s (não mecanismo); no preflight exige SHA da origem, licença, crédito e tipo correto.
- `motor4/remotion/src/formatos/Primitivas.tsx` revela 2 estados textuais sobre a mesma prova. Isso não equivale a efeitos decorativos ou novidade editorial fictícia.
- `.github/workflows/atlas-chips-v2-privado.yml`: GitHub Actions isolado, disparo explícito por `.github/atlas/chips_v2_preview.txt`, **uma chamada de narração Gemini/Charon** se houver chave; erro se faltar (não cai para Edge); Assets → Preflight → Quadros → Render → Folhas → Telegram privado → portão V3. Não manda MP4 aos artifacts públicos, não posta em redes.
- `tests/test_atlas_abertura_prova_real.py` e `tests/test_atlas_previa_chips_v2.py` com tempos **SINTÉTICOS 2,55 palavras/s** testam invariantes antes de consumir TTS. **Os tempos e a qualidade da voz TTS real continuam desconhecidos** até executar.
- No CI, reprovação em **F-COLISAO/F-PINO-FORA/F-SEM-PROGRESSAO** é problema real de storyboard que deve ser corrigido, não relaxamento artificial do fiscal.

## Gatilhos de aceitação
1. Pré-contrato de tempos e layout verde sem gastar IA. 
2. O fluxo com Gemini/Charon gera voz **aprovável** sem trocar provedor; o usuário valida timbre.
3. Primeira fotografia realmente visível em tamanho protagonista e atraente, fotos autenticadas; não parecer apresentação de slides.
4. Quadros legíveis em Reels/TikTok/Shorts; créditos abaixo das legendas sem falsa invisibilidade.
5. Conteúdo visual progride quando a narração progride; mapas mudam o entendimento, não enfeite.
6. Gate de integridade pode declarar `AGUARDANDO_APROVACAO_HUMANA`, **nunca APROVADO automaticamente**.
7. Se a execução falhar ou o vídeo for fraco, registrar causa e corrigir componente reutilizável; não inserir exceção por tema.

**Estado ao criar este documento:** storyboard e workflow preparados; validação do novo storyboard ainda deve ser confirmada; **nenhum MP4 novo aprovado/publicado**.
