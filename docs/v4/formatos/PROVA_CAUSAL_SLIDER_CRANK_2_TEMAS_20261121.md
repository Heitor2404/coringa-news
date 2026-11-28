# ATLAS A — primeira prova animada causal reutilizável (21/11/2026)

**Status:** prévias PRIVADAS, sem voz, sem Telegram, sem publicação. Não aprova direção artística nem produção.

## Decisão

A busca de referências e cinco quadros de navio não explicavam mecanismo. Em vez de nova rodada de cartões/correções da eclusa, criamos um demonstrador animado **com física aplicada de verdade**, testando duas máquinas com o MESMO renderizador e **sem TSX por assunto**.

- `motor4/remotion/src/formatos/SliderCrankRig.ts`: estado geométrico puro *slider–crank*: para ângulo θ, pino do eixo `(cx+r sinθ, cy−r cosθ)`, pino do pistão `(cx, cy−r cosθ−√(L²−r² sin²θ))`. Assim biela mede `L` em todos os frames, pistão permanece no eixo do cilindro e pino gira no raio `r`.
- `motor4/remotion/src/formatos/slider-crank-proofs.json`: dados e geometria de dois assuntos diferentes. **Motor a combustão:** demonstra o tempo de expansão que empurra o pistão e gira o eixo, sem afirmar representar todos os quatro tempos. **Compressor alternativo:** eixo gira e movimenta pistão, com admissão, compressão e saída de ar; válvulas representadas simplificadamente. O mesmo motor varia raio, comprimento de biela, ordem de destaques, portas e cores a partir de dados.
- `motor4/remotion/src/formatos/SliderCrankProof.tsx`: única cena SVG ilustrada 2.5D, com cilindro aberto, biela real ligada a pinos, volante rotativo, passagens de ar nos casos pertinentes, gás, 4 etapas com legendas e textura industrial. `motor4/remotion/src/Root.tsx` registra `ProvaA-Pistao` e `ProvaA-Compressor` privadamente, sem integrar `FilmeEditorial` nem catálogo do motor oficial.
- `tests/test_slider_crank_multitema.py`: matemática e invariantes ao longo de 254 frames, geometria distinta, seleção de etapas, safe zones e isolamento da produção.
- `.github/workflows/qa-slider-crank-multitema.yml`: tipagem TypeScript + testes Python, **dois MP4s** de 8,4 segundos/30 fps/540×960 e dez quadros de contato, mais simulação das três interfaces.

## Prova executada

- **GitHub Actions SUCCESS:** [run 44944893961](https://github.com/Heitor2404/coringa-news/actions/runs/44944893961).
- **Artifact:** `14723236851`, `qa-slidercrank-2temas-privado`; expiração 26/11/2026 20:12 UTC.
- Filmes: `pistao_A_PRIVADO.mp4` (8,4s, 540×960, ~283 kB) e `compressor_A_PRIVADO.mp4` (8,4s, 540×960, ~294 kB); SEM áudio.
- Contato: `contato_pistao_compressor_10quadros.jpg`. Segurança: `areas_seguras_3redes.jpg`; UI **simulada**, não foto real das redes.
- Alteração de quadro na região da máquina, de 0,4 para 3,6 s: motor ~29,71 RGB; compressor ~30,72 RGB. É prova grosseira de movimento, NÃO qualidade estética.
- A revisão humana dos dez quadros indica que a peça desenhada de fato muda posição e a biela continua ligada ao pino do virabrequim em ambos os assuntos. A legenda destaca fases distintas em cada assunto.
- **Erro corrigido durante o trabalho:** um cast de JSON para `Model` causou falha TypeScript e três workflows legados na branch naquele commit intermediário. Tipagem corrigida; workflow final acima compilou projeto inteiro.

## Auditoria crítica

**O que agora foi comprovado:**
1. Vídeo dinâmico e mecanismo central, NÃO cinco imagens sem explicação.
2. Relação física pistão–biela–virabrequim matematicamente conservada por toda a duração; não são 3 animações independentes.
3. Mesma cena e mesmo rig, dois temas, geometria e direção física de causa diferentes.
4. Testes e vídeos reais em arquivo, sem cota Claude e sem intervenção em `FilmeEditorial`.

**O que NÃO está comprovado:**
1. **Não existe ainda** reconstrução automática a partir de animação encontrada na internet, pois GIFs externos continuaram bloqueados HTTP 429. Esta prova foi elaborada a partir do princípio físico conhecido e referências técnicas públicas, não de extração multimodal de vídeo externo.
2. Ainda há simplificações pedagógicas: modelo de motor apenas tempo de expansão, e compressor não implementa dinâmica de pressão termodinâmica e válvulas realistas. Física da biela exata; termodinâmica não simulada.
3. Arte ainda é **esquemática** e sem som; fundo inferior bastante vazio para preservar safe UI conservadora. Vídeos NÃO prontos para postar.
4. Apenas uma **família** (slider-crank) foi demonstrada com duas aplicações. Para outro mecanismo físico é necessário adicionar operador/família sem criar exceção por tema.
5. QA estrutural verde não substitui aprovação estética e didática do usuário.

**Critério de progresso seguinte:** usar a própria estrutura de dados e runtime para um segundo par de fenómenos de outra família física (por exemplo, fluxo/valvulação e alavancas) sem TSX por episódio; melhorar o acabamento global e a câmera de atenção de TODOS os mecanismos, não `motor` em particular. Integrar o grafo de cenas causal com referências analisadas quando houver originais acessíveis.

## Referência técnica de cinemática

O mecanismo slider-crank é empregado em motores, bombas e compressores; fórmulas de geometria no plano: [Slider-Crank: Exact Kinematics](https://jd-jones-ases.github.io/Mechanic/things/slider-crank/) e [Mech Codex: Slider-Crank](https://mechcodex.com/learn/machine-design/slider-crank).

**Escopo técnico protegido:** branch `atlas-direcao-visual-20261118`; sem alterações da produção, main, NTC, DOSSIÊ ou Telegram.
