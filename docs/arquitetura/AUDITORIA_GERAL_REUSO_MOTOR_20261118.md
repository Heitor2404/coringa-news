# Auditoria geral de reaproveitamento — ecossistema Coringa
**Data:** 18/11/2026 · **Natureza:** auditoria estática + conferência seletiva de CI, NÃO refatoração nem homologação audiovisual.
**Escopo:** repositório `Heitor2404/coringa-news`, branches `main`, `motor-integral-v4`, `atlas-direcao-visual-20261118`, `atlas-piloto-chips-20261118` e `atlas-biblioteca-20261118`.
**Objetivo:** evitar criar código duplicado ao avançar ATLAS V2 / longform. **Nenhuma alteração de código ou branch produtiva foi feita nesta auditoria.**
**Limite metodológico:** examinados os trees integrais e os principais pontos de entrada, catálogos, bibliotecas, validadores, backends, workflows e alguns runs. **Não foi feita execução local da suíte inteira, leitura semântica de todos os arquivos nem auditoria exaustiva de dependências/segurança**. “Existe código” ≠ “integrado no fluxo da pauta” ≠ “testado em runner” ≠ “aprovado pelo humano”.

## 1. Inventário dos ramos e produção REAL
| Ramo | Inventário em 18/11 (arquivos de código+assets) | Responsabilidade e evidência |
|---|---|---|
| `main` (SHA `8d55069329df...`) | 329 blobs | Workflow diário `.github/workflows/gerar-videos.yml`, `main.py`, NTC e pipeline histórico. Agendamento **pausado** por `AGENDA_ATIVA` — não assumir produção diária. |
| `motor-integral-v4` (SHA `74577a7f2f76...`) | 1.321 blobs | Base extensa com V2, V3, V4 integral e `src/v4/formatos` ATLAS/DOSSIÊ; experimental/ramo de referência. Não é automaticamente o checkout do workflow `main`. |
| `atlas-direcao-visual-20261118` (SHA antes desta auditoria `1ec5ddae9701...`) | 1.328 blobs | Contrato/guia/decupagens, mudanças de direção visual e integração técnica no ramo experimental; **100 commits à frente** da base `motor-integral-v4`. |
| `atlas-piloto-chips-20261118` (`9743842e9123...`) | 1.331 blobs | Piloto de chips, narração Edge provisória, filmes privados, testes; **48 commits à frente e 18 atrás da direção**; divergiram. |
| `atlas-biblioteca-20261118` (`f1256e3d39db...`) | 1.332 blobs | Catálogo curado/galeria/mídias candidatas; **23 commits à frente e 18 atrás da direção**; divergiram. |

### CI que exige atenção
- `main`, run agendado **44390925982**, 18/11: GitHub `success`, mas job `gerar` **skipped**, porque os disparos automáticos estão pausados. **Não foi demonstrada geração de vídeo por esse run.**
- `atlas-piloto-chips-20261118`, run privado **44405950985**: GitHub `success`, narração e render concluídos, vídeo enviado ao Telegram, mas `ATLAS_FISCAL` retornou **`BLOQUEADO`** pela janela **36–40 s congelada**. **Conclusão do job não é aprovação.**
- `atlas-piloto-chips-20261118`, reuso **44405025069**: sucesso em preflight e 34 quadros amostrados, com avisos de crédito no rodapé; esse teste não avaliou o vídeo completo.
- Existirem testes em `tests/` e relatórios CI não prova automaticamente desempenho para novas pautas.

## 2. Mapa de REUTILIZAÇÃO (evitar duplicação)
| Camada | O que JÁ EXISTE | Onde | Estado / ação |
|---|---|---|---|
| **Pautas/roteiro e fatos** | Captura de pautas, roteiro, fontes, contrato por acontecimento, pesquisa factual e enumeração de fatos | `src/cacador.py`, `src/roteiro.py`, `src/fontes.py`, `src/acontecimentos.py`, `src/v2/contrato.py` | **REUTILIZAR contratos**, verificar uso real por tipo de pipeline; NÃO construir novo detector por regex. |
| **Ficha de cena audiovisual** | **`plano_av.fichas`** já possui `sujeito`, estado inicial, ação, transformação, consequência, forma visual, mídia disponível, evidência, critério, status | `src/v3/plano_av.py` | **DUPLICAÇÃO PROPOSTA DETECTADA**: nossa ideia ATLAS V2 de `ficha_cena` já tem base concreta. Criar **adaptador versionado** para o schema ATLAS, não reimplementar do zero. |
| **Escolha da linguagem pela ação** | **`linguagem.forma_do_evento`** escolhe registro, mapa, esquema, documento, comparação ou tipografia; `validar_plano` cobra justificativa para substituir forma | `src/v3/linguagem.py` | **REUTILIZAR lógica e testes**, ajustar taxonomia de ATLAS cartográfico. Revisar falso positivo semântico e as heurísticas baseadas em texto. |
| **Diretor e storyboard** | Diretor V3 com 1 correção dirigida + verificações; V4 integral com modalidade→componente; ATLAS tem diretor restrito ao catálogo de beats/slots | `src/v3/pipeline.py`, `src/v4/diretor.py`, `src/v4/formatos/diretor.py` | **SOBREPOSIÇÃO REAL**, não necessariamente código morto. Escrever adaptador de **contrato de acontecimento → cena ATLAS**, mantendo renderer e identidade isolados. **Não adicionar um quarto diretor completo.** |
| **Memória editorial** | Feedback por timestamp/categoria, erros permanentes, receitas testadas e condicionadas à aprovação humana | `src/v3/memoria.py`, `src/v3/receitas.py`, `docs/memoria/` | **REUTILIZAR como fonte única de feedback**. 14 receitas no registro: **11 testadas + 3 propostas, nenhuma aprovada**. `docs/memoria/regras_editoriais.json` contém **0 regras**. Não dizer que há políticas editoriais homologadas. |
| **Pesquisa e seleção de mídia** | Wikimedia, Wikipedia, Wikidata, NASA fotos/vídeos, Library of Congress, Smithsonian, Art Institute, Cleveland, iNaturalist, GBIF, Met, Europeana (chave), Openverse, Commons vídeos, Internet Archive, Pixabay (chave) | `src/acervo.py`, `src/midia.py`, `src/v4/acervo_v4.py` | **JÁ IMPLEMENTADO COMO CÓDIGO**, disponibilidade operacional por fonte depende rede/chave/termos. **Não adicionar mesmas APIs de novo.** Auditar taxa de candidatos aceitos/recusados e vídeo real usado. |
| **Biblioteca global** | SQLite, SHA256, pHash, regiões de interesse, classificação comercial, ingestão de arquivo local (`Biblioteca.ingerir`), CLI buscar/exportar/importar/recuperar | `src/v3/biblioteca.py`, `.claude/skills/coringa-acervo/SKILL.md` | **REUTILIZAR metadados e ingestão**. Banco e arquivos fora do Git; remoto não implementado/aprovado. Estado durável entre runners não pode ser presumido. |
| **Acervo ATLAS específico** | `src/v4/biblioteca_comprovada.json` + download SHA/URL + atribuição exigida; ramo biblioteca tem `biblioteca_atlas/catalogo.json` + candidatos | `src/v4/formatos/produzir.py`, `src/v4/viabilidade.py`; ramo `atlas-biblioteca-20261118` | **SISTEMAS SEPARADOS**: base tem **7 itens** comprovados; branch chips **9 itens** (2 fotos de chips) em manifesto experimental; biblioteca candidata está em **outro ramo**. Não confundir catálogo de candidatos com acervo pronto no render. |
| **Vídeo real** | `registro.video`, `video.documental`, `legado.render_video`, FFmpeg recorte e compatibilidade de duração | `src/v4/componentes.py`, `src/v4/episodio.py`, `src/v3/pipeline.py` | **CAPACIDADE EXISTE** no V3/V4 integral. **LACUNA ESPECÍFICA NO ATLAS**: `src/v4/formatos/produzir.py:ativos` decodifica com PIL e converte para JPG, e as composições atuais não inserem clipe documental como plano principal. Adaptar e testar, não inventar outro motor de vídeo. |
| **Mapas** | Natural Earth/OSM/MapLibre, MapLibre/Remotion, atlas `PalcoMapa`, camadas satélite/relevo com manifesto de licença, posições/ROI/câmera, zonas seguras | `src/v4/geo.py`, `motor4/remotion/src/MapaRota.tsx`, `src/v4/formatos/atlas_ref.py`, `Palco.tsx`, `plano.py` | **REUTILIZAR** geometria e dados licenciados. Câmera verdadeiramente oblíqua/satélite 3D não comprovada no ATLAS; tratar como pesquisa opcional, **não prioridade**. |
| **2D/2.5D/3D e mecanismos** | V2 catálogo de mecanismos/estados; V4 `mecanismo.nivel_vasos`, `mecanismo.eclusa`, `camadas.recorte`, `tresd.camara`, Manim e Remotion; ATLAS aceita apenas eclusa validada no catálogo | `src/render/v2/comp/*`, `src/v4/componentes.py`, `src/v4/backends/*`, `motor4/remotion/*`, `src/v4/formatos/formatos.json` | **REUTILIZAR contratos/infra**. **Revideo falhou em CI** (registro V4: `43972774128`); HyperFrames tem 457 itens indexados mas apenas pequena amostra testada e muita dependência de CDN. Não tomar “instalado” por “produção”. EUV não existe aprovado; se necessário, validar mecanismo de uso recorrente. |
| **Fiscais** | Métricas de estabilidade, cortes, áudio, factual, imagem↔fala, revisão semântica em 4 quadros, editoriais e gates de aprovação | `src/v3/fiscal_editorial.py`, `src/v3/revisao_multimodal.py`, `src/v3/estado_final.py`, `src/v4/portoes.py`, `src/v4/formatos/ritmo.py` | **REUTILIZAR lógica editorial como serviço compartilhado/versionado.** O ATLAS hoje foca pixels, geometria, testes antes de render e factual por rastreio; **não herda automaticamente a revisão semântica do V3**. Critério humano continua obrigatório. |
| **Som e locução** | `src/voz.py` tem Gemini TTS, Edge fallback e Whisper para timings; `src/v4/som.py` mix e SFX; amostra Piper no ramo chips | `src/voz.py`, `src/v4/som.py`, `.github/workflows/atlas-chips-voz-livre.yml` | **REUTILIZAR pipeline**, mas **NÃO** mudar voz aprovada automaticamente. Workflow de chips forçou Edge provisório; política editorial deve fixar preset/ID e falhar fechado se não autorizado. Verificar permissões de uso comercial do TTS. |
| **NTC vetorial** | Motor SVG próprio, Val/Juninho, kits de cenários, objetos, pessoas, regiões do céu e regras de geometria | `src/fabula.py`, `canais/ntc/vetor/*`, `tests/test_ntc_geometria.py` | **ISOLADO EM PRODUTO**, não misturar estilo ou código de render no ATLAS. Pode compartilhar apenas serviços versionados (TTS/cache/CI/telemetria). |
| **DOSSIÊ** | `src/v4/formatos/formatos.json` e `Primitivas.tsx`: mesa, documentos, marcadores, cronologia, fichas e fotos; `dossie.documentCard` já é reutilizado no ATLAS | `src/v4/formatos/`, `motor4/remotion/src/formatos/*` | **PRESERVAR contrato visual separado**. Compartilhar primitives/utilitários estáveis; qualquer alteração exige testes cruzados. |
| **Orquestração, segurança e distribuição** | GitHub Actions, logs/custos, prévia privada Telegram, arquivos cifrados e estados `BLOQUEADO` / `AGUARDANDO` / aprovação humana | `.github/workflows/*`, `src/v3/estado_final.py`, `src/v3/previa_telegram.py`, `src/caixa.py` | **REUTILIZAR**. Corrigir **sinalização de `BLOQUEADO` vs sucesso do job**; não publicar. Arquitetura multimotor por `canal+motor+versao` está **só planejada**, não implantada. |
| **YouTube LONG** | Há provas e mecanismos 16:9 em ferramentas como Remotion, mas **nenhum preset ATLAS LONG homologado** | `docs/arquitetura/PLANO_MULTIMOTORES.md`, `docs/v4/formatos/DECUPAGEM_*.md` | **NOVO PERFIL**, não novo motor nem canvas esticado. Slots/câmera/legendas/créditos/ritmo por formato, mesma semântica de direção. Não codificar antes de validação da versão vertical. |

## 3. Repetições / erros de integração mais importantes

**D1 — Nova “ficha de cena” duplicaria V3.** `src/v3/plano_av.fichas` já implementa quase todo schema proposto em `ESTUDO_REFERENCIAS_E_DIRECAO_ATLAS_V2_20261118.md`. Verificar lacunas específicas (`pergunta_aberta`, `inferencia`, `payoff`, identidade/ativos compatíveis) antes de acrescentar campos. **Prioridade alta.**

**D2 — ATLAS e V4 integral não compartilham automaticamente vídeos/documentos reais.** V4 possui `registro.video` e `registro.foto`; ATLAS `produzir.ativos` chama PIL e não encaminha vídeo documental para o Remotion Formato. **Prioridade alta.**

**D3 — Diretor genérico, diretor V4 e diretor ATLAS têm responsabilidades sobrepostas.** `src/v4/formatos/__main__.py` e workflows examinados carregam **planos JSON pré-gravados** e executam `narrar→ativos→preflight→quadros→render→telegram`; não há chamada do `src/v4/formatos/diretor.pedir` nesses entrypoints. **Não afirmar autonomia do diretor ATLAS em produção só porque há função de prompt.** **Prioridade alta.**

**D4 — Fiscais redundantes, mas sem interface comum.** Reaproveitar revisões/filtros V3/V4; *não copiar/colar* toda lógica em `formatos`. Preservar medição geométrica e plataformas do ATLAS, avaliação semântica comum e decisão final por estados. **Prioridade alta.**

**D5 — Biblioteca curada e global com políticas diferentes.** A biblioteca experimental `atlas-biblioteca-20261118` não foi incorporada ao pipeline principal. Sem migrar versões e manifestos, adicionar uma fonte NÃO faz asset aparecer em `formatos.ativos`. **Prioridade média-alta.**

**D6 — RAMOS DIVERGENTES.** As duas branches filhas (chips e biblioteca) divergem da branch direção; extrair melhorias por **commits selecionados**, com testes de regressão, não fazer merge cego. Nenhum arquivo da produção deve ser alterado por simples integração de protótipo. **Prioridade alta.**

**D7 — Receita e memória não estão aprovadas.** São **14 receitas: 11 `testado`, 3 `proposto`, 0 `aprovado`**; `docs/memoria/regras_editoriais.json` tem lista vazia. Preservar processo de aprovação baseado em evidência humana; não “promover” todas as receitas automaticamente. **Prioridade média.**

**D8 — Automatizações verdes não significam execução.** `main` run agendado `44390925982` saltou `gerar`; chips `44405950985` terminou verde com fiscal `BLOQUEADO`. Expor `etapa_executada`, `render_final`, `estado_editorial`, `aprovacao_humana`, `publicado`. **Prioridade crítica.**

**D9 — API Pexels não deve virar bloqueador.** Consulta oficial em 18/11: novas chaves pausadas. Entrada manual do asset é possível sob licença/termos, e `Biblioteca.ingerir` já recebe arquivo local; não automatizar scraping para contornar API. **Prioridade menor que D1–D4.**

**D10 — LONG 16:9 não é converter vídeo vertical.** Dividir `master_size`, safe areas e legendas por destino, compartilhar diretor semântico. Os 3 s de progressão no ATLAS são boa proteção contra congelamentos vazios em Shorts, mas precisam de outro contrato de continuidade por acontecimento no longform. **Prioridade posterior.**

## 4. Sequência de execução recomendada — NENHUMA executada aqui

**Fase A — Integração mínima sem novas animações**
1. Fixar **uma branch de integração** nova derivada de `atlas-direcao-visual-20261118`; antes de copiar commits chips/biblioteca, mapear diferenças e conflitos; nunca editar `main` nem `motor-integral-v4`.
2. Criar uma **interface mínima de direção semântica** usando `src/v3/plano_av.py`, `src/v3/linguagem.py`, `src/v2/contrato.py` **como módulos** (ou contrato compartilhado versionado). ATLAS mantém `formato/slots/tokens`. Exercitar 3 temas diversos em teste offline (infraestrutura, tecnologia geopolítica, história territorial) para evitar overfit.
3. Construir **ponte licenciada de mídia** `Biblioteca V3 / catálogo V4 → manifesto comprovado ATLAS → runtime`; incluir vídeo real com `registro.video`/FFmpeg por adaptador, mantendo verificação de URL, licença, SHA, dimensão, duração, recorte, créditos. Fazer teste real de um MP4 livre com licença auditada e sem depender Pexels.
4. Unificar **status de prévia**: CI `success` != `AGUARDANDO_APROVACAO`. Em fiscal `BLOQUEADO`, a mensagem Telegram deve ficar visivelmente `BLOQUEADO — DIAGNÓSTICO`, e o gate de qualidade deve expor conclusão não verde ou status separado (testado). Garantir voz editorial travada por ID/versão, sem fallback silencioso.
5. Prévias simples por *acontecimento* antes de plano inteiro; auditoria semântica V3 de 4 frames como aviso, nunca homologação automática. Validar política dos créditos sobre interfaces de plataformas.

**Fase B — Correção do episódio real**
6. Produzir **prova vertical 20–30 s** Guerra dos Chips com 3 modalidades **já existentes**: mapa factual + fotografia/vídeo real protagonista + sequência de documento/dado/fluxo, **sem** inventar mecanismo EUV. Quando o roteiro prometer mostrar EUV funcionando, bloquear se recurso não existir ou reescrever a fala honestamente.
7. Só acrescentar um mecanismo novo se houver **demanda e reutilização genéricas demonstradas**; Revideo está bloqueado em CI e não deve ser dependência obrigatória.

**Fase C — expansão**
8. Se prova vertical for aprovada por humano, construir preset ATLAS LONG 1920×1080 + capítulo de 90–120 s; integrar depois, com testes de regressão e sem diluir NTC/DOSSIÊ. Long não tem autorização para filmagens alheias (neo/fern) nem pressupõe TTS comercialmente liberado.
9. Após 2 episódios distintos **inteiros** e aprovados, iniciar manifesto SHA de release e seletor futuro de canais/motores, conforme `PLANO_MULTIMOTORES.md`.

## 5. Verificações que faltam antes de afirmar “auditoria completa”
- Executar testes cruzados Python/TS dos motores relevantes **na mesma branch de integração**; este estudo apenas inventariou `74` arquivos `tests/test_*.py` na base, não rodou esses testes nem os descartou.
- Medir o uso real de mídia por **100+ cenas** a partir de logs históricos de produção (se disponíveis), com taxa por fonte, tipo de asset e falha de correspondência; não há relatório quantitativo global neste documento.
- Inspecionar licenças e SDK de **cada backend** no ambiente de CI (o arquivo `docs/v4/CAPACIDADES.md` é registro de 17/11, não resultado desta auditoria).
- Verificar estado/cotas/versões de cada API por execução; código `f_...` não significa acesso válido.
- Verificar em runners limpos a preservação do banco V3 (SQLite e binários fora do Git) e a segurança de fontes/créditos no master por plataforma.
- Fazer revisão humana do **MP4 final**, não só styleframes ou status de testes.

## 6. Referências diretas de código/execução
- Fluxo `main`: `main.py` + `.github/workflows/gerar-videos.yml` (run `44390925982` `checar=success`, `gerar=skipped`).
- V2/V3: `src/v2/contrato.py`, `src/v3/plano_av.py`, `src/v3/linguagem.py`, `src/v3/pipeline.py`, `src/v3/memoria.py`, `src/v3/receitas.json`, `src/v3/biblioteca.py`, `src/v3/revisao_multimodal.py`, `src/v3/fiscal_editorial.py`, `src/v3/estado_final.py`.
- V4 integral: `src/v4/episodio.py`, `src/v4/contrato.py`, `src/v4/diretor.py`, `src/v4/componentes.py`, `src/v4/portoes.py`, `src/v4/capacidades.py`, `docs/v4/CAPACIDADES.md`.
- ATLAS: `src/v4/formatos/diretor.py`, `src/v4/formatos/planos/*.json`, `src/v4/formatos/produzir.py`, `src/v4/formatos/plano.py`, `src/v4/formatos/formatos.json`, `motor4/remotion/src/formatos/*`, `.github/workflows/atlas-validacao.yml`, `.github/workflows/atlas-chips-previa-privada.yml`.
- NTC: `src/fabula.py`, `canais/ntc/vetor/LEIAME.md`, `tests/test_fabula.py`, `tests/test_ntc_geometria.py`.
- Arquitetura planejada: `docs/arquitetura/PLANO_MULTIMOTORES.md`.
- Evidência de chips bloqueado: https://github.com/Heitor2404/coringa-news/actions/runs/44405950985 ; reuso: https://github.com/Heitor2404/coringa-news/actions/runs/44405025069 ; schedule pulado: https://github.com/Heitor2404/coringa-news/actions/runs/44390925982 .

**Parecer:** **não iniciar novo motor, novo diretor ou novas integrações de acervos como primeira tarefa**. A prioridade é **integrar semântica V3, vídeo real V4 e identidade/render ATLAS por contratos compartilhados e testar em vídeo humano**, mantendo todos os motores isolados.
