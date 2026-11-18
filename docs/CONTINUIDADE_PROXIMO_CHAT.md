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
