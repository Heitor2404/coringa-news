# Motor audiovisual V4 — arquitetura integral (ramo `motor-integral-v4`, 16/11/2026)

Base: HEAD `15e16e2` de `piloto-v24-lagartixa`. O V3 (`MOTOR_VISUAL=v3`) e a produção continuam intactos. O V4 é um caminho
paralelo (`python -m src.v4 …`) até ter substituição comprovada.

## Fluxo

```
pedido (.github/v4/pedido.json: pergunta, fatos COM fonte, famílias exigidas)
  → diretor.py      IA escreve o roteiro e escolhe POR CENA: modalidade → componente → parâmetros (frações da cena)
  → contrato.py     impor(): câmera sem motivo → fixa; transição sem motivo/proibida → corte (registrado)
                    validar(): ação física sem demonstração, recuo sem revelação, asset sem licença, rota sem fonte,
                    repetição de mídia, continuidade de tempos… → 1 correção dirigida da IA; o resto vira bloqueio
  → acervo_v4.py    Commons/vídeos livres, escolha por visão (Gemini cota grátis) + ROI; crédito/licença do PRÓPRIO arquivo
  → voz (herdada)   narração real (Gemini TTS) + tempos por palavra (faster-whisper) → frações viram segundos
  → episodio.py     render de cada cena no backend do componente (uma tentativa; falha = registrada, nunca disfarçada)
  → compositor.py   clipes 1080×1920@30 → linha do tempo (corte; dissolve justificado sem encurtar o tempo)
                    + camada ÚNICA de identidade/legendas (Remotion `Camada`, alfa) sobre todos os backends
  → som.py          voz + trilha CC0 (sidechain) + efeitos ORIGINAIS com justificativa → master −14 LUFS / ≤ −1 dBTP / 48 kHz
  → metricas.py     medidas no MP4 real (vazio, movimento, cortes reais×planejados, repetição dHash, continuidade, áudio)
  → reversa.py      engenharia reversa automática (plano a plano) — estética sempre PENDENTE HUMANO
  → __main__.py     telegram: prévia PRIVADA no chat autorizado, status visível, NÃO PUBLICADO
```

## Componentes (modalidade → backend)

| Componente | Modalidades | Backend | Arquivos |
|---|---|---|---|
| registro.foto | registro_foto, documento | palco V2 (Chromium) + decisão de layout/câmera do V3 | backends/legado.py |
| registro.video | registro_video | FFmpeg, recorte 9:16 FIXO no ROI | backends/legado.py |
| mapa.rota | mapa | Remotion + MapLibre 6 + Natural Earth/TopoJSON + Turf + D3 (localizador) + OSM | remotion/src/MapaRota.tsx, geo/preparar.mjs, src/v4/geo.py |
| mecanismo.nivel_vasos | esquema_2d | Revideo 0.11 (API Motion Canvas, headless) | revideo/src/cenas/nivel_vasos.tsx |
| camadas.recorte | composicao_25d | HyperFrames + PixiJS + GSAP + rembg | hyperframes/coringa/camadas, backends/rembg_camadas.py |
| tresd.camara | cena_3d | Remotion + @remotion/three + R3F | remotion/src/Camara3D.tsx |
| dados.escala | dados, comparacao | Manim Community 0.19 | manim/cenas.py |
| tipo.lottie | tipografia | Remotion + @remotion/lottie (animação original) | remotion/src/TipoLottie.tsx, lottie/gerar.py |
| hf.registro | tipografia, dados, comparacao, esquema_2d | HyperFrames, QUALQUER bloco do catálogo (457) | backends/hyperframes.py, catalogo/hyperframes.json |

Identidade única (`motor4/identidade/identidade.json`): cores, fontes (OFL), áreas seguras, legenda, marca, selo e crédito
— lida por todos os backends.

## Regras que viraram código

| Decisão | Onde é imposta |
|---|---|
| câmera fixa; movimento só com motivo; recuo só com `revela`; gancho nunca recua | contrato.validar/impor; legado.render_foto → v3/decisao |
| sem cartão sobre fundo vazio | v3/decisao (editorial só para documento horizontal); HF recusa bloco paisagem em tela cheia; Manim em quadro 9×16 |
| transição: corte; dissolve só justificado; whip/iris/flash proibidos | contrato; compositor |
| ação física narrada precisa ser demonstrada | contrato `R-ACAO-SEM-DEMONSTRACAO` |
| mapa: rota só com geometria de fonte | geo.py + preparar.mjs (sem fonte → sem rota); contrato `R-ROTA-SEM-FONTE` |
| crédito/selo do asset da própria cena | episodio._camada_props (nunca texto livre) |
| legendas sincronizadas, ≤ 4 palavras, área segura | Remotion `Camada` + @remotion/captions |
| áudio −14 LUFS, pico ≤ −1 dBTP, 48 kHz; efeito com intenção | som.py (masterização medida herdada) |
| mídia não repetida | contrato `R-REPETICAO`; acervo não reusa URL |
| recorte só com máscara boa | rembg_camadas (cobertura, fragmentos, borda, bordas) |
| revisão multimodal falhou → PENDENTE | episodio._revisao; estado nunca "aprovado" |

## Reprodutibilidade

`motor4/package.json` + `package-lock.json` com versões exatas; `motor4/py/lock-*.txt`; registro HyperFrames no commit
`95e4e7f`; GSAP da versão pedida por bloco em `motor4/vendor/gsap/<versão>`; modelo rembg em cache; cada etapa grava JSON.
Refazer auditoria sem IA: `python -m src.v4 auditar <saída>`; relatório: `python -m src.v4 relatorio <saída>`.
