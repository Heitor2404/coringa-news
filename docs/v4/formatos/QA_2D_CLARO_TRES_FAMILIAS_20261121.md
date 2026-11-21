# Validação multiassunto do modo 2D claro — 21/11/2026

**Origem da decisão:** o usuário gostou mais da versão clara da alavanca, mas observou que um estilo só pode ser adotado no motor após funcionar em outros mecanismos. Este arquivo descreve o experimento **privado**, não aprova publicação.

## Três modelos para comparação
| Mecanismo | Valor para o teste | Fonte da física | Ganho real |
|---|---|---|---|
| Alavanca de 1ª classe | Referência estética clara aprovada como direção inicial, ainda não homologada no motor | `Mechanism2DCore.rotateAbout`, geometria e eventos | Corpo rígido, apoio fixo, esforço e carga seguindo uma rotação |
| Polia fixa | Prova de objeto vertical que usa altura da tela | Mesmo deslocamento aumenta comprimento da corda à esquerda e diminui à direita; rotação da roda proporcional a deslocamento/r | Corda contínua, peso sobe enquanto ponta livre desce; polia fixa só muda a direção, sem reduzir força ideal |
| Par de engrenagens | Prova de duas peças simultâneas e sincronizadas | `angulo_movida=-angulo_motora*(dentes_motora/dentes_movida)` | Sentido oposto e menor velocidade na maior; torque ideal calculado do número de dentes |

## Código no GitHub
- `motor4/remotion/src/formatos/Mechanism2DPaperStudio.tsx`: cabeçalho, superfície clara sem grid arbitrário, títulos, faixa de etapa, crédito e indicação não publicável **compartilhados entre polia/engrenagens**. A alavanca ainda tem estilo claro semelhante, mas usa um layout anterior separado.
- `motor4/remotion/src/formatos/Mechanism2DOtherModels.tsx`: dois renderers de física sob a mesma direção, com estado determinado por cues do contrato, sem edição individual de quadros.
- `motor4/remotion/src/formatos/mechanisms2d-probes.json`: duração, geometria, dentes, raio da polia, eventos e títulos declarativos. Mudança de tema exige capacidade física; não prometer que qualquer prompt vira mecanismo.
- `motor4/remotion/src/Root.tsx`: registra `ProvaPolia2D` e `ProvaEngrenagens2D` em laboratório. **Não habilitado no `FilmeEditorial` produtivo, no catálogo nem no Telegram**.
- `tests/test_mechanism_2d_multifamily.py`: causalidade, razão de engrenagens, conservação do comprimento de corda, fontes originais e restrição geométrica lateral.
- `.github/workflows/qa-modelo2d-multifamilia.yml`: TypeScript, testes, duas prévias H.264 de 8,4s, contato de oito frames e relatório `publicar=false`.

## Limites da decisão visual
1. A versão clara agrada mais ao usuário na prova da alavanca, mas **não é identidade final homologada**. O novo teste serve para comparar a mesma família visual com relações físicas diferentes.
2. Os frames ainda precisam de revisão humana: ocupação do 9:16, legenda vs mecanismo, inteireza das peças, permanência das relações causais e ausência de estética genérica.
3. A polia fixa **não multiplica força**; não confundir com polia móvel/composta. O par de engrenagens mostra razão de velocidades/torque idealizadas, sem perdas nem necessidade de copiar vídeos externos.
4. O contrato de áreas seguras para Reels/TikTok/Shorts é conservador e aproximado: testes de tela/composição não substituem conferir o vídeo dentro dos aplicativos. A região abaixo de y1240 pode continuar visualmente vazia; não preencher com gráficos falsamente explicativos.
5. As três famílias dependem de desenho vetorial para objetos/capacidades conhecidas. **Ainda não existe um compositor físico universal de `actors/connections/events` para qualquer novo mecanismo**. A próxima generalização deve extrair contratos reutilizáveis e falhar explicitamente quando faltar primitiva, sem implementar uma animação separada por frase.
6. Nenhum vídeo foi publicado ou enviado ao Telegram; sem narração. Não alterar main, NTC ou DOSSIÊ.

## Resultado e decisão
O resultado de CI confirma compilação/estado físico, **não qualidade estética**. Depois do render, registrar ID, estado, artefato, parecer visual e avaliação do usuário antes de promover o padrão de produção.


## Resultado verificado — render final 21/11

- **GitHub Actions `44903955242` SUCCESS** (SHA de código/testes `d6f49c6c6fa79a7a0ef28c970adb4809fb7bf8b6`). Artifact privado `14707720229`, expira 26/11/2026. Dois MP4s 540×960 H.264 com 8,4s, sem áudio, sem Telegram, sem publicação.
- Vídeo 1 `qa_modelos2d_claro_final/polia_clara_PRIVADA.mp4`; vídeo 2 `qa_modelos2d_claro_final/engrenagens_claras_PRIVADA.mp4`; oito frames `contato_2d_multiassunto.jpg`; comparação com alavanca em `/mnt/data/comparativo_3_mecanismos_2d_claro_20261121.jpg`. Todos os caminhos sandbox devem ser confirmados no contêiner antes de compartilhar.
- A primeira prova `44903309651` passou mas a revisão humana flagrou rótulos encostando e o peso aproximando-se demais da polia. Corrigidos `mechanisms2d-probes.json`/render e estendido o fiscal `tests/test_mechanism_2d_multifamily.py` para impedir interseção peso×roldana ao longo de 101 posições. Os movimentos continuam derivados de estado físico, não keyframes específicos do episódio.
- **Parecer após inspecionar quadros finais:** o papel claro se sustenta nas três famílias; o mecanismo da polia é mais naturalmente vertical e a engrenagem apresenta peças simultâneas sem trocar de cena. Ainda há uma área inferior extensa pouco aproveitada, rótulos pequenos no celular e ausência de narração/legendas. A alavanca ainda usa layout editorial separado do novo `PaperLayout`; não afirmar padronização completa. Nenhum selo `VISUAL_OK` ou `PUBLICAVEL` antes da opinião do usuário e validação nas redes.
