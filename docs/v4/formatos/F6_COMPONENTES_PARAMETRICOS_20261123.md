# ATLAS F6 — Primitivas físicas desenháveis e compositor por configuração

**23/11/2026, branch atlas-direcao-visual-20261118; laboratório privado, sem Claude, sem publicação.**

## Problema solucionado nesta rodada

F5 catalogava 29 papéis físicos em três mecanismos, mas não desenhava peças novas. A F6 introduziu funções vetoriais parametrizadas para cinco tipos comuns, conectou-as a uma eclusa existente e demonstrou a montagem de um quarto mecanismo com dois arquivos de dados, SEM dois renderizadores específicos.

## Módulos efetivos

1. src/v4/formatos/primitivas_fisicas_parametricas.py: funções conduto, valvula, barreira, reservatorio e agua_no_tanque. Geometria validada, cores seguras, limites finitos, sem carregar SVG/media externos. Os outros oito tipos de F5 permanecem somente catalogados.
2. src/v4/formatos/render_eclusa_hidraulica_2d.py passou a consumir conduto, valvula e barreira pelo mesmo módulo. A física hidráulica própria, os sete eventos, a política de câmera e o desenho do navio não foram reescritos.
3. src/v4/formatos/grafo_causal_capacidades.json e camera_causal_geometrias.json: família experimental vasos_comunicantes, seis atores, quatro ações causais, câmera de plano geral travado e caixas seguras para os DOIS formatos.
4. src/v4/formatos/fisica_reservatorios_parametricos.py: solver separado do desenho, com A_esquerda * altura_esquerda + A_direita * altura_direita constante (profundidade igual); níveis finais se igualam quando a válvula abre. Curva temporal didática, sem calibração de vazão real, sem inércia, sem sistema 3D.
5. src/v4/formatos/compositor_mecanismo_parametrico_2d.py: interpreta a cena JSON, valida papéis/tipos/bounds/ligação física do tubo/valvula/legendas/fonte/direitos e chama as mesmas primitivas para cada quadro. Não há if por nome do preset e não são desenhados quadros à mão.
6. src/v4/formatos/cenas_parametricas/vasos_comunicantes_iguais.json e vasos_comunicantes_assimetricos.json: apenas posição, largura e identificação de componentes diferem; física, estados e compositor são compartilhados.

## Referência científica e licença

Princípio do nível comum em fluido conectado: **OpenStax, University Physics, 14.1 Fluids, Density, and Pressure**, https://openstax.org/books/university-physics-volume-1/pages/14-1-fluids-density-and-pressure. Somente a explicação física é utilizada; nenhum pixel, imagem ou animação do site foi importado. O texto não é autorização para reprodução da imagem da fonte. O tempo dos vídeos é DIDÁTICO, e não corresponde a uma medição de duração física.

## QA real (arte não aprovada)

[GitHub Actions 45115182926](https://github.com/Heitor2404/coringa-news/actions/runs/45115182926) **SUCCESS: 47 testes, sem falhas**. Vídeos H.264 540×960, 24 fps, duração exata de 12s, sem áudio, hash verificado por arquivo e relatório:

- VASOS_IGUAIS_F6.mp4 SHA256 ea8bce285a173754fb96138276024ff47262180c51af070c6357e699fb602f14; diferença de conteúdo do mecanismo 20,34 RGB na região comparada.
- VASOS_ASSIMETRICOS_F6.mp4 SHA256 6d2153c9600172e02b0fd7970cc4d4fbdd61f27d707c63f555f1c25658fc1423; diferença 19,26 RGB.
- Artifact privado 14791407195 (lab-f6-duas-cenas-parametricas-videos-privados), expira 28/11/2026 ~05:02 UTC. Contém contatos de quatro estados por formato, oito PNG e dois MP4.

Observação humana da folha COMPARATIVO_DOIS_PRESETS.jpg: níveis iniciais desiguais, água transferida após abertura e final no mesmo patamar; nos tanques de larguras diferentes a altura final muda como previsto pelo balanço de volume. Câmera estável e layout 9:16 legível. Visual é simples, esquemático e não homologado como estética final.

## Limites e próximo passo

**Concluído:** reuso comprovado de SVG desenhável e de compositor em duas cenas hidráulicas além da eclusa; dados variam sem novo código por preset. **Não concluído:** compositor universal de todas as 13 primitivas e qualquer assunto, pesquisa automática de geometria ou modelos 3D, validação visual contra referências externas e publicação. A F5 mantém suas três famílias/29 atores certificados; F6 adiciona um quarto fluxo de laboratório ainda não promovido por falta de homologação de identidade visual.

**F7 proposta:** ampliar primitives (transmissão/pistão/rotor) como ativos parametrizados; retirar contagens rígidas de F5 e exigir evidência licenciada/visualmente revisada antes de autorizar nova família; testar mecanismo com física de outra categoria (não apenas hidráulica), sem recaída no formato antigo descartado.
