# F15 — seleção estrutural de mecanismos por grafo tipado

**Data:** 23/11/2026, 11h08 BRT · **Estado:** validado TECNICAMENTE no laboratório. Seleção a partir de imagem/narração e homologação estética/industrial PENDENTES. Publicação e produção BLOQUEADAS.

## 1. Proposta resolvida

Um pedido descreve nós mecânicos (peças), arestas (tipo/direção da ligação), eventos necessários, parâmetros numéricos e evidência do princípio físico. O compilador `src/v4/formatos/compilador_topologia_f15.py` escolhe **apenas** entre duas famílias que efetivamente têm kernel e compositor:

- **`slider_crank_parametrico` (F7/F11/F13)**: rotor → correia → rotor → biela → pistão → cilindro, com eventos de descida e subida;
- **`external_spur_gear_reduction` (F14)**: roda dentada motora → roda dentada movida, com contato externo e eventos de engrenamento/redução.

A escolha é feita por isomorfismo exato de grafo com tipos de nó e junta, não pelo título, nome de episódio, IDs iguais aos do código ou heurística de palavras. Os identificadores dos atores podem mudar completamente. A montagem aplica **novos parâmetros** à cena de aparência curada da família escolhida e chama a validação e renderização verdadeiras daquele kernel.

**Não é** interpretação de linguagem natural, reconhecimento de objetos a partir de vídeos, reconstrução CAD/3D, pesquisa de referências, nem geração de mecanismo sem família implementada. Há reutilização de núcleos comprovados, mas **templates editoriais de cada família continuam explícitos**.

## 2. Implementação

- `src/v4/formatos/compilador_topologia_f15.py`: schema `coringa-topology-request-f15-v1`; registro de assinaturas tipadas, matcher de grafo com todos os atores/arestas exigidos, validação de eventos, fontes de equações e parâmetros; saída `coringa-topology-compiled-f15-v1` com SHA de pedido, mapeamento de atores, cena privada e `publish=false`.
- `src/v4/formatos/pedidos_topologia_f15/pedido_estrutura_biela_f15.json`: novo rig de biela configurado para **curso 100 px** (raio da manivela 50 px, haste 175 px), motor/correia e cabeçalho lateral F13. IDs arbitrários `eixo_motriz`, `transmissor`, `volante`, `haste`, `bloco`, `camisa`.
- `src/v4/formatos/pedidos_topologia_f15/pedido_estrutura_engrenagens_f15.json`: novo par **20/40 dentes**, módulo 5,8 px, entrecentros **174 px**, entrada 2 voltas por vídeo, relação 2:1. IDs arbitrários `lado_entrada` e `lado_saida`.
- `tests/test_compilador_topologia_f15.py`: invariância do roteamento sob mudança de IDs, ordem de lista e título; validador dos kernels físicos, dados impossíveis e 13 classes negativas; seleção/execução privada; preservação do `catalogo_mecanismos.py` produtivo.
- `.github/workflows/qa-compilador-topologia-f15.yml`: suites F15/F14/F7, dois MP4s roteados **sem nome de renderer na linha de comando**, cinco contraprovas explícitas, PNG comparativo e integridade SHA. Sem Claude, IA paga, mídia de terceiros, Telegram ou postagem.

A montagem de biela usa o layout F13 e continua recusando automaticamente título editorial que não cabe. Isso causou duas execuções CI falhas intermediárias devido a textos adversariais longos usados no teste. Os testes foram ajustados para medir **separadamente** que o título não muda a seleção e que título não cabível bloqueia a prévia, sem flexibilizar o gate visual.

## 3. Resultado real da CI

- **Execução FINAL:** https://github.com/Heitor2404/coringa-news/actions/runs/45190338285 — **SUCCESS, 56 testes aprovados**, com dois planos físicos compilados, dois MP4s gerados e cinco pedidos de topologia/permissionamento recusados.
- Execuções intermediárias `45189775525` e `45190093010`: teste do título propositalmente enganoso foi recusado pela segurança de quebra de linha F13. Essas falhas foram entendidas e corrigidas nos **testes**, preservando a rejeição de texto não cabível.
- **Artifact GitHub:** `lab-f15-selecao-topologia-duas-familias-privado`, ID **14825951376**, expira **28/11/2026 14h06 UTC**. ZIP baixado e extraído no diálogo; conteúdo conferido: planos JSON, relatório QA, cinco recusas, oito quadros, MP4s e SHA:
  - `BIELA_COMPILADA_F15.mp4`: SHA256 **`73acf8cb1892f65e5e22e08a8bed0297fbf7b5516d2608ef2dd960094bef1599`**
  - `ENGRENAGENS_COMPILADAS_F15.mp4`: SHA256 **`87652fc2d39bfa185b0b8d24791338f908737b133b6cf784e4cec3eb4e7c8d33`**
  - ambos **9s, 540×960, 24 fps, sem áudio, PRIVADOS**.
  - `COMPARATIVO_F15_2_FAMILIAS_8_QUADROS.jpg` aberto e inspecionado: biela com pistão e correia móveis e engrenagens 20/40 representadas em quatro fases cada; sem câmera dinâmica. A prova é de **seleção de topologia e aplicação de números**, NÃO uma evolução de realismo.
- `RECUSAS_F15.json` comprova bloqueio de: junta invertida/incorreta, peça adicional não cadastrada, evento inexistente, licença visual forjada e pedido para publicar.

**Limite editorial:** no vídeo da biela o título essencial continua na lateral esquerda; a estética segue desenho explicativo. No vídeo de engrenagens o redutor é uma caixa ilustrativa original, não um objeto de fabricante; origem de equações técnicas não é licença de ilustração.

## 4. Próximo gate F16

O gargalo permanece **obter o grafo estruturado a partir de evidência externa correta**. A F15 exige que outro módulo já entregue tipos, conexões e eventos. Na F16, construir uma entrada de referência verificável capaz de:
1. reunir fonte técnica específica com direitos e escopo registráveis; separar texto/fato físico de licença de pixel;
2. coletar e confrontar atributos observáveis de cada componente (eixos, conexão, mecanismo) com o grafo pretendido, marcando incertezas e pontos de revisão humana;
3. bloquear alegações não suportadas, especialmente reconstrução da cinemática a partir de imagem parada;
4. provar a saída em uma terceira descrição com topologia distinta ou formalmente rejeitar caso não suportado, sem liberar a produção prematuramente.

Não multiplicar vídeos de biela/engrenagens apenas mudando números; buscar **capacidade de ingestão/entendimento** e arte de máquina crível. `main`, produção documental, NTC, DOSSIÊ, Telegram e postagem permaneceram intocados.
