# Piloto real Ever Given (V2.2) — material preservado para regressão

Execução única do fluxo real (GitHub Actions, piloto-v22, execução 43540333049, commit 4b9fd30, 13/11/2026).
Nada aqui foi editado à mão, exceto o que está listado em "Reconstruções".

| Arquivo | Origem |
|---|---|
| roteiro.json | `roteiro.json` do pacote de diagnóstico (roteirista real, com contratos e a pesquisa em `fatos`) |
| acervo.json | `acervo.json` do diagnóstico (catálogo do acervo: título, `mostra`, tipo, ano, crédito) |
| v1_cenas_original.json | cenas que o fluxo real entregou ao motor V2.2 (tempos da voz de produção) |
| v2_dados_original.json, direcao_original.json | o que a V2.2 montou e a decisão do seletor por cena |
| fiscal_original.json, relatorio_original.json | fiscal V2.2 do piloto (26 bloqueios) e medidas (−18,5 LUFS) |
| cobertura.json | classificação de cobertura da produção |
| img/*.jpg | as 10 imagens usadas (graduadas pela produção), reduzidas a 1080 px |
| audio_final_piloto.ogg | áudio do vídeo final do piloto (Opus 96 kbps) |

## Reconstruções

- `acervo.json` ganhou o campo `arquivo` (o nome do arquivo de cada id). O diagnóstico original não tinha esse
  vínculo: os arquivos são numerados pela ordem de download e os ids depois do filtro (achado 7 do piloto).
  O vínculo veio dos pares que o próprio piloto registrou: `foto` da cena no roteiro ↔ `img` da mesma cena.
  Cada id corresponde a exatamente um arquivo.
- Caminhos `/home/runner/...` das cenas são resolvidos pelos testes para `img/<nome>`.

## Licenças das imagens (créditos do próprio acervo)

Copernicus Sentinel 2021 / Pierre Markuse (CC BY 2.0) · Robert Schwemmer / NOAA (CC BY-SA 2.0) · Suez Canal Authority
(domínio público) e derivado (domínio público) · NASA JPL (domínio público) · kees torn (CC BY-SA 2.0) · S.J. de Waard
(CC BY-SA 3.0), via Wikimedia Commons / Openverse.
