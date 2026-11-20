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
