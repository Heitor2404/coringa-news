# CONTINUIDADE — Projeto Coringa / ATLAS / Biblioteca / Multimotores

**Estado de referência:** 18 de novembro de 2026, após criação da biblioteca inicial.  
**Objetivo deste arquivo:** permitir que uma nova conversa entenda rapidamente o que foi decidido, o que está implementado e o que falta **sem inventar progressos**. Atualizar este arquivo ao fim de marcos significativos e antes de trocar de chat.

> **IMPORTANTE:** primeiro consultar o GitHub ao retomar, confirmar os SHAs, workflows e diferenças entre branches. Esta página é um marco histórico, não substitui inspeção do código atual.

## 1. Objetivo do usuário

Criar um ecossistema de canais dark automatizados ao máximo possível, com qualidade profissional, priorizando reutilização do GitHub, Claude e ChatGPT, **sem depender de novas despesas recorrentes**. O usuário quer uma avaliação crítica sincera, sem concordância automática, sem prometer resultados antes de ver vídeos reais. A produção documental **ATLAS**, a animação vetorial **NTC 2D** e outros motores não devem ser confundidos.

O usuário autorizou trabalho prático no GitHub, com mudanças isoladas e correção proativa de erros; não alterar produção e outros motores sem validação. O **segundo tema do ATLAS foi escolhido pelo usuário: GUERRA DOS CHIPS**.

## 2. Identidade e alcance do ATLAS — DECISÃO EDITORIAL CENTRAL

ATLAS é um **formato documental cartográfico**, não um gerador universal de qualquer vídeo e não um motor exclusivo de engenharia. Pode tratar de geopolítica, geografia, história com dimensão territorial, infraestrutura, rotas comerciais, conflitos, recursos naturais, economia global e tecnologia geopolítica (ex.: guerra dos chips). Astronomia pura, biologia microscópica e histórias de personagens 2D cabem melhor em motores próprios.

**O mesmo visual/edição em diferentes temas; não inventar estética por episódio.**
- **Mapas animados são a espinha dorsal**, mas **NÃO** ocupam 100% do tempo obrigatoriamente.
- Fotos/vídeos reais com procedência e crédito; cards, comparações e fontes; motion graphics existentes.
- Animações técnicas só quando houver estrutura ou mecanismo relevante à fala.
- Diretor de narrativa escolhe fatos e progressão; diretor visual escolhe composições **do catálogo existente**; render determinístico executa movimento, paleta, tipografia, slots e limites.
- Preservar identidade já desenvolvida: mapas editoriais escuros, cartões retos/alinhados em papel off-white, amarelo `#FFD21F` para foco, legendas brancas em baixo com destaque amarelo, créditos em faixa separada, dimensões/safe areas, áudio, factual e licença.
- Não forçar novos efeitos, modelos ou componentes para salvar episódios isolados.
- Capacidades genéricas só podem ampliar ATLAS após testes de regressão, **sem mudar a identidade aprovada**.
- **Não reintroduzir o erro do motor antigo**: tentar misturar todos os estilos visuais em toda história.

Referência: `docs/v4/formatos/GUIA_VISUAL_ATLAS_V1.md` e `docs/v4/formatos/CONTRATO_DIRECAO_VISUAL_ATLAS.md`.

## 3. Status concreto do ATLAS — 18/11/2026

Repo: `Heitor2404/coringa-news`.

**Branch primária experimental:** `atlas-direcao-visual-20261118` — SHA da branch no momento da criação deste documento: `02d9b5c46daea3baac11544260c9b39dedf099cc` (o próximo commit muda esse SHA). A branch de produção `motor-integral-v4` não foi alterada nesta etapa, tampouco NTC/DOSSIÊ.

O piloto **Canal do Panamá** serve como teste de regressão geral, não produto a ajustar manualmente. Uma prévia privada curta de **~24,93 s** recebeu avaliação positiva do usuário e auditor visual: mecanismo da eclusa mostra finalmente o navio saindo, com enquadramento mais amplo e mais coerência. A direção foi **aprovada como base** — **não** afirmar que todo episódio foi homologado ou que o ATLAS está 100% pronto. Ajustes menores observados: ancoragem de rótulos técnicos e sincronização da ação final com a fala. Devem ser regras genéricas se realizados, não alterações exclusivas do Panamá.

Validação anterior `44346041090`: **86 testes Python passaram**, mais checagens JS/TypeScript. Prévia privada acionada em `44346421515` e inspecionada por meio do MP4 enviado pelo usuário. Nunca confundir testes automatizados com aprovação visual de novo vídeo.

Arquivos-chave:
- `src/v4/formatos/formatos.json`: catálogo de formatos ATLAS/DOSSIÊ, composições, limites de componentes e contrato de clipe técnico.
- `src/v4/formatos/canais/coringa.json`: tokens visuais, câmeras, cores, legibilidade.
- `src/v4/formatos/plano.py`: validações do storyboard, final de ação etc.
- `src/v4/formatos/diretor.py`: prompts e seleção visual.
- `src/v4/formatos/produzir.py`: narrar → ativos → preflight → render → controles.
- `src/render/v2/nucleo.js`, `src/render/v2/comp/mecanismos.js`: câmeras e geometria dos mecanismos.
- `motor4/remotion/src/formatos/`: render das composições.
- `.github/workflows/atlas-validacao.yml`, `.github/workflows/atlas-previa-curta.yml`: testes e preview privado.
- `src/v4/formatos/planos/atlas_panama.json`: fixture de referência Panamá.

## 4. Segundo piloto — GUERRA DOS CHIPS

O usuário escolheu testar a generalização de ATLAS com um tema **não hidráulico**: cadeia global de semicondutores, Taiwan, EUA, China, Holanda.

**Branch de isolamento:** `atlas-piloto-chips-20261118`, criada a partir de `atlas-direcao-visual-20261118`; na última verificação, **nenhum piloto novo foi produzido** nessa branch.

Já havia no repositório `src/v4/formatos/planos/reuso/atlas_chips.json`, um **teste antigo de reuso** com tempos sintéticos (sem narração real e sem vídeo pronto), contendo mapas mundo/Pacífico/leste asiático, conexão Holanda–Taiwan, EUA–Taiwan/China, cards e hierarquia. Não tratar números e afirmações desse JSON como fatos atuais aprovados. Precisam revisão/revalidação (especialmente porcentagem de chips avançados, export controls de 2022 em diante, relação projeto/fabricação).

**Roteiro do segundo piloto:** narrar uma história geopolítica usando o padrão ATLAS (mapas como palco, fotos verificadas, cards, rotas/conexões e motion graphics existentes). Medir o que de fato pode ser produzido com componentes atuais; não transformar em projeto de efeitos novos. Não publicar sem revisão humana. Custo e cota de IA/TTS devem ser respeitados.

## 5. Biblioteca ATLAS — decisão e implementação inicial

**Decisão:** uma biblioteca **operacional e curada**, não banco infinito de assets nem substituto da investigação factual de cada vídeo.

**Branch própria:** `atlas-biblioteca-20261118`, criada a partir da branch experimental do ATLAS. Último SHA verificado: `90697302532a7214b0670f2b0aa0c844b1401d37`.

Arquivos criados:
- `src/v4/formatos/biblioteca_atlas/catalogo.json`: índice inicial de ativos existentes e status explícito.
- `docs/v4/formatos/BIBLIOTECA_ATLAS_OPERACIONAL.md`: arquitetura, contratos de curadoria, prioridades e fases.
- `tests/test_biblioteca_atlas.py`: cinco testes offline.
- `.github/workflows/atlas-biblioteca.yml`: valida apenas essa branch, **sem IA/TTS/render/publicação**.

CI workflow run `44364986366` foi **SUCCESS** com **5 testes**. Isso prova integridade de referências, **NÃO** que mídias novas foram adquiridas nem que a guerra dos chips foi renderizada.

**Inventário inicial reaproveitado sem cópias:**
- 5 referências cartográficas existentes: `ne2_mundo`, `ne2_pacifico`, `ne2_asia_leste`, `bmng_asia_continente`, `ne2_istmo_panama`.
- 6 composições atuais: `atlas.abertura`, `atlas.protagonista`, `atlas.escada`, `atlas.painel`, `atlas.tecnica`, `atlas.manchete`.
- 7 itens na `src/v4/biblioteca_comprovada.json` (seis sobre Panamá e um institucional chinês) com metadados de origem/licença/crédito, mas sem presumir confirmação humana individual.
- Pacotes temáticos no catálogo: chips (fixture existente, **não aprovado para publicação**), Ormuz, fronteiras históricas, infraestrutura global (**candidatos, não preparados**).
- Previews já mostrados ao usuário: cartografia, componentes/motion graphics, acervo, pacote chips (MOCKUP, não render aprovado), curadoria; também três trechos curtos do vídeo Panamá, e um ZIP com galeria.

**Ponto importante:** biblioteca experimental **não está importada** pelo pipeline produtivo e não deve estar até homologação. O usuário solicitou ver **prévia de cada coisa**: manter a distinção entre exemplos reais do render e mockups conceituais.

Próximos passos da biblioteca:
1. Verificar documentação, resolução, geometria e licença dos rasters/acervo.
2. Curar **fotografias realmente relacionadas a semicondutores** (TSMC, ASML, fábricas, chips, Taiwan) com procedência e licenças, sem reutilizar mídia genérica ou do Panamá.
3. Fatos e restrições **sempre revalidar no episódio**, com fontes oficiais e data; não congelar geopolítica atual.
4. Testar reuso com o piloto chips e métricas reais de economia/qualidade, sem assumir porcentagens 70/30.
5. Expandir o acervo apenas de acordo com utilidade e frequência de reutilização.

## 6. Plano futuro de vários canais e motores

A ideia foi **aprovada conceitualmente**, mas não implementada:
- Motor documental ATLAS como release imutável (`atlas-v1.0.0` é **exemplo futuro**, NÃO homologado).
- Motor NTC 2D para animações `E se...?`, BIO para biologia, ASTRO para astronomia etc.
- **Interruptor** `canal + motor + versão + tema`, scripts/paletas/estilos exclusivos e infraestrutura comum somente por interfaces versionadas.
- Mesmo motor pode servir a diferentes canais com identidade própria.
- Congelar release no SHA, manifesto de dependências, mídias, testes regressivos, golden samples, rollback.
- Primeiro concluir piloto Panamá + segundo piloto bem sucedido, depois congelar e expandir.
- Documento técnico: `docs/arquitetura/PLANO_MULTIMOTORES.md` no ramo `atlas-direcao-visual-20261118`.

## 7. Restrições práticas

- Custos: não pressupor uso grátis/ilimitado de Claude/ChatGPT por API; preferir render local/CI, GitHub Actions dentro de limites, cache e mídia licenciada.
- Segurança/qualidade: fontes adequadas, direitos autorais, fatos sem exagero, visual sincronizado, cortes e animações completos, revisão no MP4.
- Não misturar diffs e objetivos das branches `atlas-direcao-visual-20261118`, `atlas-piloto-chips-20261118` e `atlas-biblioteca-20261118`.
- Não tocar no NTC/DOSSIÊ ou produção estável.
- Não dizer que um novo vídeo ou integração de biblioteca já foi executado quando apenas se criou um catálogo, teste ou mockup.

## 8. Como retomar em um novo chat

O usuário pode enviar:

> Estamos continuando o projeto Coringa/ATLAS do repositório `Heitor2404/coringa-news`. Primeiro leia `docs/CONTINUIDADE_PROXIMO_CHAT.md` na branch `atlas-direcao-visual-20261118`; verifique no GitHub o estado mais recente das branches `atlas-direcao-visual-20261118`, `atlas-piloto-chips-20261118` e `atlas-biblioteca-20261118`, e os documentos citados. Não altere produção, NTC nem DOSSIÊ. Estamos preparando a biblioteca operacional ATLAS e o segundo piloto, guerra dos chips. Diferencie o que foi implementado, testado e aprovado visualmente. Continue a partir do último estado, preservando as regras editoriais e visuais do ATLAS.

### Aviso sobre limite de conversa

O usuário pediu que **o assistente o avise quando a conversa estiver ficando longa**, para preparar a passagem. Não há medidor confiável de tokens restantes da interface. Por isso, manter **este documento atualizado por marcos**, sem aguardar o limite, e, ao perceber sinais de contexto longo ou troca iminente de chat, avisar explicitamente e indicar este arquivo.


## 9. Atualização de 18/11 — curadoria real de fotos para a guerra dos chips

Na branch experimental **`atlas-biblioteca-20261118`**, após a criação do catálogo inicial, foi executada a primeira curadoria de imagens reais de terceiros para o tema **GUERRA DOS CHIPS**. As fontes originais foram verificadas na Wikimedia Commons; ainda NÃO foram incorporadas à produção, e continuam com `estado: candidato`:
- TSMC Fab 18 em Taiwan, exterior (4300streetcar, CC BY 4.0, 2025).
- Sede ASML em Veldhoven (A ansems, domínio público, 2008). **NÃO é fotografia de equipamento EUV**.
- Fábrica SMIC em Shenzhen (Lhzss8, CC BY-SA 4.0, 2022; verificar obrigação share-alike na edição).
- Wafer de silício em close (Le hollandais volant, CC BY 4.0, 2017); não prova marca/modelo/nó.
- Sala limpa de microfabricação NASA Glenn (domínio público); não é interior da TSMC/ASML/SMIC.

Arquivos criados: `src/v4/formatos/biblioteca_atlas/midias_candidatas_chips.json`, `scripts/atlas_biblioteca.py` (consulta offline sem uso produtivo), `scripts/atlas_acervo_chips_preview.py` (baixar miniaturas e auditar), `.github/workflows/atlas-acervo-chips-preview.yml`; testes ampliados para **7 testes** de gate/isolamento.

**Execução CI de download/preview:** `44368431700` — SUCESSO, 5/5 miniaturas recuperadas, hashes e dimensões conferidos, galeria + relatório + créditos salvos em artifact `atlas-chips-acervo-candidato` (ID `14456888348`, retenção 7 dias). A primeira execução `44368262210` falhou por bug no verificador de assinatura de JPEG, já corrigido em `4a027c6c`. O SHA da miniatura NÃO equivale ao do arquivo original. Precisa analisar visualmente fotos, resolver imagem real do equipamento EUV (se apropriado) e só então decidir importação ao índice comprovado.

**Branch `atlas-piloto-chips-20261118` continua separada; não declarar piloto renderizado.** A mudança foi apenas na biblioteca. Documento operacional: `docs/v4/formatos/BIBLIOTECA_ATLAS_OPERACIONAL.md` da branch da biblioteca. O vídeo do Panamá e produção estável não foram alterados.


## 10. Continuação autônoma — auditoria da biblioteca e teste da guerra dos chips

Em 18/11/2026 o usuário autorizou que o assistente continue **autonomamente nas branches experimentais**, corrigindo problemas sem pedir aprovação a cada alteração; isso NÃO revoga a necessidade de revisão visual antes de publicar ou de proteger ATLAS estável, NTC e DOSSIÊ.

### Biblioteca de mídia — branch `atlas-biblioteca-20261118`

- Catálogo ampliado para **6 mídias candidatas**, com contêineres aéreos da ASML fotografados em Taiwan, 2025, licença CC BY 4.0. **Não há comprovação do conteúdo dos contêineres.** Ver `src/v4/formatos/biblioteca_atlas/midias_candidatas_chips.json`.
- Mídia `How EUV lithography works.webm` do IBM Research **não liberada**: página Commons assinala `License review needed`. Fotografia histórica do LLNL também não é scanner ASML moderno.
- Galeria original recomprimia JPEG e guardava SHA256 **da miniatura pré-recompressão**, divergindo do arquivo realmente salvo. Corrigido: `scripts/atlas_acervo_chips_preview.py` mantém bytes baixados, mede SHA256 do arquivo, registra metadados da licença do Commons; CI reconcilia CC BY, CC BY-SA e domínio público. Não basta a palavra `licenciado` sem as condições do Commons.
- Consulta `scripts/atlas_biblioteca.py`: agora `liberado_para_render(item, arquivo_local)` **exige arquivo real, SHA-256 conferido, licença/crédito, dimensão, correspondência e aprovação editorial**, não se satisfaz com hash inventado no JSON. Ainda NÃO importada pelo motor.
- CI comprovada **`44371334155`: sucesso, 6/6 imagens baixadas, seis hashes verificados byte a byte, licença registrada conciliada**. **`44370287354`: sucesso, 7 testes**. Os artefatos são temporários, retenção 7 dias.
- Documento operacional atualizado `docs/v4/formatos/BIBLIOTECA_ATLAS_OPERACIONAL.md` na branch de biblioteca.

### Piloto guerra dos chips — branch `atlas-piloto-chips-20261118`

- Criado `docs/v4/formatos/PILOTO_CHIPS_BRIEF_20261118.md` com narrativa ATLAS cartográfica, storyboard de composições existentes, e fontes primárias TSMC/ASML/BIS. Corrige risco de confundir **74% da RECEITA DE WAFERS da TSMC em 2025** com quota mundial e tratar restrições de 2022 como regras imutáveis; BIS atualizou políticas em janeiro/novembro de 2026. O plano legado `planos/reuso/atlas_chips.json` ainda é **teste geométrico com voz sintética e fatos não homologados para publicação**.
- Criado `.github/workflows/atlas-chips-reuso.yml`: **somente testes offline, quadros reais, voz sintética de teste** — não chama IA, não gera MP4 nem publica; usa catálogo e render ATLAS existentes.
- Primeira execução **`44370810497` SUCESSO**: **86 testes** do motor, preflight **23 itens sem falhas**, **27 quadros renderizados, 0 erros bloqueadores**, mas **81 avisos `A-CREDITO-RODAPE`**: a posição muito baixa dos créditos pode colocá-los sob UI de TikTok/Reels/Shorts em todos os quadros. **Não chamar de homologação visual ou de publicação.** Ver workflow e relatório.
- Auditoria revelou que a posição baixa de crédito do ATLAS foi **decisão visual consciente**: `src/v4/formatos/plano.py:zonas()` força `creditos` para o rodapé `H-160`, enquanto `layout.faixa_inferior()` calcula a área segura unificada (base aprox. `H-480`). **Não elevar créditos globalmente às cegas** — prejudicaria o enquadramento que usuário aprovou. Registrar risco e validar no aplicativo/plataformas com usuário antes de publicar; possível solução: tratar créditos/cartelas específicas por plataforma mantendo estética.
- Adicionado relatório por categoria de aviso e estado `AGUARDANDO_APROVACAO_HUMANA` em `scripts/formatos_reuso.py` apenas na branch de chips; workflow reduz artefato de ~153 MB para apenas folhas e relatórios, economizando armazenamento. Revalidação acionada **`44372220176`** (estava em andamento na última consulta; confirmar resultado no GitHub).

### Prioridades de continuação

1. Ver o artefato de **folhas de quadros** da guerra dos chips e decidir qualidade visual/uso de mapa. Lembrar que este teste **não tem fotos definitivas nem voz real** e pode conter fatos do fixture legado.
2. Resolver o risco dos **81 avisos de crédito** sem desfazer identidade visual aprovada; não ocultar atribuições obrigatórias sob interface.
3. Integrar novas mídias somente após conferir licença/proveniência/conteúdo real, hashes e teste de alinhamento com frases; separar mídia candidata de comprovada.
4. Produzir o **verdadeiro piloto audiovisual** com roteiro factual atualizado, voz real e prévia privada, sem publicação, usando o mesmo padrão ATLAS (mapas, cards, fotos e motions existentes).
5. Preservar branch produtiva, NTC/DOSSIÊ e atualizar esta passagem sempre que mudar o estado.


## 11. 18/11 — roteiro factual, styleframes e voz Piper

Esta atualização registra o progresso feito após o usuário autorizar autonomia técnica ("Manda bala").

### Diagnóstico e correções no piloto Guerra dos Chips

- Branch: `atlas-piloto-chips-20261118`. Criado `src/v4/formatos/planos/reuso/atlas_chips_factual_2026.json` com **139 palavras, 62,5s sintéticos** e fontes TSMC/ASML/BIS; mantém fixture legado `atlas_chips.json` **sem alterações**. O novo vídeo narra Taiwan/TSMC (74% da receita de wafers da própria empresa com tecnologia avançada em 2025, **não share global**), Holanda/ASML EUV, EUA/Nvidia e política de exportação EUA-China 2022 vs Jan 2026.
- Sob os mesmos componentes visuais ATLAS, foram corrigidas progressão visual >3s, pino Nvidia fora de safe area, cenas com cards e continuidade factual.
- **Defeito GENÉRICO no fiscal** `src/v4/formatos/plano.py`: `F-COMPOSICAO` somava camadas sequenciais como simultâneas; agora varre intervalos abertos e exige número real de cards sobrepostos, sem alterar o limite. Teste de regressão `test_atlas_substituicao_de_cards_nao_conta_como_todos_simultaneos` foi adicionado e revisado depois de ter referenciado cards removidos do storyboard; consultar CI atual para confirmação final.
- Workflow `.github/workflows/atlas-chips-reuso.yml` desacoplado do runner `ubuntu-latest` (que usou Ubuntu 26.04 e falhou instalando FFmpeg): pin `ubuntu-24.04` + `imageio-ffmpeg==0.6.0` portátil; roda **86 testes** (1 montagem MP4 requer ffprobe e fica no CI completo). Não chama Claude/Gemini/Edge.
- Execução `44379818856` **SUCESSO** (85 testes/1 deselect antes do último teste), preflight verde, **34 quadros reais** sem bloqueios, avisos `102 A-CREDITO-RODAPE` (34×3 plataformas). Os créditos baixos continuam risco editorial antes da publicação; base Natural Earth é domínio público (cortesia), fotos CC BY precisam atribuição realmente acessível.
- Execução `44381002660` **SUCESSO** (86 testes, 1 deselect), 34 quadros, zero erros bloqueadores; troca entre cartão "OUT 2022" → "JAN 2026" verificada **visualmente** em artefato. Arquivo de amostragem extraído no chat `/mnt/data/atlas_chips_factual_atualizado/quadros/cenas_2022_2026.jpg`, sem inferir que está acessível em novo chat: o artifact CI `44381002660` é a referência.
- Na sequência, duas fotos reais foram integradas **SOMENTE À BRANCH EXPERIMENTAL DO PILOTO**, com registros em `src/v4/biblioteca_comprovada.json`: foto exterior TSMC Fab 18/Tainan e close wafer, ambas Commons CC BY 4.0, IDs correspondentes, SHA256 conferido. `p-tsmc` virou foto; componente de wafer usa estrutura ATLAS já existente. Ambas foram escolhidas após inspeção visual de thumbnails; **não aprovadas para publicação**. Workflow exige origem/licença e resolução. Tentar foto sem SHA/license/legibilidade deve falhar fechado.
- Primeira CI multimídia `44381945281`, `44382124573` falhou em TESTE AUTOMATIZADO por `StopIteration` do novo teste de regressão que assumia cards descartados do roteiro, antes de prévia. Corrigido em commit `e5f3ad67`, agora usa cópias sintéticas da camada `pct`, e workflow atualizado `77f8b3b1` para rerun quando testes mudam. **Execução `44382454681` em andamento na última consulta**. Confirmar status, logs, assets e inspecionar styleframes, não chamar integração aprovada antes disso.

### TTS PT-BR experimental, offline e custo zero de API

- Criado `scripts/atlas_voz_livre_amostra.py` e `.github/workflows/atlas-chips-voz-livre.yml`, **sem modificar a voz oficial**.
- Piper `pt_BR-cadu-medium` da coleção `rhasspy/piper-voices` PINNED commit `cf910fb59f1d79ab3b625a63993a108751c6c25d`; modelo explicitamente re-treinado do base `rdh` CC0, dataset CC0 conforme MODEL_CARD, motor Piper GPL-3.0; rever obrigação jurídica final se incorporar. **Não usar versão antiga Cadu baseada em modelos não comerciais!**
- Workflow **`44381558476` SUCCESS**, gerou 7,755s em 22.050Hz de narração original do gancho chips; ONNX SHA256 `d5a662e3f606d5a49dd29ba9ce90c304ae45dd9543f8b0c773bcb0de282499de`; WAV SHA256 `291cfb14d6ac2cba5f0a0ebded80877f187f0ce4168158d6f316ecec28edf4b4`; artifact `atlas-chips-amostra-piper-cadu` ID `14462873018` com WAV e MODEL_CARD, retenção 7 dias.
- Arquivo MP3 convertido do WAV e entregue ao usuário `sandbox:/mnt/data/atlas_chips_voz/voz_ptbr_cadu_amostra.mp3`, **apenas como amostra para ouvir**. Qualidade/naturalidade NÃO comprovada por teste; jamais substituir voz atual sem aprovar audio. Relevante: termos comerciais de Edge/Azure gratuitamente não devem ser pressupostos; recurso Piper é candidata livre sem serviço extra.
- **Nenhum MP4 real da guerra dos chips foi publicado nem homologado**. Os tests de quadros continuam com WAV de teste e narracao sintética; precisam aprovar fotos, créditos, narração e MP4 final.

### Próximos passos sem pedir autorização em todo ajuste

1. Confirmar CI `44382454681`; resolver falhas reais e ver contato do vídeo **com fotos**.
2. Inspecionar safe areas/legendas/créditos e sincronização de 2022 vs 2026.
3. Ter amostra Piper avaliada, considerar teste de voz real integral somente sem assumir licença comercial do produto Edge.
4. Produzir MP4 privado da guerra dos chips com **voz e fotos reais corretamente atribuídas**, depois validação humana e sem publicação.
5. Registrar métricas reais de qualidade, custos e reutilização na biblioteca; preservar produção, DOSSIÊ e NTC.


## 11. Piloto chips com fotos reais — validação experimental

**Em 18/11, após a interrupção do streaming do ChatGPT,** o teste cartográfico factual `44379818856` terminou SUCCESS: preflight 22 itens, **34 quadros sem erros bloqueadores**, mas 102 avisos de crédito no rodapé (34 × 3 redes). O assistente baixou e inspecionou `styleframes.jpg` e `amostragem.jpg`: confirmou a linguagem do Panamá, mas constatou que o episódio precisava de fotografias reais para não ficar somente mapa + cards.

Na branch **`atlas-piloto-chips-20261118`** foram adicionadas **somente para prévia privada** duas mídias de origem Commons ao `src/v4/biblioteca_comprovada.json`, cada uma com SHA256 **do arquivo exato de miniatura 960 px**, licença e comprovação visual:
- `commons:TSMC_Fab_18_May_2025.jpg`: fachada TSMC Fab18 em **Tainan**, 2025, 4300streetcar, CC BY 4.0, fonte https://commons.wikimedia.org/wiki/File:TSMC_Fab_18_May_2025.jpg. Foto circular ancorada em Tainan no plano factual; **não** comprova produção interna/porcentagem.
- `commons:Silicon_wafer_close_view.jpg`: foto de wafer de silício, Le hollandais volant, CC BY 4.0, https://commons.wikimedia.org/wiki/File:Silicon_wafer_close_view.jpg. Foto **genérica** de wafer em cartão de evidência; **não** atribuída à produção da TSMC. Não foi escolhida a foto da sede ASML como substituto de máquina EUV.

Os direitos e SHA das miniaturas foram rechecados na galeria Wikimedia de execução `44380034537`. O índice global **da produção permaneceu intocado**; esses dois novos registros só existem no ramo experimental e aguardam conferência do MP4/créditos antes de homologar.

O plano `src/v4/formatos/planos/reuso/atlas_chips_factual_2026.json` ganhou beat `b2b-wafer`: foto real durante a palavra **wafers** e notas factuais sucessivas, sem poluir. A tentativa inicial de usar `atlas.tecnica` falhou corretamente (`F-TECNICO-SEM-MECANISMO`); foi substituída por `atlas.painel` com ROI correspondente a Taiwan, mantendo fundo cartográfico e **sem afrouxar o fiscal**. Foram corrigidos intervalos de `F-COLISAO` e `F-SEM-PROGRESSAO`; prévia ainda aguarda validação.

O renderizador `motor4/remotion/src/formatos/Primitivas.tsx` foi alterado **somente para ATLAS**: foto/cartão `dossie.documentCard` fica 0° (reta e centralizada), enquanto estilo inclinado do DOSSIÊ é preservado. Testes em `tests/test_formatos.py` foram adaptados para verificar **quatro cards simultâneos** sem depender dos IDs de conteúdo do episódio.

**Novas validações**:
- `44382124573`: falhou por teste legado que citava cards removidos do roteiro, corrigido.
- `44382454681`: preflight encontrou colisão de etiquetas, uso incorreto de palco técnico e parâmetro de estilo proibido; corrigidos.
- `44383067422`: auditoria apontou `atlas.painel` sem ROI geográfico; corrigido.
- `44383504685`: falhou em F-SEM-PROGRESSAO de 3s no beat do wafer; corrigido introduzindo nota ligada à fala.
- **`44383964727`**: validação com fotos, última consulta **in_progress**, conferir status final/logs/artefato. **Não afirmar sucesso até ver os resultados.**

Workflow prévia completa **`.github/workflows/atlas-chips-previa-privada.yml`** está preparado: dispara apenas ao registrar `.github/atlas/chips_previa.txt` no ramo experimental; usa Edge TTS (não Gemini/Claude pago), mídia aprovada por SHA, preflight, quadros, render completo, fiscal e Telegram privado. **NÃO foi disparado nesta atualização**, pois a prova de quadros ainda estava sob revisão. Essa prévia NÃO publica em redes; usa Edge como voz provisória, ainda exigindo aprovação de voz e termos antes de postagem.

**Próximo passo:** conferir resultado de `44383964727`, corrigir se falhar. Se ficar verde, baixar a folha de quadros e inspecionar de verdade — principalmente foto TSMC, wafer, cartões retos, não sobreposição, créditos. Só então disparar a prévia privada completa, inspecionar MP4, marcar limites factuais e atualizar aqui.


## 12. Recuperação da interrupção e correção genérica do slot de foto (18/11, 19h55 UTC)

Após aviso do usuário de **transmissão interrompida**, o assistente retomou a leitura ao vivo do GitHub sem pedir que o usuário repita o histórico. O branch do segundo piloto **`atlas-piloto-chips-20261118`** já havia recebido uma sequência de correções de foto/cartão até `0c7c30a3`. A validação `44385191234` falhou somente no teste novo que tratava `P.COMP["atlas.painel"]["slots"]["foto"]` como objeto, quando o motor converte para `[x,y,w,h]`. Corrigido no commit **`139107ac`**.

A execução seguinte **`44385594668`** chegou aos testes: **86 passaram, 1 foi deselecionado, 1 falhou** com **F-COLISAO entre fotografia do wafer e duas notas** — o slot de foto anterior sobrepunha a faixa de notas. O commit **`60c39276`** corrigiu `atlas.painel.slots.foto` de modo genérico (novo `y=510, h=565` com nota iniciando em `y=1130`, intervalos separados) na configuração ATLAS, sem mexer no estilo DOSSIÊ.

O commit **`63f47fbc`** ampliou os paths de trigger de `.github/workflows/atlas-chips-reuso.yml` para revalidar automaticamente alterações em `formatos.json`, `plano.py`, `Primitivas.tsx` e `tests/test_formatos.py`, além do plano e scripts. Isso evita que mudanças estruturais escapem da execução de teste. A execução disparada é **`44386176261`**, ainda **em andamento quando este registro foi escrito**; nunca apresentar resultado verde sem consultar logs.

A prova anterior **`44379818856`** foi SUCCESS para 34 quadros **sem fotos** (cartografia+cards), não confundir com prova do novo plano **com duas fotos reais**, ainda dependente de validação. O artefato de fotos do piloto tem problemas de texto/crédito detectados em `44383964727`, motivando ajustes. **Não foi disparado** o workflow de MP4 `atlas-chips-previa-privada.yml`, nem publicação/merge, pois as fotos precisam passar na inspeção real primeiro.

**Próximas tarefas:** conferir `44386176261`; se houver falhas, corrigir sem flexibilizar o fiscal. Se verde, **baixar e inspecionar folhas de quadros com as duas fotos** antes de disparar episódio privado com Edge TTS, entregue apenas no Telegram. Depois verificar créditos de imagens CC BY 4.0 e possibilidade de sobreposição de interface de plataformas. Preservar todos os demais motores.


## 13. Composição fotográfica reutilizável no ATLAS

A prova CI **`44386176261`** não foi aprovada: **87 testes Python passaram** (1 teste de montagem MP4 deselecionado) e as duas fotografias tiveram SHA/origem/licença validados, mas o preflight bloqueou corretamente porque o cartão de wafer invadia a área do território geográfico (`F-COBRE-TERRITORIO`, em torno dos 15,9/16,7/21,3 segundos). O motor não deve relaxar esse fiscal.

**Solução arquitetural experimental implementada na branch `atlas-piloto-chips-20261118`:** composição reutilizável `atlas.fotografia` em `src/v4/formatos/formatos.json`, com `palco=mapa`, `quadro=null`, foto central reta/verificável (`y=445,h=650`) e nota (`y=1130,h=88`), sem novo mecanismo nem visual exclusivo. Isso permite que o mapa ceda espaço a uma fotografia factual quando faz sentido, como o usuário pediu; não finge que a área do mapa continua visível ao mesmo tempo. A câmera continua cartográfica ao fundo, a foto é protagonista. O beat `b2b-wafer` do plano factual usa a nova composição.

Commits relevantes: **`c6ebdc35`** (catálogo), **`545cd5df`** (plano do wafer) e **`83827ffc`** (teste para foto legível, slots separados, proteção do território e motor DOSSIÊ intacto). Workflow reativado no run **`44387091456`**, ainda não havia conclusão na última consulta. **NÃO afirmar aprovação visual/CI até abrir resultado.** Antes de prévia MP4, inspecionar styleframes e checar pequenos créditos/título das fotografias, que tiveram problemas de truncamento em execução anterior.

Esse último ajuste é geral ao ATLAS, não adapta o motor ao assunto dos chips. O plano da produção não foi mesclado com branches estáveis; não houve postagem.

## 14. 18/11 — correção da máscara de Shorts, CI verde e prévia privada acionada

O usuário disse **"Continua"** e o assistente retomou a inspeção do GitHub, na branch experimental `atlas-piloto-chips-20261118`, sem alterar produção, DOSSIÊ ou NTC.

A execução `44387091456` **FALHOU** após 87 testes Python verdes, preflight de 32 itens e 34 quadros por **um bloqueador**: `R-PLATAFORMA` da `fotografia-wafer` em 20,88 segundos sob a coluna de ícones do YouTube Shorts. Causa identificada no renderizador `motor4/remotion/src/formatos/Formato.tsx`: a função `respira` aplicava um `scale` progressivo de até **1,5%** a `dossie.documentCard`, também quando usado como foto ATLAS, ultrapassando a área segura já calculada em `layout.slot`.

**Correções pontuais na branch de chips:**
- Commit `9a0e256f`: impede o `respira` externo de TODAS as camadas ATLAS; preserva movimento de mapa/entrada e comportamento DOSSIÊ.
- Commit `11ef2961`: regressão `test_atlas_fotografia_nao_respira_sobre_icones_de_plataforma` em `tests/test_formatos.py`; verifica geometria da composição em relação às máscaras e a guarda contra `scale` externo.
- Commit `1828f297`: inclui `Formato.tsx` nos gatilhos do workflow `atlas-chips-reuso.yml` (arquivo antes omitido) e remove duplicata de gatilho de testes.
- **CI `44403285791` SUCESSO**: 32 itens de preflight, 34 quadros, **zero bloqueadores** e duas fotos verificadas (SHA e licença). Foram inspecionados `styleframes.jpg` e métricas do artifact `atlas-chips-reuso-sintetico`, mas **isso não equivale a MP4 homologado**.
- **Persistem 102 avisos `A-CREDITO-RODAPE`** (34 quadros × 3 redes). Respeitar a decisão visual do usuário de manter créditos baixos; não elevá-los globalmente nem publicar enquanto condições de atribuição e interface não estiverem resolvidas.
- Commit `da68c4d6`: criou `.github/atlas/chips_previa.txt` na branch de chips para disparar **apenas** `atlas-chips-previa-privada.yml`. Workflow `44404242103` estava **QUEUED** na última consulta (21:42 UTC): obter status real antes de afirmar MP4 gerado ou entregue. Workflow usa Edge TTS de teste, fontes licenciadas por SHA, fiscal, render e entrega somente ao Telegram privado autorizado se passar; **não publica nas redes**.

**Próxima ação:** consultar `44404242103` pelo GitHub (steps e logs); se falhar, corrigir causa na branch experimental sem relaxar o fiscal. Se concluir, assistir ao MP4 REAL recebido no Telegram, verificar voz, ritmo, geografia, visual da foto wafer, autoria de mídias e créditos. Só depois cogitar homologação. Não fazer merge nem afetar produção/NTC/DOSSIÊ.

## 15. 18/11 — voz real e progressao do gancho (atualização após 21:52 UTC)

O workflow privado MP4 **`44404242103` falhou no preflight, não gerou MP4 nem enviou Telegram**. A narração de teste Edge TTS foi gerada em **58,862 segundos**; o fiscal detectou `F-SEM-PROGRESSAO` por **3,1 segundos** sem novo acontecimento visual entre ~2,2 e ~5,3s. Portanto, o verde anterior com temporização sintética não certificava o plano sob voz real. Não reduzir o limite nem tratar as legendas como eventos visuais para falsear aprovação.

A correção editorial foi feita **no plano experimental de chips** `src/v4/formatos/planos/reuso/atlas_chips_factual_2026.json`, commit **`85f94156`**: no beat inicial, a pergunta sobre a ilha termina quando a narração chega a "Estados", e entra um título "EUA × CHINA" ligado à palavra `@estados` com a mesma composição `atlas.abertura` e componente `editorial.titleOrPayoff`. Não foi criado estilo, efeito ou componente exclusivo, nem alteração no motor. O gancho preserva o mapa como palco.

A revalidação de quadros **`44405025069` terminou SUCCESS**: preflight 32/32, 34 quadros, 0 bloqueadores e 102 avisos de créditos no rodapé (inalterados). O assistant baixou e inspecionou a folha de estilo corrigida; fotos, cartões, mapas e texto seguem linguagem ATLAS. Isso ainda **não prova sincronização real sob TTS**, pois reuso usa tempos sintéticos.

Novo acionamento do workflow audiovisual privado mediante atualização do arquivo de gatilho `.github/atlas/chips_previa.txt`: commit **`9743842e`**, execução **`44405950985`**, que estava **in_progress** na última consulta (21:52 UTC). Consultar GitHub antes de dizer se foi gerado vídeo ou enviado ao Telegram; baixar logs e corrigir eventual falha do fiscal sem afrouxar limites. O workflow não publica nas redes.

**Pendências:** risco dos 102 avisos de crédito, condições de CC BY verificáveis no arquivo final, qualidade visual e naturalidade da voz do MP4, alinhamento factual com as falas. Não mexer em produção, NTC ou DOSSIÊ; o ATLAS de chips continua experimental.

## 15. 18/11 — retomada após transmissão interrompida

O usuário relatou **"Deu transmissão interrompida"**. A retomada ao vivo do GitHub confirmou:
- CI sintética `44405025069` (commit `85f94156`) **SUCCESS**, preflight 32 itens, 34 quadros, **0 erros bloqueadores**, 102 avisos `A-CREDITO-RODAPE` persistentes. A correção havia dividido a abertura em dois títulos, terminando a pergunta antes de mostrar `EUA × CHINA` ao citar Estados Unidos, sem relaxar `F-SEM-PROGRESSAO`.
- O primeiro workflow privado `44404242103` teve **FAILURE** em preflight com Edge TTS de 58,862 s: `F-SEM-PROGRESSAO` (2,2–5,3 s) e por isso nenhum MP4 foi renderizado. Não confundir sucesso sintético com TTS real.
- A segunda tentativa de episódio privado foi disparada pelo commit `9743842e`, que atualizou apenas `.github/atlas/chips_previa.txt`. Workflow `44405950985` estava **in_progress** na inspeção às 21:54 UTC, na etapa `34+ quadros, legibilidade/posicionamentos/plataformas`. **Consultar status atualizado** antes de dizer que o MP4 ou Telegram foram entregues.
- Nenhuma publicação em rede, merge para produção, mudança de NTC ou DOSSIÊ. Os créditos na faixa baixa permanecem pendência crítica para revisão nas interfaces reais e para licenças CC BY.

Próximo passo: conferir `44405950985`. Se falhar, analisar etapa e log, corrigir branch experimental e reexecutar; se passar, exigir revisão humana no vídeo PRIVADO real (ritmo, voz, créditos, fotos) antes de homologar. Não recomeçar atividades já comprovadas.

**Atualização de execução 44405950985:** na consulta de 18/11, a etapa de narração Edge TTS, obtenção de mídias com SHA, **preflight completo com tempos reais** e **checagem dos quadros renderizados com voz real** estavam todas **SUCCESS**. O job avançou à etapa **"MP4 + áudio + portões de qualidade do ATLAS"**, ainda **IN_PROGRESS**. Não afirmar que MP4 existe, que gates finais passaram ou que foi entregue no Telegram até consultar o estado final da execução e seus logs. A etapa de render final pode ser demorada. Link: https://github.com/Heitor2404/coringa-news/actions/runs/44405950985


## 16. 18/11 — estudo de seis referências e proposta ATLAS V2

Após o usuário **reprovar visualmente o MP4 privado Guerra dos Chips de 58,862 s** (voz considerada ruim, cards destoando, mapas zenitais repetidos, pouco acontecimento e aparência robótica), o assistente analisou o arquivo enviado e buscou referências de edição documental. O workflow `44405950985` terminou `success` na infraestrutura e entregou a prévia privada, mas seu próprio `ATLAS_FISCAL` marcou `estado=BLOQUEADO` por `G-MP4-JANELA 36–40 s: CONGELADO`. **Nunca declarar o vídeo editorialmente aprovado.** O workflow experimental desligou a chave Gemini e usou Edge TTS provisório; o usuário **não aprovou a substituição da voz**.

O usuário aprovou a ideia de estudar neo, Branch Education, Wendover Productions, CNBC, Johnny Harris/Vox Borders e fern, pedindo investigação minuciosa e adaptação à identidade Coringa. Foi produzido o **guia PROPOSTO**, sem modificar código nem a identidade aprovada:

- Documento: `docs/v4/formatos/ESTUDO_REFERENCIAS_E_DIRECAO_ATLAS_V2_20261118.md` (branch `atlas-direcao-visual-20261118`), commit `cba5fdeb85ed2f0abb51b314a100441438169533`.
- Contém métodos/sources verificadas (neo FAQ; Branch official; fern official; vídeos Johnny Harris/Wendover/CNBC; decupagem terceirizada fern explicitamente delimitada), matriz de seis referências, identidade inalterada, gramática de 6 verbos `LOCALIZAR/MOSTRAR/DEMONSTRAR/CONECTAR/COMPARAR/REVELAR`, schema conceitual de `ficha_cena`, proposta de preview de 22–25s e gates automáticos/humanos.
- **Gap concreto confirmado:** o catálogo ativo ATLAS só dispõe de mecanismo `mecanismo.eclusa`, e não de litografia/semicondutor; atual `diretor.py` pede `prova`, mas a escolha visual não garante que a narração tenha referente/ação correspondente. São necessárias mídia real **licenciada e comprovada** e capacidade explicativa antes de substituí-la por rota/card.
- **Não implementado:** componentes, perspectiva de mapa 3D, guardas de voz, workflow final e render do novo trecho. Não houve mudança na produção, NTC/DOSSIÊ nem publicação.
- **Próxima prioridade:** aprovar/ajustar a proposta editorial, travar voz anteriormente aprovada, montar storyboard de 22–25s para a Guerra dos Chips, checar mídia EUV comprovada/licença e viabilidade do mecanismo simplificado, e só então implementar em branch isolada e renderizar preview curto real.
