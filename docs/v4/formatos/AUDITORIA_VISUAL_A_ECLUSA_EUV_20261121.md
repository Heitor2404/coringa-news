# Auditoria visual independente — direção A / Eclusa e EUV (21/11/2026)

**Contexto:** novo chat após `docs/CONTINUIDADE_PROXIMO_CHAT.md`. Feedback explícito do usuário: **eclusa: estilo agradou, mas a animação está muito bugada; EUV: não corresponde em nada ao estilo A escolhido e também está bugado**.

**Escopo:** análise dos MP4s verdadeiros do run `44911687311`, artifact `14709649130` (até 26/11); branch `atlas-direcao-visual-20261118`, commit testado `1277530d7306a39ac014b43f79decb847b69b9d1`. Cada vídeo tem **7,8 s, 540x960, 30 fps, sem áudio**. Inspecionados os vídeos, as dez capturas e `AtlasAProof.tsx`, `AtlasAStudio.tsx`, contrato JSON e testes. Não são versões de produção. Este documento **não altera código**.

## Veredito
- **Eclusa:** a ilustração colorida, o cargueiro dominante e o corte do terreno são **um ponto de partida visual que o usuário gostou**, não uma aprovação do vídeo. Há defeitos de ritmo, condução causal e arte física.
- **EUV:** **reprovado no visual e na legibilidade**. Sua composição conserva a ideia de fonte/máscara/espelhos/wafer, mas a execução é um diagrama de elipses/linhas sobre um painel escuro. O mesmo shell de título não significa que ambos tenham o mesmo acabamento A.
- **QA:** CI `SUCCESS` significa compilação/renderização e invariantes estáticas; não existe aprovação visual, física detalhada, interface real ou publicação. Preservar `FilmeEditorial`, main, NTC e DOSSIÊ.

## Defeitos comprovados e causas no código

### Eclusa
1. **Hook promete movimento que não acontece.** A cue `UM NAVIO SUBINDO NA ÁGUA` aparece em t=0, mas o enchimento `lockState.fill` só começa no evento `inlet` em **t=2,35s**. O primeiro terço é essencialmente estático. Os eventos `rise` e `hook` mudam o texto sem conduzir o início da ação.
2. **Circuito hidráulico com representação pouco natural.** O único caminho `M166 878 V1440 H355 V993` é tecnicamente contínuo no SVG, mas foi desenhado no primeiro plano e aparece como grande U luminoso no terreno; a transição visual para a câmara/galerias não comunica com clareza a passagem de água pela parede/piso.
3. **Final não resolve a narrativa espacial.** `gateShift=open*57` e `boatTravel=open*20` quase não deslocam a comporta/navio. O clipe termina sem mostrar saída ou transição da embarcação, embora o nível se iguale. Não declarar ciclo completo da eclusa demonstrado.
4. **Área inferior pouco funcional:** muito estrato de solo para pequena quantidade de informação útil; texto sobrepõe parte do mecanismo na faixa central. Melhorar linguagem de corte contextual sem criar objetos novos por episódio.
5. **Qualidade ilustrativa irregular:** casco, ponte e contêineres são primitivos SVG; a cena ainda não atinge o acabamento previsto pela concept art A.

### EUV
1. **Sobreposição real de texto.** `AtlasAProof.tsx` põe `WAFER · RESINA FOTOSSENSÍVEL` em **y=1181**, e `AtlasAStudio.tsx` coloca cue absoluta começando em **top=1090** com extensão que intercepta o rótulo. Sobreposição visível desde 0,4 s até etapas posteriores.
2. **Hook sem correspondência visual.** A cue inicial diz `UM PADRÃO NASCE NO WAFER`, mas `euvState.resist` só começa em **t=5,1s**. Durante o primeiro segundo a máquina fica basicamente parada, sem revelar o acontecimento prometido.
3. **Reflexão ambígua.** Os dois raios usam o vértice `(513,664)`; esse ponto fica **dentro da área desenhada da máscara inclinada**, não inequivocamente na superfície refletiva. O código busca reflexão, mas o quadro não comunica um contato ótico inequívoco. Refinar como metáfora 2D validada, sem fingir desenho real de máquina ASML.
4. **Não há acabamento A compartilhado:** ótica feita de elipses simples flutuantes, wafer como disco, máscara como barra e carcaça inferior como retângulo de máquina. Sem profundidade, oclusão, materialidade ou ambientação persuasiva análoga à eclusa.
5. **Tela ocupada por decoração:** carcaça inferior tem muitos traços/parafusos e quase nenhuma informação causal, enquanto conectores e objetos críticos ficam comprimidos acima.

## Falha de arquitetura/QA observada
O shell `AtlasAStudio` compartilha título/paleta/cue, mas as artes físicas são dois SVGs artesanais independentes `LockActors` e `EuvActors`, escolhidos por um `kind==='lock' ? ... : ...`. **Não há biblioteca visual/semântica suficientemente compartilhada para generalizar estilo entre temas.**

Os testes `tests/test_atlas_a_visual_lab.py` passam por asserções de **strings do código** (path, scale, texto), valores sintéticos e caixas declaradas. Não medem as bounding boxes renderizadas de todos os textos/atores nem a promessa semântica de cada cue. Daí CI verde com sobreposição óbvia.

## Próxima etapa técnica recomendada
1. **Parar de mexer só em zoom/safe e em detalhes avulsos.** Definir um **kit de ilustração A reutilizável**: atores, superfícies, materialidade, perspectiva/oclusão, sombras, cenário contextual, conectores, etiquetas ancoradas, densidade e coreografia de movimento. Shell editorial sozinho não basta. Arte no SVG/Remotion é viável, mas haverá biblioteca de capacidades físicas distintas, não geração irrestrita.
2. **Corrigir o sistema de eventos antes de polir arte:** `hook` deve representar um estado ativo demonstrado; `cue` e fonte não podem encobrir o objeto; cada beat exige mudança visível medida; a causa→efeito deve percorrer conexões (eclusa) e interfaces reflexivas (EUV).
3. **Reconstruir EUV COM O MESMO KIT A da eclusa**, não apenas pintar diagrama de roxo; redesenhar fonte, máscara reflexiva, espelhos, wafer e carcaça como ilustração contextual, mantendo plausibilidade física e os mesmos princípios de volume/camada que funcionaram na eclusa.
4. **Novo portão automatizado:** extrair frames de cada beat e checar interseção em pixels das caixas de rótulos/editorial, bbox de atores essenciais, clipping, alinhamento da ação com a cue, movimento significativo por beat e cenários não apenas decorativos. Falha automática em colisão do rótulo do wafer. Testar safe por altura nas três redes com legenda real depois.
5. **Gate multitema:** passar em eclusa, EUV e mais uma família diferente sem alterações de regras ad hoc do episódio. Inspeção humana de MP4 antes de qualquer integração ao `FilmeEditorial`.

**Decisão de produto:** direção A permanece a referência. **Eclusa = base estética promissora mas execução reprovada; EUV = identidade e execução reprovadas**. Sem promoção de status, Telegram ou publicação.
