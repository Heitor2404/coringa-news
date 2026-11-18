# Biblioteca ATLAS — plano operacional e prévias
**18/11/2026 · Sprint 0 / planejamento executável · Branch `atlas-biblioteca-20261118`.**

## Decisão

**SIM, vale construir uma biblioteca ANTES de escalar episódios, mas somente um núcleo pequeno de recursos repetíveis.** Não é eficaz congelar roteiros, dados atuais, posições arbitrárias de elementos ou produzir milhares de imagens antecipadamente. O propósito é preservar a identidade do ATLAS e evitar refazer pesquisa de licença, estilo, geometria e rendering a cada vídeo, **não** eliminar apuração ou roteiro.

A biblioteca é um **índice de referências versionadas**, não a cópia dos arquivos existentes nem um novo editor. O motor aprovado permanece isolado. Uma categoria só vira recurso de produção depois de comprovar origem, licença, aderência à fala, integração e teste visual.

## Diagnóstico auditado

- `src/v4/formatos/formatos.json`: **6 composições** atlas (abertura, protagonista, painel, escada, técnica, manchete), diversas primitivas aprovadas no catálogo; o formato ATLAS usa mapas e não obriga animação técnica.
- `motor4/formatos/dados/raster/`: rasters nomeados com arquivos e metadados de licença/procedência. A seleção inicial indexa **5 bases que já existem**: `ne2_mundo`, `ne2_pacifico`, `ne2_asia_leste`, `bmng_asia_continente` e `ne2_istmo_panama`. Não há geração nova de mapas nesta fase.
- `src/v4/biblioteca_comprovada.json`: **7 itens** com licença, crédito e prova registrados; **6 estão ligados ao Panamá** e **1 a Pequim**. Isso não é acervo pronto para TSMC, ASML e semicondutores; o campo `confirmacao_humana` pode continuar nulo.
- `src/v4/formatos/planos/reuso/atlas_chips.json`: existe um **plano de teste com tempos de voz SINTÉTICOS**, não vídeo validado para publicação. Serve como *fixture* visual/reuso, não como fatos automaticamente aprovados.
- `src/v4/formatos/canais/coringa.json` e `docs/v4/formatos/GUIA_VISUAL_ATLAS_V1.md`: identidade editorial já está definida. **Não modificar os tokens nem a paleta para enfeitar a biblioteca.**

## As cinco coleções

### 1. Cartografia

**Reutilizar:** bases de mapa com procedência, resolução, licenças e regiões; camadas geográficas consistentes; zoom/ROI calculado pelo conteúdo; marcadores/rotas/distâncias validados.

**Não congelar:** fronteiras históricas, disputas territoriais e situação geopolítica atual. Isso precisa de data, fonte e nível de incerteza. O raster é estável, mas o *overlay* de informações pode mudar por episódio.

**Preview:** `01_cartografia.png` — frames reais do vídeo ATLAS atual; `04_pacote_chips.png` — mockup geográfico ilustrativo de um tema novo.

### 2. Componentes e motion graphics

**Reutilizar:** composições e slots do catálogo atual; pins, rota, destaque territorial, reveal de número, hierarquia, cards e, quando cabível, clipe técnico.

**Nunca deixar a IA inventar:** cor, posição, tipo de transição, tamanho ou efeito. O diretor seleciona componentes, o motor renderiza. Novos comportamentos exigem exemplos em dois assuntos, testes e aprovação.

**Preview:** `02_componentes.png` — quadros reais de cards, dados, mecanismos e mapa do piloto.

### 3. Mídia com procedência

**Reutilizar:** IDs de mídia, hash, descrição exata, origem, licença, restrição de uso, autor/crédito e indicação de correspondência. Preferir um único índice, sem duplicar os arquivos. Status editorial e status jurídico são verificações distintas.

**Não reutilizar indiscriminadamente:** foto real de um local ou pessoa não serve para ilustrar outra fábrica, evento ou país. Sem fonte/licença, não entra na produção. Busca de mídia por episódio continua quando o tema não está coberto.

**Preview:** `03_acervo.png` — exemplo do padrão de registro de acervo, com imagem real do piloto e proveniência do catálogo.

### 4. Pacotes temáticos

Agrupar **referências reutilizáveis**, não roteiros prontos nem narrativas imutáveis. Um pacote aponta para mapas, registros de mídia, componentes adequados, fontes estruturais e campos que exigem atualização.

**Pacotes iniciais:** guerra dos chips (há fixture de teste, ainda não validado), Estreito de Ormuz (candidato), fronteiras históricas (candidato), infraestrutura global (candidato). Os três últimos não estão aptos a produzir um vídeo: nem dados, mídia ou geometria foram curados.

**Preview:** `04_pacote_chips.png` — ilustração da combinação de mapas, elos e cards, NÃO um render do ATLAS nem prova de fatos atuais.

### 5. Fluxo de curadoria

`descobrir → verificar origem/licença → verificar correspondência → registrar SHA/crédito → curar/padronizar → testar render → liberar → revisar`. Descartar duplicatas por SHA/perceptual hash quando fizer sentido. Itens com licença incerta ou que mostrem algo diferente do roteiro permanecem bloqueados.

**Preview:** `05_curadoria.png` — visão de um portão operacional que não consome IA paga.

## Estrutura mínima inicial

```text
src/v4/formatos/biblioteca_atlas/
  catalogo.json               # índice de fontes e capacidades existentes (status explícito)
docs/v4/formatos/
  BIBLIOTECA_ATLAS_OPERACIONAL.md
tests/
  test_biblioteca_atlas.py     # teste offline; nenhuma mídia nova, sem render
.github/workflows/
  atlas-biblioteca.yml         # validação restrita à branch
```

**Fonte de verdade:** para cada foto, `src/v4/biblioteca_comprovada.json`; para mapas, os pares `raster/<nome>.jpg|webp` + `raster/<nome>.json`; para estilos e composições, os catálogos existentes. A nova biblioteca só referencia nomes e IDs.

## Regras de qualidade (portões)

1. **Reutilização sem alteração de estilo:** o nome do asset, composição e perfil devem ser reais e permitidos; o motor de produção não importa a biblioteca experimental.
2. **Licenças e créditos:** sem título, autor quando exigido, licença, atribuição, origem e correspondência verificável, BLOQUEAR.
3. **Atualização factual:** números, regras de exportação, líderes, fronteiras disputadas, guerras e movimentos econômicos devem ser verificados por episódio. Um pacote temático nunca substitui pesquisa.
4. **Mapa coerente:** toda ligação precisa expressar a relação exata na fala; não desenhar uma “rota comercial” que parece trajeto físico quando é somente dependência industrial.
5. **Edição limpa:** continuar usando regras atuais de legenda, sobreposição, contraste, safe areas, áudio, ritmo e motion graphics.
6. **Economia:** manter um orçamento por rodada incluindo chamadas repetidas; preferência por recursos públicos/licenciados e cache. NÃO supor percentual de reutilização antes de medir.
7. **Isolamento:** este sprint não muda motores ATLAS, DOSSIÊ ou NTC; o piloto chips segue na branch isolada `atlas-piloto-chips-20261118`.

## Ordem executável

**Sprint 0 (feito neste documento):** inventário sem duplicação, política, catálogo, teste offline e prévias de cinco categorias.

**Sprint 1:** comprovar visual e licenças dos 5 rasters e 7 mídias; inspecionar os exemplos no celular; eliminar ativos insuficientes/duplicados. Criar busca por metadados com pontuação por `mostra`, país, período, função narrativa e licença.

**Sprint 2:** focar no segundo piloto, guerra dos chips: curar apenas imagens pertinentes (Taiwan/TSMC, Holanda/ASML, EUA/China) e revisar fontes atuais. Se o pacote não cobrir uma fala, buscar um asset novo e acrescentar depois da curadoria, sem inventar foto.

**Sprint 3:** testar vídeo completo com o **mesmo motor de produção já aprovado**. Medir tempo de curadoria, reutilização de asset, taxa de bloqueio, qualidade humana e custo. Sem inventar motion graphics específicos dos chips para mascarar deficiência genérica.

**Sprint 4:** expandir as regiões/temas apenas onde os próximos vídeos comprovarem necessidade e retorno, sem meta arbitrária de milhares de assets.

## Critérios para aceitar a biblioteca

- Uma seleção prévia é capaz de preencher o que **existe**, e explicar por que uma cena **não** pode usar determinado item.
- Nenhum import da biblioteca experimental dentro do motor de produção.
- Fontes de imagem e mapas com atribuição e licença.
- Reutilização preserva estética do piloto e funciona em pelo menos dois temas após validação humana.
- Auditoria em CI usa exclusivamente JSON/Python; nenhuma IA, sem TTS, sem publicar e sem renderizar por padrão.

## Resumo executivo

**Uma biblioteca operacional de capacidades e provas. Não um banco de vídeos sem contexto.** Não parar a produção do segundo piloto até “completar” a biblioteca: manter desenvolvimento e curadoria desacoplados, integrando somente recursos efetivamente aprovados. O catálogo é expansível, mas o motor ATLAS continua limitado à gramática visual homologada.

## Sprint 1 — primeira curadoria fotográfica da guerra dos chips (18/11)

A branch experimental contém `src/v4/formatos/biblioteca_atlas/midias_candidatas_chips.json` com **5 candidatas verificadas na página da Wikimedia Commons**. A seleção cobre:
- **Taiwan:** TSMC Fab 18, exterior em Tainan, 2025, 4300streetcar, CC BY 4.0.
- **Holanda:** sede corporativa ASML em Veldhoven, foto de 2008, A ansems, domínio público; NÃO representa uma máquina EUV.
- **China:** exterior da SMIC em Shenzhen, 2022, Lhzss8, CC BY-SA 4.0; obrigações de atribuição/compartilhamento precisam revisão para edição final.
- **Tecnologia:** wafer de silício em close, Le hollandais volant, CC BY 4.0; não identifica chip, fabricante ou nó de produção.
- **Processo genérico:** sala limpa de microfabricação da NASA Glenn, domínio público; NÃO é interior da TSMC/ASML/SMIC.

**Exclusão explícita:** foto histórica `Extreme ultraviolet lithography tool.jpg` do Lawrence Livermore (1998) não é imagem de scanner moderno da ASML; não atribuí-la a equipamento contemporâneo.

**Diferença de status:** as páginas/licenças foram checadas, mas as cinco mídias **ainda NÃO foram aprovadas editorialmente** nem copiadas para `src/v4/biblioteca_comprovada.json`. Falta baixar/inspecionar o arquivo aprovado, checar enquadramento vertical, autoria/alterações, SHA256 binário, atribuição completa e adequação à frase exata. A biblioteca não pode renderizá-las enquanto estiverem como candidatas. A presença de arquivo com licença não garante uso honesto.

Ferramentas introduzidas (isoladas do pipeline):
- `scripts/atlas_biblioteca.py`: `resumo` e `buscar <termo>` com resultados `CANDIDATO_BLOQUEADO`; falha fechada para liberação.
- `scripts/atlas_acervo_chips_preview.py`: consulta API Wikimedia Commons, baixa miniaturas com origens permitidas, calcula SHA256 da **miniatura** e registra SHA1 do original informado pela fonte; gera galeria, créditos e auditoria JSON. A miniatura NÃO vira automaticamente mídia comprovada, e seu SHA não é SHA do original.
- `.github/workflows/atlas-acervo-chips-preview.yml`: CI visual, upload de **artefato temporário (7 dias)**, sem IA, vídeo, TTS ou publicação.
- `tests/test_biblioteca_atlas.py`: sete testes offline com bloqueio de candidata sem SHA, correspondência e revisão editorial.

**Decisão editorial:** se não obtivermos foto livre de equipamento EUV moderno, **não substituir por foto histórica nem pela sede ASML fingindo ser máquina**. Podemos usar mapa, card e texto validado para explicar ASML; a fotografia do equipamento continua como pendência.

**Uso nos vídeos:** biblioteca continua em branch própria, aguardando integração homologada, e não altera o segundo piloto nem o ATLAS aprovado.
