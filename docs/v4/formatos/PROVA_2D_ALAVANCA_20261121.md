# Prova 2D-first de alavanca — laboratório privado, 21/11/2026

## Por que esta prova existe
O usuário reprovou a versão de mecanismos miniaturizados e o palco imersivo fragmentado, além do fundo genérico. Após análise de dois vídeos enviados pelo próprio usuário (The Efficient Engineer: alavancas/polias/engrenagens; 3Blue1Brown: blocos/colisões), a conclusão foi separar **narrativa causal persistente** da **engenharia de estados programáticos**. A meta imediata é uma **prova pequena, não uma reescrita de todo o motor**, para revisar uma nova identidade 2D antes de integrar EUV/eclusa.

## Estado do código (branch `atlas-direcao-visual-20261118`)
- `motor4/remotion/src/formatos/Mechanism2DCore.ts`: helpers puros `eventAt`, `eventTime`, `rotateAbout`, `leverAdvantage`. A mesma rotação define posição de carga e força, sem animações divergentes.
- `motor4/remotion/src/formatos/lever2d-contract.json`: geometria e cues do laboratório (sem texto de episódio no componente). Cinco ações `introduce`, `load`, `effort`, `actuate`, `explain`, duração 11,5s.
- `motor4/remotion/src/formatos/LeverMechanism2D.tsx`: cena original vetorial 1080×1920, alavanca de 1a classe com apoio fixo, carga no braço curto, esforço no longo, movimento rígido idealizado. Duas paletas sobre MESMA física: `paper` clara/editorial e `graphite` escura.
- `motor4/remotion/src/Root.tsx`: `ProvaMecanismo2D` **isolada**, `private_review_only=true`. Nenhum `mechanism` foi incluído no catálogo produtivo, nem foram alterados `FilmeEditorial`, `NTC`, `main`, `DOSSIÊ`.
- `tests/test_mecanismo_2d_alavanca.py`: prova monotonia: braço curto sobe, braço longo desce; pivô/distâncias rígidas; verificação geométrica da região de ícones; texto ancorado no safe e arte original.
- `.github/workflows/qa-modelo-2d-alavanca.yml`: TypeScript, pytest, render privado em MP4 de duas variantes 540×960, contato de 6 instantes, status bloqueado para publicação, sem áudio/Telegram, retenção 5 dias.

## Decisões de desenho
- O desenho é autoral do Coringa; **não copiar** textura, cenas, gráficos, narração, música ou modelos dos vídeos de referência.
- Sem grid holográfico, cartões sequenciais ou trocas da cena. O fundo claro usa aparência de prancha editorial/solo; o escuro mantém grafite sem ilustrações gratuitas. O suporte é parte física central, não elemento decorativo.
- Figura e textos permanecem em telas 9:16; esforço aparece acima da altura onde a UI lateral conservadora começa. Rótulos indispensáveis e etapa da explicação ficam no setor central protegido.
- A cena ilustra **cinemática de uma alavanca ideal**, não resultado quantitativo de um corpo específico. A razão de braços é derivada da geometria (aprox. 2,1×); sem considerar atrito, deformação ou massas medidas.
- A versão foi revista visualmente: a primeira renderização tinha colidido a medição com o suporte e o crédito com a última etapa; isso foi corrigido em código e teste. Na última inspeção restou um rótulo de FORÇA perto da medição superior, afastado em ajuste final.

## Gate de aprovação
**Nunca inferir `VISUAL_OK` de CI success.** Necessário (1) arquivos MP4 abertos e 6 quadros revisados após último commit; (2) usuário gostar do estilo; (3) avaliar leitura no celular/3 plataformas; (4) teste com voz/legenda; (5) testar generalização para eclusa/EUV. O terceiro teste não significa que os dois temas já serão gerados automaticamente — ainda precisam de primitivas físicas próprias.

## Pendências assumidas
- Ainda há área visual pouco ocupada na parte inferior do 9:16, em parte porque a zona crítica de UI termina em y1240. Não preencher com logos, números ou grids sem função.
- Sem narração, sincronização por palavras, música, imagens externas ou autorização de publicação.
- Só após validar estética integrar um modo 2D genérico baseado em `actors`, `connections` e `events` ao catálogo produtivo; se faltar capacidade física, bloquear em vez de simular com cartões.
