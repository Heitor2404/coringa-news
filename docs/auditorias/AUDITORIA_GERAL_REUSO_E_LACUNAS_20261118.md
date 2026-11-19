# Auditoria geral de reaproveitamento — Coringa / ATLAS / DOSSIÊ / NTC
**18/11/2026 | Diagnóstico arquitetural de código + GitHub workflows, somente leitura.**
**Escopo:** `main` (padrão do repo), `motor-integral-v4`, `atlas-direcao-visual-20261118`, `atlas-piloto-chips-20261118` e `atlas-biblioteca-20261118`.
**Objetivo:** antes do ATLAS V2, descobrir capacidades já existentes, sua ligação ao fluxo real, testes, duplicações e lacunas. **Não há homologação artística, execução nova da suíte, merge, mudança produtiva ou publicação.** Não é auditoria exaustiva de cada linha do repositório: foram examinados os pontos centrais de execução, contratos, render, acervo, testes e documentos técnicos.

## 1. O achado fundamental
**O motor JÁ tem um cérebro editorial por acontecimentos em V2/V3 e ferramentas concretas de V4. O piloto ATLAS ainda é uma integração parcial dessas capacidades.** A proposta anterior de criar «ficha de cena», «biblioteca global», «revisão semântica», «vídeo real» e «memória de direção» DO ZERO iria duplicar funcionalidades existentes. O trabalho é criar **adaptadores comprovados, contratos compatíveis e portões de homologação**, não novo sistema paralelo.

### Branches e roteamento NÃO são sinônimos de runtime único
| Linha | Código / uso comprovado pela leitura | Situação e cuidado |
|---|---|---|
| `main` | **branch padrão do GitHub**; `.github/workflows/gerar-videos.yml` com schedule / repository_dispatch / manual; `main.py` é entrada | O agendamento depende da variável `AGENDA_ATIVA=1`; a configuração efetiva dos segredos/vars não foi lida. **Não afirmar que está automaticamente ativo**. `main.py` tem seleção explícita de V2/V3 por `MOTOR_VISUAL`; sem ela, há fluxo legado. |
| `motor-integral-v4` | Base de código ampla com legado, V2, V3, V4 e formatos; `.github/workflows/v4-episodio.yml` para teste privado `workflow_dispatch` | **Não** se deve concluir que V4 é o motor atualmente publicado só pelo nome da branch. Testes do V4 integral são isolados do pipeline programado de `main`. |
| `atlas-direcao-visual-20261118` | rama experimental com direção ATLAS, correções, contratos, documentos e validação | Não mergeado em `main`; estudos neo/fern e diretrizes documentadas. |
| `atlas-piloto-chips-20261118` | storyboard fixo, testes de 34 quadros, TTS e MP4 privado | Workflow 44405950985: infraestrutura `success`, **fiscal editorial `BLOQUEADO`**, voz Edge não aprovada. É regressão visual, não prova de direção automatizada generalizada. |
| `atlas-biblioteca-20261118` | catálogo/curadoria ATLAS, 6 fotos candidatas, hashes/licenças, sete testes descritos e workflow privado | **Outra branch que divergiu** da de direção e chips. Sua ferramenta `scripts/atlas_biblioteca.py` é índice offline; **não alimenta** o render produtivo. |
| NTC `canais/ntc/vetor/` + `src/fabula.py` | motor vetorial SVG próprio, personagens, cenários, objetos e testes | Independente editorialmente de documentário. Não portar UI/cards/voz/câmera sem justificativa e regressão isolada. |

**Evidência de divergência:** comparação GitHub de `atlas-direcao-visual-20261118...atlas-piloto-chips-20261118` → ramas divergentes (48 commits à frente no piloto, 18 atrás relativos ao diretor). `atlas-direcao-visual-20261118...atlas-biblioteca-20261118` → igualmente divergentes (23/18). **Não fazer merge/cherry-pick em massa.**

## 2. Inventário de capacidades e decisão sobre reutilização
Legenda: **CÓDIGO** = implementado no repositório; **TESTE** = tem teste/documentação/CI associado; **ATLAS** = uso efetivo pelo pipeline específico de formatos; **PENDENTE** = adaptação necessária. Um teste isolado não é aprovação visual humana.

| Domínio | Onde está HOJE | Evidência e status | Recomendação |
|---|---|---|---|
| Contrato factual de acontecimentos, sujeito/ação/estados | `src/v2/contrato.py` | **CÓDIGO**: declaração, classificação, observabilidade, composições viáveis e exigência de mecanismo | Reaproveitar contrato, não criar outro «evento» sem adapter |
| Ficha audiovisual por acontecimento | `src/v3/plano_av.py::fichas` | **CÓDIGO**: sujeito, estado inicial, ação, transformação, evidência, modalidade, critério e recursos | **PRIORIDADE 1:** adaptar saída para beats ATLAS; estender apenas o que falta (inferência, finalidade narrativa) |
| Escolha de forma ANTES da câmera | `src/v3/linguagem.py`, `src/v3/decisao.py` | **CÓDIGO/TESTE**: registro/mapa/esquema/documento/comparação/tipografia, evita zoom como «demonstração»; `tests/test_v3_linguagem.py`, `test_v3_decisao_visual.py` | Não recriar «diretor semântico» separado |
| Diretor automático com revisão | `src/v3/pipeline.py`, `src/v4/diretor.py` e `src/v4/formatos/diretor.py` | **TRÊS CAMADAS** diferentes, **não** 3 motores igualmente usados. V3 monta storyboard; V4 escolhe componente; ATLAS formatos preenche primitivas/slots. Piloto Chips usou plano fixo; não demonstrou generalização do diretor | Definir qual motor orquestra decisões e integrar via schema em vez de copiar prompts |
| Receitas e feedback editorial versionado | `src/v3/receitas.py` + `receitas.json`; `src/v3/memoria.py` | **CÓDIGO** com estados proposto/testado/aprovado, feedback por timestamp e regra aprovada com prova | Reusar para aprender com reprovação da Guerra dos Chips, sem promoção automática de regras |
| Revisão semântica fala → sequência de quadros | `src/v3/revisao_multimodal.py` | **CÓDIGO**: 4 frames/trecho + fala + critério de acontecimento, feedback «não demonstra» e «mapa decorativo»; via Gemini. Falha = NÃO REVISADO | Alimentar o ATLAS como revisão diagnóstica, nunca substituir julgamento humano |
| Fiscal técnico/editorial | `src/v3/fiscal_editorial.py`; `src/v4/portoes.py`; `src/v4/formatos/ritmo.py`; `scripts/formatos_validar.py` | **CÓDIGO + teste parcial**, mas interfaces/estados são diferentes. ATLAS Chips teve `BLOQUEADO` interno e GitHub job verde | Adapter de **estado editorial unificado** e aviso inequívoco no Telegram; não criar quarto fiscal |
| Aprovação humana/publicação | `src/v3/estado_final.py` | **CÓDIGO**: BLOQUEADO → AGUARDANDO → APROVADO_HUMANO → PUBLICAVEL, ações separadas | **Reaproveitar invariantes**; render concluído NUNCA significa aprovado |
| Acervo aberto multifornte | `src/acervo.py` + `src/midia.py` | **CÓDIGO**: Commons, Wikipedia, NASA, LoC, Europeana (chave), Openverse, iNaturalist, GBIF, Smithsonian, Met, Art Institute, Cleveland, Wikidata, Pixabay (chave), Internet Archive e vídeos Commons/NASA/Archive | Não criar nova busca redundante; medir taxa de sucesso/adequação por fonte e por acontecimento |
| Biblioteca global com SHA, pHash e licença | `src/v3/biblioteca.py` | **CÓDIGO/TESTE**: `Biblioteca.ingerir`, deduplicação, regiões, origem, reuso, SQLite, manifesto; `tests/test_v3_biblioteca.py` | **Não criar outro banco**; índices ATLAS devem referenciar IDs e usar curadoria sobre mídia global |
| Biblioteca de mídia «comprovada» do V4/ATLAS | `src/v4/biblioteca_comprovada.json` + `src/v4/viabilidade.py` | **EM USO no ATLAS específico**: somente assets com licença/crédito/prova, SHA opcional, preflight. Snapshot branch chips: **9 itens**; no snapshot da biblioteca independente eram 7 | Mapear para registro V3 sem relaxar gates; evitar duas verdades de licença/prova |
| Biblioteca ATLAS candidata isolada | `atlas-biblioteca-20261118`: `src/v4/formatos/biblioteca_atlas/catalogo.json`, `scripts/atlas_biblioteca.py` | **TESTE/CI** bibliotecário; 6 itens candidatos, não integrados ao render | Aproveitar curadoria como índice, NÃO fundir banco/asset sem validação |
| Vídeo documental REAL | `src/midia.py`, `src/acervo.py::f_videos`, `src/v4/episodio.py::render_cena`, `src/v4/componentes.py` (registro.video) | **CÓDIGO** para pesquisar/recortar/normalizar MP4 no legado/V4 integral | **ATLAS formatos AINDA NÃO**: `src/v4/formatos/produzir.py::ativos` trata bytes via `PIL.Image.open` e produz JPG; criar adapter de MP4 verificado + componente de prova dominante, não novo downloader |
| Mapa e geografia | `src/v4/geo.py`, `motor4/remotion/src/MapaRota.tsx`, `motor4/remotion/src/formatos/Palco.tsx`, `atlas_ref.py` | **CÓDIGO + ensaios**: OSM/Natural Earth/MapLibre, mapas com raster/proveniência e câmera; sem prova de qualidade para todos os temas | Não refazer biblioteca de mapas. Neo usa mapas zenitais: priorizar função semântica e troca de escala, não inclinação 3D obrigatória |
| Mecanismos/2.5D/3D | `src/render/v2/comp/mecanismos.js`, `src/v4/componentes.py`, `src/v4/backends/*`, `motor4/remotion/src/Camara3D.tsx`, rembg/Pixi/HyperFrames/Manim/Revideo | **CÓDIGO em diferentes graus.** A capacidade eclusa foi efetivamente usada; Revideo registrou falha CI; HyperFrames tem centenas de itens, poucos homologados. ATLAS formatos só autoriza `mecanismo.eclusa` no catálogo do piloto | Reusar backend aprovado quando fizer sentido; um componente no catálogo não prova funcionamento em Actions nem qualidade visual |
| Identidade e layout | `src/v4/formatos/canais/coringa.json`, `formatos.json`, `plataformas.json`, `layout.py`, `motor4/remotion/src/formatos/Primitivas.tsx` | **EM USO** e testado em frames. O próprio formato compartilha `dossie.documentCard`; chips ficou com «cara de card» | Preservar tokens, criar uso editorial específico por modalidade, não duplicar paleta/tema a cada vídeo |
| Narração e sincronização | `src/voz.py`, `src/v4/formatos/legenda_sync.py`, `src/v4/som.py`, `src/v4/formatos/produzir.py::narrar` | **CÓDIGO** com fornecedores/fallback. O workflow Chips usou Edge TTS provisório, rejeitado pelo usuário | Descobrir e **fixar por versão o preset aprovado** (não inferir que voz Edge ou Gemini é aprovada); sem fallback não autorizado |
| Prévia, avaliação e remessas | `src/v3/microcena.py`, `src/v3/previa_telegram.py`, `src/v4/metricas.py`, `scripts/atlas_previa_curta.py`, workflows privados | **CÓDIGO**, testes de microcenas 5–8 s com resultados mistos; prévia Telegram existente | Reusar harness e feedback de cena; vídeos longos exigirão capítulo horizontal próprio |
| NTC 2D | `canais/ntc/vetor/*`, `src/fabula.py`, `tests/test_ntc_*.py` | **MOTOR SEPARADO**: SVG, kits, cenas, regiões do céu, personagem e som; não usa o motor documental | Preservar isolamento e testar regressão antes de qualquer compartilhamento de serviços |

## 3. Evidência: código, teste e produção são três colunas diferentes
1. Na base `motor-integral-v4` foram identificados **79 arquivos de testes Python** no diretório `tests/` (não afirmar 79 testes individuais, nem que a suíte passou agora): 18 nomes V2, 13 V3, 5 V4/formatos, 6 ligados a NTC/fábula e 37 demais.
2. `docs/v3/CORRECAO_ESTRUTURAL_DIRECAO.md` relata **19 regressões falhando antes da correção** e ensaios V3 em microcenas: História com revisão, Geografia bloqueada, Biologia e Ciência com esquemas visualmente pequenos; documentação também avisa que parte de correções não foi reexecutada. **Não chamar V3 universalmente aprovado.**
3. `docs/v4/CAPACIDADES.md` distingue instalado, integrado, CI e qualidade humana; muitos itens continuam `not_tested`, Revideo falhou CI de episódio anterior, e catálogo HyperFrames ~457 entradas não significa 457 composições prontas.
4. No piloto ATLAS Chips, houve suíte/quadros verdes e render MP4, **mas o fiscal o marcou BLOQUEADO**. A qualidade editorial continua insatisfatória segundo revisão humana do próprio usuário.
5. Não executei nova suíte, render, revisão de licenças online, teste das variáveis de Actions ou auditoria dos binários; estas conclusões indicam **estado de integração**, não certificação operacional completa.

## 4. Cinco causas de retrabalho que devem ser eliminadas
**A. Quatro fluxos de direção com contratos parcialmente diferentes.** V2 estrutura acontecimentos; V3 determina o que mostrar; V4 integral seleciona recursos; ATLAS preenche slots. Falta uma interface canônica entre eles. **Solução:** adapter/evento editorial versionado, com tests; escolher orquestrador ao invés de expandir os 3 diretores paralelamente.

**B. Duas verdades de mídia.** Biblioteca global V3 e biblioteca comprovada V4/ATLAS; catálogo ATLAS separado só com candidatos. **Solução:** resolução de identidade por SHA, licença, prova, aprovações e URL, sem copiar arquivos e sem desativar portões de procedência; mídia com licença não prova correspondência factual.

**C. Motor visual rico sem caminho até o ATLAS.** V4 integral despacha vídeo real e outros backends, mas ATLAS formatos consome JPG e catálogo estreito (eclusa). **Solução:** extensão pequena do renderizador e documentação de capacidade efetivamente homologada; não reconstruir FFmpeg/Remotion.

**D. Teste verde confundido com qualidade.** Fiscal e workflow têm semântica própria; QA pode resultar em BLOQUEADO com job success. **Solução:** separar tecnicamente conclusão de job, qualidade de render, estado editorial e autorização humana de publicar.

**E. Pesquisa de referências gerando «novas» propostas já implementadas.** V3 já trabalha com ficha, forma antes da câmera, memória, microcena, revisão multimodal e bloqueio de substituição inadequada. **Solução:** primeiro mapear o que falta em interfaces, depois só criar recursos realmente não existentes.

## 5. Lacunas REAIS para o objetivo curto + YouTube longo
| Lacuna | Prioridade | Como fechar sem duplicar |
|---|---|---|
| Adapter V2/V3 `ficha por acontecimento` → beat ATLAS e `prova` estruturada | P0 | Contrato pequeno de integração; testes de «ação física ≠ card/rota» e de mídia indisponível, sem refazer o V3 |
| Estado editorial unificado com Telegram/Actions e gate humano | P0 | Reusar `src/v3/estado_final.py`, mapear estados do fiscal do ATLAS e tornar `BLOQUEADO` inequívoco |
| Preset de voz e ausência de fallback silencioso | P0 | Identificar voz anteriormente aprovada a partir de evidência real, registrar ID/parâmetros e bloquear troca |
| Prova real grande e vídeo MP4 licenciado no ATLAS | P1 | Adapter do catálogo de mídia + FFmpeg/V4 `registro.video`; validar subclips, duração, créditos, sincronização, área segura |
| Gestão editorial dos cards e mapas por pertinência | P1 | Herder regras V3 de linguagem (ação, registro, mapa, documento); ATLAS só implementa o acabamento visual |
| Sequências de investigação e payoff longform | P2 | Reusar fichas V3 + memória/receitas, **estender** estado de capítulo e referidos causais, sem criar «quarto diretor» |
| Layout horizontal 1920×1080 para YouTube | P2 | Preset separado: textos/legendas/créditos/câmera/zonas seguros; não esticar 9:16 |
| Creditação legível em 3 plataformas | P0/P1 | Validar licenças e overlays de tela; aviso existente `A-CREDITO-RODAPE` não é homologação legal/editorial |
| Caminho Pexels sem API | Opcional | **Download manual sob licença**, registrar URL/licença/autor/arquivo no acervo V3; não scraping nem servidor paralelo |
| Homologação cruzada e regressão NTC/DOSSIÊ | P2 | Golden samples + testes de módulos consumidos; não promover mudança sem revisão real em 2 temas |

## 6. Plano executável em sprints de baixa duplicação
### Sprint 0 — congelar diagnóstico (este documento)
- Inventariar branch/commit e estado das integrações; estabelecer V2/V3/V4/formatos com fonte de verdade por capacidade.
- **Sem código agora:** registrar matriz com lacunas exatas, dependências e restrições. Solicitar aprovação do caminho de integração antes de mexer no render.
- Comparar contrato V3 vs JSON ATLAS; criar especificação de adapter, não copiar 500 linhas.

### Sprint 1 — corrigir governança do ATLAS, sem mudar estética
- Guardar voz/preset aprovado: informar erro explícito quando indisponível.
- Gate: `BLOQUEADO` não vira prévia «aprovada», nem CI verde interpretado como aprovação; prévia diagnóstica continua disponível com rótulo.
- Especificar métrica de progressão semântica: uma demonstração que evolui pode durar 20 s sem ser tratada como imagem parada. Detectores de pixel continuam como diagnóstico, nunca critério editorial completo.

### Sprint 2 — ligar repertório EXISTENTE ao formato ATLAS
- Adapter das fichas V3 e escolha de modo para o diretor ATLAS, com seleção de evidência, registro de indisponibilidade, e testes.
- Adapter de mídia comprovada e vídeo real de V4 para ATLAS, com auditores de integridade.
- Não mudar tokens nem DOSSIÊ, NTC ou mapas sem regressão.

### Sprint 3 — duas provas reais (não produção inteira)
- Vídeo vertical privado de 20–30 s Guerra dos Chips com mídia específica verdadeira e voz aprovada; validação humana por ação e narrativa.
- Vídeo horizontal de 90–120 s com um mini-arco completo, baseado em neo + fern, em branch/preset próprio.
- Se um desses falhar, reparar a **capacidade genérica**, não inserir exceções para TSMC, Taiwan, Panamá ou outros nomes.

## 7. Não fazer
- Não criar `src/v5/diretor.py`, «novo banco de acervo» nem importar vídeos de referências sem direitos.
- Não habilitar automaticamente 457 templates HyperFrames nem trocar backend por suposição de qualidade.
- Não migrar telas do NTC para o documental; NTC tem gramática/renderer independentes.
- Não reescrever a identidade ATLAS aprovada porque piloto foi monótono; rever escolhas de prova e acontecimentos.
- Não anunciar sucesso só pela conclusão verde do workflow.
- Não dar merge global entre branches ATLAS divergentes. Migrar **commit/arquivo/função estritamente necessários**, com diffs, testes e revisão.
- Não ativar agendamento, publicação, custos API pagos nem mudar produção sem autorização.

## 8. Fontes auditadas
- `https://github.com/Heitor2404/coringa-news/blob/main/.github/workflows/gerar-videos.yml`
- `https://github.com/Heitor2404/coringa-news/blob/motor-integral-v4/main.py`
- `src/v2/contrato.py`, `src/v3/plano_av.py`, `src/v3/linguagem.py`, `src/v3/pipeline.py`, `src/v3/receitas.py`, `src/v3/memoria.py`, `src/v3/revisao_multimodal.py`, `src/v3/estado_final.py`, `src/v3/fiscal_editorial.py`, `src/v3/biblioteca.py`
- `src/acervo.py`, `src/midia.py`, `src/v4/diretor.py`, `src/v4/episodio.py`, `src/v4/componentes.py`, `src/v4/portoes.py`, `docs/v4/CAPACIDADES.md`
- `src/v4/formatos/diretor.py`, `src/v4/formatos/plano.py`, `src/v4/formatos/produzir.py`, `src/v4/formatos/formatos.json`, `motor4/remotion/src/formatos/Primitivas.tsx` e `Formato.tsx`
- `docs/v3/CORRECAO_ESTRUTURAL_DIRECAO.md`, `docs/v3/INVENTARIO_FERRAMENTAS.md`, `docs/v3/ARQUITETURA_V3_1.md`
- `atlas-biblioteca-20261118/docs/v4/formatos/BIBLIOTECA_ATLAS_OPERACIONAL.md`, `atlas-biblioteca-20261118/scripts/atlas_biblioteca.py`
- `canais/ntc/vetor/LEIAME.md`, `src/fabula.py`, `.github/workflows/v4-episodio.yml`, `.github/workflows/atlas-validacao.yml`
- GitHub tree das cinco branches; comparações inter-branch; execuções `44405950985` (MP4 Chips) e `44371334155` (biblioteca candidatas) conforme histórico de Actions/documentos.

**Veredito:** **aumentar integração e capacidade homologada, não quantidade de sistemas**. A implementação só deve começar por P0 depois de revisar contratos de interface e riscos de regressão. **Nenhuma alteração de motor foi realizada neste estudo.**
