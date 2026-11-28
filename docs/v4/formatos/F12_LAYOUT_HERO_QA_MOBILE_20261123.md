# F12 — layout HERO elevado, máquina na mesma escala e QA mobile por pixels

Data: **23/11/2026, ~03h43 BRT**. Branch `atlas-direcao-visual-20261118` — **não integrado à produção**.

## Resultado

**F12 tecnicamente validada, mas UI e estética NÃO homologadas.** O compositor existente agora oferece um layout opcional `hero_elevado_f12` com cabeçalho de 134 px e uma **única translação vertical de todo o conjunto** calculada a partir de `camera_causal_geometrias.json` e da pose fixa. **A escala da máquina NÃO foi reduzida**; física do pistão, biela, manivela, polias e correia é preservada. O código rejeita geometria fora do palco e configurações não cadastradas, em vez de fazer um zoom arbitrário.

Os modos F7/F11, sem `--hero-f12`, mantêm o SVG antigo. Nenhuma nova câmera móvel foi introduzida; a transmissão animada F11 funciona com o layout alto. O cabeçalho foi compactado, o status mudou de baixo para a faixa superior; a anotação redundante inferior foi removida do modo HERO.

## Arquivos

- `src/v4/formatos/layout_hero_mecanico_f12.py` — algoritmo de disposição baseado na câmera curada, preserva poses, move a composição inteira e reorganiza somente o editorial.
- `src/v4/formatos/compositor_cinematico_parametrico_2d.py` — flag `--hero-f12` / `enquadramento_mobile="hero_elevado_f12"`.
- `src/v4/formatos/qa_svg_mobile_f11.py` — mesmo auditor de pixel efetivo, com relatórios F11 e F12 separados, sem redefinir os perfis do repositório.
- `tests/test_layout_hero_mecanico_f12.py` — invariância de todos os elementos físicos no XML, escala/câmera e testes de que os papéis ganham visibilidade sem minimizar o rig.
- `.github/workflows/qa-layout-hero-f12.yml` — três MP4s privados, quatro instantes por vídeo, métricas das máscaras e regressões.

## Evidências verificadas

**GitHub Actions:** https://github.com/Heitor2404/coringa-news/actions/runs/45125785520 — **SUCCESS: 41 testes aprovados** e todas as etapas de render/QA cumpridas.

**Artifact privado:** `lab-f12-hero-alto-mecanica-mascara-privado`, ID **14795926259**, 3.95 MB compactados, expira em **28/11/2026 ~06h42 UTC**. ZIP baixado, extraído e MP4s conferidos localmente pelo SHA256:

- `BIELA_CURTO_F11_BASELINE.mp4`: **`13b43cb2a5ef39e53774740b84e9119cf2a489c93ce54c734e8ceb0b96ae9451`**, hash idêntico ao F11.
- `BIELA_CURTO_F12_HERO.mp4`: **`9fa2f51843219339b870b4d69c5312049e30317d1032d03ff802ce20b0693a72`**.
- `BIELA_LONGO_F12_HERO.mp4`: **`c578a8a419307b6d8abdb7f387a120d7392a888592255de7f7ba4c3d2155c40c`**.

Todos: **9s / 540×960 / 24 fps / sem áudio / não publicados**. `COMPARATIVO_F11_VS_F12_12_QUADROS.jpg` (1080×1440), folhas F11/F12 de UI simulada e `QA_F12.json` verificados. Mudança média RGB de frame H264 antes→depois em 4 instantes: 42,862 / 41,204 / 40,537 / 41,494, o que confirma reorganização VISIBLE do layout, não qualidade artística.

## Cobertura simulada por papel (pior caso amostrado: 1,1s / 3,6s / 6,7s)

| Papel | Curso curto F11 | Curso curto F12 | Curso longo F11 | Curso longo F12 |
|---|---:|---:|---:|---:|
| Pistão | 25,61% | **17,07%** | 31,58% | **19,90%** |
| Biela | 100% | **22,81%** | 100% | **42,01%** |
| Volante | 100% | **58,10%** | 100% | **58,38%** |
| Correia | 100% | **51,16%** | 100% | **52,13%** |

As porcentagens foram calculadas **apenas com máscaras conservadoras ESTIMADAS do nosso `plataformas.json:ativos_seguros`**, sobre pixels de ator efetivamente renderizados, e representam máximo de três amostras por peça. Não representam cobertura real garantida do TikTok/Reels/Shorts. A versão F12 não encolheu a máquina e melhorou visivelmente a leitura das polias, mas **não cumpriu uma homologação mobile**.

## Inspeção visual franca da prancha

- Ganho perceptível: conjunto máquina sobe no vídeo e aparece mais cedo/alto; cobre menos a zona inferior crítica e conserva tamanho de pistão/volante. Câmera não balança.
- O cabeçalho menor está mais carregado de informações tipográficas. A composição ainda parece **diagrama didático**, não representação realista/industrial pronta para o Coringa.
- Nos overlays simulados, a **faixa superior inteira do cabeçalho ainda é considerada coberta** pela política conservadora (topo 240–280 / 1920 equivale a 120–140 / 960). Logo, NÃO afirmar que a identidade/título ficaram seguros, mesmo que as peças melhoraram. Uma safe zone universal plena para conteúdo essencial não está demonstrada.
- A faixa inferior do palco ficou bem mais vazia; isso é intencionalmente espaço para legendas e UI, mas precisa ser validado contra screenshot real para não prejudicar estética/ritmo. Parte do volante/correia continua interceptando a coluna direita e/ou a faixa inferior nas máscaras conservadoras.
- A melhora de composição NÃO representa capacidade de pesquisar qualquer máquina e criar automaticamente modelos 2D/3D. Não instalar novamente versões antigas minúsculas.

## Próximo gate: F13

**Antes de diminuir fonte, máquina ou sobrepor legendas:** usar screenshots **reais e atuais** dos aplicativos (celular, vídeo, legenda/ícones visíveis) para calibrar uma política de UI por tipo de enquadramento; comparar com estes mesmos 3 MP4s e aceitar apenas se título, ação e legenda tiverem evidências. Se as zonas de risco forem incompatíveis, usar tomada com máquina maior, orientação de texto alternada e um enquadramento editorial que não exija miniaturizar o objeto.

Prosseguir depois para identidade industrial/peças reaproveitáveis com direitos e geometria verificados. A F9 Wikimedia segue bloqueada por HTTP 429, sem SHA do original. `main`, NTC, DOSSIÊ, Telegram e sistemas produtivos permanecem intocados. Aprovação estética e publicação **FALSAS/BLOQUEADAS**.
