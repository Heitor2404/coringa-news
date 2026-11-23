# F5 — biblioteca verificável de componentes físicos (ATLAS)

**Data:** 23/11/2026. **Escopo:** branch `atlas-direcao-visual-20261118`, QA privado, sem Claude e sem publicação.

## Inventário reutilizado
Não duplicar ferramentas já existentes:
- `ponte_biblioteca.py` integra mídia V3, licença, autoria e SHA para conteúdo editorial; **não** garante que uma peça de máquina esteja visível no fotograma.
- `referencias_mecanismos.py` encontra **candidatos** Commons / Sketchfab, mas metadados e licença declarada não são provas de rig, componente animável nem direitos efetivos.
- `grafo_causal.py` é a fonte de atores/relações/estados.
- `camera_causal_geometrias.json` tem caixas de segurança de todas as fases.
- `realce_causal_svg.py` já enfatiza peças e trajetos curados.
- `identidade_visual_maquina.py` já contém um gate específico do compressor.

A lacuna de F5 era o vínculo verificável ator→tipo→caixa→SVG→origem da física, consumido pelo **mesmo** contrato em três renderizadores.

## Artefatos
1. `src/v4/formatos/biblioteca_componentes_fisicos.json`: 3 famílias; **29 atores** e **13 tipos** (rotor, transmission, piston, chamber, filter, valve, conduit, reservoir, fluid_body, igniter, channel, gate, floating_vessel). Não são 29 assets criados.
2. `src/v4/formatos/biblioteca_componentes_fisicos.py`: `validar`, `etiquetar_svg` e `fichas`. Bloqueia peças essenciais ausentes, duplicadas, fonte malformada, direitos presumidos, renderer/ator/câmera incoerentes; etiqueta os grupos SVG reais `data-primitive`, `data-source-tech` e `data-visual-identity=PENDENTE`. Zero pixels novos.
3. `src/v4/formatos/rastreador_componentes_svg.py`: bbox **no instante** derivada da primitiva e da transformação SVG, só 3 rastreadores curados (cabeçote compressor, pistão Otto, navio inteiro da eclusa). Distinguir **bbox instantânea** de **envelope de movimento** da câmera. Nunca afirmar detecção por VLM. O cabeçote do compressor não mede a biela; constar no scope.
4. Renderizadores Python de compressor, Otto e eclusa agora passam pelo catálogo (componente ausente gera bloqueio do frame). No Otto, 5 atores antes sem ID foram identificados; grupos de ar inativos permanecem vazios.
5. `tests/test_biblioteca_componentes_fisicos.py` e `tests/test_rastreador_componentes_svg.py`. Workflow `.github/workflows/qa-biblioteca-fisica-multifamilia.yml`.

## Fontes técnicas externas, SEM direitos de imagem
- Compressor alternativo — **Atlas Copco**, explicação pública de pistão, cilindro, válvulas e fases de compressão: https://www.atlascopco.com/en-ca/compressors/wiki/compressed-air-articles/piston-compressors
- Motor Otto 4 tempos — **U.S. Department of Energy**, admissão, compressão, ignição/expansão e escape: https://www.energy.gov/cmei/vehicles/articles/internal-combustion-engine-basics
- Eclusa — **U.S. Army Corps of Engineers**, enchimento por gravidade através de válvulas e condutos: https://www.swl.usace.army.mil/Missions/Water-Management/Water-Management-FAQ/

Essas páginas são **fontes textuais de funcionamento**, não assets incorporados, licença para replicar desenho, reconhecimento automático de referência nem prova de fidelidade do modelo 2D. A geometria das três provas é de desenho próprio, e sua aprovação humana segue **PENDENTE**.

## QA real
[Run **45113985166**](https://github.com/Heitor2404/coringa-news/actions/runs/45113985166): **SUCCESS, 84 testes**, 11 avisos Pillow, **3 PNGs** 540×960 e folha combinada com as peças monitoradas, JSON de cobertura. Artifact **14789724951**, até **28/11/2026 04:48 UTC**. Primeira execução `45113581772` também teve 80 testes aprovados; ao inspecionar sua prancha, detectou-se marcação enganosa de **envelope total** como se fosse bbox da peça atual. A prova final usa o rastreador do SVG real para 3 atores, **sem câmera móvel**.

## Metas ainda não alcançadas
- Não existe detector confiável de peças em imagens do mundo real, extração automática de geometria de vídeos, downloads licenciados nem geração de modelo 3D novo.
- Não existe compositor paramétrico universal: apesar de 13 tipos, os desenhos/física ainda estão curados por família.
- A existência dos 29 IDs SVG não significa que os 29 componentes estejam fisicamente corretos ou legíveis; só alguns são validados por dinâmica e quadro.
- Bloqueadores continuam ativos: novas famílias sem grafo/rig/geometria, fonte sem licença de pixels, e estética não aprovada.

**F6 proposta:** componentes realmente desenháveis/animáveis (primitivas paramétricas) compartilhados entre famílias + entrada de referência visual auditável; só então testar um **quarto mecanismo** sem novo script específico completo.
