# Rasters do palco ATLAS — procedência e licença

| arquivo | conteúdo | fonte | licença | atribuição exigida na tela |
|---|---|---|---|---|
| `ne2_istmo_panama.jpg` | relevo sombreado + cobertura do solo + fundo do mar, reprojetado (Web Mercator) e com a grade do canal | Natural Earth II `NE2_HR_LC_SR_W` (1′) — sha256 da fonte no `.json` | domínio público | "Relevo: Natural Earth II" (cortesia) |
| `s2_panama_canal.webp`, `s2_miraflores_eclusas.webp`, `s2_gatun_eclusas.webp` | imagem orbital (mosaico sem nuvens) × sombreamento do relevo; acabamento (gama, cor) e borda suave em alfa (WebP) | Sentinel-2 cloudless **2016** (EOX, camada `s2cloudless_3857`) + Terrain Tiles (AWS Open Data) | **CC BY 4.0** (só a edição 2016; 2018+ são CC BY-NC-SA e NÃO podem ser usadas em vídeo monetizado) | "Sentinel-2 cloudless 2016 · EOX IT Services GmbH · s2maps.eu (modified Copernicus Sentinel data 2016 & 2017)" |

Gerados por `scripts/formatos_ne2.py` (local, a partir do GeoTIFF oficial) e `scripts/formatos_raster.py` (coleta
`formatos-coleta.yml`, execução 44100398329). Nenhum tile comercial (Esri/Google/Mapbox) é usado.
A composição desenha a atribuição de cada raster visível no rodapé do mapa (`data-atribuicao`), e o preflight recusa
raster sem `.json` de procedência.
