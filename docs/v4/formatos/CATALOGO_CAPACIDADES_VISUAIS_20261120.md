# Motor FilmeEditorial — Catálogo de capacidades físicas (20/11/2026)

## Problema encontrado
O motor executava a explicação parcial da eclusa (`lock_explainer`) quando a promessa narrativa exigia um **ciclo completo**. Entrada e saída não aparecem num vídeo só porque estão descritas no título. Encontramos que `LockCausalCycle.tsx` já tinha entrada→fecho→válvula→subida→equalização→abertura→saída, mas a seleção do recurso não era dirigida pelas ações exigidas.

## Mudança transversal implementada
- `src/v4/formatos/catalogo_mecanismos.py`: registry de capacidades reais. O storyboard pode enviar `mechanism: "auto"` + `processo_visual.acoes_necessarias` e `fases_necessarias`. O programa escolhe o renderer somente por cobertura de **ações, na ordem, com fases exigidas**. Nunca por palavras "Canal do Panamá", "EUA" ou "chips".
- `filme_editorial.py`: chama o catálogo **antes do preflight** e traduz a escolha para props Remotion. Falha se o roteiro exigir entrada/saída enquanto o renderer só tem enchimento/equalização. Permanece o veto a filmagem de terceiros sem procedência. Continua obrigatório renderizar e revisar visualmente o MP4.
- `FilmeEditorial.tsx`: `lock_cycle_standalone` reutiliza `LockCausalCycle` em modo privado sem fingir filmagem de referência. O antigo `lock_cycle` segue exigindo **ponte de vídeo original** e mantém suas regressões. O ciclo calcula saída a partir do tempo real do storyboard, em vez de segundos fixos.
- Regra de composição comum: desenhos de `type='mechanism'` controlam sua própria hierarquia gráfica, portanto o Filme **não** acrescenta headline gigante nem gradiente que esconda o processo. Isso vale também para futuros mecanismos.
- Regressões e workflow `qa-diretor-capacidades.yml` provam dois processos diferentes em um filme com duas seleções automáticas e testes negativos.

## O que se pode inferir, e o que NÃO
| Solicitação do storyboard | Capacidade | Estado |
| --- | --- | --- |
| Fonte EUV, máscara, projeção, resist | `optical_projection` | Executável, ilustrativo |
| Ciclo completo de eclusa: entra, fecha, enche, sobe, iguala, abre, sai | `lock_cycle_standalone` | Executável como ilustração privada |
| Apenas enchimento e subida | `lock_explainer` | Executável, mas **não** cobre entrada/saída |
| Ciclo de eclusa com filmagem real como referência | `lock_cycle` | Executável só após ponte de origem verificada |
| Tornado, digestão, motor a combustão, classificação logística, reação química ou outro processo não cadastrado | Não existe renderer físico correspondente no catálogo | **Bloquear**, ou escolher evidência real adequada. Nunca simular automaticamente com desenho genérico |

**Limitações explícitas:** o catálogo **não gera** geometria, física, objetos ou animações para fenômenos arbitrários. Não substitui o trabalho de direção de eventos nem extrai sozinho ações verificáveis de texto livre. Uma nova capacidade exige componente visual implementado, contrato de causalidade, fonte e regressões. A escolha automática garante cobertura contratual, **não** comprova pela metadata que os pixels realmente representam a operação. Só inspeção do render e aprovação do usuário fazem isso.

## Validação para outros temas
O teste positivo com óptica EUV e hidráulica demonstra que a seleção **não depende do tema** e preserva renderers diferentes. Os testes negativos requerem recusa de cenas que exigem ações não implementadas (ex.: triagem de encomendas), evitando falsas promessas. **Ainda falta ampliar o acervo de capacidades** e comprovar melhora estética em três domínios independentes antes de declarar generalização plena.

## Política de uso
Branch experimental `atlas-direcao-visual-20261118`. Não tocar `main`, NTC, DOSSIÊ. Sem Claude/Gemini/voz/Telegram/publicação. O eixo editorial atual continua `Guerra dos Chips EUA × China`; estes são apenas mecanismos demonstrativos. A arquitetura não aprova automaticamente o roteiro, a licença de mídia nem o vídeo final.


## Proteção de área segura para atores móveis — atualização de 20/11

O feedback do usuário identificou um **corte do navio durante a subida**, sem interesse em trocar o desenho, pois é um teste não destinado a publicação. O defeito foi localizado na máscara **INTERNA** `cycleMapClip` do `LockCausalCycle.tsx`: ela começava em `y=715`, enquanto o topo do desenho subia até aproximadamente `y=625` no estágio alto. O recorte cortava o objeto antes que a lógica hidráulica terminasse.

Em vez de trocar o ativo ou apenas mover a máscara arbitrariamente:
- `motor4/remotion/src/formatos/AreaSeguraMovimento.ts` é um **utilitário transversal de cena** para objetos que se movem. Recebe caixa do ator (incluindo folga de sombra), pivô, clipping SVG, margens e posições-chave. Calcula o maior dimensionamento uniforme que mantém o objeto inteiro visível, restringe destino e **recusa render** se só couber encolhendo demais.
- `areaInterna()` deriva margens do **mesmo retângulo** usado pelo `clipPath`, de modo que câmera e área segura não divergirão por duplicação.
- `LockCausalCycle.tsx` agora usa esse utilitário para a sequência inteira. Limita o destino lateral **somente se** o objeto ainda completar a saída além do portão. O mesmo desenho do navio foi preservado; o ajuste é de **escala/enquadramento**, não de tipo de embarcação.
- `motor4/tests/area-segura-movimento.test.mjs` usa o Node 22 para verificar 50 pontos entre entrada, subida e saída, além de um **balão hipotético** com outra geometria e o caso impossível em que a função deve bloquear em vez de cortar.
- A QA `qa-diretor-capacidades.yml` agora compila, executa os testes geométricos e renderiza MP4 privado após mudanças no utilitário.

**Limitação:** o utilitário está disponível para componentes novos, mas só está conectado automaticamente ao `LockCausalCycle` nesta rodada. Não dizer que cada animação existente passou a ter detecção automática de recorte: elas terão de declarar limites e trajetória para aproveitar a regra. Teste visual do MP4 ainda é obrigatório.
