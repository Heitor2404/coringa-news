# Componentes editoriais — origem, licenças e dependências

Este protótipo **não copia código** de terceiros. A coreografia de cada componente (ordem dos gestos e tempos de entrada) foi estudada nos componentes abaixo do **HyperFrames** (HeyGen, licença Apache-2.0) e reescrita no motor próprio do Coringa, que usa `seek(t)`, sem GSAP e sem o runtime do HyperFrames.

| Componente do Coringa | Referência no HyperFrames | O que foi aproveitado | O que foi descartado |
|---|---|---|---|
| abertura | `titlecard-lockup`, `titlecard-calm` | kicker mono, título que assenta, traço que se desenha | fundo claro, wordmark de produto, variáveis do runtime |
| revelacao | `headline-slam`, `editorial-flash-overlay`, `marker-highlight` | assentamento com 3 quadros de tremor, clarão curto, marcador na palavra | escala exagerada, cores de marca |
| mapa | `nyc-paris-flight`, `north-korea-locked-down` | aproximação de câmera, arco que se desenha, rabisco no destino, etiqueta que salta | **mapa raster CARTO/OSM**: o Coringa usa vetor Natural Earth |
| etiqueta | `vox-annotate`, `lt-kicker-name` | anel desenhado, conector fino, faixa de tipo, nome forte | cartão branco, estética de podcast |
| encerramento | `logo-brand-close` (e `cta-close` como contraexemplo) | marca letra a letra, ponto de destaque por último | botão de CTA em cápsula (corporativo) |

## Dependências em tempo de execução

Todas já estão no `node_modules` do Coringa e já são usadas pelo template atual:

- `d3-geo` e `d3-array`: licença ISC.
- `topojson-client`: licença ISC.
- `world-atlas`: licença ISC. Redistribui os dados do Natural Earth, que são de domínio público.
- Fontes Montserrat e JetBrains Mono (via `@fontsource`): licença SIL OFL 1.1.

Nenhuma CDN é usada, nem o GSAP, nem rede.

## Mídia das demonstrações

São placeholders usados apenas para mostrar os componentes; não são imagens do acervo.

- `midia/pele_macro.jpg`: gerada pelo motor ESQUEMA.
- Fundo "oceano": gerado em SVG.
- `assets/img/fundo_b.jpg`: ilustração que já está no repositório do Coringa. Na demonstração, a própria etiqueta a declara como "ILUSTRAÇÃO".
- Mascote: `assets/mascote3d/apontando.png`, do próprio canal.
