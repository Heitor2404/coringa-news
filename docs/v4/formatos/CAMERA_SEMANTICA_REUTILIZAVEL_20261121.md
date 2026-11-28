# ATLAS — câmera semântica reutilizável: pistão e compressor (21/11/2026)

**Status:** laboratório privado, NÃO prontidão de produção, NÃO aprovação estética humana.

## Objetivo

A prévia anterior do `slider-crank` tinha máquina pequena demais, concentrada na metade superior, e muito vazio na faixa de UI inferior (por desenho seguro Reels/TikTok/Shorts). A direção não poderia simplesmente dar zoom com valores manuais no pistão porque precisava continuar utilizável pelo **motor** e não quebrar outros temas.

## Implementado

- `motor4/remotion/src/formatos/MechanismCamera2D.ts` — câmera **independente do assunto** que recebe caixa de limites (bbox da máquina crítica), viewport de introdução, viewport de detalhe, foco atual/anterior e tempo do evento. Aplica ease, zoom limitado pelo espaço real, clamps horizontais e verticais e transição suave de foco. Sem estado mutável por episódio.
- `motor4/remotion/src/formatos/slider-crank-proofs.json` — parâmetro `camera` compartilhado por motor e compressor. Zoom máximo pedido 1,16 (16%); começa aos 1,65s. Dimensionamento efetivo respeita bbox + viewport para não cortar pistão, biela e eixo.
- `motor4/remotion/src/formatos/SliderCrankProof.tsx` — físicos independentes da câmera, que agora destaca os atores `piston`, `rod`, `crank`, `intake`, `outlet` conforme o evento narrativo; a cena inicia completa com manchete e depois dá lugar à máquina ampliada. Foram adicionados realces visuais vinculados às peças, não glow solto.
- Correção narrativa: etapa de saída do compressor alterada para 7,02s, próxima da fase de descarga desenhada (lógica de válvulas ainda simplificada, sem simulação termodinâmica).
- Correção de layout após abrir um frame do vídeo real: contador `04/04` colidia com `SAÍDA PRESSURIZADA`. Foi separado por regra comum e o denominador agora vem de `fixture.steps.length`, não de literal fixo.
- `tests/test_mechanism_camera_2d.py` — testa reaproveitamento, clamping, continuidade de pan e zoom, mudança de alvo e parâmetros em **252 frames por configuração**, além dos 5 testes anteriores da cinemática.

## Resultado real

- [GitHub Actions 44946937219](https://github.com/Heitor2404/coringa-news/actions/runs/44946937219) — **SUCCESS**; TypeScript passou, 9 testes Python passaram, 2 renders de MP4 foram executados e foi gerada folha de contato.
- Artifact `14724082789`, nome `qa-slidercrank-2temas-privado`, expiração 26/11/2026 20:35:49 UTC.
- `pistao_A_PRIVADO.mp4`, `compressor_A_PRIVADO.mp4` — cada um 8,4 s, 30 FPS, 540×960, silencioso, não publicado.
- `contato_pistao_compressor_10quadros.jpg` — 5 quadros de cada configuração. `areas_seguras_3redes.jpg` — simulação das interfaces TikTok, Reels e Shorts; não se trata de captura real das plataformas.
- Inspeção humana dos quadros: na fase explicativa, máquina visivelmente ampliada; foco no componente importante sem cortes do conjunto pistão/biela/eixo; textos essenciais ficam à esquerda da área lateral de UI. Um frame a 7,35s confirmou fim da colisão `04/04SAÍDA`.

## Auditoria crítica

A mudança é útil e **reutilizável nas duas configurações**. Mas:
- Ainda são apenas dois assuntos da MESMA família física. A câmera por contrato foi implementada genericamente, porém ainda não demonstrada em uma família totalmente diferente.
- O aspecto continua ilustrativo/esquemático, sem narração; não temos aprovação de qualidade editorial nem prova de retenção.
- O vazio inferior permanece: segue intencionalmente disponível para as interfaces das plataformas, enquanto a máquina crítica foi ampliada dentro da área interseção segura. Não inflar métricas de pixel-change para alegar estética.
- Não foi demonstrada reconstrução automática de animação encontrada na internet, nem importação 3D, nem geração de múltiplos assuntos arbitrários. Isso requer referências realmente acessíveis e grafo semântico de objetos, relações e acontecimentos.
- O modo `slider-crank` **não** foi promovido ao `FilmeEditorial` nem ao catálogo de produção. `main`, NTC e DOSSIÊ preservados.

## Próxima prova difícil

Integrar `MechanismCamera2D` a uma segunda família de mecanismo diferente (polia / alavancas / hidráulica), conduzida por um **grafo de eventos e atores** reutilizável e por referências de movimento inspecionadas. Comparar visualmente duas famílias sem correções TSX por assunto. Se ref for inválida/incompleta, bloquear em vez de gerar animação genérica.
