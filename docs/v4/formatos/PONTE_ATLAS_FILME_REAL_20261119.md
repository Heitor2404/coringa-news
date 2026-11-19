# Ponte ATLAS → FilmeEditorial (19/11/2026)

## Problema resolvido

O usuário rejeitou qualquer mapa elementar ou reimplementação da cartografia. Já havia \`PalcoMapa\`/MapLibre em \`motor4/remotion/src/formatos/Palco.tsx\`, com bases raster de relevo/satélite, câmera, pins, rotas, escala e atribuição. A nova integração **não desenha mapas** e **não reimplementa essa camada**.

## Contrato implementado

\`src/v4/formatos/ponte_mapa_atlas.py\` fornece três operações:
- \`prepare\`: exige plano **ATLAS já resolvido** e \`P.validar\` sem falhas; verifica ROI, seleção de palco cartográfico original, raster efetivamente ativo/nítido, hashes SHA-256 do manifesto e aprovação comercial das fontes. Copia os **mesmos arquivos de raster** para \`motor4/remotion/public/_formato/raster\` e gera \`props_atlas_formato.json\` com \`plano.props\`/Remotion \`Formato\` original. **Não cria mapas novos.**
- \`confirm\`: aceita somente MP4 gerado com 1080×1920, intervalo exato, sem áudio; extrai amostras de quadros reais e guarda \`comprovante_atlas.json\` com hash do MP4, raster de origem, ROI e câmera. Resultado: \`PRONTO_PARA_REVISAO_HUMANA\`, nunca \`APROVADO\`.
- \`attach\`: só permite substituir um shot existente num storyboard \`PROVA_VISUAL_PRIVADA\` e somente se o SHA do MP4 corresponder ao comprovante; exige mesma duração do shot e marca o vídeo \`atlas_map\`, \`evidence=explainer\`, \`atlas_direcao\`, referente e intenção. Não altera os demais shots. Os mapas não são registro histórico nem substituição enganosa.

\`FilmeEditorial.tsx\` agora reconhece **\`atlas_map\`**, que recebe o MP4 gravado pelo ATLAS, em tela inteira com \`objectFit:contain\`, sem crop/zoom/gradiente adicional, preservando rótulos, pins, créditos e composição originais. A barra de progresso global continua no compositor do episódio. O antigo tipo \`map\` permanece **F-MAPA-PROIBIDO**.

\`filme_editorial.py\` exige \`validar_comprovante\` para cada clipe ATLAS, confere que é \`video\` e que tem fonte e licença explícitas. \`contrato_visual_comum.py\` usa intenção \`LOCALIZAR\` e rubrica \`mapa_informativo\`; \`direcao_eventos.py\` só admite o \`atlas_map\` para \`localizar\`/\`trajeto\` e requer ROI e direção, em vez do desenho simplificado.

**Voz:** não foi gerada nem alterada. O preset produtivo do canal segue **Gemini Charon**, sem fallback Edge; a aprovação auditiva humana continua obrigatória. A ponte prepara mapas silenciosos para avaliação antes de consumir cota.

## QA e resultados

- \`tests/test_ponte_mapa_atlas_filme.py\`: plano ATLAS original, requisitos de raster real, hash e integridade, importação ao filme sem alterar a narrativa, rejeição de arquivo adulterado/comprovante ausente, mapa primitivo proibido, intenção geográfica, proibição de Edge na produção.
- Workflow \`.github/workflows/qa-ponte-atlas-filme.yml\`, gatilho \`.github/qualidade/ponte_atlas_filme.txt\`: sem render, sem rede de mídia e sem TTS. **Run 44586313967 SUCCESS: 135 testes, TypeScript e preparo de mapa original com um raster ativo autenticado.** O primeiro run 44586057951 falhou por dependências de teste ausentes; CI corrigido.
- Workflow de prova audiovisual privada \`.github/workflows/qa-mapa-atlas-taiwan-filme.yml\`, gatilho \`.github/qualidade/mapa_atlas_taiwan_ponte.txt\`: usa *plano existente de Taiwan/chips* e timing de palavras **real registrado de Gemini Charon** (nenhuma chamada Gemini nova) para renderizar apenas 2,6 s de cartografia ATLAS original, validar MP4 real, e integrar o resultado como primeiro shot no storyboard \`filme_taiwan_prova.json\`. **Somente se todos os gates passarem.** Não enviará ao Telegram nem publicará sem inspeção visual.

## Limites que NÃO podem ser omitidos

- Contrato e pré-produção funcionando ≠ demonstração estética; somente quadros reais inspecionados permitem julgar o mapa.
- Integração permite reutilização no **FilmeEditorial**, mas a escolha automática de qual trecho geográfico e qual momento usar ainda depende de direção/roteiro e validação factual. Não promete que já esteja conectada ao workflow diário de produção.
- **Run de render nativo 44587183552 SUCCESS**: janela Taiwan do ATLAS (2,5–5,1 s), raster `ne2_asia_leste` verificado, MP4 real 1080×1920 de 2,6s, sem áudio, sidecar autenticado, importado e validado pelo storyboard `filme_taiwan_prova.json`. Artefato `14560809433` (`qa-taiwan-mapa-atlas-original-integrado-filme`). **Inspeção de cinco frames do MP4 local** constatou relevo físico real e Taiwan corretamente destacado, muito superior ao mapa elementar rejeitado. Porém o primeiro 0,1s da janela mostrou transição escura com resquícios da cena anterior — **não aprovar ainda essa versão visual**.
- A ponte recebeu bloqueios genéricos `F-ATLAS-ENTRADA-ESCURA` (entrar somente após 0,55 s da troca de palco, evitando fade preto) e `F-ATLAS-ATRAVESSA-BEAT` (proíbe um clipe que atravesse outro beat). Foi ajustada a janela de Taiwan para iniciar após essa transição e acrescentados testes `tests/test_ponte_mapa_atlas_filme.py`. Nova execução de render `44588617776` em andamento ao registrar esta atualização. Não declarar essa versão aprovada até inspecionar seus quadros.
- Este workflow é **prova de cartografia real dentro da arquitetura**, não um episódio final e não usa a voz de produção; a intenção continua ser entregar uma versão visualmente adequada só depois de inspeção real.
- \`main\`, NTC, DOSSIÊ e produção diária continuam intactos; nenhum vídeo publicado.

## Referência de uso em CI (sem executar automaticamente em produção)

\`\`\`bash
python -m src.v4.formatos.ponte_mapa_atlas prepare atlas_resolvido.json stage_atlas/clip --start 2.5 --duration 2.6 --public motor4/remotion/public
# render nativo com Remotion Formato usando --props stage_atlas/clip/props_atlas_formato.json e --frames START-END
python -m src.v4.formatos.ponte_mapa_atlas confirm stage_atlas/clip stage_atlas/clip/mapa.mp4
python -m src.v4.formatos.ponte_mapa_atlas attach filme.json shot_id stage_atlas/clip/mapa.mp4 stage_atlas/clip/comprovante_atlas.json stage_atlas/clip/filme_com_mapa.json --intent localizar
\`\`\`
