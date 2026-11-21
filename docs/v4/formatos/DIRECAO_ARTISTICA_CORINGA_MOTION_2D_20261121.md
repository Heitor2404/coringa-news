# CORINGA MOTION 2D — nova direção artística proposta (21/11/2026)

**Estado:** PROPOSTA PARA STORYBOARD, ainda NÃO aprovada como padrão e NÃO implementada no renderizador de produção.
**Escopo:** apenas o MOTOR DOCUMENTAL ATLAS, branch experimental `atlas-direcao-visual-20261118`; não mudar main, NTC, DOSSIÊ ou publicar. Nenhum token do Claude necessário.

## Por que a direção anterior foi reprovada
Feedback explícito do usuário ao ver alavanca, polia e engrenagens: objetos continuam muito pequenos e a estética é sem graça. Antes, também reprovou o visual de cartão, diagrama tecnológico azul, fundo genérico e mecanismos cortados/desconectados. **Testes físicos/CI dos três mecanismos passaram; são um laboratório de causalidade, não um produto visual aprovado.** A nova direção NÃO deve recomeçar a física do zero.

O print do usuário é da interface de prévia/edição do Instagram (ex.: botão `Avançar` e timeline inferior). Ele demonstra percepção de espaço mal utilizado, **não garante os pixels exatos do overlay do Reels publicado**. Não converter a imagem em máscara oficial; usar perfis `src/v4/formatos/plataformas.json` + teste com sobreposição real em dispositivo, inclusive legendas.

## Direção escolhida: ilustração 2D editorial CINEMÁTICA

**Referências com papéis separados, não cópia de suas obras:**
- **Kurzgesagt**, referência de energia da ILUSTRAÇÃO: silhuetas marcantes, cores vivas, grupos visuais expressivos, transformação 2D com sombra e volume simples. A produção integral é artesanal e extensa — não tentar copiá-la nem usar personagens, paleta exata ou layouts reconhecíveis.
- **Vox**, referência de DIREÇÃO: montagem por acontecimento, corte narrativo com continuidade, tipografia de impacto, destaque que nasce do objeto ou fato. Não copiar o branding, fotos, mapas ou composições.
- **The Efficient Engineer**, fonte da CLAREZA CAUSAL já analisada a partir de `videoplayback 3.mp4`: o mecanismo permanece e novas peças/forças são introduzidas sem desmontá-lo.
- **3Blue1Brown**, fonte da ENGENHARIA DE ESTADOS já analisada a partir de `videoplayback 4.mp4`: objeto físico, valores e gráficos derivam do mesmo estado matemático.

**Linguagem autoral almejada:** `CORINGA MOTION 2D`, nome interno provisório, NÃO marca nova. Mistura 2D vetorial ilustrado e motion editorial. Formas têm materialidade leve (2–3 tons de sombra, contorno e oclusão), mas sem pedir modelagem 3D. O amarelo `#FFD21F` pertence a destaques/atos; não pintar tudo de amarelo. Fundo definido PELO AMBIENTE DO FENÔMENO — água da eclusa, luz/óptica do EUV, metal/ambiente de máquina — e não um background tecnológico fixo ou papel bege em todos os temas. Isso exige biblioteca de fundos de contexto por capacidade, NÃO um designer diferente por episódio.

### O que deve surpreender no primeiro segundo
**Mostrar o acontecimento imediatamente**, não título em cima de uma máquina pequena: p.ex. navio começa a subir enquanto a água entra, engrenagem menor impulsiona a maior; a pergunta entra integrada ao movimento, no máximo duas linhas, depois se recolhe. Se a explicação exige estado inicial, abrir com o resultado e voltar com transição clara para a causa. O objetivo é visual compreensível, não efeitos vazios.

### Gramática repetível, independente de tema
1. `hook_visual`: fenômeno em ação grande e inteiro, situação intrigante, 0–1,2s. Evitar tela só com texto ou logo.
2. `reveal_context`: câmera reenquadra para mostrar origem/destino das forças e todas as peças causais essenciais.
3. `activate_actor`: peça muda estado e ativa animação da conexão. A mesma propriedade controla posição/fluxo/flecha/ponto de contato.
4. `cause_effect`: movimento da causa alcança a consequência por fio, tubo, arco, luz, dente, etc. Nunca deslocar objetos de forma independente e fisicamente inconsistente.
5. `payoff`: dado curto, mudança de estado ou comparação com forte contraste visual; não card genérico no rodapé.
6. `next`: passar à próxima causa com match de objeto ou corte editorial legível; sem glitch ou zoom aleatório.

**Direção de atenção:** ator principal em cores saturadas, demais em contraste reduzido mas visíveis. Duas ou três camadas para profundidade ilustrada, sombra direcional discreta, não neons/grades/glows decorativos. Flechas apenas enquanto existe movimento/força; rótulos junto às âncoras dos objetos e legíveis no celular.

### Ocupação vertical sem sacrificar informações
- **Não encolher a máquina toda para o retângulo universal**. Os textos críticos e as relações causais essenciais devem ser protegidos por máscaras reais dependentes da altura `y`. O desenho de contexto pode ocupar tela cheia; segmentos essenciais não podem cair sob os botões/legendas.
- **Meta visual de design, NÃO regra universal rígida:** no plano de demonstração, o conjunto principal deve usar tipicamente cerca de **70–85% da largura visual disponível naquele intervalo vertical**, se isso não amputar peças. A cena deve aproveitar a altura com relações causa→efeito, evitando um bloco de 400px rodeado de vazio. O fiscal mede `bbox(actor_essencial)`, `bbox(conexoes)` e `bbox(textos)` por frame/etapa, NÃO só uma porcentagem bruta.
- Parte superior: título curto como overlay temporário, diminui quando o mecanismo precisa de espaço; marca secundária e discreta. Centro: protagonista/ação e conexões. Região inferior: legenda/crédito protegidos; detalhes **não essenciais** podem continuar full-bleed no fundo, sem imitar uma máquina ou fluxo inexistentes.
- A captura de editor enviada não é prova da UI final de Reels; antes de publicar: overlay instrumentado e inspeção na plataforma. Um limite x fixo para toda a altura pode desperdiçar espaço; nenhum layout deve depender de coordenadas presumidas do print.

### Variações permitidas SEM trocar a identidade
- `editorial_clear`: fundo claro com cores fortes e sombras, somente quando ajuda a distinguir atores; não voltar ao bege uniforme com caixa cinza.
- `editorial_dark`: noite/ambiente escuro com objetos coloridos, sem grade tecnológica, brilho só quando existe luz real (EUV).
- A escolha depende do fenômeno e do contraste em celular, não do gosto do prompt em cada render. Estrutura editorial, tipografia e movimento são os MESMOS nas duas variantes. **Não migrar automaticamente** o código claro de alavanca/polia/engrenagens para o motor produtivo.

## Provas que devemos produzir antes de IMPLEMENTAR outro renderizador

**Fase 0: referências e gramática (ESTA ETAPA)** — estudo dos dois vídeos enviados e benchmark de Vox/Kurzgesagt. Resultado: documento de direção + storyboard da mesma ação para 2 temas distintos. Não declarar protótipo visual entregue se só existe texto.

**Fase 1: storyboard A/B de 4–6 quadros**, com mesmo roteiro/física:
- **Eclusa:** (a) navio parcialmente elevado (gancho), (b) corte mostrando os dois níveis + ligação hidráulica, (c) válvula abre/fluxo entra, (d) navio SOBE JUNTO com a água, (e) portão abre. Um mesmo mecanismo espacialmente contínuo; narração/legenda simuladas e overlays Reels/TikTok/Shorts. Quadros bonitos, mas COM conexões fisicamente plausíveis.
- **EUV:** (a) padrão aparece no wafer (gancho), (b) fonte e máscara refletiva em contexto, (c) espelhos refletem e dirigem, (d) wafer recebe a exposição; um único trajeto óptico didático, rotulado esquema. Não usar fontes de eclusa em EUV.
- Cada quadro tem **um mock de UI** sobreposto e outro limpo. Não gerar vídeo grande antes da escolha visual do usuário.

**Fase 2: prova de 6–10s com uma máquina** após aprovação do storyboard, reuse `Mechanism2DCore`, `actors`, `connections`, `events` e não cria 3D. Fazer duas versões A/B apenas se comparáveis, não 15 estilos.

**Fase 3: generalização mínima** a outra família física independente, sem reescrever o tema. Alavanca, polia e engrenagens atuais funcionam como regressão da física; eclusa e EUV testam causação de água e luz. Novo mecanismo sem primitivas é bloqueado, não descrito com cards para disfarçar ausência.

## Critérios de avaliação — aprovação em duas dimensões independentes

**Engenharia:** sem objetos cortados, relações físicas conectadas, estado estável, fontes corretas, bbox protegido, testes tipográficos e de timeline, custo sob teto conhecido; falhas bloqueiam. **Estética:** desenho com escala dominante, um foco claro a cada beat, movimento expressivo sem falsear física, informação legível no tamanho de celular, ausência de fundos/overlays genéricos e de “cara de apostila”. É necessária avaliação humana do usuário após ver **storyboards** e **clipe**; CI verde sozinho nunca autoriza `VISUAL_OK`.

### Aposentadorias desta rodada
**Reprovados como identidade visual:** `MechanismsImmersive.tsx` fragmentado em dois painéis e `Mechanism2DPaperStudio.tsx` / `LeverMechanism2D.tsx` em aparência atual de apostila. **Preservar física/testes** e deixar composições privadas; não apagar ferramentas válidas ou migrar o problema para outro projeto. Nada deve ser publicado ou enviado automaticamente ao Telegram antes de QA audiovisual final.

## Fontes públicas e limite de cópia
- Página oficial Kurzgesagt: https://kurzgesagt.org/what-we-do?visit=videos — vetor vibrante e produção pesquisada; **não usar assets/cenas/propriedade visual reconhecível de terceiros sem licença**.
- Entrevista Vox com diretor de arte: https://www.storybench.org/how-vox-uses-animation-to-make-complicated-topics-digestible-for-everyone/ — animação ligada à narrativa e à atenção.
- Vídeos de referência enviados pelo usuário já estudados e documentados em `REFERENCIA_MOTOR_2D_EFFICIENT_ENGINEER_20261121.md`; a mídia não deve ser copiada ao GitHub.
