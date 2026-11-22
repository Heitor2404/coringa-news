# ATLAS — SceneGraph causal F1, antes do renderer

**Data:** 22/11/2026. **Status:** contrato estrito de desenvolvimento, com integração ao diretor existente. **Não** representa criação genérica de máquinas, aprovação visual ou autorização de publicação.

## Por que não criar outro diretor
O repositório já dispõe de `catalogo_mecanismos.py`, `diretor_processos.py` e de `filme_editorial.avaliar`. Já havia escolha de capacidade a partir de `acoes_necessarias` e `fases_necessarias`, além de geração automática de cues e tempos. A lacuna era declarar exatamente quem atua, como uma etapa depende de outra e qual ligação a câmera deve mostrar.

## Mecanismo novo
- Fonte declarativa e revisável: `src/v4/formatos/grafo_causal_capacidades.json` (três capacidades reais de duas famílias físicas: óptica e hidráulica).
- Motor independente do assunto: `grafo_causal.py` lê essas fichas, valida `atores[]`, `relacoes[]`, `eventos[]`, estados, precondições e mudanças, e escreve um `plano_causal` serializável. Não recebe título, localização ou tema para escolher física.
- Diretor opt-in de ações estruturadas: `diretor_processos.expandir` solicita esse grafo para a capacidade escolhida e o insere no shot; `catalogo_mecanismos.decidir` o recompila para evitar fraude, cortes ou divergência.
- O contrato pode requerer `direcao_evento.atores_essenciais` (IDs existentes) e `direcao_evento.relacoes_essenciais` (objetos from/type/to exatos); se faltarem, recusa em vez de substituir por setas e cards decorativos.
- O campo `processo_visual.grafo_causal_requerido=true` ativa gate obrigatório. Projetos manuais anteriores sem essa flag continuam validados no caminho legado.

## Três capacidades verificadas
| Capacidade | Atores | Relações | Etapas | Mudança conclusiva declarada |
|---|---:|---:|---:|---|
| Litografia `optical_projection` | 5 | 4 | 4 | `resist.exposure=exposed` |
| Eclusa `lock_cycle_standalone` | 9 | 9 | 7 | `ship.location=upper_channel` |
| Hidráulica `lock_explainer` | 7 | 6 | 5 | `outlet_gate.open=true` |

Ex.: evento `rise` da eclusa tem operador `fill`, foca `water`, `ship`, `chamber`, `conduit`, exige `valve.open=true`, altera `water.level=rising`, e apresenta a relação `ship floats_on water`. A altura real do navio segue a água no renderer especializado já existente. **Não foram criados keyframes por assunto.**

## QA e limite de prova
[Run 45078527193](https://github.com/Heitor2404/coringa-news/actions/runs/45078527193): **39 testes** com sucesso, artifact privado `prova-scenegraph-causal-tres-processos-privada`, ID **14776311278**. Mecanismo ausente bloqueado; grafo adulterado rejeitado.

**Falha legítima do primeiro teste:** faltava `lower_channel` no foco da etapa de fechamento, então não havia relação conectada visível. A regra detectou o problema; a ficha foi corrigida sem suprimir a validação.

**NÃO homologado:** inspeção automática de pixels, identificação livre de maquinário, desenho de novos assets, geração de eventos a partir de prosa, direção de câmera consumida pelo Remotion, direitos, fatos e aprovação artística. `plano_causal` chega ao `props`, mas ainda não move a câmera; conectar isso ao renderer será a F2.

## Critério da F2
Sem escrever um renderer por assunto: ao menos duas famílias devem receber do mesmo contrato alvos/caixas anotados em seus componentes, usar `MechanismCamera2D.ts` ou câmera equivalente, mostrar as relações por evento, e passar teste de frames com atores essenciais realmente visíveis. Se faltar ativo, relação, bbox ou implementação física, bloquear o shot; não usar animação decorativa como fallback.
