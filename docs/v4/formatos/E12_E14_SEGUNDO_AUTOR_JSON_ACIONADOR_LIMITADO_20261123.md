# Bloco E12–E14 — segunda origem independente de juntas + acionador oscilatório + quatro vídeos privados

**Data:** 23/11/2026 · **Branch:** `atlas-direcao-visual-20261118`
**Resultado:** integração entre duas ORIGENS e dois FORMATOS de geometria confirmada, 75 testes verdes, 4 JSONs convertidos, 4 MP4s privados. **Não houve importação de contornos CAD reais nem direção de arte homologada.**

## Mudança de processo aplicada

Usuário pediu execução contínua sem precisar enviar repetidamente “Prossiga”. Neste turno, o assistente implementou três partes do mesmo objetivo, criou CI, testou e corrigiu um erro real de manifesto, validou os arquivos, baixou e inspecionou o artifact, e registrou a continuidade.

**Limitação operacional:** o trabalho ocorre durante uma execução de ChatGPT, não continua em background quando a resposta acaba. ChatGPT Work pode ser o ambiente adequado para delegar trabalhos extensos entre sessões; não afirmar que um gatilho de conversa mantém programação espontânea permanente.

## Fonte externa realmente nova

Repositório MIT independente de autor e formato: `MeghRaval30/compliant-linkage-toolkit`, commit **`bb6137456a04d9afaa51240e9fc3e8540d269532`**, arquivo `LICENSE` SHA Git blob **`c59d45323926af6c3ebed8264aecffa096065a91`**.

O código/conteúdo da origem fornece `bodies[]`, `joints{...}` com `bodies=[a,b]`, `xy_mm`, `kind=revolute`, `input_joint`, `input_range_deg` e `meta.reference_input_deg`. Dados espaciais são explícitos; o motor NÃO os reconstruiu por análise de prosa.

A licença upstream tem campo de copyright com texto placeholder **`TODO-TEAM-NAME`**. O laboratório preserva sua licença original, hash e commit, **não publica** nem afirma direitos de mídia industrial. O autor também informa que seus modelos STL são **mecanismos flexíveis/complacentes**, alguns com propriedades de material placeholder e `is_physical=false`; não podem ser atribuídos a corpos RÍGIDOS do solver E1 como se fosse montagem industrial real. **STL foi deliberadamente EXCLUÍDO da animação**, em vez de deformá-lo falsamente. Esta distinção entre topologia de juntas e contorno real é essencial.

Manifesto imutável para teste: `benchmarks/e12_independent_planar_json_v1.json` com quatro arquivos:
- `examples/fourbar.json`
- `examples/designs/fb_02_0052.json`
- `examples/designs/fb_02_0090.json`
- `examples/designs/fb_02_0203.json`

Todos possuem origem por commit e SHA Git blob; licença MIT incluída em artifact. O modelo continua sendo de quatro barras, embora os quatro arquivos sejam parametrizações reais distintas — **não são quatro novas classes de mecanismos**.

## E12 — importador genérico de JSON de juntas

`src/v4/formatos/importador_juntas_json_e12.py`:
- Busca HTTPS em host fixo `raw.githubusercontent.com`, commit exato, paths permitidos, tamanho limitado, sem redirects e comparação SHA Git blob de cada arquivo/licença.
- Rejeita juntas sem tipo, corpos duplicados, geometrias desconectadas, IDs de entrada inválidos, pivôs não associados e escala/ângulo de origem inconsistentes.
- Converte todos os corpos nomeados `is_ground`, juntas `revolute` e posições `xy_mm` em `MechanismSpec` E1 em METROS, com âncoras locais derivadas das posições mundiais na pose inicial. **Não há ramificação por nome `fb_02_0052` ou pela família four-bar**, a entrada é lida por grafo explícito.
- Cria apenas segmentos visuais ilustrativos conectando posições das juntas. **Não finge que tem chapa, carcaça, furos dimensionados, STL por peça ou CAD fiel.**
- Valida geometria de todas as juntas a `t=0`, solve numérico e posto do jacobiano, preservando a revisão da fonte em cada auditoria.

## E13 — acionador angular restrito, sem forçar rotação completa

`src/v4/formatos/solver_restricoes_e1.py` mantém driver legado `{body,theta0,speed}` para E1/E2/E7/E8, e **opcionalmente** aceita `profile`:

```json
{"kind":"oscillating","range_min_rad":-0.3,"range_max_rad":0.3,"phase_rad":1.57079632679}
```

A equação comum do driver passa a usar `mid + amplitude*cos(phase + speed*t)` quando há profile; caso contrário continua `theta0 + speed*t`. Exige `range_min < range_max`, amplitudes limitadas, fase finita e **pose inicial coerente com a fonte**. O importador deriva os limites do JSON fonte relativos ao ângulo de referência medido, sem escolher arbitrariamente valores para dar movimento. Mantém solver de corpos/juntas/fechamento único e sem código por família.

## E14 — QA completo e quatro vídeos

Workflow `.github/workflows/qa-fonte-independente-e12-e14.yml`: testes E12 + regressões E1/E2/E7/E8/E9/E10, reconsulta live de quatro JSONs com hash + licença, limite rígido de pelo menos uma spec realmente aceita, verificação de postos do jacobiano e resíduos, geração de todos os vídeos aceitos com compositor E9 comum, auditoria E10 (área segura, câmera fixa, movimento, SVG, posições de juntas) e FFprobe de MP4.

**Falha inicial HONESTAMENTE registrada:** [Actions **45275751318**](https://github.com/Heitor2404/coringa-news/actions/runs/45275751318) teve 75 testes unitários PASS, mas a coleta live BLOQUEOU o quarto JSON por erro de transcrição do SHA Git blob no manifesto (`6d0c... ` incorreto, blob real `6e4e570b4be2206155792472fb00db8442d314a5` conferido no upstream por commit). A origem, conteúdo, split e código não mudaram; manifesto corrigido com `source_blob_correction_log` e CI reexecutado. Não encobrir o run inicial vermelho.

**Veredito final:** [Actions **45276058168**](https://github.com/Heitor2404/coringa-news/actions/runs/45276058168) **SUCCESS, 75 testes PASS**, quatro downloads reais, **4/4 `PASS_SOURCE_JSON_TO_COMMON_SOLVER`**, **0 bloqueios** e **4/4 MP4s privados** com sha conferido. Artifact `lab-e12-e14-second-author-real-joints-private` ID **14867361709**, expira **28/11/2026 22:05:41 UTC**. ZIP baixado em `/mnt/data/lab_e12_e14_verified.zip` e extraído em `/mnt/data/e12_e14_verified`; todos os quatro hashes MP4 verificados e storyboard REAL `E14_SECOND_SOURCE_STORYBOARD.jpg` aberto.

| Fonte | Resultado | Faixa de entrada em graus | Maior resíduo reportado |
|---|---|---|---:|
| `fourbar.json` | PASS 121 frames + MP4 | 40,0°–100,0° | 1,39e-17 m |
| `fb_02_0052.json` | PASS 121 frames + MP4 | 48,89°–70,60° | 2,78e-17 m |
| `fb_02_0090.json` | PASS 121 frames + MP4 | 80,75°–97,56° | 1,39e-17 m |
| `fb_02_0203.json` | PASS 121 frames + MP4 | 61,15°–80,49° | 1,39e-17 m |

As quatro animações mostram quatro barras articuladas com apoio, elos e parafusos ilustrativos. São confirmadamente diferentes em comprimentos/ângulos/tempos, mas **visual ainda muito genérico e esquemático**. Nenhuma representa rigidamente as peças complacentes originais. **ARTE REPROVADA para publicação**, mesmo com física e QA verdes.

Vídeos e assets privados:
- `E14_SECOND_SOURCE_fourbar.mp4`
- `E14_SECOND_SOURCE_fb_02_0052.mp4`
- `E14_SECOND_SOURCE_fb_02_0090.mp4`
- `E14_SECOND_SOURCE_fb_02_0203.mp4`
- `E14_SECOND_SOURCE_STORYBOARD.jpg`
- `QA_E12_SOURCE_JSON.json`, `QA_E14_SUMMARY.json`, quatro `*_E12_SPEC.json` e `UPSTREAM_MIT_LICENSE.txt`.

## O que foi comprovado e o que falta

**Novo e legítimo:** o mesmo solver e renderer agora executam dados de **dois autores e dois formatos externos**, CSV E7 e JSON E12, com fonte por campo de junta, escala, curso e pose. Em particular a adição de **perfil oscilatório** remove o bloqueio artificial de se impor volta completa a um corpo com movimento limitado.

**Limites ainda não resolvidos:** quatro variações do mesmo tipo four-bar no segundo autor, nenhum mecanismo de contato intermitente ou engrenagem complexa nova, nenhum CAD STEP/DXF/SVG/STL com **contornos de peças individuais alinhados aos mesmos pivôs** foi importado. Uma malha flexível contínua não é conjunto de peças rígidas. Não existe inferência autônoma de forma real a partir de prosa, foto ou vídeo; nenhum vídeo possui visual aprovado; nenhuma publicação. Benchmark congelado de 12 permanece **4/12 alvos históricos numéricos**, zero holdout mecânico genuinamente não preparado fora dos casos escolhidos, sem aumentar score por quatro variantes.

## Próxima atividade com maior impacto

Buscar fonte independente **com assembly CAD de peças separadas + pivôs ou mates** em formato aberto e licença efetivamente verificável, e construir `CAD part ID → anchor joint ID → local transform → solver body ID`. Só depois de garantir origem/escala/encaixe, substituir cápsulas ilustrativas pelos contornos do CAD. Não tentar obter uma máquina industrial fiel apenas retocando a UI de barras mais uma vez.

Verificações de pista:
- `BrayEngineering/Crank-Slider-Mechanism` MIT tem arquivos `.ipt` por peça (Inventor proprietário). **Não provado importador** ou alinhamento às juntas.
- `shakc04/strandbeest-forge` MIT tem fonte OpenSCAD e STL de kits; não provado que existam assets separados por corpo com pivôs mapeados.
- `clawbit` MIT tem SVG meramente ilustrativo com aviso expresso que dimensões CAD ainda precisam de medição; sem STEP/DXF prontos, não usar como prova.
- Projetos livres com exportação CAD podem fornecer conversões futuras, mas exigir direitos e geometria de fato, sem confiar em descrição de README.

**Ambiente preservado:** branch experimental apenas; `main`, NTC, DOSSIÊ, Telegram, pipeline de produção e publicação intocados.
