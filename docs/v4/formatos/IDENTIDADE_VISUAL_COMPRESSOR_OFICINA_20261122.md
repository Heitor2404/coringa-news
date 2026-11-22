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
