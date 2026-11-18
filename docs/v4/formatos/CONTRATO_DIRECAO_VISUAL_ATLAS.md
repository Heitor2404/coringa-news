# ATLAS — Contrato de direção visual reutilizável

## Princípio

O episódio do Canal do Panamá é um **caso de teste/regressão**, não um template editorial nem uma exceção que justifique regras específicas. O motor deve generalizar decisões para outros assuntos sem reaproveitar coordenadas, segundos, rótulos ou cenas daquele roteiro.

## Sequência de decisão do diretor

1. A narração determina a pergunta visual: contexto geográfico, acontecimento comprovado, mecanismo/fluxo, comparação ou revelação de dado.
2. Escolher prova adequada: vídeo real quando demonstra a ação; mapa quando a informação é geográfica; gráfico quando revela um dado; animação técnica **somente** para demonstrar algo que não ficaria claro de outro modo.
3. Uma explicação contínua de processo conserva o MESMO mecanismo na tela, com destaques nas partes ou estados citados na fala. O desenho pode mudar de câmera, mas não desaparecer em favor de caixas com nomes.
4. Encerrar depois da última revelação e da conclusão falada, sem repetir visualmente uma explicação já concluída.
5. Abertura ATLAS = mapa, pergunta e/ou prova real. **Não** antecipar animação técnica no gancho só para gerar movimento.

## Contrato verificável (por episódio)

Um clipe de mecanismo no ATLAS requer uma entrada `explicacoes` com `id`, `tipo="mecanismo"`, `t0`, `t1` e `recurso`, indicando o componente aprovado e o intervalo da fala. O motor resolve âncoras de narração e verifica:
- `F-EXPLICACAO-SEM-CONTRATO`: todo clipe técnico tem contrato válido e compatível.
- `F-MECANISMO-SEM-CONTINUIDADE`: nenhuma explicação de mecanismo declarada fica fora da cobertura do clipe.
- `F-GANCHO-MAPA-PRIMEIRO`: nenhuma animação técnica toma o lugar da abertura do ATLAS.
- Fiscal de ritmo sem câmera: zoom/pan não contam como mudança de conteúdo; evolução de dados localizada pode contar.
- `motivos_bloqueio`: informa causas específicas por portão, inclusive duração de cenas paradas, legenda e áudio.

O fluxo **não pode** declarar automaticamente que algo foi compreendido apenas porque o contrato estrutural passou. A fidelidade entre a narração e a animação ainda exige inspeção visual e eventualmente revisão semântica.

## Parâmetros globais × dados particulares

**Globais:** seleção da prova, continuidade de mecanismo, alinhamento à narração, limite de ritmo do conteúdo, hierarquia e legibilidade, erro factual bloqueador, atribuição de fontes, final sem repetição.

**Por episódio:** fatos verificados, texto, referência de mídia, intervalos de fala, componente escolhido, alvos narrados, sequência e localização dos elementos. Nenhuma destas escolhas deve ser promovida a valor fixo do motor.

## Clareza visual — parâmetros do MOTOR, não do episódio

Os tokens estão em `src/v4/formatos/canais/coringa.json → direcao_visual` e são aplicados aos mecanismos pelo renderizador. Um episódio não escolhe fonte, quantidade de etiquetas ou pixels de câmera.

- **Legibilidade**: rótulos com tipografia de pelo menos 34 px no quadro 1080×1920, limite de 22 caracteres por destaque semântico, caixa adaptativa e proteção contra cortes nas áreas seguras.
- **Hierarquia e densidade**: no máximo duas camadas editoriais independentes simultâneas; durante foco de mecanismo, até dois rótulos físicos, com prioridade para a peça narrada e depois a informação de estado.
- **Câmera didática**: o recurso declara alvos **semânticos** (`focos`, com t/alvo/rotulo); o componente fornece as posições físicas. A câmera acompanha o alvo sem perder todo o contexto e interpola suavemente entre peças. Não há coordenadas de câmera por episódio.
- **Fiscal genérico**: `F-POLUICAO-VISUAL`, `F-FOCO-SEM-ALVO`, `F-ROTULO-ILEGIVEL`, `F-FOCO-RAPIDO` e `F-FOCO-TEMPO` reprovam planos com excesso ou com foco inconsistente. O catálogo de alvos por componente fica em `src/v4/formatos/formatos.json`.
- **Testes independentes de assunto**: `tests/test_clareza_v2.js` exercita câmera, contexto, densidade e limites com alvos sintéticos. `tests/test_formatos.py` cobre integração, conversão da linha do tempo e isolamento do DOSSIÊ.

As utilidades de foco e rótulos ficam no núcleo V2 para reaproveitamento por novos componentes. **Hoje a aplicação renderizada está integrada ao componente eclusa, o único mecanismo técnico atualmente aprovado no ATLAS; outros mecanismos exigem integrar o mesmo contrato.** Testes verdes não comprovam compreensão visual: a prévia ainda exige revisão no celular.

## Critérios de avanço

- Testes Python e tipagem JS/TS verdes, sem regressão em DOSSIÊ/NTC.
- Prévia integral **do trecho explicativo** sem quebra de continuidade nem perda de narração.
- Conferir visualmente a clareza de cada componente no celular; teste automatizado não equivale a aprovação.
- Antes de afirmar generalização, demonstrar as mesmas regras em **um segundo assunto escolhido pelo usuário**. Não escolher nem criar o segundo assunto sem consulta.
- Evitar render completo e custo de IA enquanto os testes locais e a prévia dirigida não estiverem aprovados.

Status: fase experimental em branch isolada; regras estruturais implementadas e validação do segundo assunto pendente.
