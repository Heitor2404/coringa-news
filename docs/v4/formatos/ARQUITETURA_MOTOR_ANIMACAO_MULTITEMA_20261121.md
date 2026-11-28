# ATLAS — arquitetura para animações explicativas reutilizáveis (21/11/2026)

**Status:** especificação técnica e gate de desenvolvimento. Não é implementação, aprovação visual nem autorização de publicação.
**Branch:** `atlas-direcao-visual-20261118`; não alterar `main`, `motor-integral-v4`, NTC, DOSSIÊ ou o pipeline `FilmeEditorial` sem homologação.
**Decisão do usuário:** “A gente precisa fazer de uma maneira que fica bacaba visualmente e que seja explicativo e a grande questao é o motor precisa saber fazer essas animações para outros temas também, de nada adiante corrigir navio,feixe de lazer e etc se no futuro der problema nos outros temas”.

## 1. Diagnóstico confirmado no repositório

**Já existe fundamento útil; não criar um segundo motor concorrente:**
- `motor4/remotion/src/formatos/Mechanism2DCore.ts`: `eventAt`, `eventTime`, `rotateAbout`, `clamp01`, easing. Não contém grafo de entidades, restrições de conexão ou composição visual automática.
- `src/v4/formatos/catalogo_mecanismos.py`: capacidades `lock_cycle`, `lock_cycle_standalone`, `lock_explainer`, `optical_projection`; seleção por ações, fases e ordenação, rejeição sem capacidade. Esse contrato é uma boa base, mas cada renderer ainda corresponde a mecanismo especializado.
- `motor4/remotion/src/formatos/AtlasAArtKit.tsx`: painel, junta, rebite e materiais. São apenas componentes de acabamento, NÃO uma linguagem suficiente de atores, conectores, profundidade, enquadramento e semântica.
- `AtlasAProof.tsx`: ainda escolhe `kind === 'lock' ? LockActors : EuvActors`; geometria e posições escritas em TSX. A V3 foi estruturalmente testada no run `44917475253`, mas foi rejeitada visualmente pelo usuário por cortes, navio ruim, feixe ruim e explicação insuficiente. Não tratá-la como estilo aprovado.
- `docs/v4/formatos/CONTRATO_DIRECAO_VISUAL_ATLAS.md`: já separa regras globais dos dados particulares, câmera semântica, gates de legibilidade e escolha de mídias. Estender, não duplicar.

**Falha de estratégia:** trocar `navio.svg` por um mais bonito, aumentar o feixe e escolher 3 tempos específicos pode melhorar dois testes; NÃO melhora a capacidade futura de explicar fenômenos desconhecidos. Pior: uma alteração só para mudar movimento no primeiro segundo pode desincronizar causa e efeito.

## 2. O que é e o que não é universalizável

**Universalizável:** contrato de eventos, entidades, relações, restrições físicas e visuais, linguagem de arte, composição 9:16, timing derivado da fala, montagem por acontecimentos, validação de legibilidade, transformação/câmera, transições e telemetria.
**Especializado por família de fenômeno:** leis e estados de flutuação/enchimento, engrenamento, alavanca, reflexões ópticas, circuitos, combustão, fluxo de pessoas etc.
**Especializado por ativo:** a silhueta de um cargueiro, espelho de projeção, bomba, pulmão ou turbina. Esses ativos exigem biblioteca ilustrada, montagem paramétrica, imagem/vídeo real com procedência ou nova capacidade curada. Não prometer qualidade arbitrária para objetos inéditos por regra de SVG.

O objetivo realista é **gerar novos episódios com edição de dados e escolha de capacidades já homologadas, sem alterar TSX por episódio**. Quando um tema pede uma família de física ou um ativo que não existe, registrar `CAPACIDADE_INDISPONIVEL` e usar outra prova adequada (mapa, mídia real licenciada, gráfico) ou desenvolver um novo componente reutilizável uma única vez; jamais inventar uma animação “pronta” com setas/cards.

## 3. Contrato intermediário: grafo de cena causal, não nomes de assuntos

O roteiro verificado é traduzido para uma **representação estruturada** antes de renderizar:
- `actors[]`: entidades semânticas com tipo/família, ativo aprovado, dimensão relativa e limites de escala; não coordenadas absolutas fornecidas pelo LLM.
- `relations[]`: `connected_to`, `inside`, `rests_on`, `moves_with`, `flows_to`, `reflects_to`, `rotates_with`; âncoras pertencem aos atores, não são soltas.
- `events[]`: uma operação de estado `open|close|translate|rotate|fill|drain|flow|reflect|transfer|reveal|compare`, com pré-condições, atores, relação e resultado esperado. O operador deve existir na biblioteca; novos fenômenos acrescentam operadores/famílias por revisão.
- `phases[]`: etapas semânticas exigidas pela narração; os 3 atos início–causa–resultado servem como estrutura editorial, NÃO como limite rígido para qualquer mecanismo. Se o conteúdo exigir 5–7 estados, respeitar essa causalidade.
- `shots[]`: intenção de câmera `show_context|follow_actor|show_connection|show_consequence|compare`; o layout calcula bboxes e visibilidade em função dos objetos.
- `assets[]`: proveniência, licença, hierarquia de detalhamento e paleta de material; não pedir ao renderizador que desenhe livremente qualquer objeto.

Exemplo **neutro** (não codificar como episódio):
```json
{
  "actors": [{"id":"source","role":"source","asset_family":"fluid"},{"id":"target","role":"container","asset_family":"fluid"}],
  "relations": [{"type":"flows_to","from":"source","to":"target","via":"pipe"}],
  "events": [
    {"action":"open","target":"valve","requires":"closed"},
    {"action":"flow","from":"source","to":"target","through":"pipe","requires":"valve_open"},
    {"action":"fill","target":"target","driven_by":"flow"}
  ],
  "shots": [{"intent":"show_connection","focus":["source","pipe","target"]}]
}
```
Esse contrato é uma meta de API: só o implementar quando for possível validá-lo contra as capacidades existentes, sem quebrar `processo_visual` ou `cues`.

## 4. Cinco camadas obrigatórias

1. **Diretor semântico**: fatos e fala → ações, atores, relações, etapas; rejeita contradições e capacidades ausentes. O modelo escolhe **o que mostrar**, nunca coordenadas e estética livre por episódio.
2. **Motor de estados por família física**: cada evento atualiza uma propriedade única com relações derivadas; navio move com nível d'água, luz segue vértices/reflexões, engrenagens mantêm relação angular. Invariantes reais e teste de replay determinístico.
3. **Biblioteca ilustrativa A**: composição de atores/peças reusáveis, ativos originais com nível de detalhe suficiente, 2–3 planos de profundidade, oclusão, sombras e materiais padronizados. Consistência de arte, mas cenário contextual por fenômeno. Sem desenhar tudo com retângulos e elipses genéricas.
4. **Diretor de atenção e layout 9:16**: enquadramento por bounding box, câmera dirigida por acontecimento, texto próximo da sua âncora, visibilidade de conexões causais, slots por altura e interface por rede. Fundo pode ser full bleed; ator, conexão e rótulo essenciais não podem ser cortados ou cobertos. Proibir zoom para esconder falha.
5. **Fiscal visual e semântico**: testes de geometria por frame, clipping/colisão, continuidade de conexões, progressão causal alinhada à fala, objeto reconhecível, capacidade coberta, leitura no celular, fonte e direitos. Variância de pixels sozinha não é comprovação: brilho decorativo também muda pixels. QA verde não é aprovação estética; inspeção humana obrigatória.

## 5. Sequência de desenvolvimento (evitar nova rodada de remendos)

**F0 — Inventário/integração, sem render:** listar primitivas e operadores existentes, relacioná-los às capacidades em `catalogo_mecanismos.py`, registrar lacunas. Não criar kit duplicado.
**F1 — Contrato/IR e simulador de estados offline:** montar parser estrito de `actors/relations/events`; validar conexão, pré-condição, sequência, colisão e limites. Testes por propriedades para cenas sintéticas. Os operadores universais entram na biblioteca, não nas condições `if subject === ...`.
**F2 — Primeiro render genérico orientado por dados:** demonstrar uma família conhecida (por exemplo, fluxo/enchimento) com **dois conjuntos de atores diferentes**, sem alterar TSX entre eles. Se trocar o objeto/posição exige modificar código específico do episódio, o gate falha.
**F3 — Família independente:** integrar reflexão óptica usando a MESMA API de atores, cenas, materiais, câmera e fiscal; física de reflexão especializada apenas em seu próprio operador. Testar sem ajustes exclusivos de posição no EUV.
**F4 — Holdout cego:** assunto novo escolhido somente após o motor estar fechado. Critério: toda a montagem usa contrato e ativos existentes, sem editar TSX para esse assunto; caso falte capacidade, deve bloquear justificadamente ou escolher mídia real adequada. Incluir ao menos uma prova sobre assunto que não seja eclusa nem EUV e um segundo caso dentro de uma família já homologada. Fazer auditoria no celular.
**F5 — Promover com regressão:** só após QA estrutural+visual, direitos, narração e interface real; preservar `FilmeEditorial` até autorização.

## 6. Gates objetivos

**Bloqueadores automáticos:**
- Ação pedida não existe ou pré-condições violadas.
- Ator essencial/canal causativo sai do frame, cruza peça fisicamente impossível ou desaparece em um corte sem aviso.
- Conexão causal quebra em algum frame, a posição de elementos relacionados diverge de estado único.
- Rótulo crítico invade UI, bloqueia a ação ou não cabe; texto pequeno em escala de celular.
- Beat muda apenas o texto, glow, zoom ou cor, sem demonstrar a mudança semântica exigida.
- Evento terminal prometido não foi representado (entrada → mecanismo → saída quando requisitado).
- Ausência de asset com procedência, física não validada ou suporte anunciado sem implementação.

**Aprovação humana:** o espectador entende o mecanismo sem depender de um parágrafo explicativo; objeto principal reconhecível e artístico; um foco por etapa; ritmo de short; composição consistente entre temas. Critério explícito `VISUAL_OK` separado de `CI_PASS`.

## 7. Arquivos que devem evoluir

- `src/v4/formatos/catalogo_mecanismos.py`: mapa de operadores/famílias/ativos/limitações, compatível com as capacidades já existentes.
- `motor4/remotion/src/formatos/Mechanism2DCore.ts`: ponto de partida da representação de estados físicos; evitar adicionar nomes de episódios.
- `motor4/remotion/src/formatos/AtlasAArtKit.tsx`: materiais/oclusão, depois hierarquia de atores e níveis de detalhe; não tratar como universal só por conter componentes.
- Novo módulo `SceneGraph`/validador e novo compositor orientado pelo IR **somente após inventário F0**.
- `AtlasAProof.tsx`: fixture de regressão, não fundação para copiar a cada assunto; produção `FilmeEditorial` intocada até gate.

**Conclusão operacional:** não encomendar “V4 de navio e laser”, nem pedir ao Claude um motor mágico de qualquer assunto. Construir gramática causal + biblioteca de atores e materiais + direção de câmera + QA visual; integrar capacidades existentes, provar troca de dados **sem editar código de episódio** e só então polir imagens finais de eclusa/EUV.