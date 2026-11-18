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
