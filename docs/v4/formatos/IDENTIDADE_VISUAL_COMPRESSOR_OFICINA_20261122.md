# ATLAS: compressor reconhecível ≠ pistão genérico com válvulas

**22/11/2026 — prova visual privada, não integrada à produção.**

## Reprovação

Usuário, ao assistir a `COMPRESSOR_AR_FISICO_2D_PRIVADO.mp4`: **“Mas isso não me parece um compressor.”**

A objeção é procedente: vídeo anterior representava **um mecanismo pistão–biela num invólucro genérico**, quase idêntico a um motor a combustão desprovido de ignição. Um pequeno tanque vertical lateral, sem motor elétrico identificável nem filtro, não formava visualmente um equipamento típico de compressor de oficina. Passar em testes de pressão/válvulas NÃO demonstra identidade visual.

## Fonte verificável (não copiada para render)

- [Atlas Copco: piston air compressors](https://www.atlascopco.com/en-us/compressors/wiki/compressed-air-articles/piston-compressors): unidade acionada por motor, pistão movido por biela/manivela, válvulas de admissão/descarga.
- [Kaeser: oil-lubricated workshop compressors](https://www.kaeser.com/in-en/products/reciprocating-compressors/stationary-reciprocating-compressors/oil-lubricated-workshop-compressors): unidade com filtro de ar, bomba, motor e reservatório, com tubulação flexível e suportes.
- [Industrial Air parts manual (PDF)](https://www.industrialairusa.com/pdfs/200-2735.pdf): arranjo ilustrado de conjunto **tanque horizontal, motor elétrico, bomba com aletas e transmissão por correia**. Não copiar ilustração de terceiros; usar apenas para entender topologia/identidade.

**Configuração selecionada:** `compressor_ar_eletrico_tanque_horizontal_correia`. Outros compressores (parafuso, scroll, sem reservatório integrado, acionamento direto etc.) NÃO são iguais. A família visual precisa ser nomeada e selecionada por processo e contexto, não por uma palavra vaga “compressor”.

## Prova visual renderizada localmente nesta conversa

- Novo render `/mnt/data/compressor_assembly_lab/out/COMPRESSOR_COMPLETO_EM_CORTE_PRIVADO.mp4` — 8s, 24fps, 540×960, desenho SVG autoral (CairoSVG + FFmpeg), sem narração, publicação bloqueada.
- Nova prancha `/mnt/data/compressor_assembly_lab/out/CONTATO_8_ESTADOS_COMPRESSOR_COMPLETO.jpg`.
- Comparação do MESMO estágio com vídeo anterior `/mnt/data/compressor_assembly_lab/out/COMPARACAO_IDENTIDADE_VISUAL.jpg`.
- Fontes de render da prova local `/mnt/data/compressor_assembly_lab/src/v4/formatos/render_compressor_conjunto_2d.py`. Código usa física da família `CompressorPV2D` com pressão e válvulas automáticas; não extraiu malha CAD nem vídeo externo. **Esse renderizador experimental ainda não foi promovido ao repositório: a prova visual requer aprovação artística antes de integração**. Não afirmar que motor de produção agora gera essas máquinas.
- A proposta apresenta bomba com cabeçote/aletamento, janela de corte com pistão/biela e válvulas, motor elétrico à esquerda, polias/correia, filtro de entrada, descarga para o reservatório horizontal e indicador de pressão do cilindro independente do manômetro do tanque.

## Avanço no GitHub, passível de repetição

- `src/v4/formatos/identidade_visual_maquina.py`: gate novo **separado da cinemática**, com exigência de peças identificáveis, relação de acionamento, fluxo do filtro ao cabeçote, descarga ligada ao tanque e proporções coerentes; regras para essa configuração específica e sem extrapolar para outros compressores.
- `docs/v4/formatos/reference_first/identidade_compressor_oficina_tanque_horizontal.json`: manifesto de topologia anotado da **prova local** com bounding boxes, peças e conexões, não prova automática por pixels.
- `tests/test_identidade_visual_maquina.py`: falhas para pistão genérico com garrafa lateral, falta de acionamento/filtro, linha de descarga solta, tanque irreal, mistura com Otto, subtipo incorreto, bbox inválida ou publicação.
- [GitHub Actions 45068011240](https://github.com/Heitor2404/coringa-news/actions/runs/45068011240): **SUCCESS, 8 testes**.
- Resultado permitido: `ESTRUTURA_DECLARADA_OK_VISUAL_NAO_CERTIFICADO`. O gate valida um manifesto, **NÃO analisa quadros nem certifica estética**, não substitui revisão humana/VLM.

## Próximo portão (não inflar capacidade)

1. Usuário avaliar se a configuração completa e estilo de corte estão na direção certa. Ainda é SVG didático simples, não CAD mecânico ou modelo 3D real.
2. Somente se fizer sentido, integrar renderer `compressor_conjunto` ao motor V4 por modelo de componentes, não por exceção no tema. Preservar física `compressor_pv_core`, separar apresentação externa de cutaway interno e validar conexões em frame real.
3. Capturar referência animada realmente correspondente de compressor e obter/anotar eventos com atribuição e licença. Não declarar reconstrução reference-first só por ter visto fotos/diagramas.
4. Criar inspeção **por pixels e cenas** além do gate de manifesto, e bloquear inconsistência entre objeto anunciado e objetos efetivamente desenhados.

Produção, `main`, NTC, DOSSIÊ, `FilmeEditorial` e Telegram permanecem intocados. Não usou Claude.

## Integração reprodutível no laboratório — 22/11, após "Prossiga"

A fonte Python do render anterior estava descrita em documentação, mas **não existia mais no container ativo**; só o MP4 e as imagens estavam disponíveis. Em vez de afirmar que a fonte original foi recuperada, foi escrito um **novo renderer de laboratório** no repositório, baseado na configuração visual já testada, com parametrização e dependência do core P–V preexistente.

- `src/v4/formatos/render_compressor_conjunto_2d.py`: renderer **novo** da família `compressor_ar_eletrico_tanque_horizontal_correia`, CLI, SVG + CairoSVG + FFmpeg. Motor elétrico, polias, correia, bomba com cabeçote/aletamento, filtro, válvulas e corte de cilindro, descarga contínua ao tanque horizontal. Cálculo de `estado(t)` vem diretamente de `compressor_pv_core`. A rotação da polia motora é proporcional ao inverso do raio relativo da polia, preservando relação de transmissão.
- Renderizador só aceita manifesto topológico válido em `identidade_visual_maquina` e `publicar:false`. Sua identidade gráfica ainda é avaliada por desenho manual, não por segmentação automática ou importação de modelo 3D.
- `src/v4/formatos/reference_first.py`: `CompressorConjunto2D` cadastrado **como EXPERIMENTAL/NÃO APROVADO**, com capacidades visuais completas mas bloqueado em `verificar_renderizador()`. Falta validação visual externa independente e referência animada real.
- `tests/test_compressor_conjunto_2d.py`: verifica identidade, recusa da configuração Otto, física de pistão, correia, 4 fases e testes reais de **pixels do SVG** (janela muda, reservatório/motor/filtro/tubo presentes em ROIs), além de integridade/privacidade. `.github/workflows/qa-compressor-conjunto-2d.yml` renderiza realmente vídeo de 8s/24fps/540x960 e extrai 8 quadros para comparar evolução do pistão, pressão e fluxo.
- Primeira execução [45072897759](https://github.com/Heitor2404/coringa-news/actions/runs/45072897759) **SUCCESS, 20 testes**, MP4 renderizado. Auditoria viu que **título ainda estava muito alto na faixa que a interface de Reels/Shorts pode cobrir**. Corrigiu-se somente o cabeçalho — título baseline y168, etapa y207, descrição y239, barra y253, faixa de categoria y268; fundo de cabeçalho até y266. Peças mantiveram mesmo tamanho e posições físicas.
- **Versão final validada:** [GitHub Actions 45073144150](https://github.com/Heitor2404/coringa-news/actions/runs/45073144150) **SUCCESS — 21 testes novos/integrados, vídeo final e análise dos quadros**. Artifact **14773099622**, expira **27/11/2026 21:38 UTC**. MP4 8s/24fps/540×960 sem áudio, hash `d4b782778e15227a164fadcfc723c0b94b9c67011061eba7427fc54533bf42f8` era da primeira versão; **novo hash verificar no relatório**. QA da versão final: diferença média RGB pistão 47,704, pressão 39,373, fluxo 1,488 nos respectivos ROIs, o que prova mudança visual, NÃO correção semântica universal.
- Mídias verificadas localmente nesta execução em `/mnt/data/lab_compressor_completo_final/COMPRESSOR_CONJUNTO_2D_PRIVADO.mp4`, `CONTATO_8_FASES_COMPRESSOR_COMPLETO.jpg`, `QA_IMAGENS_E_INTEGRIDADE.json`. Revalidar paths em outra conversa antes de link.
- `main`, `FilmeEditorial`, NTC, DOSSIÊ, Telegram e o Claude continuam intocados. Não publicar. O próprio relatório JSON registra `identidade_por_pixels_aprovada:false` e `revisao_estetica:PENDENTE`.

**Avaliação independente:** fisicamente e estruturalmente muito melhor que o vídeo de pistão genérico, mas ainda tem aparência de motion gráfico didático e o produto ainda não reproduz automaticamente outras máquinas por pesquisa visual. A prova não deve ser apresentada como domínio de CAD, extração automática de atores ou identidade visual certificada. Aguardar aprovação da direção antes de integrar o template ao pipeline do Coringa.

## Revisão de composição — 22/11/2026, mecanismo 40 px acima

Pedido: “a área em azul escuro tá sendo mal aproveitada”, “subir mais a animação”. Feito na branch experimental, sem Claude nem alterações em produção.

- Em `src/v4/formatos/render_compressor_conjunto_2d.py`, campo reutilizável `AssemblyLayout.mechanism_lift_px = 40.0` e agrupamento SVG único `<g id="machine-assembly" transform="translate(0 -40.0)">`. Move **todas** as peças, filtro, correia, bomba, válvulas, tanque, partículas e card de pressão; cabeçalho y0–266, faixa de categoria y268–300 e rodapé y905+ preservados. O tamanho físico das peças e as equações P–V não mudaram. O limite é 44px, pois maior subida faria rótulos/peças invadirem a faixa editorial; para ocupar mais do topo azul precisaria redesenhar cabeçalho respeitando overlays de Reels/Shorts.
- Testes extras de transformação integral, invariância do cabeçalho, alterações reais de pixels e limite de subida em `tests/test_compressor_conjunto_2d.py`.
- [GitHub Actions 45073742153](https://github.com/Heitor2404/coringa-news/actions/runs/45073742153) **SUCCESS**: 24 testes, render MP4 8s/24fps/540×960, QA de oito quadros; artifact **14774311938** expira **27/11/2026 21:45 UTC**. Mídias verificadas nesta sessão: `/mnt/data/compressor_completo_subiu_40px/COMPRESSOR_CONJUNTO_2D_PRIVADO.mp4`, `CONTATO_8_FASES_COMPRESSOR_COMPLETO.jpg`, comparação com versão anterior `/mnt/data/comparativo_compressor_conjunto_40px_nov22.jpg` (verificar paths no próximo chat).
- Auditoria visual dos 8 quadros: bomba completa ficou mais central, filtro e seu rótulo ainda abaixo da faixa de categoria, tanque totalmente dentro do frame; cabeçalho/legenda essencial intocados. Ainda é um protótipo SVG didático; aprovação estética e identificação automática de máquinas pendentes. `publicar=false`.
 
## Segunda reorganização — cabeçalho compacto e montagem 100px acima

Em 22/11, após reclamação de área azul-escura desperdiçada, `EditorialHeader` compartilha as posições compactadas em `render_compressor_conjunto_2d.py`. O topo do fundo azul cai de 266 para 202px, linha de categoria termina em 235px; `AssemblyLayout.mechanism_lift_px=100` mantém FILTRO separado da faixa (folga mínima programada 7px), tanque e rodapé sem recorte. Qualquer subida maior é BLOQUEADA pelo cálculo `max_mechanism_lift_px`.

[Actions 45074956737](https://github.com/Heitor2404/coringa-news/actions/runs/45074956737): 25 testes passando, MP4 real privado 8s, 8 quadros de amostra e QA dos ROIs relativo à subida; artifact 14775086810. **Qualidade artística ainda não homologada; não publicar.**
