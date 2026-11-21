# STORYBOARD VISUAL — Coringa Motion 2D / eclusa e EUV
**21/11/2026 · branch experimental `atlas-direcao-visual-20261118` · NÃO PUBLICAR**

## O que foi realmente produzido

Três **folhas de concept art estático** (não foram feitas no Remotion):
- **A — infográfico saturado:** 6 painéis de eclusa + 6 de EUV, elementos menores e densidade alta de textos. Apenas comparação de direção, **não aprovada**.
- **B — eclusa cinematográfica:** 6 painéis de sequência vertical, cargueiro grande, ambiente canal, água e foco contínuo. Sem dizer que os quadros são geometria original de motor ou prova da elevação correta.
- **B — EUV cinematográfico:** 5 painéis, fonte → máscara reflexiva → espelhos → wafer → efeito, apresentando linguagem original vibrante, porém trajeto óptico e cores **apenas ilustrativos**.
- **Auditoria de UI:** uma folha com seis mockups (2 temas × 3 plataformas) sobre os painéis B. Máscaras derivadas da configuração `src/v4/formatos/plataformas.json`, `ativos_seguros`. Não usar screenshot do editor do Instagram como prova de UI publicável.

Os arquivos raster foram entregues como anexos de conversa, **não subidos ao repositório**; o GitHub conectado nesta rodada editou APENAS documentação. Paths de cópia da sessão: `/mnt/data/Coringa_Storyboard_A_20261121.png`, `/mnt/data/Coringa_Storyboard_B_20261121.png`, `/mnt/data/Coringa_Storyboard_EUV_20261121.png`, `/mnt/data/Coringa_Mock_Interfaces_20261121.jpg`. Estes paths não constituem links persistentes do GitHub. Se necessário no próximo chat, solicitar os anexos ou reconstituir conceitos; não presumir acesso a paths antigos.

**Nota sobre os mockups:** os painéis de concept art não eram literalmente 1080×1920. Foram ajustados por `contain` a 1080×1920, com laterais estendidas/desfocadas, *sem deformar o conteúdo original*; overlay vermelho mostra potenciais áreas encobertas, traçado verde a região aproximada. Portanto, **NÃO é prova final de cobertura em aplicativo ou um teste pixel-perfect de vídeo**. Qualquer próxima prova deve ser renderizada nativamente em 1080×1920.

## Comparação editorial independente

| Critério | A: infográfico saturado | B: cinematográfico |
|---|---|---|
| Tamanho do protagonista | Alterna entre close e diagramas menores | Cargueiro e componentes maiores, percebidos imediatamente |
| Clareza do mecanismo | Mais rótulos, tubulação e etapas, mas torna-se cheio | Mais emoção, mas alguns frames cortam a ligação física (problema a corrigir) |
| Copiabilidade do estilo para vetor 2D | Mais simples para setas/cortes, risco de virar cards | Mais desafiador com paisagem/camadas, possível via vetor com templates e oclusão |
| Legibilidade 9:16 | Texto excessivo e algumas métricas frágeis | Título grande, porém texto ainda desce para zonas cobertas |
| Decisão | **Referência técnica de cutaway** | **Candidato estético mais forte**, AINDA NÃO APROVADO |

**Parecer recomendado:** manter o **B** como direção visual provisória, aproveitando **do A somente a clareza das tubulações e do corte transversal**. Para escala automática, não fazer desenhos panorâmicos exclusivos de um episódio. O motor deve usar biblioteca de elementos + estados, com câmera e escala por acontecimento.

## Achados da revisão contra UI (bloqueadores de produção)

A composição B é visualmente mais chamativa que o modo claro, **mas falha no mock de UI**:
- Marca no topo e frases de conclusão na parte inferior ficam frequentemente sob as máscaras aproximadas.
- Wafer e rótulo podem avançar para o rodapé invadido; lado direito do equipamento colide com a coluna de ícones.
- A máscara conservadora interna considera por exemplo `instagram_reels_multiplataforma` topo 270px, base 672px e coluna direita 300px começando em y840; `tiktok_multiplataforma` topo240/base660/direita300/y840; `youtube_shorts_multiplataforma` topo280/base660/direita300/y840. As restrições podem variar com versões e dispositivos; **não são garantias oficiais**.
- Próxima arte deve trazer `hook`, título, fonte e legenda para o intervalo protegido correspondente; **não miniaturizar o mecanismo inteiro**. Cenário/água/paisagem podem ocupar full bleed, conexões cruciais não.

## Revisão factual obrigatória

**Canal Panamá — fonte oficial** `https://pancanal.com/en/history-of-the-panama-canal/` e `https://pancanal.com/en/design-of-the-locks/`:
- Lago Gatún está cerca de **26 m acima do mar**, alcançados através das eclusas do sistema, **não corresponde a dizer que UMA câmera sobe 26 m**. O quadro B rotulado como subida de 26m em uma única etapa deve ser reescrito/removido.
- Água provém do reservatório por **gravidade**, percorre galerias laterais/centrais e condutos sob o piso e entra por aberturas; na ilustração a conexão precisa aparecer. O navio flutua junto com a superfície; não atravessa parede ou se move como elevador mecânico.
- Quaisquer volumes por navio, comprimentos e tempos gerados automaticamente devem ser retirados até ter fonte contextual correta. O storyboard A criou números de aparência factual sem aprovação.

**ASML — fonte oficial** `https://www.asml.com/en/en/careers/working-at-asml/united-states/technical-field-optics` e `https://www.asml.com/en/technology/lithography-principles/lenses-and-mirrors`:
- Fonte EUV → iluminador → luz **REFLETE na máscara** → espelhos ópticos de projeção → exposição da camada fotossensível no wafer. Máscara transmissiva como vidro é FALSO para EUV.
- Raios roxos/neon usados em concept art são **metáfora gráfica**: EUV real é invisível ao olho humano. Não afirmar que qualquer feixe emitido é visível.
- Não inventar contagem fixa de espelhos, tamanho de estrutura em nm, geometria exata interna ou acabamento litográfico instantâneo de chip. O wafer recebe uma exposição; etapas posteriores completam a fabricação.
- O terceiro poster “B/EUV” tem um desenho com aparência de projetor tipo lente; **precisa ser redesenhado como espelhos refletivos**, preservando um caminho legível e fisicamente plausível.

## Roteiro visual mínimo a seguir, antes de programar vídeos

### Eclusa — 5 beats mantendo a mesma estrutura física
1. **Gancho:** navio claramente grande, já flutuando e subindo; título somente dentro do slot seguro.
2. **Contexto:** revelar câmara, níveis alto/baixo, portões e origem da água, mesma posição relativa.
3. **Causa:** válvula habilita passagem; água por gravidade pelo conduto **conectado** sob o piso; animação da mesma linha, sem salto de cenário.
4. **Efeito:** superfície sobe e navio acompanha pela flutuação; nível superior e inferior ficam mais próximos; não cortar o casco.
5. **Resultado:** igualdade do nível relevante; portão abre; navio segue. Nenhuma estatística não revisada.

### EUV — 5 beats mantendo o mesmo trajeto
1. **Gancho:** wafer ilustrado com padrão se revelando; não sugerir chip final pronto após exposição.
2. **Fonte:** luz EUV simbólica sai da fonte e passa pelo iluminador; contorno do trajeto começa a aparecer.
3. **Máscara REFLEXIVA:** caminho até máscara e sua reflexão fisicamente legível, NÃO atravessando a máscara.
4. **Espelhos e wafer:** caminho refletivo leva luz a incidir na camada fotossensível; um mesmo estado controla trajetos/ativação.
5. **Resultado:** padrão de exposição evidenciado, com texto `ESQUEMA ILUSTRATIVO`; créditos corretos da família EUV.

## Portões para o motor (NÃO cumpridos nesta rodada)
- [ ] Dois storyboards editáveis verdadeiramente `1080×1920` com os mesmos atores ao longo dos cinco beats.
- [ ] Mock com todos `ativos_seguros` e legibilidade de texto sem sobreposição crítica.
- [ ] Física revisada: corte da eclusa/galerias e reflexão EUV correta.
- [ ] Duas propostas estéticas comparáveis no **mesmo storyboard**, antes da escolha do usuário.
- [ ] Aprovação visual humana explícita.
- [ ] Só depois, animação curta no Remotion e extração de componentes reutilizáveis.
- [ ] Main, NTC, DOSSIÊ e Telegram permanecem intocados.

**Nunca interpretar as imagens geradas como render do motor ou como aprovação de Física/SAFE/PUBLICAÇÃO.**


## Feedback posterior do usuário — A preferida, A/B não são estilos distintos

**Feedback explícito 21/11/2026:** “Eu preferi a opção A, mas tbm achei elas praticamente o mesmo estilo”. **Esta declaração substitui a recomendação anterior do auditor de seguir B como referência de preferência.** A é a opção preferida pelo usuário entre os conceitos que viu, MAS NÃO foi homologada como identidade estética final nem está tecnicamente pronta.

**Diagnóstico do erro de comparação:** A e B repetem a mesma família de cores (azul intenso, amarelo), 2.5D/3D ilustrado, contraste saturado, tipografia e navio/óptica semelhantes. A diferença está basicamente na quantidade de informação e no foco de apresentação: A tem mais cortes, tubulação e rótulos; B amplia o personagem físico e coloca a câmera na ação. Isso NÃO é um teste válido entre duas direções de arte; é um A/B de **composição editorial** com a mesma arte. O usuário percebeu corretamente a falta de variedade.

**Decisão revisada:** usar A como referência de **clareza e demonstração do mecanismo**, priorizando cutaways e visualização da causa física; não copiar automaticamente os rótulos, estatísticas e erros da imagem. Para uma comparação estilística válida, produzir, no mesmo storyboard/temas e com as mesmas ações, uma segunda direção realmente distinta: **vetor 2D gráfico contemporâneo**, silhuetas recortadas, blocos de cor limitados, contraste forte, transições expressivas, quase sem renderização 3D nem néon. O design deve ser ilustrado originalmente e factualmente plausível; não copiar identidade de Kurzgesagt/Vox. Evitar uma terceira variação de azul/amarelo sem diferença de material/desenho. Fazer comparação de quadros específicos, não novos posters de estilos aparentemente iguais.

**Portões ainda abertos:** checar o físico de eclusa/EUV e os overlays por plataforma; produzir ao menos alguns quadros nativos 1080×1920 com mesma composição entre temas; confirmação visual do usuário antes de implementar animação. **Nenhum renderizador alterado ou publicado por este feedback.**
