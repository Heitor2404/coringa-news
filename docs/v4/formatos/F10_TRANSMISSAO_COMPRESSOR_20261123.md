# F10 — transmissão por correia parametrizada no compressor completo (23/11/2026)

**Estado:** implementação técnica e vídeo privado comprovados; estética e identidade industrial ainda NÃO homologadas.

## Objetivo e contexto

Depois da F7 (primitiva `transmissao_correia`), F8 (entrada SVG autoral) e F9 (referência visual externa bloqueada por HTTP 429), a F10 conecta **o compressor de oficina completo** à mesma primitiva de correia usada pela montagem mecânica configurável, sem reescrever a máquina nem importar/afirmar ter copiado uma referência.

O motor atual continua representando **compressor elétrico por correia com bomba alternante e reservatório horizontal**; NÃO foi criado um novo compressor industrial reconhecido de fábrica. A representação permanece ilustração didática.

## Alterações reais

- `primitivas_fisicas_parametricas.py`: `transmissao_correia(..., deslocamento_trama_px=None)` preserva saída antiga quando argumento omitido. O opt-in agrega marcas `stroke-dashoffset` sobre o caminho tangente calculado; entradas impossíveis, NaN e posições fora do palco são bloqueadas.
- `render_compressor_conjunto_2d.py`: novo `transmissao_parametrica=True` e flag CLI `--transmissao-parametrica`, desligada por padrão. Traçado calculado de **centros e raios físicos parametrizados** das duas polias; relação tangencial ideal sem escorregamento. Correia no modo F10 é desenhada **ATRÁS das faces opacas das polias**, sem cruzá-las visualmente. O modo anterior mantém ordem e pixels antigos.
- Compressor P–V, pistão, válvulas, fluxo, motor, tanque, editorial, tempo de vídeo e câmera F2B estável não foram convertidos em nova física nem refeitos por tema.
- `tests/test_transmissao_parametrica_f10.py`: primitiva compartilhada, reuso F7, invariância de câmera e texto em SVG, geometria invalidada, movimento de marcas e ordem de pintura da correia.
- `.github/workflows/qa-transmissao-compressor-f10.yml`: valida e renderiza **dois vídeos reais**, versão anterior e opt-in, em ambiente CI sem IA, Telegram ou publicação.

## Evidências auditadas

**Workflow final:** https://github.com/Heitor2404/coringa-news/actions/runs/45122774333 — `SUCCESS` no commit `73990ea89a63f14fc9f3bc45e719b2331d4fe95a`: **58 testes aprovados, 11 warnings Pillow**, MP4s renderizados e folha de quadros.

**Artifact:** `lab-f10-compressor-correia-antes-depois-privado`, ID **14794895623**, expira **28/11/2026 ~06h15 UTC**. Baixado e verificado. Contém:
- `COMPRESSOR_F10_ANTES.mp4`: 540×960, 24 fps, 8.000 s, sem áudio; SHA256 **`45a848b92ba7da35886590cac856584a1938825875af02a3ca1eeaffa2f4f3a5`**, preserva resultado F2B anterior.
- `COMPRESSOR_F10_CORREIA_PARAMETRICA.mp4`: 540×960, 24 fps, 8.000 s, sem áudio; SHA256 **`2ab986d07f4c6e9008c172f7f4582b4002ed23a14e1d2c99ae9e347eb3b97e4c`**.
- `COMPARATIVO_COMPRESSOR_F10_8_QUADROS.jpg`, quadros individuais, `QA_F10_TRANSMISSAO.json` e relatórios de cada MP4.

**QA de quadros de MP4 (H.264):** diferença média na região da correia ~4,47 a 5,04 RGB entre os dois modos nos quatro instantes; texto do header registrou 0 a 0,3124 RGB por ruído de quantização do codec, mas a igualdade **exata** dos pixels do SVG rasterizado é testada no teste Python; rodapé ~0 a 0,0022 RGB. A tolerância de H.264 evita falso positivo de renderização comprimida, não relaxa a invariância do SVG.

**Inspeção visual da prancha REAL em conversa nova após transmissão interrompida:** o compressor completo permanece grande no palco claro, mostrando motor elétrico à esquerda, bomba em corte no centro, filtro no topo, descarga e reservatório embaixo. A correia geométrica/face das polias melhorou a coerência local; **mudança é pequena para o público geral**. Os quatro estados (reexpansão, admissão, compressão, descarga) seguem com textos e câmera estável. Imagem não demonstra conformidade total com interfaces de Reels/TikTok/Shorts nem validação por especialista mecânico.

**Regressões:** `qa-compressor-conjunto-2d` run `45122474566` SUCCESS, `qa-realce-causal-svg` run `45122474743` SUCCESS após integração da pintura da correia. F10 foi isolada; não interpretar falhas e cancelamentos intermediários como falha do último commit.

## Limites e decisões

1. Reuso do código de cinemática/traçado é ganho REAL; não equivale a pesquisa, segmentação de peças externas, transferência automática de geometria ou geração universal 2D/3D.
2. Os números de pressão e a relação ideal entre polias continuam **modelo didático**, não calibração dimensional/RPM de compressor específico.
3. Ganho estético da F10 é incremental, não resolverá sozinho a qualidade de um vídeo final. Não ativar automaticamente para publicação, não adotar composições antigas miniaturizadas e não refazer o visual aprovado de cada episódio por improviso.
4. A ilustração Commons da F9 continua **não adquirida por HTTP 429, SHA ausente**. A F10 não se apropria da licença dessa ilustração.
5. Para próxima fase, priorizar **identidade visual de máquina e ação específica demonstrada**: produzir contrato de geometria/encaixe/escala para componentes de máquina inteira com referência real verificável (sem reproduzir tipo errado), e testar a capacidade em outra família, não só card/efeito de correia. Preservar plano geral legível e checagens de área segura para vídeo mobile.
6. Produção, `main`, NTC, DOSSIÊ, Telegram, publicação e voz ficaram **intocados**. A F10 está apenas na branch experimental `atlas-direcao-visual-20261118`.
