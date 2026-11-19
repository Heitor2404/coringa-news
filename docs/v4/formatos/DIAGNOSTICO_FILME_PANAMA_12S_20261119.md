# Filme Editorial — prova Panamá 12 s (19/11/2026)

**Status: NÃO APROVADO PARA PUBLICAÇÃO OU EXPANSÃO AUTOMÁTICA.**
**Branch isolada:** `atlas-direcao-visual-20261118`. Nenhuma mudança em `main`, NTC ou DOSSIÊ.

## O que foi realmente produzido

Compositor novo `motor4/remotion/src/formatos/FilmeEditorial.tsx`, registrado em `Root.tsx`, desligado do antigo ATLAS de slots/mapas/cartões. Contrato no Python `src/v4/formatos/filme_editorial.py`; mídia com procedência e SHA; storyboard `docs/v4/formatos/filme_panama_12s_prova.json`.

O experimento final teve **12,0 segundos, 540 × 960 pixels (escala 0,5, amostra de qualidade, não formato final), sem áudio, sem Claude, sem APIs de imagens, sem publicação**.
- 0–3s: filmagem U.S. Navy transitando pelo Canal do Panamá (arquivo já versionado).
- 3–6,6s: mecanismo 2D da eclusa. A água entra, o nível da câmara sobe e o navio sobe com ela. **Esquema original ilustrativo, não registro real daquela eclusa.**
- 6,6–9,3s: foto real das eclusas de Gatún, março de 1913, Library of Congress.
- 9,3–12s: timelapse real da passagem pelo Canal do Panamá (arquivo já versionado).
- Fonte visual/página/licença em `tests/midia/*.json` e `motor4/formatos/dados/raster/*.json` para demais mídias. Os clipes utilizados são U.S. Navy domínio público e Morrison Mast CC BY 3.0; foto de 1913 domínio público.
- GitHub Actions `44467983265`: `success`, artefato `filme-panama-12s-prova-movimento-privada` (7 dias). Quadro de auditoria: `contato.jpg`, `props.json`, `midias.json`, `contrato.json`, `prova_panama_12s.mp4`.

## Problemas constatados e corrigidos no próprio turno

1. Primeiro experimento Taipei usava seis fotos e mapa sem ação e falhou ao baixar mídia externa (Wikimedia 429); não insistir.
2. Primeiro teste Panamá renderizou cenas full-bleed e vídeo real, mas **reprovado editorialmente**: grande volume de mar/céu na imagem do navio, mapa genérico e foto histórica sem explicar mecanismo.
3. Segunda prova substituiu mapa por **movimento físico do processo hidráulico**; detectadas sobreposições entre título, legendas explicativas SVG e callouts.
4. Terceira prova `44467983265`: removidas sobreposições e legendas repetidas, padronizada fonte sans na animação; render final da AMOSTRA e QA técnico passaram.

## Veredito editorial atual

**Melhor que slides porque tem movimento causal visível na cena da eclusa, mas ainda NÃO é um documentário no nível dos dois vídeos de referência.** O material do navio é distante e mostra a proa/água, não uma ação de eclusa. Os 12 s não têm narração, sincronização, sound design ou montagem contínua completa; não confundir com episódio aprovado.

**Próximo trabalho correto:** escolher footage onde o evento ocorre visivelmente (eclusa/navio entrando/saindo), ou filmagem equivalente verdadeiramente representativa com identificação honesta; refinar a anatomia física da eclusa e a conexão entre objeto real e esquema; avaliar o filme completo e não apenas contagem de fotos, passes e storyboards. Se não houver mídia adequada, **não renderizar 60s**.

## Princípio de arquitetura

Substituir **somente** a direção/montagem, preservando pipeline funcional de roteiro, voz, licenças, legendas, render e Telegram. O compositor não pode pressupor mapa ou fluxo de cards como template obrigatório. Usa filmagem real, comparação, cenas de foto com eventos e mecanismos de engenharia quando a história exige. Aceita representação autêntica de objetos genéricos, mas não implicação de identidade específica falsa. Não promover como motor produtivo sem passar em **dois temas** e avaliação audiovisual explícita humana.
