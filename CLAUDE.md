# Coringa Explica — memória permanente do projeto

**Objetivo comercial:** vídeos documentais curtos (9:16, 45–70 s), automatizados, com custo sustentável (meta histórica
≈ US$ 0,30 por vídeo, tentativas incluídas), para Instagram, TikTok, Facebook e YouTube Shorts. Qualidade audiovisual vem
antes de preservar a arquitetura.

## Regras de segurança (sempre)
- **Não alterar o NTC** (`src/fabula.py`, `src/ntc_*`, `canais/ntc/`, branch `ntc`). Não ler sem pedido.
- Não mexer em `main` nem na produção (`gerar-videos.yml`); não fazer merge; não publicar; não enviar ao Telegram.
- Nenhum serviço pago novo sem autorização do Heitor. Não ativar `ORCAMENTO_MODO=aplicar`.
- Segredos nunca no log nem no repositório (público). Resultado interno sai **cifrado** (GPG) para `.github/piloto/chave_publica*.asc`.
- Teste automático não é aprovação visual: **só o Heitor aprova**. Não ajustar teste/tolerância para passar.
- Não rodar execução real cara em loop; uma tentativa por caso, registrada.

## Arquitetura atual (branch `piloto-v24-lagartixa`)
- `main.py` → pesquisa (`src/roteiro.py`, cofre de prompts privado) → acervo (`src/acervo.py`) → roteiro com contratos de
  acontecimento (`src/v2/contrato.py`) → **motor visual** escolhido por `MOTOR_VISUAL`:
  - vazio = motor antigo (produção); `v2` = seletor + palco V2 + fiscal V2.2; **`v3` = diretor automático V3.1**.
- **V3.1** (`src/v3/`): `pipeline.py` (fluxo), `biblioteca.py` (mídia global SQLite + armazém por sha256), `receitas.json`
  (direção por função narrativa/tipo de acontecimento), `memoria.py` (erros + feedback + regras com estado),
  `fiscal_editorial.py` (técnico + editorial + PySceneDetect). Execução dos planos: `src/v2/diretor.py`; render:
  `src/render/v2` (palco Chromium com `seek` determinístico) → `src/render/render.py` (FFmpeg).
- Arquitetura e decisões: `docs/v3/ARQUITETURA_V3_1.md`. Histórico: `docs/evidencia/*.md` (leia só o que precisar).

## Motor V4 (ramo `motor-integral-v4`, experimental)
- `python -m src.v4 {sondar|episodio|auditar|relatorio|telegram}`; arquitetura `docs/v4/ARQUITETURA_V4.md`; capacidades
  `docs/v4/CAPACIDADES.md` (status honesto); backends em `motor4/` (Node isolado, versões exatas) + `src/v4/backends/`.
- Contrato único de cena e regras verificáveis: `src/v4/contrato.py`; componentes por modalidade: `src/v4/componentes.py`.
- Teste técnico (não estético): `scripts/v4_fumaca.py`; episódio real só no Actions (`.github/v4/pedido.json`).
- **Antes de qualquer execução:** `python -m src.v4 prerender .github/v4/pedido.json [roteiro.json] [narracao.json]` (sem IA): viabilidade do
  acervo (`src/v4/viabilidade.py` + `biblioteca_comprovada.json`), parâmetros, contrato, narração reutilizada e geometria do palco
  contra as zonas V4. Só dispare o Actions com 9/9 prontas e autorização do Heitor.

## Onde está cada coisa
| Preciso de… | Arquivo |
|---|---|
| erros já corrigidos (não repetir) | `docs/memoria/erros.json` → `python -m src.v3.memoria erros [tag]` |
| feedback humano por timestamp | `docs/memoria/feedback.jsonl` → `python -m src.v3.memoria abertos` |
| regras editoriais (estado) | `docs/memoria/regras_editoriais.json` |
| receitas de direção | `src/v3/receitas.json` |
| forma visual por acontecimento e regras das referências | `src/v3/linguagem.py`, `docs/v3/LINGUAGEM_CORINGA.md` |
| layout (vertical → alternativa → editorial → revisão) e câmera (fixo; recuo só com `revela`) | `src/v3/decisao.py` |
| fiscal de decisão ruim (ocupação, mapa, gancho) e calibração | `fiscal_editorial.decisoes`, `tests/dados/londres_decisoes_humanas.json` |
| ferramentas avaliadas (não reavaliar) | `docs/v3/INVENTARIO_FERRAMENTAS.md` |
| última entrega / GO-NO-GO | `docs/v3/ENTREGA_V3_1.md` |

## Testes
- Rápidos (V3.1): `python -m pytest -q tests/test_v3_*.py` (~15 s).
- Suíte inteira: `python -m pytest -q` (~6 min). Falhas conhecidas de ambiente: prompts do cofre privado, Natural Earth
  ausente (`python scripts/v2_natural_earth.py` resolve), caso polvo. Lista em `docs/v3/ENTREGA_V3_1.md`.
- Integridade da memória: `python -m src.v3.memoria conferir` (cada erro aponta para um teste que existe).

## Prévias e render
- Prévia barata (quadros, sem MP4): `src.v3.pipeline.previa_quadros` ou `python -m src.v2.galeria`.
- Vídeo completo só depois que a prévia não mostrar defeito; o fiscal (`src/v3/fiscal_editorial.py`) gera
  `fiscal_v3.md` e `folha_contato.jpg` — olhe a folha antes de assistir.
- Execução real: editar `.github/v3/pedido.json` (workflow `v3-validacao.yml`); resultado cifrado no ramo
  `v3-validacao-resultado`.

## Registrar erros e decisões
- Erro corrigido → nova entrada em `docs/memoria/erros.json` (ID novo, causa raiz, arquivos, **teste de regressão**).
- Feedback de vídeo → `python -m src.v3.memoria feedback <video> <mm:ss> <categoria> "texto" --direcao <direcao.json>`.
- Regra nova nasce `proposto`; só vira `aprovado` depois de `testado` e com evidência (`memoria estado`). Só aprovada
  entra no prompt do diretor.

## Skills do projeto (carregue só a pertinente)
`coringa-direcao` (storyboard/receitas) · `coringa-acervo` (biblioteca/licenças) · `coringa-edicao` (render, FFmpeg,
transições) · `coringa-auditoria` (fiscal, feedback, regressão) · `ffmpeg-skill` (operações FFmpeg locais, MIT).
