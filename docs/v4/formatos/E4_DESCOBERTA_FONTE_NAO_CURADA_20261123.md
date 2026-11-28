# Experimento E4 — descoberta de fontes sem URLs pré-registradas e prova por revisão

**Data:** 23/11/2026. **Branch:** `atlas-direcao-visual-20261118`.
**Veredito:** descoberta pública e proveniência de texto **PASSARAM**; interpretação completa da máquina e geração autônoma de `MechanismSpec` **NÃO passaram**.

## Motivação real

E3 havia recuperado três URLs previamente cadastradas em F16 e extraído poucas relações por expressões léxicas F17. Ainda faltava a capacidade de descobrir a página sem um manifesto de URL + trechos fixados pelo desenvolvedor. E4 prova somente esse primeiro elo, com limites claros; não deve aparecer como um motor que agora compreende qualquer máquina.

## Implementação e limites de segurança

Novo arquivo `src/v4/formatos/descoberta_fontes_e4.py`:
- Usa o endpoint fixo da MediaWiki Action API `https://en.wikipedia.org/w/api.php`. **A consulta textual varia, não as URLs externas arbitrárias**. Faz `list=search` com até quatro resultados e escolhe até dois por consulta, com pontuação léxica de título sem `if` pelo nome da família.
- Para cada resultado, faz **um SEGUNDO GET por `pageid`** com `prop=extracts|revisions`, validando `pageid`, `revid`, esquema de resposta, texto obtido e SHA256. O snippet de busca **não pode** ser utilizado como evidência: serve somente à descoberta. A página e seu texto são confirmados pela API pública; conteúdo correto/fidedigno do ponto de vista da engenharia **ainda precisa ser avaliado**.
- URL base fixa, HTTPS, rejeição de redirecionamentos, limite de bytes/tempo, máximo de 2 páginas por consulta, consultas limitadas e recusa de texto ausente ou retorno malformado. Não há crawling de domínios novos, sessão de navegador, download de CAD ou imagem de terceiros.
- Seleciona automaticamente até 12 frases do texto recuperado por vocabulário genérico de mecanismo. Passa essas frases a `F17.extract` para **candidatos de relação**, mas nunca transforma reconhecimento léxico em geometria válida sem evidência.
- Extrai **candidatos numéricos com unidades** (`mm`, `cm`, `m` escritos, etc.) e **contagens estruturais literais** (ex.: “four joints”), sempre com ID do excerto. O valor fica `usable_to_fill_mechanism_spec=false`, e as contagens ficam `safe_to_instantiate_joint=false`: extrair um número sem comprovar a peça, endpoints, eixo, escala e variante não autoriza preencher uma junta.
- Fonte enciclopédica: **não** é desenho industrial autorizado, catálogo CAD, identidade de máquina, prova de mídia licenciada ou prova de funcionamento detalhado. `render_allowed=false` e `publish=false` permanentes.

Testes em `tests/test_descoberta_fontes_e4.py` cobrem proveniência dupla, dados forjados, revisões/hashes corrompidos, consultas adversariais, subdomínios não autorizados, snippets de busca falsos, limites, e contagens estruturais que **não** preenchem juntas.

Workflow `.github/workflows/qa-descoberta-fontes-e4.yml` testa o código, faz consultas live e gera JSON/auditoria privada com total de fontes **distintas**, não misturando repetição em buscas.

## Execução REAL (GitHub Actions)

**Run final:** https://github.com/Heitor2404/coringa-news/actions/runs/45216575775 — **SUCCESS, 41 testes PASS**, busca real por HTTP e prova de texto/revisão. Execuções anteriores incluíram ajuste de dependência `cairosvg`, um colchete extra no agregador e correção de `\\b` do regex de contagens, resolvidos com CI, sem alterar benchmark/produção.

**Artifact privado:** `lab-e4-public-search-provenance-no-publish`, ID **14837647914**, expira **28/11/2026 16:27:11 UTC**. ZIP com `E4_whitworth_quick_return.json`, `E4_four_bar_linkage.json` e `QA_E4_DISCOVERY.json`. Dados conferidos diretamente; contém IDs de página, revision IDs, SHA256, trechos e contagens, **sem mídia de terceiros**.

### Resultados live

Duas consultas **fornecidas manualmente**:
1. `Whitworth quick return`: encontrou **Quick return mechanism** (pageid 49162954, revid 1386479381) e **Four-bar linkage** (pageid 1442361, revid 1380680795).
2. `four bar linkage`: encontrou **Four-bar linkage** (mesma revisão) e **Six-bar linkage** (pageid 33346874, revid 1380705291).

**TOTAL:** quatro recuperações de páginas, mas **três artigos/revisões únicos**, nenhum URL desses artigos estava pré-registrado no motor. Cada artigo foi encontrado por busca e obtido novamente por ID, com versão registrada.

**Trechos e evidência:** 24 excertos por consulta, 48 ocorrências de excertos coletadas (com repetição de Four-bar). **15 ocorrências de contagens estruturais literais** (também com repetição). Exemplos conferidos:
- Four-bar: `four bodies`, `four joints`, `four links`.
- Six-bar: `one degree of freedom`, `six links`, `seven joints`.
- Quick return: `three turning pairs`.

**Resultado negativo essencial:** o vocabulário de F17 retornou **0 arestas mecânicas tipadas** nas quatro recuperações. Foram encontrados **0 parâmetros com unidade de dimensão** nas frases selecionadas. Isso significa que a nova busca localizou material de referência, mas a etapa de compreensão e montagem ainda não está operacional para páginas com linguagem diversa da F17. Não há qualquer prova de que `four joints` informa os endpoints dos quatro pinos, nem de que três pares permitam simular o retorno rápido.

Os exemplos pesquisados continuam **sem nova trajetória, vídeo, 3D ou spec gerada** nesta etapa. E1/E2 preservam 3 topologias já demonstradas **manualmente**, não acrescentar pontuação aos 12 desafios. Não houve teste dos quatro holdouts.

## Score estritamente verdadeiro

- **2 consultas** → **3 páginas únicas encontradas com fonte, texto e revisão**.
- **41 testes PASS** na implementação e regressões selecionadas.
- **0/4 recuperações com arestas compatíveis F17**, **0 specs completas**, **0 animações novas**, **0 aprovações de visual**, **0 publicações**.
- Busca limitada a uma API enciclopédica, sem pesquisa aberta em artigos acadêmicos, fornecedores, CAD ou vídeos. Não inferir licença de mídia de artigo de texto.
- Não houve chamada de LLM paga no código E4; possíveis custos de infraestrutura não medidos.

## Próxima fase recomendada — E5

Aumentar **a interpretação das fontes**, não fabricar 3D por palpite. Construir avaliação de extração de relações em **frases de fonte real** com um conjunto de exemplos rotulado e separado de teste; comparar um extrator linguístico de propósito geral (quando disponível) com a F17 léxica e medir falsos positivos, cobertura, custo e conferência humana. Exigir citação por ligação e parâmetros que realmente estejam na fonte. Provar `MechanismSpec` completa num mecanismo **não utilizado para desenvolver as regras** antes de tentar renderização; nunca editar o benchmark de 12 para facilitar o teste.

**Isolamento:** nenhuma mudança em `main`, NTC, DOSSIÊ, Telegram, motor de produção, publicação ou catálogo produtivo. Estética antiga descartada continua bloqueada.
