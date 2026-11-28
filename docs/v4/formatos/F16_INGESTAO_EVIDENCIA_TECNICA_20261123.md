# F16 — fonte técnica verificável → grafo parcial → pré-voo ou bloqueio

**Data:** 23/11/2026, ~11h23 BRT. **Branch:** `atlas-direcao-visual-20261118`. **Estado:** validação técnica do ingestor F16b concluída. Nenhuma aprovação industrial, direito visual ou produção. **Nenhuma animação de terceira família gerada.**

## Objetivo e resultado

A F15 seleciona entre biela e engrenagens a partir de um **grafo previamente estruturado**. A F16 introduz um passo anterior: buscar HTML de uma URL permitida, encontrar trechos técnicos curtos nela, extrair um **grafo candidato limitado** das relações evidenciadas, informar o que não foi demonstrado e chamar a F15 somente para topologia realmente suportada. Não usa modelo linguístico, visão computacional, pesquisa autônoma ampla nem CAD; os excertos ainda são **selecionados manualmente** e o parser tem regras pré-definidas. Seu ganho é a **verificação automática da fonte e o bloqueio de extrapolações**, não a inteligência geral.

**Workflow final:** https://github.com/Heitor2404/coringa-news/actions/runs/45193303090 — **SUCCESS: 58 testes aprovados**, inspeção remota de quatro URLs cadastradas, prova de três documentos reais recuperados, um bloqueio explícito de site e validação de todos os gates.

**Artifact privado:** `lab-f16-tres-fontes-grafos-e-bloqueios-privado`, ID **14825723808**, expira **28/11/2026 ~14h22 UTC**. ZIP baixado e inspecionado; contém `QA_F16.json`, 4 relatórios `*_AUDITORIA.json`, `DEMONSTRACAO_OFFLINE_NAO_COMPROVA_ORIGEM.json` e **um** `par_engrenagens_educacional_PLANO_F15.json`. **Sem MP4.**

## Fontes e resultados de verdade

| Fonte | HTTPS/âncoras verificadas na CI? | Extração | Resultado |
|---|---|---|---|
| [Applied Mechanics / spur gears](https://mechanics.ju.se/MachineElements/spur-gears.html) | SIM, três trechos | 2 rodas `spur_gear` e aresta `meshes_with`, sentido oposto | **Pré-voo F15 válido**, MAS parâmetros de dentes/módulo **fornecidos pelo projetista** e revisão humana pendente |
| [Mechanic / slider-crank](https://jd-jones-ases.github.io/Mechanic/things/slider-crank/) | SIM, três trechos | manivela, biela, pistão, cilindro; juntas e deslizamento | **BLOQUEADO**: documento citado não prova motor, polia, correia e volante exigidos pela montagem F15 |
| [Hydra Products / scissor lift](https://hydraproducts.co.uk/hydraulic-power-packs/power-pack-applications/commercial-systems/scissor-lift/) | SIM, três trechos | motor elétrico → bomba → cilindro hidráulico → braços de tesoura | **BLOQUEADO**: topologia reconhecida, mas não existe núcleo de hidráulica/tesoura, geometria de pivôs nem física de elevação no LAB |
| [AHydraulics / scissor lift](https://www.ahydraulics.com/en/about-us/frequently-asked-questions/frequently-asked-questions-about-scissor-lifts/how-does-a-scissor-lift-work-hydraulically/) | NÃO: resposta HTTPError | nenhuma inferência remota | **BLOQUEADO_ORIGEM**; a fonte foi inspecionada no navegador durante a pesquisa, mas NÃO baixada/verificada pelo pipeline, não contabilizar como prova runtime |

**SHA256 dos BYTES reais recebidos na CI, sem salvar o HTML completo dos terceiros:**
- Applied Mechanics: `9ce7ac8639bfbfe7f3ebdc8fa45e7e68a66cbd33dae5e5ca5d2294efb9fffe8b`
- Mechanic slider-crank: `4b67df19838531d3afc8065806d36c9ce9d76adfb151c299ed4e942b2aa3d897`
- Hydra Products: `b0259e470995a0cd1655b8f9fd92058ab961244843216ee2faebc1dab298b175`

O hash de cada HTML é prova de bytes adquiridos **naquela execução**, não garantia de permanência do site. As citações textuais têm âncoras identificadas e o `source_retrieval` separa `HTTPS_SOURCE_SAME_URL_AND_ANCHORS` de fixtures locais. O pipeline não armazenou imagens/código CAD de terceiros nem inferiu licença.

## Arquitetura F16b

- `src/v4/formatos/evidencias_f16/*.json`: quatro manifestos com URL, trechos pequenos identificados, locator, data de verificação humana e proibição de publicação. Uma especificação separada fornece os números da engrenagem; eles não são extraídos do artigo.
- `src/v4/formatos/ingestao_evidencias_f16.py`: permite **somente quatro URLs exatas, https, sem redirect**, limite de tamanho e timeout; extrai texto HTML ignorando scripts, compara trechos normalizados, cria relações apenas nas três gramáticas reconhecidas, classifica lacunas e bloqueia solicitações com prova incompleta. Executa `compilador_topologia_f15.py` somente após prova de HTML + trechos + parâmetros manuais validados no kernel. Flags `publication_allowed=false` e `human_review_required=true` sempre.
- `tests/test_ingestao_evidencias_f16.py`: inclui fixtures DESCRITAS como testes offline (não são provas da web), URL host indevido, licença forjada, alteração de citação, corpo sem citação, tipos desconhecidos, perda de correia/biela, hidráulica sem núcleo, texto em SVG/HTML e F15.
- `.github/workflows/qa-ingestao-evidencias-f16.yml`: regressões F16/F15/F14, teste **online** das quatro URLs, JSONs e revisão de gates no artifact; quando servidor bloqueia, o workflow permanece verde apenas porque a situação real é documentada como bloqueio, **não sucesso de ingestão**.

**Duas distinções decisivas:** (a) o grafo de duas engrenagens foi apoiado na descrição do engrenamento; quais delas são a entrada e a saída são uma **escolha do projetista**, não descoberta visual; (b) os eventos `engagement`/`reduction` e cinemática ideal de F14 vêm de **kernel técnico já validado** e números fornecidos manualmente, não de texto daquela fonte como se medisse relação real.

## Avaliação e próximos gates

**Aprovação técnica F16b:** testada como ingestão restrita, auditoria de trechos e pré-voo condicional. **Não afirmar capacidade autônoma de identificar qualquer mecanismo na web**, nem de copiar/reconstruir animações industriais. O sistema ainda depende de curadoria dos trechos e de kernels específicos.

**Próxima fase de maior valor (F17):** adicionar busca/extração textual com validação de relações sem um padrão por página, grafo com evidências por aresta e eventos físicos sustentados; para hidráulica, mapear exatamente que novas primitivas matemáticas/peças seriam necessárias (reservatório, bomba, atuador, braços articulados, pivôs), sem desenhar um mecanismo industrial fictício antes de dominar a física. Trabalhar com licença/identidade de mídia independentemente da evidência textual. Depois testar com referências de subtipos de máquina e vídeo real, não apenas gráficos didáticos.

**Estado de produção:** branch experimental apenas. `main`, NTC, DOSSIÊ, Telegram, publicação e motor documental produtivo **intocados**.
