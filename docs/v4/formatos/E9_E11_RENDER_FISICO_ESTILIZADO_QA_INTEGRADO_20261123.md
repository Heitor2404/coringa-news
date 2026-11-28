# Lote E9–E11 — representação técnica estilizada, auditoria física e quatro vídeos privados

**Data:** 23/11/2026 · **Branch:** `atlas-direcao-visual-20261118`
**Veredito:** avanços visuais e QA técnicos **APROVADOS**, mas fidelidade industrial/documental **NÃO comprovada**.

## Mudança de método solicitada pelo usuário

Em vez de depender de mensagens sucessivas “Prossiga”, o desenvolvimento deve avançar em **lotes com objetivo funcional**, executar CI, examinar quadros reais, corrigir erros internamente e só então entregar um resumo de resultados com o documento de continuidade atualizado. Um lote **não** significa trabalho em background após o fim da resposta; para projetos realmente longos, o usuário pode usar ChatGPT Work ou iniciar outra execução. Evitar promessas de autonomia temporal inexistente.

**Meta do lote E9–E11:** parar de apenas engrossar/posicionar “paus e pontos” e criar um perfil gráfico mais inteligível vinculado às poses e aos segmentos geométricos do solver comum, com QA independente de posicionamento, fonte e segurança. Não presumir forma física que o CSV não descreve.

## E9 — compositor visual 2D, único e sem dispatch por máquina

Novo `src/v4/formatos/renderer_mecanico_e9.py`. Consome **EXATAMENTE a `MechanismSpec`** gerada por E7/E8 e poses do solver existente `solver_restricoes_e1.py`. Reutiliza câmera e SVG-base `renderer_corpos_e1.py`, substituindo apenas a camada gráfica de corpos; nunca escreve novas restrições ou trajetórias por título de arquivo.

Primitivas/regras **genéricas**:
- Corpos de múltiplos elos desenhados como **ligações metálicas ilustrativas** com espessura em tela, contorno, reflexos, extremidades circulares e furos estilizados. Coordenadas e ângulos são os do CSV/solver; espessura, cores e rasgos ilustrados NÃO são CAD dimensionado.
- `slotted_link`: canal representado no próprio elo. Juntas `slot` recebem pino móvel baseado em `world(pose,pa)`, sem modificar trajetória.
- Pivôs de terreno: símbolo visual de mancal e suporte da estrutura. `slot` ancorado no terreno: guia desenhada a partir da direção de fonte e do curso medido dos frames, **sem afirmar limites industriais dos batentes**.
- Entrada rotativa: arco indicativo próximo ao pivô comprovado. Não simula torque.
- Layout 9:16 com grade discreta azul-petróleo, câmera fixa e painel técnico. Texto explícito **“PEÇAS ILUSTRATIVAS”**, status **“NÃO PUBLICAR”**. Não cola fotos de terceiros, não usa imagem gerada para se passar por máquina real.
- Não há `if` para `shaper`, `hoekens`, `pump-jack` ou `knuckle-press`. O título só entra como texto, escapado para SVG; as peças e movimentos vêm exclusivamente das estruturas.

**Bug encontrado e corrigido:** primeira execução E9 rejeitou números **NumPy** finitos vindos do solver na rotina de serialização SVG (`E9-VISUAL-NAN`). Corrigido com `numbers.Real` + `math.isfinite(float())` e rejeição de bool/string/NaN. CI reexecutado e verde.

## E10 — auditoria técnica separada da aparência

Novo `src/v4/formatos/auditoria_visual_e10.py` e testes `tests/test_renderer_mecanico_e9_e10.py`:
- Soluciona 61/91/121 estados, verifica posições das âncoras dos pinos e distância normal dos rasgos até o eixo contra o solver comum.
- Enquadra todos os segmentos e envoltórias do mecanismo na área mecânica `[25,515]` horizontal e `[168,754]` vertical. Detecta miniaturização, saída de quadro e câmera variando.
- Faz render de quatro frames em PNG, valida SVG como XML, exige todos os corpos/camadas, nenhum ID duplicado e proíbe `script`/`href`/URLs externos.
- Compara **somente pixels da área do mecanismo** entre estados para provar que existe movimento real, sem confundir barra de progresso da interface com animação física.
- **NÃO** certifica recognoscibilidade industrial: `industrial_part_contours_sourced=false`, `housing_dimensions_verified=false`, `aesthetic_approved=false`, `publish=false` sempre. Nenhum limiar artificial de cor substitui avaliação estética humana.

## E11 — prova cruzada em quatro geometrias reais externas

Workflow `.github/workflows/qa-lote-visual-e9-e11.yml`:
1. Executa testes E9/E10 + regressões E1/E2/E7/E8.
2. Baixa novamente os **seis CSVs** predefinidos no E8, exigindo bytes/commit/hash/licença MIT idênticos aos do manifesto.
3. Preserva recusas legítimas de `watt` (driver parcial não suportado) e `hydraulic-boom` (representação e atuação linear sem suporte).
4. Para quatro specs aceitas, verifica 91 estados em E10 e gera os **quatro MP4s** E9 (540×960, 18 fps, 2 s, sem áudio, câmera fixa), cada um com SHA de mídia, CSV de origem, número de corpos/juntas e status visual falso.
5. Cria folha de contato de quatro vídeos e imagem comparativa E8 vs E9, geradas a partir de SVGs reais no mesmo instante; não compara somente screenshots sintéticas.

**Execução final:** [GitHub Actions 45273454934](https://github.com/Heitor2404/coringa-news/actions/runs/45273454934) **SUCCESS — 60 testes PASS**. Run inicial **45273218179** falhou no bug de NumPy, foi corrigido e revalidado. Artifact `lab-e9-e11-four-generic-machines-illustrative-private`, ID **14866735562**, expira **28/11/2026 21:50:09 UTC**. ZIP baixado, extraído e os dois painéis de comparação e quatro exemplos foram abertos visualmente.

| Arquivo-fonte | MP4 E9 | Corpos / juntas | Movimento RGB (QA) |
|---|---|---|---:|
| `shaper.csv` | `E9_INDUSTRIAL_ILLUSTRATION_shaper.mp4` | 4 / 7 | 8,67 |
| `hoekens.csv` | `E9_INDUSTRIAL_ILLUSTRATION_hoekens.mp4` | 3 / 4 | 12,15 |
| `pump-jack.csv` | `E9_INDUSTRIAL_ILLUSTRATION_pump_jack.mp4` | 3 / 4 | 10,21 |
| `knuckle-press.csv` | `E9_INDUSTRIAL_ILLUSTRATION_knuckle_press.mp4` | 5 / 8 | 10,84 |

**Comparação real `E11_BASELINE_VS_E9.jpg`:** aumentou o preenchimento gráfico do mecanismo e alterou significativamente a composição (diferença RGB média 185,57 dentro da área dos desenhos). **Isto não é uma pontuação de beleza**. A E9 é graficamente mais elaborada e deixa as conexões mais evidentes, mas as imagens ainda lembram **braços, elos e mancais**, e não máquinas industriais completas, com chapas, guias e carcaças comprovadas. A identidade exata de um `pump jack` industrial ou de uma prensa não é representada de forma fiel. Visual **NÃO HOMOLOGADO**.

Sinal de integridade: E9 não alterou solver E1/E2, fonte upstream, IDs de corpo/junta ou benchmark de 12. A contagem de alvos históricos numéricos do projeto continua **4/12**, nenhum novo alvo do benchmark foi oficialmente validado, nenhum teste de holdout mecânico, nenhum modelo criado a partir de vídeo/foto/prosa, zero vídeo publicado.

## Próxima prioridade MATERIAL (não mais contagem artificial de etapas)

Para transformar “esqueleto em máquina”, precisamos de **contornos reais e posição de cada peça** derivados de arquivos CAD/STEP/DXF/SVG de conjuntos articulados; suportes e carcaças não podem ser inferidos como se fossem fatos. A interface precisa mapear cada perfil ao corpo, pivô, unidade, referência de montagem e licença. Depois o renderizador deve movimentar esses contornos com poses do solver sem deslizamentos visuais, com inspeção humana em pelo menos quatro mecanismos.

Foi pesquisado material potencial (sem integração nem prova de licença em runtime) como `pkqzzt/Auto-linkage-mechanisms` — descreve produção de arquivos CAD/DXF com corpos/juntas e regras de fabricação — e `birneamstiel/linkage-fab`, que exporta perfis SVG a partir de desenhos `.slvs`. **São pistas para E12, não funcionalidades já implementadas.** Priorizar primeiro a prova de uma peça real com contorno mapeado e licença, não novas centenas de imagens de barras.

**Isolamento:** apenas `atlas-direcao-visual-20261118`; `main`, NTC, DOSSIÊ, Telegram, produção e publicação inalterados.
