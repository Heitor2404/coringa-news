# Referência visual 2D-first — estudo do vídeo fornecido (21/11/2026)

**Estado:** DIRETRIZ DE DESIGN PARA EXPERIMENTAÇÃO, não código homologado e NÃO autorização de publicação.
**Origem:** vídeo enviado pelo usuário neste chat, `videoplayback 3.mp4` (15min53s, 640×360, 24fps), do The Efficient Engineer: *How Levers, Pulleys and Gears Work*.
**Nota de rigor:** observações abaixo decorrem da inspeção do vídeo em intervalos regulares e em amostras densas dos três trechos mecânicos. Não houve transcrição completa da voz nem teste de sua sincronização palavra a palavra. Os timestamps são aproximados. O material mistura elementos 2D, aparência 3D/2.5D e objetos renderizados: NÃO classificar a obra como 2D puro.

## 1. O que de fato funciona no vídeo (observação, não especulação)

| Trecho aproximado | Observação verificável | Técnica transferível |
|---|---|---|
| 0:00–1:35 | Introdução com guindaste de aparência 3D, fórmula de vantagem mecânica, breves engrenagens e sistema hidráulico com material/volume. Não é padrão 2D leve. | Evitar tentar reproduzir 3D detalhado; a demonstração é apoiada em relações força→movimento |
| **1:35–4:45 — alavancas** | Barra isolada, entra fulcro, massa e seta de esforço. A barra passa a girar; flechas de momento, distâncias, equação e resultado surgem sobre a MESMA alavanca. Depois compara posições do apoio. | **Referência principal:** construção progressiva de uma cena persistente, novos fatos no mesmo espaço, cada marca/medida responde a uma pergunta |
| **4:50–8:55 — polias** | Polia aparece primeiro, depois corda/carga; substituição gradual por configurações móvel e composta. Setas mostram tração e segmentos sustentando carga, números de vantagem mecânica só quando a configuração justifica. | Introduzir complexidade incrementalmente; preservar conexões visíveis entre corda, polias e peso enquanto a força muda |
| **9:00–13:05 — engrenagens** | Par grande/pequeno com cores distintas; número de dentes; torque/direção; engrenagens com eixos; setas, equação e comparação de saída; engrenagem intermediária. | Mesmo mecanismo recebe camadas de significado, não quadros independentes. Cor identifica partes, flechas explicam direção e resultado |
| 13:05–13:50 | Exemplos/artefatos em render mais realista. | Úteis como contexto, mas não necessários ao motor de diagramas |
| ~13:50–15:53 | Passa a vídeos/sites e publicidade/encerramento. | NÃO copiar a dinâmica de publicidade, planos com marca, nem o encerramento para nossas demonstrações |

### Vocabulário visual observado
- Fundo consistente de aspecto texturizado azul-marinho com manchas quentes terrosas ao longo das três demonstrações. Funciona porque a cena física é a protagonista; NÃO reproduzir exatamente a textura, cores nem enquadramentos do criador.
- Objetos bem separados do fundo por contraste, sombreamento e volume simples. Alavanca de madeira, fulcro ciano claro, engrenagem amarela vs roxa e seta verde ilustram diferenciação de funções.
- **A informação visual entra quando há causa visível:** seta de esforço só depois da alavanca montada; torques/medidas só depois do movimento; vantagem numérica só após a configuração que a sustenta.
- Câmera em geral pouco movimentada durante o mesmo mecanismo; movimento principal acontece nos objetos, nas setas e nos estados. Transições de assunto são legítimas, mas não se deve substituir toda a cena a cada frase.
- Algumas letras e fórmulas são muito pequenas já em 640×360 e ficariam ilegíveis em 9:16 com sobreposição de UI. Nossa versão deve simplificar e aumentar os rótulos, NÃO transplantar o mesmo layout 16:9.

## 2. O que COPIAR como princípio e o que NÃO copiar

**Adotar princípios de linguagem** (não expressões protegidas):
1. Persistência espacial: cada objeto introduzido mantém identidade e posição relativa enquanto participa do mecanismo.
2. Entrada progressiva: o motor pode começar com só uma peça e introduzir outras. Depois de introduzida, ela não some sem causalidade ou transição explícita.
3. Um **grafo causal de objetos e conexões** dirige a animação, e não uma lista de cartões.
4. Física causa o movimento: a alavanca gira ao redor do fulcro; massa segue a corda; engrenagens ligadas giram em razão inversa dos dentes; o navio flutua no nível da água; feixes seguem o caminho óptico ilustrado.
5. Anotações vêm como camadas vinculadas ao ator: setas, medidas, palavra curta e resultado, com prioridade da ação, não como objetos de decoração.
6. Movimento moderado, temporalmente legível; não inventar zoom, splash ou glitch para tapar falta de acontecimento.

**Não reproduzir:** desenhos e cenas exatos, textura/grunge característica, asset de engrenagem, branding, música, locução, enquadramentos ou frames como material publicável. As capturas servem só de referência interna. Não assumir licença para copiar, nem caracterizar o vídeo como domínio público.

## 3. Contrato proposto para o MOTOR DOCUMENTAL 2D

**Decisão de produto:** `mechanism` 2D-first em Remotion/SVG com leve `2.5D` (gradientes/oclusão/sombra) quando indispensável. Não introduzir Blender/Three.js como dependência de produção, nem confundir este formato com NTC vetorial. Não tocar main, NTC ou DOSSIÊ durante experimentos.

### A. Cena persistente = um grafo físico
Modelo de dados conceitual, não implementação imediata:
- `actors`: objetos, materiais, bounds, papel físico, âncoras;
- `connections`: `supports`, `hinged_at`, `rope_links`, `pipes_to`, `meshes_with`, `reflects_to`;
- `state`: posição, orientação, nível, progresso de transferência, válvula/porta;
- `events`: mudança física observável com tempo aprovado pelo diretor/roteiro;
- `annotations`: entidades semânticas ligadas a ator/âncora e a evento específico.

Essa estrutura não gera qualquer mecanismo do zero por magia. **É biblioteca crescente de primitivas físicas**; se faltar capacidade, fiscal bloqueia, não inventa seta ou usa card para fingir ação.

### B. Gramática de animação
`introduzir` → `conectar` → `acionar` → `revelar_consequencia` → `explicar` → `comparar` / `concluir`. A ordem precisa fazer sentido com o fenômeno. Atores podem começar ocultos antes de serem introduzidos; uma vez conectados, só podem sair com transição justificada.

### C. Direção e texto
- A narração decide o que observar, mas NÃO comanda geometria fictícia.
- A câmera pode enfatizar sem destruir contexto. Se uma ligação essencial sai de quadro, usar inserto contextual com ponte visível, ou não aproximar.
- Título forte e breve; rótulos curtos e bem maiores do que os do vídeo 16:9; 1 mensagem semântica por beat. Medidas e equações somente quando necessárias à explicação.
- Fundo do Coringa: superfície original escura de baixo contraste, textura/material mínimo e **sem** grid, elipses gigantes, objetos abstratos ou halos sem relação física. O fundo existe para destacar o mecanismo.
- Cores descrevem PAPEL (água, luz, peça motriz, peça conduzida, bloqueio, ação em curso). Paleta ATLAS amarelo e grafite como base; uma cor ciano/azul para meio físico quando apropriado. Não copiar as cores específicas de cada objeto da referência.
- A física importante e rótulos indispensáveis devem sobreviver às zonas de UI TikTok/Reels/Shorts. As máscaras orgânicas são estimativas; exigir prova em dispositivo. Não reduzir cena inteira à caixa de x150..770 nem fingir que objeto crucial fora dela está protegido.

## 4. Como aplicar às nossas duas provas

### Eclusa (mecanismo único, nunca dois cards)
- Desenhar **mesma** câmara, água, portões, reservatório, conduto, válvula e navio ao longo da cena; conexões físicas permanecem reconhecíveis.
- Revelar causa em ordem: estado inicial/níveis diferentes → válvula abre → fluxo gravítico pelo fundo → água sobe → barco flutua junto → equalização → portão abre e navio sai.
- Não mostrar barco subindo sem água, nem fluxo pela parede/portão, nem camadas fora do palco.
- Se um detalhe da válvula for ampliado, uma ligação visual explícita deve indicar onde pertence no corte completo. Não separar em painéis independentes.

### EUV (diagrama ilustrativo, não simulação exata da máquina)
- Manter fonte, máscara reflexiva, trajeto por óptica e wafer em um espaço de processo **conectado**.
- Luz aparece/avança → padrão da máscara atua → espelhos direcionam → wafer muda. Dar mais presença ao componente ativo sem sumir com os vizinhos necessários à compreensão.
- Não inventar trajetórias físicas precisas se a ilustração é didática e não está em escala. Informar que é esquema ilustrativo com fontes corretas da família, nunca crédito hidráulico numa cena EUV.

## 5. Prova mínima antes de mais commits

**Não fazer outro motor nem reabrir a regressão do palco largo.**

1. Fixar mesma linha narrativa e mesmos estados de duas versões A/B: `A` referência antiga contínua; `B` novo layout 2D contínuo vertical-first. Identidade gráfica de `B` original do Coringa.
2. Produzir **uma prova curta** contendo um fenômeno novo simples (alavanca) para testar generalização, mais eclusa/EUV como regressões. Se a máquina só reproduz demos codificadas, NÃO afirmar que gera qualquer tema.
3. Auditar frames no começo/meio/fim de CADA estado, posições de atores, continuidade geométrica, proporção ocupada de quadro, tipografia em celular, zonas por plataforma, procedência e sincronismo narração/legenda.
4. Aprovação visual humana independente do teste de código: marcações `ESTRUTURAL_OK`, `FISICA_OK`, `VISUAL_OK`, `SAFE_OK` e `PUBLICAVEL`; não promover se faltar qualquer uma das últimas etapas.
5. Manter `portrait_experiment` e o `MechanismsImmersive.tsx` atual como **reprovados** até substituição e inspeção; preservar o `reference_style_preview` só para comparação privada.

## 6. Parecer
O melhor trecho para emular como **SISTEMA** é a alavanca em **01:35–04:30**. O vídeo não ganha clareza por exibir vários cards, fazer uma câmera frenética ou encher o rodapé com decoração: ganha porque o espectador consegue acompanhar **o mesmo objeto mudando de estado**. Nosso padrão 2D deve priorizar essa gramática e ser um mecanismo autêntico sem copiar a estética autoral do canal de referência.


## 7. Comparação posterior — segundo vídeo enviado (colisões e π)

**Fonte estudada:** upload do usuário `videoplayback 4.mp4` de 21/11/2026, 26min07s, 640×360, 30fps, com áudio. Registro do vídeo explica contagem de colisões de dois blocos, relações 3, 31, 314, 3.141… conforme razão de massas; depois deriva energia/momento, plano de estados e geometria circular. A análise inspecionou quadros regulares de 30 em 30 segundos ao longo de todo o arquivo e amostra adicional de 10 em 10 segundos nos primeiros seis minutos. NÃO se trata de validação física rigorosa da derivação, nem de transcrição completa da locução.

**Observações concretas sobre o vídeo:**
- ~00:50–03:40: começa com apenas parede, dois blocos, plano de apoio e contador de colisões; varia massa e mostra 3/31/314/3.141… colisões. Posição dos atores e contador derivam de um estado único da simulação, sem remontar a cena a cada evento.
- ~03:40–04:30: insere registro de experimento físico e princípios de resolução de problemas, abrindo um novo raciocínio.
- ~04:40–06:15: acrescenta fórmulas de energia e momento com valores e setas ligados às colisões; o dado muda quando o estado físico muda.
- ~06:20–13:30: introduz plano de estados, curva e restrições geométricas. Mantém blocos na mesma tela, pequenos na base, para associar movimento observado e abstração matemática. A curva/diagrama recebe camadas sem fragmentar completamente o contexto.
- ~13:30–22:45: explora geometria circular, reflexões, arcos, ângulos e limites; grande parte da narrativa é predominantemente matemática abstrata. Elementos e textos finos pequenos em tela 16:9.
- ~23:00–26:07: retoma a contagem e apresenta conclusões/encerramento. Há trechos de slides muito simples e muito espaço preto.
- **Não é 2D puro em todos os frames:** os blocos e a parede têm sombras, perspectiva e aparência de volume simples, enquanto gráficos e fórmulas são vetoriais 2D. Essa aparência 2.5D é viável no Remotion/SVG.

### O que aproveitar (engenharia de animação)
1. **Estado canônico único:** `simulationState(t)` determina posição, velocidade, contador, restrições e destaque. Nada muda arbitrariamente porque mudou o card.
2. **Camadas sincronizadas:** o mesmo evento altera o objeto físico e também a seta, medição, número ou gráfico correspondente. A física é a fonte de dados da UI editorial.
3. **Transformações estáveis:** novas fórmulas e diagramas entram como explicação do estado que já existia, em vez de apagar tudo e recomeçar o desenho.
4. **Depuração visual:** seria útil permitir que os objetos declarem pontos de ligação, área segura, estado e transições verificáveis em testes.

### O que NÃO escolher como estética principal do Coringa
- Fundo predominantemente preto sem material ou ambiente: serve ao formalismo matemático, não demonstra sozinho bom acabamento documental.
- Letras/fórmulas muito finas e pequenas, insuficientes na tela de celular 9:16.
- Longos períodos com objetos pequenos no rodapé e gráfico distante; nossa UI orgânica agravaria essa limitação.
- Fórmulas, contadores e matemática abstrata aplicadas a todo tema, mesmo quando não esclarecem um fato.

### Decisão objetiva para o MOTOR
- **The Efficient Engineer = referência principal de composição, narrativa causal e hierarquia visual.** Não copiar imagens, texturas, fundo, modelos nem cenas.
- **Segundo vídeo das colisões e π = referência principal de engenharia de estados e ligação física↔dados.** Não copiar a estética preta, a tipografia matemática ou o ritmo de vídeo longo.
- **Não buscar uma terceira referência genérica agora.** Já há variedade suficiente para escrever um contrato e provar em uma alavanca simples, EUV e eclusa. Se a futura prova falhar por questão estética específica, pesquisar então uma referência de animação técnica vetorial 2D estritamente nesse aspecto.
- **Sem mudar ferramentas nem criar outro motor:** Remotion + React/SVG já são adequados. Manim é uma inspiração de abordagem, não migração.
- **Prova de generalização obrigatória:** biblioteca de objetos e relações + estados determinísticos (sem hardcode do tema). Se falta primitiva, bloquear e registrar capacidade faltante; não esconder ausência de animação com setas aleatórias.
- Essa decisão de referência NÃO autoriza publicar nem aprova o experimento `MechanismsImmersive`, reprovado pelo usuário.
