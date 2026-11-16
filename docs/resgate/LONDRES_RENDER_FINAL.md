# Londres 1666 — render completo final (16/11/2026)

**Estado:** `AGUARDANDO_APROVACAO_HUMANA`. Prévia PRIVADA enviada ao Telegram; **não publicado**. Avaliação audiovisual: Heitor.
**Branch:** `piloto-v24-lagartixa` · sem merge, sem NTC, sem `main`, sem produção, sem redes sociais.

## Ajustes antes do render (storyboard supervisionado)

| Trecho | Ajuste |
|---|---|
| 12–15 s placa | plano fixo só no bloco de texto: linhas inteiras com margem, primeira linha abaixo do selo; a foto ocupa ~65% da tela (antes ~35%). O brasão saiu (não é informação da fala). |
| 38–44 s mapa | em "terça… quase toda a cidade" o quadro recua por ~3 s para a extensão inteira do incêndio e volta ao oeste em "muralha"; no resto o mapa cobre a altura toda. |
| 47–49 s Golden Boy | mantido (P1b aprovada). |
| 49–58 s Monumento | foto completa mantida; monumento à esquerda; linha dos 61,5 m à direita, do chão ao topo da urna, sem cruzar selo, legenda nem crédito (crédito passou para a esquerda: parâmetro novo `credito_lado`). |

Conferido em 3 quadros estáticos do palco, sem MP4, antes de disparar.

## Execução no GitHub Actions (infraestrutura existente: `resgate-londres.yml`)

- Modo `chave` (run 43917273546, 1 min): o workflow derivou do `CHECKPOINT_KEY` um par X25519 e publicou só a parte
  pública (ramo `resgate-chave`). A narração já gravada foi cifrada com ela (`.github/resgate/narracao.enc`): só o
  workflow decifra (`src/v3/material.py`).
- Modo `render`: imagens do checkpoint em cache + 3 fotos do Commons por título + narração cifrada + música do
  repositório → `scripts/render_londres.py` (palco + FFmpeg, fiscal, estado final, prévia privada).
  **Nenhuma IA:** sem chaves de IA no passo; caixa aberto com todos os provedores de IA bloqueados → livro: 0 chamadas.
- Tentativas: 43917549168 falhou no concat do FFmpeg com pasta relativa (**ERR-034**, corrigido no `render.py`);
  43919175364 gerou o MP4, mas a trava recusou o chat (exigia tipo "private"; o canal do bot é grupo privado,
  **ERR-035**); **43920582178 gerou e enviou** (grupo privado do bot atual, 3 membros; cópia de 37,6 MB, porque o
  original tem 68 MB e o bot aceita até 50 MB).

## Resultado

- MP4: 64,6 s · 1080×1920 · −14,5 LUFS · pico −1,5 dBTP · render 168 s.
- Fiscal: 0 bloqueios · 4 revisões · 4 notas estéticas (planos longos):
  - 21,5 s — plano 4 (gravura vitoriana 1560×873) em `integral`, com margem: troque a mídia se puder;
  - 22,6 s — zoom a 45%/s (no limite provisório);
  - 38,1 s — recuo do mapa a 48%/s (pedido para mostrar a extensão "brevemente");
  - 54–57 s — imagem parada no plano do Monumento (a câmera assenta antes da seta; o fiscal pediu movimento).
- Pendência fixa: revisão multimodal não executada (sem IA nesta execução).

## Permissões (separadas)

- Prévia privada: `src/v3/previa_telegram.py` — destino único = `TELEGRAM_CHAT_ID` do bot atual, aceito se não for
  público (sem @nome) e, sendo grupo/canal, com até 5 membros; status sempre na legenda ("PRÉVIA PRIVADA — NÃO
  PUBLICADO"), inclusive pendente ou bloqueado.
- Publicação: `estado_final.pode_publicar` só com `PUBLICAVEL` (aprovação + autorização humanas). Não existe código que publique.

## Artefatos

- Run 43920582178: artefato `londres-render-cifrado-43920582178` (cifrado, 90 dias) com MP4, fiscal, folha de contato,
  direção, estado e custos. O push ao ramo falhou (pacote de 107 MB > 100 MB); o workflow agora tira a cópia do
  Telegram do pacote e divide em partes acima de 95 MB.
- Ramo `resgate-render` (permanente, cifrado): resultado do run 43919175364 — mesmo storyboard, narração e código de
  render; muda só o módulo de envio.

## Custos

Cobrança efetiva **US$ 0** · chamadas de IA 0 · crédito de assinatura 0 · cota grátis 0 · GitHub Actions: 4 execuções
(~18 min no total, runner público). Teto US$ 0,80 / alerta 0,60 mantidos; provedores pagos desabilitados.

## Testes

Suíte inteira: **960 passam, 12 falham, 13 pulados** — as mesmas 12 falhas do `2beb111`. Novos: `test_v3_previa_render.py`
(16: cifragem do material, prévia só ao chat autorizado, recusa de chat público, grande ou desconhecido, estado
desconhecido, recompressão dentro do limite, render sem IA, concat absoluto).

## Pendências registradas (não resolvidas aqui)

- Armazém remoto do caixa ainda não validado contra o GitHub real (só repositório local nos testes).
- Identificação única por episódio no caixa (hoje: rótulo do pedido).
- Faturamento dos provedores declarado por configuração (Gemini/Groq "cota"); conferir a conta real.
- O canal de prévia tem **3 membros**: confirmar quem é o terceiro.
- O pipeline automático (`main.py`, V3) ainda não usa `previa_telegram`; só este render de referência.
- `pedido.json` está em modo `render`: qualquer mudança nele dispara o workflow de novo (e um novo envio).
