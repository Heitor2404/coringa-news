# Filme Taiwan 27,445s — portão editorial e lacunas de mídia (19/11/2026)

## Estado técnico e editorial

**BLOQUEADO_EDITORIAL_SEM_PROVA.** A autorização para seguir com o piloto significa completar provas antes de gerar Gemini Charon ou renderizar, **não autoriza repetir o slideshow rejeitado anteriormente**. Planos, validadores e relatórios apenas na branch experimental `atlas-direcao-visual-20261118`; sem alteração de `main`, NTC ou publicação.

### Rodada real

Workflow `.github/workflows/qa-filme-taiwan-portao.yml` com gatilho `.github/qualidade/filme_taiwan_portao.txt`: **run 44596487271 SUCCESS, 34 testes e relatório**, artefato **14565822829** (`qa-taiwan-acervo-antes-de-narracao`). O sucesso é do **bloqueio correto**, não da qualidade do filme.

O portão encontrou **10 bloqueios**: mídia de vídeo sem curadoria, prova de roteiro insuficiente, ausência de arquivo de mapa nesse runner, relação equipamentos/fábrica sem prova e último acontecimento sem fonte. Até agora, **0 vídeos reais de ação conferida** e **0 mapas com comprovante local neste runner**; mapa ATLAS de Taiwan 2,6s existe e foi validado separadamente no run **44588617776**, precisa apenas ser recuperado com o sidecar na execução do filme.

### Quadro por cena (início/fim na referência de 27,445 s)

| Cena | Instante | Evidência prometida | Situação |
| --- | --- | --- | --- |
| 01 Fab18 | 0–2,5 | Fachada TSMC REAL, identificada | Foto no catálogo V4, SHA/licença; não mostra máquinas/processo |
| 02 mapa Taiwan | 2,5–5,1 | Mapa geográfico útil | ATLAS original disponível no artifact 14564100281; **ainda não copiado ao runner do filme** |
| 03 chip em movimento | 5,1–7,8 | Objeto real em vídeo | Mixkit `microchip-technology-close-up-1140` anuncia Free License comercial; **não ingerido em bytes, sem SHA ou inspeção** |
| 04 wafer | 7,8–11,0 | Wafer de silício real e ilustrativo | Foto comprovada Commons, não é fábrica TSMC |
| 05 equipamento | 11–14,8 | Ferramenta de fabricação | UC Davis Cleanroom (45490137372) no Commons com CC BY 2.0 e revisão FlickreviewR (2019), mas **fora da biblioteca V4** |
| 06 fabricação em operação | 14,8–18,7 | Vídeo de processo físico real | STMicroelectronics `How ST designs and manufactures...` marcado **License review needed** no Commons: não aproveitar até comprovar licença/autoria/uso; não é TSMC |
| 07 relação internacional | 18,7–22,3 | Equipamentos/suprimento realmente ligados à fábrica | Não há prova audiovisual da relação. Cartão com EUA/Holanda/Taiwan não vale |
| 08 consequência | 22,3–27,445 | Desdobramento real da dependência | Fonte e ação ausentes; slogan não é payoff |

**Fonte da narração:** `tests/dados/atlas_chips_v2_tts_real_run_44450584008.json` contém **timestamps de 27,445s de uma execução histórica de Charon**, mas NÃO o arquivo WAV correspondente. Não fingir que temos voz original preservada. Gerar Gemini Charon só depois do portão visual (ou recuperar pacote original verdadeiro com SHA). Nenhum TTS novo feito.

## O que foi implantado

- `docs/v4/formatos/CONTRATO_PILOTO_TAIWAN_INTEGRAL_20261119.json`: oito cenas, ação/referente por etapa, origem conhecida ou candidatura NÃO curada, tempos, rubrica de diversidade, mandato de não publicar.
- `src/v4/formatos/gate_filme_completo.py`: portão independente de tema que lê o catálogo **já existente** via `ponte_biblioteca.catalogo()`, não inventa banco de imagens. Exige mídia com origem/licença/SHA e inspeção, capacidade de vídeo mostrando a ação, mapa autenticado via `ponte_mapa_atlas.validar_comprovante()`, não repetição, foto não excessiva, evidência de relação/resultado e preset Gemini Charon. WAV só conta após existir com hash e referência de texto; timestamps não contam como som.
- `tests/test_gate_filme_completo.py`: aprova exemplo **sintético explicitamente curado**, bloqueia caso real incompleto, vídeo falsificado por fotografia, repetição de foto, falta de prova de causalidade e Edge como voz final. 
- Workflow não baixa mídia, não executa renderização nem chama Gemini; grava diagnóstico privado.

## Fontes candidatas (NÃO aprovadas automaticamente)

- <https://mixkit.co/free-stock-video/microchip-technology-close-up-1140/> — vídeo real do chip em placa, Mixkit Free License publicada, 11 s; não prova fabricação em TSMC. Curar no V3/V4 com arquivo, SHA, inspeção quadro a quadro e contrato de licença antes de usar.
- <https://commons.wikimedia.org/wiki/File:UC_Davis_Cleanroom_(45490137372).jpg> — foto de sala limpa/litografia UC Davis, CC BY 2.0 e licença revisada; falta download/curadoria/hash do projeto.
- <https://commons.wikimedia.org/wiki/File:How_ST_designs_and_manufactures_semiconductor_devices.webm> — gravação real de outra fabricante, porém **licença não revisada** (YouTube→Commons). Bloqueio até evidência suficiente; não tratar ST como fábrica Taiwan.
- <https://commons.wikimedia.org/wiki/File:How_EUV_lithography_works.webm> — IBM, igualmente **License review needed**; não utilizar como fallback só porque combina semanticamente.
- Biblioteca original conserva Fab18 e wafer em `src/v4/biblioteca_comprovada.json` com hashes e fontes.

## Próximo trabalho de fato

**Curadoria de pelo menos dois clipes diferentes com movimento físico observável e licença comercial verificada**, uma prova visual adequada para o elo da cadeia e uma consequência factual verificável; recuperar clipe ATLAS com sidecar via artifact de GitHub (sem rerender); só então montar plano audiovisual de 25–30 s, produzir uma única voz Charon sincronizada e submeter ao QA por cena + Telegram privado. Se fonte de ação não existir, mudar roteiro ANTES de gastar TTS, em vez de substituir por mapa/pan/etiqueta.

**Nenhuma nova prévia foi entregue ou publicada nesta rodada.**