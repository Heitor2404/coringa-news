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


## 17. 18/11 — neo vídeo completo, decupagem e ATLAS LONG

O usuário enviou `videoplayback.mp4` e confirmou que o vídeo é do **neo**, *How One Ship Caused a Global Traffic Jam*, pedindo estudo minucioso pensando em **futuros vídeos longos no YouTube**. Estudo completo consolidado em `docs/v4/formatos/DECUPAGEM_NEO_SUEZ_ATLAS_LONGFORM_20261118.md` da branch **`atlas-direcao-visual-20261118`**, commit **`ed0fad18b131ebeae555597f33a39e3604dcc05f`**.

- Arquivo de origem: 489,732 s, 640×320 (2:1), 25 fps; 12.242 quadros decodificados; estudo visual com 245 amostras a cada 2 s, mudanças medidas em 0,2 s; 38 transições fortes estimadas (não número total de planos); −17,66 LUFS, −0,59 dBTP, LRA 5,80. **Não foi feita escuta subjetiva verificável da voz.**
- Decupagem completa: mapa global→satélite→3D do navio→escavadeira/rebocadores reais→rotas alternativas→congestionamento→efeitos logísticos representados com destaque vermelho em portos/contêineres→desbloqueio real→payoff de navio e mapa.
- Conclusão crítica: neo usa muito **mapa zenital**; a superioridade não exige obrigatoriamente mapa inclinado 3D, e sim **mapa com função, alternância de escala e objetos/mecanismos reais, progressão dentro de long takes (20–35 s)**. Copiar cenas, assets Getty, cor vermelha ou modelo 3D cinzento não é apropriado; adaptar **gramática causal** preservando tokens do Coringa.
- Proposta longform **não implementada**: preset horizontal 1920×1080 separado do Short vertical 1080×1920, diretor semântico comum e assets com licença, novo tratamento de legenda/créditos, progressão por ação e mudança de entendimento (não regra cega 3 s), voz aprovada, capítulos/narrativa com consequências, prova de produção de 90–120 s antes de vídeo 8–10 min.
- Nenhum código alterado, sem merge, sem vídeo produzido, sem postagem, NTC/DOSSIÊ/produção intocados.


## 18. 18/11 — fern integral decupada, pronta para ATLAS V2

O usuário enviou `videoplayback 2.mp4`, filme integral **fern — The Hunt for the King of the Dark Web**, e pediu auditoria audiovisual minuciosa para futuro YouTube longo. O vídeo original da versão em inglês foi adaptado do canal alemão **Simplicissimus** (conforme sua descrição). Relatório completo da análise do arquivo **salvo em GitHub**: `docs/v4/formatos/DECUPAGEM_FERN_DARK_WEB_LONGFORM_20261118.md` branch `atlas-direcao-visual-20261118`, commit **e0c06e2cbaf27184c86773f35a779d7ec4b1b761**.

**Mídia verificada:** 18min49,56s, 640×320, 25fps, 28.239 frames metadados. 226 amostras visuais a cada 5 s em 6 folhas; FFmpeg full-scan scene threshold 0,28 gerou 209 picos agrupados em 153 transições visuais fortes (não contagem exata de cuts), mediana entre detecções ~3,48s. Som medido: **−10,5 LUFS, +0,9 dBTP, LRA 4,8 LU** — NÃO copiar mastering; meta Coringa −14 LUFS e pico ≤−1 dBTP. Não afirmar ter escutado/avaliado subjetivamente voz/trilha; arquivo 640×320 não comprova nitidez tipográfica original.

**Elementos essenciais:** cold open 0–55 s com investigação policial encenada; retrospectiva e cronologia 1:25–5:40; bloco de publicidade integrada NordVPN **5:50–6:37, excluir das métricas editoriais**; investigação com mapa + **cadeia de provas email→perfil→identidade (~8:10–9:55)**; Bangkok/maps/calendário (~10:00–11:40); hotel 3D ~11:40–12:20; operação internacional com duas tramas convergentes 12:20–15:15; **retorno/payoff do cold open 15:15–16:15**; documentos reais do DOJ 17:30–17:45; consequência aberta e plataformas sucessoras até o final. A fern usa páginas reais, mapas, reconstituições, linhas do tempo e arquivo por função narrativa, sem alternância mecânica.

**Lição combinada neo+fern:** neo mostra `objeto → mecanismo → geografia → consequência`, fern mostra `promessa → pistas verificáveis → conexão → payoff → consequência`. Ambos reaproveitam cenários/telas quando há progressão semântica; regra de 3 s de cards/cortes é inadequada se aplicada rigidamente a longform. Gramática ATLAS existente 6 verbos preservada, acrescentar operações **ANTECIPAR/INVESTIGAR/RETORNAR** no contrato sem inventar estética. ATLAS segue cartográfico, escuro, off-white, amarelo; não copiar vermelho cinematográfico fern nem bonecos genéricos, não presumir que tudo precisa 3D.

**Estado:** estudo documental concluído; **nenhum código, renderer, workflow, clip ou voz alterado**, nenhuma publicação, produção e NTC/DOSSIÊ intactos. Próximo passo recomendado **parar pesquisa por ora**, implementar P0 em branch isolada: fichas de cena/evidência/prova, travar narrador aprovado, mostrar `BLOQUEADO` adequadamente, criar teste curto de 20–30s chips; só após aprovação um capítulo horizontal 90–120s, não render 19min de imediato.


## 19. 18/11 — auditoria real de fontes e Pexels API pausada

Após o estudo neo/fern, usuário corrigiu que a maioria dos acervos externos **já estava conectada ao motor** e relatou indisponibilidade da API Pexels. Auditoria no GitHub confirmou:
- `src/acervo.py` na branch `motor-integral-v4` pesquisa **Wikimedia/Wikipedia, NASA imagens, iNaturalist, Library of Congress, Metropolitan Museum, Europeana (se chave), Openverse, Wikidata, museus Art Institute/Cleveland, GBIF, Smithsonian e vídeos**; `src/midia.py` já implementa **Pixabay foto/vídeo (com PIXABAY_API_KEY), NASA vídeo, Commons vídeo, Internet Archive e Openverse imagens**. `src/v3/biblioteca.py` possui SQLite/hash/ingestão de arquivos locais `Biblioteca.ingerir(arq,meta)`, reuso e classificação de licença. Não apresentar essas fontes como integrações novas nem alegar que simplesmente aumentar provedores resolve a direção.
- **ATLAS específico**: `src/v4/formatos/produzir.py` `ativos` usa SOMENTE itens de `src/v4/biblioteca_comprovada.json`, com URL/licença/prova/hash; carregamento da imagem usa **PIL Image.open** e gera JPG, não incorpora MP4 Pexels automaticamente. Biblioteca do ramo de chips tem 9 itens (2 fotos experimentais) na última inspeção. A biblioteca global v3 e catálogo específico ATLAS são sistemas diferentes; integração não comprovada, e ainda não há composição de vídeo real dominante aprovada no ATLAS.
- Consulta 18/11/2026 às páginas oficiais Pexels: `https://www.pexels.com/api/` e `https://help.pexels.com/hc/en-us/articles/900004904026-How-do-I-get-an-API-key` declaram **New API key issuance is currently paused**; Pexels usa API vigente apenas para contas com chave antiga. Licença `https://www.pexels.com/license/` permite download manual e uso comercial conforme restrições. Termos `https://www.pexels.com/terms-of-service/` (atualizados out/2026) **proíbem scraping e extração automatizada não autorizados**: não recomendar robôs sem API nem endpoints internos para contornar bloqueio.
- **Plano recomendado**: `Pexels manual/download legítimo → pasta privada de mídia + URL do item, autor, licença vigente, hash e nome do objeto → função de importação/curadoria v3 → adaptar catálogo ATLAS e render para clipe MP4 verdadeiro (com licenças/atribuição, FPS, duração, audio, segurança) → preview privado`. Não hospedar biblioteca Pexels crua em repositório público; também verificar condições de armazenamento/cópia pela licença. `api@pexels.com` pode ser consultado para futuro acesso oficial, sem prometer exceção. Primeiro priorizar os APIs de vídeo JÁ existentes.
- Estado: apenas auditoria/recomendação, nenhum código produtivo alterado.


## 20. 18/11 — auditoria geral do repositório antes do ATLAS V2

O usuário solicitou **verificar o motor inteiro antes de desenvolver novas funcionalidades**, para não duplicar código e encontrar caminhos de reaproveitamento. Foi feita auditoria estática dos cinco ramos principais e leitura dos fluxos V2/V3/V4/ATLAS/DOSSIÊ/NTC, com inspeção de executores e registros de runs. Relatório detalhado: `docs/arquitetura/AUDITORIA_GERAL_REUSO_MOTOR_20261118.md` na branch `atlas-direcao-visual-20261118`, commit **`53f81832ca0cabec3f6d76307f8888822dbc6e44`**.

**Achados P0:**
1. `src/v3/plano_av.fichas` **JÁ IMPLEMENTA** sujeito/ação/transformação/consequência/prova/mídia/status; `src/v3/linguagem.forma_do_evento` escolhe forma adequada à ação. **Não construir ficha_cena ATLAS nova**; criar adaptador versionado para beats/slots ATLAS.
2. `src/v4/componentes.py` **JÁ TEM** `registro.video` e `registro.foto`, `mapa.rota`, recorte 2.5D, câmera 3D e esquema, mas **ATLAS** `src/v4/formatos/produzir.py:ativos` só baixa/decode de imagens por PIL e converte em JPG. **Reutilizar vídeo real V4 via ponte**, mantendo licença/SHA/tempo/creditação, sem tentar reescrever renderer.
3. `src/acervo.py`/`src/midia.py` têm muitos provedores; `src/v3/biblioteca.py` já ingere arquivos locais com SHA, pHash, SQLite, classificação de licença, sem armazenamento remoto aprovado. `src/v4/biblioteca_comprovada.json` tem 7 itens na base, 9 no ramo chips; curadoria experimental está isolada na branch `atlas-biblioteca-20261118`. **Integrar sem confundir os acervos.**
4. V3 já tem `src/v3/revisao_multimodal.py`, `src/v3/fiscal_editorial.py`, `src/v3/memoria.py`, `src/v3/receitas.json`: **14 receitas (11 testado, 3 proposto, 0 aprovado)** e `docs/memoria/regras_editoriais.json` com 0 regras. ATLAS tem fiscal de imagem/geom/ritmo próprio, mas não herda revisão semântica do V3.
5. `src/v4/formatos/diretor.py` contém função de geração `pedir`, porém os entrypoints/workflows ATLAS examinados executam **plano JSON pré-existente**, sem invocá-la. **Não afirmar ATLAS plenamente autônomo**.
6. Ramo `main` ainda possui workflow diário, mas **AGENDAMENTO PAUSADO** por variável; execução `44390925982` aparenta GitHub `success`, porém job de geração **skipped**. Ramo chips `44405950985` sucesso operacional, mas fiscal `BLOQUEADO` por 36–40s congelados; reforçar estados de produto separados da conclusão do CI.
7. Branches de direção, chips e biblioteca **divergiram**. Não fazer merge cego nem mudar produção, DOSSIÊ e NTC. NTC vetorial tem próprio `src/fabula.py` e `canais/ntc/vetor/*`; reutilizar apenas serviços versionados.
8. `docs/v4/CAPACIDADES.md` registra HyperFrames 457 itens (poucos testados), Revideo falhou no CI e outros status `not_tested`; não tratar registro como homologação de qualidade.
9. ATLAS LONG horizontal 1920x1080 continua **proposta**, não implementação; um único diretor semântico com perfis de saída separados.
10. Relatório baseado em trees completos e inspeção seletiva de arquivos e CI; **não executou suíte inteira nem auditoria dinâmica de todos os módulos**. Foram encontrados **74 arquivos de testes Python** na branch `motor-integral-v4`, mas isso não indica número de testes individuais executados.

**Prioridade recomendada:** criar branch isolada de integração, mapear contratos existentes → adaptar fichas V3/linguagem → habilitar vídeo real V4 no ATLAS por módulo compartilhado e biblioteca curada → consertar estado editorial/voz autorizada → produzir 20–30s vertical com imagens reais → só depois criar preset Long 16:9 e prova de 90–120s. **Nenhuma linha de código do motor foi alterada nesta auditoria**, apenas documentação experimental.


## 20. 18/11 — auditoria geral anti-duplicação antes do ATLAS V2

Usuário pediu **auditoria geral do motor, não só mídia, antes de implementar ATLAS V2**, para não duplicar capacidades. A resposta foi interrompida no app; auditoria retomada e concluída como **revisão arquitetural de código e workflows**. Relatório detalhado salvo **somente** em `atlas-direcao-visual-20261118`:
- `docs/auditorias/AUDITORIA_GERAL_REUSO_E_LACUNAS_20261118.md` — commit `1043e41f7533f61c4e35affc995fffa22ecb3bf6`.
- Escopo: `main`, `motor-integral-v4`, `atlas-direcao-visual-20261118`, `atlas-piloto-chips-20261118`, `atlas-biblioteca-20261118`, NTC. `main` é a branch padrão; workflow do dia condicionado à variável `AGENDA_ATIVA` para automático, cuja configuração não foi inspecionada.
- Achado central: **V2/V3 já têm contrato de acontecimentos, fichas audiovisuais por cena (`src/v3/plano_av.py`), escolha de forma antes da câmera (`src/v3/linguagem.py`), receitas e memória humana, revisão multimodal, fiscal, gate humano; V4 integral já tem render de MP4 real, mapas, clipes, 2.5D e backends; biblioteca global `src/v3/biblioteca.py` já possui hash, licença, ingestão local**. NÃO recriar diretor, banco, fiscal nem mecanização genérica antes de integrar estas capacidades.
- ATLAS formatos `src/v4/formatos/produzir.py::ativos` **continua JPG/PIL** com `src/v4/biblioteca_comprovada.json`, diferente de `src/v4/episodio.py` com `registro.video`; biblioteca experimental `atlas-biblioteca-20261118` já existe com catálogo, 6 candidatos, workflow/testes, mas não integrada. Branch chips e branch biblioteca divergiram de branch direção; evitar merge indiscriminado.
- Testes: 79 arquivos Python em `tests/` base V4 (NÃO contagem de testes executados), documentos anteriores de regressão V3 e CI chips; **não houve nova suíte nem render executados nesta auditoria**. Chip privado com job `success` mas fiscal `BLOQUEADO`, e voz provisória não aprovada; NTC e DOSSIÊ isolados.
- Próximas etapas em ordem: **P0** estados/editorial e voz/preset aprovado + adapter ficha V3→beat ATLAS, **P1** usar vídeos reais aprovados no ATLAS e direção por prova, **P2** prova vertical 20–30s e piloto horizontal 90–120s, ambas com revisão humana. Plano editorial original ATLAS conservado sem mudanças.
- Nenhuma alteração de código, workflow, produção estável, NTC ou DOSSIÊ; **somente docs no ramo experimental**.


## 21. 18/11 — ATLAS V2 P0 implementado e CI 98 testes

O usuário autorizou **prosseguir com integração ATLAS V2**, após auditoria anti-duplicação. Nesta rodada o assistente **alterou código** somente no ramo experimental `atlas-direcao-visual-20261118`, SEM render, sem IA, sem merge/publicação, sem mudanças `main`/estável/NTC/DOSSIÊ.

**Implementação concluída:**
- `src/voz.py::narrar(exigir_gemini=True)` parâmetro opcional, default False, recusa fallback Edge para ATLAS. `src/v4/formatos/canais/coringa.json → narrador` fixa Gemini `Charon`, velocidade 1, tom "narrador de documentário, voz grave e firme" (configuração original `config.json`). `src/v4/formatos/produzir.py::narrar` aplica somente quando gera voz **nova** ATLAS e registra provedor, voz, hash; arquivo cifrado já existente é preservado sem alegar aprovação auditiva. Os outros motores continuam com comportamento anterior.
- `src/v4/formatos/estado.py` **reutiliza `src/v3/estado_final.py`**, exige MP4 íntegro, `nao_publicado`, portões de áudio/ritmo/legenda, zero congelamentos e zero bloqueios. `src/v4/formatos/__main__.py` ganhou `gate` com exit code 1 em BLOQUEADO; `src/v4/formatos/produzir.py::telegram` exibe estado conferido; `.github/workflows/formatos-piloto.yml` ganhou gate **após** Telegram privado, antes de arquivar evidência cifrada, impedindo conclusão verde se fiscal BLOQUEADO. Workflow piloto de chips antigo na branch separada NÃO foi modificado.
- `src/v4/formatos/diretor.py` ganhou ponte **opcional** `contexto_v3={roteiro,acervo,fatos,eventos}` que **chama `src/v3/plano_av.fichas` e `texto_prompt`**, com validações `F-EVENTO-SEM-BEAT` e `F-MECANISMO-FORA-ATLAS` para evento crítico. **Ainda não foi conectada a um gerador totalmente automático de episódios**; não anunciar isso como concluído.

**Testes reais no Actions:** `https://github.com/Heitor2404/coringa-news/actions/runs/44427175545` — success, 96 testes Python + JS/TS; `https://github.com/Heitor2404/coringa-news/actions/runs/44427556402` — **success, 98 testes Python + JS/TypeScript** com ponte V3. `tests/test_atlas_integracao_p0.py` e `.github/workflows/atlas-validacao.yml` foram atualizados. CI sem Gemini, Claude, vídeo ou Telegram.

**Documentação P0:** `docs/v4/formatos/INTEGRACAO_P0_ATLAS_20261118.md`. Próxima prioridade **P1**: ligar `contexto_v3` a orquestrador real, reusar vídeo real `registro.video` + FFmpeg da V4 integral no ATLAS formats com licenças/proveniência e plano de prova real grande; só depois gerar prévia curta de chips com voz aprovada e validar a qualidade visual. Sem retorno automático ao mapa/card se cena exige ação.


## 22. 19/11 — ATLAS P1 prova visual dominante, vídeo real V4 e Pexels manual

Usuário autorizou CONTINUAR após o ATLAS P0 98 testes verdes. Nesta rodada o assistente **implementou P1 audiovisual** só na branch `atlas-direcao-visual-20261118`, **sem mexer em main, `motor-integral-v4`, NTC, DOSSIÊ, produção e sem gerar/publicar novo episódio**.

**Código:** `src/v4/formatos/formatos.json` adicionou composição `atlas.prova`, primitiva `atlas.provaVisual` (foto grande) e clipe `registro.video` APENAS no catálogo ATLAS. `motor4/remotion/src/formatos/Primitivas.tsx` adicionou foto principal sem card/pino; `src/v4/formatos/produzir.py` passou a incluir vídeos reais do catálogo `src/v4/biblioteca_comprovada.json`, conferir SHA original, `uso_comercial=sim`, natureza, autor/licença, `ffprobe`, duração e link de origem, e reusar **`src/v4/backends/legado.render_video` já existente** (FFmpeg, recorte vertical fixo, sem audio original). `src/v4/formatos/plano.py` bloqueia tipo errado, vídeo sem duração, sobreposição de camadas escondidas, falta de crédito da foto. `motor4/remotion/src/Camada.tsx` exibe crédito do vídeo na banda INFERIOR abaixo da legenda, com selo REGISTRO em vez de ESQUEMA; `scripts/formatos_validar.py` recebe imagens ao gerar a prévia e pode exibir a atribuição no styleframe. `src/v4/formatos/diretor.py` recebeu instrução para escolher mídia real relevante (não vídeos genéricos fingindo ser a máquina/fábrica).

**Pexels sem API:** `produzir.ativos` pode usar **URL direta do vídeo** OU página do Pexels + campo `arquivo_ext=".mp4"`, mas só quando `CORINGA_MIDIA_LOCAL` contém arquivo local legítimo nomeado `<sha256>.mp4`, com bytes conferidos por hash da origem. Não faz scraping e não supõe que API voltou. Essa importação continua exigindo que curadoria registre direito comercial, autoria e prova factual. A biblioteca global V3 e a V4 comprovada **não estão fundidas**; precisa de ponte posterior.

**Validação e limites:** `tests/test_atlas_integracao_p1.py` + CI ATLAS P0/V1, testes unitários de proveniência/tipo/creditação, e teste FFmpeg com mp4 sintético criado na CI, recortado REALMENTE pelo backend legado para 1080×1920, sem áudio de origem; nenhuma chamada Gemini/Claude. Run `44429572086`: success, 108 testes Python + JS/TS. Run `44430232954`: success, 108 testes + smoke FFmpeg real. A primeira tentativa de smoke `44429900573` FALHOU **ANTES** dos testes porque a action externa setup-ffmpeg não conseguiu ler readme de versão; `.github/workflows/atlas-validacao.yml` agora usa FFmpeg pré-instalado do runner, apt como fallback. **Última rodada de Pexels manual `44430724950`: SUCCESS; 108 testes Python passaram e verificações JS/TypeScript verdes**, sem chamadas a IA.

**Documento completo:** `docs/v4/formatos/INTEGRACAO_P1_ATLAS_20261119.md`. **A prova de engenharia NÃO é prova estética**: ainda não existe vídeo real licenciado de TSMC/EUV no catálogo que tenha sido testado em uma prévia; nenhuma validação audiovisual final, som no ouvido ou seleção dinâmica fim-a-fim foi realizada. Não afirmar que melhorou vídeo dos Chips ainda. Próximos passos: ponte controlada do acervo V3 ao ATLAS + curadoria de mídia para a pauta → prévia vertical 20–30s com Gemini/Charon aprovado → avaliação humana → capítulo horizontal 90–120s.


## 23. 19/11 — ATLAS V2 P1 fotos, video real e biblioteca V3 integrados

**O usuário disse "Continue", autorizando seguir a integração audiovisual após P0**. Implementação realizada **SOMENTE** em `atlas-direcao-visual-20261118`. Sem merge, sem modificação da produção/NTC/DOSSIÊ, sem publicação, sem chamadas de Claude/Gemini ou vídeo documental novo nesta rodada.

**P1 audiovisual:**
- `src/v4/formatos/formatos.json` permite `atlas.provaVisual` (foto documental grande, sem card/pino) + `atlas.prova` e clipe `registro.video`. Remotion `motor4/remotion/src/formatos/Primitivas.tsx` desenha a foto principal com crédito; `Camada.tsx` coloca atribuição dos vídeos na faixa inferior.
- `src/v4/formatos/produzir.py` usa **o backend existente** `src/v4/backends/legado.render_video` (FFmpeg; 9:16, sem áudio original, sem congelar para alongar, proteção de ampliação). `ativos()` agora identifica vídeo real pelo tipo, exige licença comercial, prova e hash da origem, registra via ffprobe; usa cache local por SHA para Pexels baixado legitimamente (sem API/scraping).
- `src/v4/formatos/plano.py` valida tipo, duração, crédito e sobreposição invisível; prévia `scripts/formatos_validar.py` recebe créditos da mídia. Diretor em `src/v4/formatos/diretor.py` pode pedir vídeo real/foto grande comprovada, sem se passar por instalação não filmada.
- **Ponte opt-in sem criar banco novo**: `src/v4/formatos/ponte_biblioteca.py` usa `src/v3/biblioteca.Biblioteca` + os registros já comprovados do V4. Só habilita com `CORINGA_ATLAS_APROVACOES_V3` apontando a um manifesto **com revisão humana, acontecimento, SHA, provas de licença, `licenca_exata`**, com `BIBLIOTECA_DB` e `BIBLIOTECA_ARMAZEM` contendo originais locais verificáveis. Sem manifesto, comportamento antigo inalterado. Não duplica SHA e recusa ausência/corrupção. `diretor.prompt(..., inventario=None)` pode construir inventário contextual da biblioteca aprovado filtrando coincidência de 2+ termos via `viabilidade.SCORE_MIN`. Não é verificador factual, revisão de imagem continua essencial.
- Falha do teste de licença V3 (CC BY 4.0 resumido a CC BY) corrigida preservando **licença exata** informada na aprovação; CC BY ≠ CC BY-SA.
- **CI FINAL `https://github.com/Heitor2404/coringa-news/actions/runs/44433077213` SUCCESS, 118 testes Python + JS/TypeScript verdes**, após problemas anteriores de fixture de teste e action externa de FFmpeg (substituída só no CI). Testes sem IA, sem render de episódio e usando vídeo sintético local para smoke real FFmpeg.
- Documentação: `docs/v4/formatos/INTEGRACAO_P1_ATLAS_20261119.md`. Não dizer que o motor já produz vídeo de qualidade neo/fern automaticamente: **não existe novo vídeo Guerra dos Chips aprovado, nem instalação TSMC/EUV com footage nova curada**. Actions GitHub são efêmeras: V3 DB/arquivos de mídia devem ser provisionados legalmente e de modo durável antes de ativar modo V3.

**PRÓXIMO PASSO:** curar 2–3 mídias reais específicas para um teste de 20–30 segundos (prova exata de assunto/fábrica/ação, licença/autor/URL/SHA) e criar prévia privada com voz Gemini/Charon. Validar som/corte/composição/atribuições no MP4 completo e revisão humana. Ainda existe restrição legada `F-GANCHO-MAPA-PRIMEIRO` em `src/v4/formatos/plano.py` que obriga mapa no início e proíbe clipes até 3 s — contradiz a possibilidade de um gancho físico tipo neo; quando o roteiro final do teste for escolhido, avaliar relaxá-la com testes **sem quebrar a referência cartográfica antiga**. Só depois considerar 16:9/YouTube longo. Não aceitar que cada vídeo exija código específico.


## 24. 19/11 — Falha de envio no Telegram de Chips V2: preflight e resolução

Usuário reportou "Não apareceu nada no Telegram ainda". Diagnóstico feito em GitHub Actions **44437665279** (01:32–01:34 UTC): job `failure` **antes do render MP4**. Narração Gemini/Charon **OK**, duração **30.773s**, `GEMINI_API_KEY` presente; duas fotos Commons + rasters com SHA e licença **OK**. `preflight` 32 verificações e **3 falhas exatas**: `F-TEMPO` payoff 26.47–31.29 (>30.773); `F-TEMPO` CTA 29.09–31.24; `F-SEM-PROGRESSAO` 5.7–8.8, 3.0s sem informação nova. Quadros e render pulados, `resultado.json` ausente. Etapa Telegram estava marcada `success` porque a condição `if [ -s "$SAIDA/resultado.json" ]` pulou o envio, apesar dos segredos Telegram presentes: **nenhuma tentativa de enviar**.

Correções **somente branch experimental ATLAS**:
- `src/v4/formatos/plano.py::resolver_tempos(..., duracao_audio=...)` novo parâmetro opcional: a âncora `@fim` passa a significar fim **real** do WAV quando disponível; `inserir_cta` usa duração real ANTES de gerar CTA. Sem `duracao_audio`, comportamento anterior conservado.
- `src/v4/formatos/produzir.py::preflight` agora fornece `duracao_audio=meta['duracao']`, para impedir última camada e CTA excederem áudio.
- `src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json`: a segunda linha da pergunta "TAIWAN?" é revelada na palavra `@importa`, criando evento informativo e removendo pausa de 3s. Tentativa intermediária de card `IMPACTO GLOBAL` foi **revertida** por violar `F-TEXTO-NAO-CABE` e `F-COBRE-TERRITORIO`, preservando mapa limpo.
- `.github/workflows/atlas-chips-v2-privado.yml` executa Telegram `if: always()` com segredos disponíveis **mesmo sem resultado.json/MP4**. `produzir.telegram` já suportava relatar preflight BLOQUEADO, apenas o workflow não chamava. Ausência de segredos passa a ser erro explícito. Não permitir publicação.
- `tests/test_atlas_previa_chips_v2.py`: novos testes fecham payoff/CTA no WAV real 30.773, verificam progressão sem card sobre mapa e capturam notificação Telegram de preflight sem MP4 com mock offline.
- **GitHub Actions 44447485283: success, 130 testes Python + TypeScript.** Erro intermediário de card rejeitado foi tratado, não se enganou o portão.
- Após testes verdes, disparada **NOVA** prévia privada via `.github/atlas/chips_v2_preview.txt`: **GitHub Actions 44447705090**, estado **in_progress** na última consulta. **Não declarar MP4 pronto, Telegram enviado ou vídeo aprovado até inspecionar esse run e seu resultado/Telegram.** Se BLOQUEADO, deve mandar mensagem com motivo mesmo sem MP4; verificar logs do passo e status efetivos.

Próximo passo: checar `https://github.com/Heitor2404/coringa-news/actions/runs/44447705090` para completar diagnóstico. Em caso de `quadros`/render/fiscal falho, não contornar bloqueios nem publicar. Se chegar Telegram e houver MP4, solicitar revisão visual humana da prévia antes de evoluir o motor. NTC, DOSSIÊ e main/produção intactos.


## 25. 19/11 — Chips V2 segundo bloqueio: abertura 0,6–3,8 s sem progressão

Após correção do `@fim` e do Telegram, run **44447705090** gerou com sucesso narração **Gemini/Charon de 27.922s**, identificou as mídias corretamente, mas foi bloqueado no preflight: `F-SEM-PROGRESSAO 0.6–3.8s (3.3s)`. O Telegram PRIVADO desta vez enviou corretamente uma **mensagem BLOQUEADO sem MP4**; portanto credenciais Telegram não eram o problema.

Tempos da narração registrados em `tests/dados/atlas_chips_v2_tts_real_run_44447705090.json`, com 61 palavras do log (originais antes do realinhamento). Valores documentados: FAB em 0.63, TAIWAN em 2.65 e POR em 3.91. Foto inicial só revelava primeiro rótulo em 0.63 e mapa só entrava aos ~3.79, causando pausa visual longa. Correção editorial: segunda revelação "FAB 18 · TAIWAN" em `rotulo2_t:"@taiwan"`, já suportado pelo componente de fotografia e sem precisar de novos cards ou mídia genérica; limite de ritmo de 3s **inalterado**.

Teste novo `test_gancho_com_tempo_real_gemini_nao_congela_tres_segundos` usa cronologia real da execução bloqueada, exige ambos rótulos nas palavras corretas e nenhum `F-SEM-PROGRESSAO`/`F-TEMPO`. CI `.github/workflows/atlas-validacao.yml` recebeu job **ritmo_real** independente de FFmpeg para avisar rápido, além de timeout explícito no instalador apt do job de regressão completa.

**CI completo 44448821495: success, 131 Python + TypeScript aprovado.**
**CI 44449070038: success, job `ritmo_real` verde e completo verde, 131 testes.**
A nova prévia privada foi acionada pela atualização de `.github/atlas/chips_v2_preview.txt`: **GitHub Actions 44449171248**, estava `in_progress` na última consulta na etapa de dependências. **NÃO afirmar envio, produção de MP4 ou sucesso sem conferir o resultado desse run**. Caso falhe no preflight, o Telegram deve avisar o bloqueio; se renderizar, checar quadro a quadro e fiscal antes de chamar aprovado. Nunca publicar redes automaticamente.

Os dois ciclos fracassados foram originados por diferenças reais de timing TTS; não relaxar `progressao_max_s` para esconder pausas e não duplicar fotos/cards. Continuidade: só alterar a branch experimental `atlas-direcao-visual-20261118`.


## 26. 19/11 — Correção de rótulos da prévia Chips V2 e Telegram

Usuário encaminhou notificação Telegram `STATUS: BLOQUEADO (não renderizado); preflight:` sem detalhes. O run **44449171248** foi consultado diretamente: áudio Gemini/Charon criado (**27.013s**), mídias/hash válidos, preflight OK; **19 quadros** renderizados para diagnóstico, **5 bloqueios `R-TEXTO-PEQUENO`** em rótulos do componente `atlas.provaVisual` (font 24px contra mínimo 26), e **57 avisos `A-CREDITO-RODAPE`**. Etapa MP4 foi pulada; Telegram privado enviou apenas texto e nenhum vídeo; **não houve publicação**.

Correções **somente em `atlas-direcao-visual-20261118`**:
- `motor4/remotion/src/formatos/Primitivas.tsx`: fonte de rótulo fotográfico **30px** em `atlas.provaVisual` reutilizável; não alterar limiar do fiscal, nem rótulos de DOSSIÊ.
- `src/v4/formatos/produzir.py::telegram`: se preflight estiver verde e não houver `resultado.json`, mostrar resumo dos quadros e erros reais do `quadros/relatorio.json` em vez de deixar `preflight:` vazio. Mantém aviso claro de erro preflight se houver.
- `tests/test_atlas_previa_chips_v2.py`: dois novos testes de regressão, um para mensagem de falha em quadros, outro para legibilidade da composição foto.
- GitHub Actions **44450404274 SUCCESS**, **133 testes Python + checagens TypeScript**. Run anterior **44449171248 FAILURE** preservado como evidência.
- Nova prévia privada disparada em **44450584008**; status `in_progress` na última conferência. **Não declarar MP4 entregue/aprovado antes de consultar esse run, logs e Telegram.** `A-CREDITO-RODAPE` permanece como aviso editorial conhecido; não subir os créditos cegamente, pois a posição baixa segue identidade visual aprovada e requer revisão da UI das plataformas.

Próxima ação: verificar conclusão da execução **44450584008**, inspecionar preflight, quadros, render/portões e Telegram. Se MP4 surgir, avaliar quadro a quadro antes de qualquer integração ou publicação. Main/produção/NTC/DOSSIÊ intactos.


## 27. 19/11 — Gancho real de Chips com piso temporal e câmera segura

O segundo run privado **44450584008** confirmou o Telegram diagnóstico corrigido: Gemini/Charon gerou **27,445s**, mídia verificada, porém `F-GANCHO-PROVA-REAL` bloqueou preflight. A palavra **POR** aconteceu em **2,418s**; o final da foto do primeiro beat `@por-0.12` ocorreu aos **2,298s**, abaixo do mínimo 2,5s. Sem MP4, Telegram enviou bloqueio corretamente; nenhuma publicação.

Mudanças **somente experimentais**:
- `src/v4/formatos/plano.py::resolver_tempos` recebeu expressão genérica `@max(piso_segundos,@palavra+offset)`, para impedir corte cedo quando voz TTS varia. Mantida regra de `F-GANCHO-PROVA-REAL` 2,5s.
- Plano `atlas_chips_v2_prova_25s.json` segura foto até pelo menos 2,5s e sincroniza transição do mapa com fim da foto; pergunta não antecede o mapa.
- Primeiro teste novo com os 61 tempos reais `tests/dados/atlas_chips_v2_tts_real_run_44450584008.json` apontou um SEGUNDO erro `F-COBRE-TERRITORIO`: a entrada do título ocorreu durante chegada de câmera. O motor ganhou `entrada_apos_voo` opcional para camadas cartográficas, que espera dinamicamente a câmera atingir posição segura, adiando também a primeira linha da revelação. O plano usa esse contrato sem alterar qualquer limite do fiscal.
- Dois testes Python e um smoke direto com cronologias reais da voz rápida **44450584008** e lenta **44447705090**. **GitHub Actions 44452013618 finalizou SUCCESS: 135 testes Python e TypeScript verdes**, incluindo os dois cenários de voz real (rápida/lenta), sem relaxar os fiscais.
- Run anterior **44451262176** não exercitou os testes: o Ubuntu 26.04 do runner `ubuntu-latest` expirou o `apt-get update` para FFmpeg (exit 124). CI `.github/workflows/atlas-validacao.yml` pinou `validar` em `ubuntu-22.04` (mesmo alvo do workflow privado), e `ritmo_real` agora testa diretamente as duas vozes antes de instalar dependências.
- Testes de regressão em `tests/test_atlas_previa_chips_v2.py` foram ampliados. A suíte completa está comprovada verde. A **prévia audiovisual não está aprovada** até render/inspeção do MP4.

Próximos passos: conferir status/log completo de **44452013618**; se verde, disparar **prévia privada sem publicação** via atualização de `.github/atlas/chips_v2_preview.txt`, verificar quadros, MP4, fiscal e mensagens Telegram. Não alterar `main`, `motor-integral-v4`, NTC ou DOSSIÊ; não baixar limiares de ritmo, imagem real nem segurança de território.


### Complemento verificado após interrupção — 19/11

- Execução GitHub Actions **44452013618** terminou **SUCCESS**: `ritmo_real` verde e `validar` verde; log do job `validar`: **135 testes Python passaram**, tipagem Remotion/TypeScript sem erro.
- A nova prévia privada, acionada após esses testes pela atualização de `.github/atlas/chips_v2_preview.txt`, é a execução **44452281285** (em andamento na última leitura). Link: https://github.com/Heitor2404/coringa-news/actions/runs/44452281285 .
- **Não há MP4 novo aprovado, enviado ou publicado confirmado nesta atualização.** Conferir logs das etapas preflight, quadros, render e Telegram antes de relatar progresso. Preservar diagnóstico mesmo se bloqueado; não alterar limites do fiscal.


### Reteste privado após CI verde (19/11, 03:33 UTC)

- Duas execuções do mesmo workflow `atlas-chips-v2-privado.yml` apareceram em poucos segundos: `44452281285` (SHA `2b36e5c`) e `44452293201` (SHA `da4773d`). A primeira foi disparada por commit do repositório antes do commit deste atendimento; a segunda foi acionada neste atendimento após a CI verde. **Não disparar terceira execução**, evitar custos/filas.
- A primeira estava `in_progress` e a segunda `pending` na última consulta; **não afirmar MP4, aprovação humana ou envio Telegram** sem consultar os resultados e os logs correspondentes.


## 28. 19/11 — REPROVAÇÃO EDITORIAL P0 DO PILOTO CHIPS: PARAR RENDERS E REVER DIREÇÃO

Usuário recebeu MP4 privado de 32,1 s `Por que Taiwan importa tanto na indústria dos chips?`: 30/30 preflight, 21 quadros sem bloqueadores, áudio −14,4 LUFS, legenda alinhada, zero janela preta, portões técnicos verdes, estado `AGUARDANDO_APROVACAO_HUMANA`. **Rejeição humana explícita e integral:** edição e estética consideradas péssimas; mapas distantes, imagens estranhas, excesso de mapas e nenhuma demonstração. O usuário apontou que entregou **dois vídeos originais de referência** e gastou horas em correções sem obter algo próximo da referência. Assistente reconheceu erro de prioridade/gestão: otimizou testes em vez de direção e qualidade.

Inspecionados MP4 anexado (32,133 s, 512×910, 30fps), os três contatos visuais de 0–31s e código. 0–2,5 fachada pequena sobre mapa; 2,5–7 mapa de Taiwan com texto; 7–15 foto wafer muito escura/letterbox sobre mapa; 15–27 mapa-múndi global com etiquetas EUA/Holanda/Taiwan e Antártida dominante; 27–32 fecho abstrato no mapa. **Mapa onipresente ≠ mapa informativo**. Na engenharia reversa `docs/v4/formatos/ENGENHARIA_REVERSA_REFERENCIAS.md` as referências A/B quase não tinham cortes, porém acumulavam provas visuais concretas a cada 1–2 s. `MATRIZ_FIDELIDADE_ATLAS.md` já alertava mapamúndi 9:16 mostrando Antártida, e `ESTUDO_REFERENCIAS_E_DIRECAO_ATLAS_V2_20261118.md` já dizia que faltavam ASML/EUV/mecanismo e não se deve substituir máquinas por mapa/card. **O diagnóstico já existia mas não virou bloqueio.**

Auditoria P0 formal salva em `docs/v4/formatos/INCIDENTE_QUALIDADE_CHIPS_20261119.md` (commit `1ae1bce3a8b142b796ec9fbb24baba25d97eb39c`).

**Decisão: este vídeo REPROVADO. Não publicar, não continuar microcorreções, não disparar outro render.** Novo fluxo: inventário de provas com imagens de qualidade e licenças antes do roteiro final; storyboard visual (objeto/ação/relação/consequência); capa e cenas comparadas à função das referências; avaliação humana do animatic barato; só então voz final e vídeo completo; motor precisa de portão `F-PROVA-NARRATIVA-INSUFICIENTE` e regras reutilizáveis, não caso Taiwan. Evitar confundir `AGUARDANDO_APROVACAO_HUMANA` com estética aprovada.

No momento da auditoria, Actions `44452281285` estava concluído com success, `44452293201` constava in_progress e é duplicado; **não abrir outro**. Não foi possível cancelar a execução através dos conectores GitHub disponíveis nesta sessão. Main/produção/NTC/DOSSIÊ intactos.


## 29. 19/11 — Recuperação editorial P0 com portões antes de TTS e MP4

Usuário pediu solução real para falta de resultado após duas semanas, aprendizado/autoevolução e acompanhamento visual automático. Verificações reais em `atlas-direcao-visual-20261118`:
- `docs/memoria/erros.json` tinha 84 erros de engenharia; `docs/memoria/feedback.jsonl` 8 feedbacks antigos ainda abertos do Panamá; `docs/memoria/regras_editoriais.json` **ZERO regras**. `src/v3/memoria.py` é recuperação/versionamento, NÃO treinamento de rede neural. `src/v3/pipeline.py` usava memória e revisão `src/v3/revisao_multimodal.py`, MAS `atlas-chips-v2-privado.yml` não executava essas etapas. `src/v3/receitas.json`: 14 receitas (11 testadas, 3 propostas, ZERO aprovadas). Motor ATLAS aprendia testes de geometria, não estética.
- Render de Chips de 32,1 s reprovado humanamente: mapa para substituir fábrica/máquina/design/relação causal; imagem escura de wafer; mapa-múndi exageradamente afastado porque `camera_roi` calcula enquadramento de ROIs globais [114,12,242,52] e [0,16,126,56]; título final em mapa, 2 fotos apenas. Workflow exigia exatamente 2 fotos, 6 beats e zero clipes.
- **Mudanças implementadas exclusivamente nesta branch experimental**: criado `src/v4/formatos/triagem_editorial.py` para exigir prova por beat (direção visual e ativos reais) **antes de voz**, com erro `E-SEM-CONTRATO-VISUAL` para storyboard antigo; elimina limite arbitrário de 2 fotos/6 beats do workflow. Novo `src/v4/formatos/revisao_visual.py`: Gemini Vision recebe duas amostras renderizadas por beat antes do MP4, detecta referencial ausente, enquadramento ruim, imagem ilegível, mapa decorativo e falta de aprendizado; revisão ausente ou falha bloqueia, **não corrige automaticamente ainda**. `produzir.render` exige revisão aprovada para ATLAS, sem exigir em DOSSIÊ. `telegram` envia motivos de triagem pré-voz e revisão de quadros.
- Memória: `feedback.jsonl` ganhou **FB-0009…FB-0013** com reprovação humana e constatações de auditoria, atribuições separadas; `regras_editoriais.json` ganhou **REG-001…REG-003** em estado `proposto` (nenhuma aprovada automaticamente). O `src/v4/formatos/diretor.py::prompt` passou a consultar **reprovações humanas como contraexemplos** e regras somente se formalmente `aprovado`; V3 e ATLAS agora compartilham esse repositório de memória.
- `.github/workflows/atlas-chips-v2-privado.yml` passa por triagem editorial antes do TTS e crítico visual independente depois dos quadros antes do MP4. Inspeção do vídeo final/movimento e autocorreção dirigida limitada ainda são etapas **pendentes**; não confundir veto de visão sobre quadros com homologação estética.
- CI `44456958676`: **144 testes Python e TypeScript verdes** no primeiro conjunto de novos gates. Alterações adicionais de integração com a memória/Telegram submetidas à validação separada via `.github/atlas/validacao.txt` (último SHA `3d9fefcb1746eff32feca8bccdc07105403f337b`); consultar resultado antes de declarar validação completa.
- Plano P0 e decisões disponíveis em `docs/v4/formatos/PLANO_REESTRUTURACAO_P0_20261119.md`. No segundo estágio: acervo de provas com curadoria e licenças ANTES do roteiro, storyboard visual/animatic barato ANTES do TTS, crítico de cenas + movimento (adaptador V3), UMA autocorreção controlada com revalidação, comparação com referências A/B e aprovação humana para promover regras. **Não iniciar outro render full só para testar estética, não publicar vídeo atual.** Nunca tocar `main`, V4 produtivo, DOSSIÊ nem NTC.
