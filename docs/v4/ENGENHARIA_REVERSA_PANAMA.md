# Engenharia reversa — episódio V4 "Por que os navios precisam subir no Canal do Panamá?"

Execução **43972774128** (ramo `motor-integral-v4`, commit `da1af41`). MP4 de 72,7 s, 9 cenas, entregue como prévia
privada no Telegram (NÃO PUBLICADO). Estado do motor: **BLOQUEADO** (2 bloqueios). Nada aqui é aprovação estética —
aguarda a auditoria do Heitor. Fontes: `ENGENHARIA_REVERSA_AUTOMATICA.md`, `metricas.json`, `linha_do_tempo.json`,
revisão multimodal (Gemini, todas as 9 cenas revisadas), logs dos backends, folha de contato e quadros extraídos.

## Histórico das tentativas do teste integrado

| Execução | Resultado | Causa |
|---|---|---|
| 43954271637 | falhou no CI | Python/lockfiles (ERR corrigido em 977c1f3) |
| 43954670866 | quebrou no acervo | fontes chamadas sem consultas (ERR-043) |
| 43955781237 | parou na direção | limite de 5 h da assinatura (ERR-046) |
| 43956541084 | MP4 BLOQUEADO; Telegram 502 | caminhos relativos em 5 backends (ERR-042), licença, rembg, loudness, 5xx (ERR-044/045/047) |
| **43972774128** | **MP4 BLOQUEADO; prévia entregue** | vídeo de outro lugar (ERR-048), Revideo não abre o Chrome (ERR-050) |

## Tabela por recurso

| Recurso / backend | Cena (s) | Funcionou? | Evidência | Causa | Origem | Correção geral |
|---|---|---|---|---|---|---|
| Foto real, legacy (gancho) | c1 0,0–6,9 | **sim** | quadro cheio, navio + mula, crédito; revisão "sim" | — | — | — (a métrica "vazio 50%" é falsa: casco escuro conta como fundo) |
| MapLibre + Natural Earth + OSM + Turf, Remotion | c2 6,9–14,5 | **parcial** | Lago Gatún, Colón e localizador legíveis; rota OSM desenhada mas fina; "Cidade do Panamá" cortado na borda; "Oceano Pacífico" sob a legenda; "Atlântico" sem rótulo | rótulos sem área segura nem verificação de borda; traço da rota fino demais para celular | backend/componente | rótulos dentro da área segura + fiscal de borda/colisão no mapa; espessura mínima da rota em px |
| Manim (dados) | c3 14,5–22,7 | **parcial** | barra 26 m sobe; prédio de ~9 andares presente; rótulos do eixo colidem entre si e com a legenda; metade de baixo vazia | layout do gráfico ignora a faixa de legenda; composição só na metade de cima | componente | gráfico ocupa a área útil inteira; rótulos fora da faixa de legenda |
| Foto de arquivo 1913 (documento) | c4 22,7–32,8 | **parcial** | foto correta e datada; a MESMA foto aparece em cima e embaixo; 10 s parada (aviso) | composição editorial com detalhe quase igual ao geral → duplicação | composição | detalhe só quando amplia de fato (≥ 2×), senão foto única |
| Vídeo real (FFmpeg) | c5 32,8–38,9 | **não** | vídeo do Pixabay de canal urbano europeu ao pôr do sol; revisão "não corresponde" | visão aceitou canal urbano como eclusa; ROI em pixels; crédito vazio | acervo | ERR-048 (nome próprio nas tags, ROI validada, crédito Pixabay) |
| Revideo (mecanismo 2D) | c6 38,9–45,9 | **não** | quadro preto, só legenda | Chrome fecha na partida no runner (TargetCloseError) | backend/CI | ERR-050 (dumpio + flags mínimas + headless-shell) — **não verificado** |
| Three.js/R3F, Remotion (3D) | c7 45,9–55,0 | **não** (revisão "parcial") | câmara vira faixa inclinada fina no topo; rótulos sobrepostos e cortados na borda; aquedutos/piso não visíveis | câmera 3D longe/rasante; rótulos sem colisão nem área segura | componente | enquadramento da câmara ≥ 60% do quadro; rótulos com colisão e borda |
| rembg + HyperFrames (2.5D) | c8 55,0–62,9 | **sim** | navio recortado sobe sobre a água do esquema; "+6 m"; revisão "sim" | — (crédito sobre a imagem) | — | crédito fora da área do objeto |
| Lottie/tipografia, Remotion | c9 62,9–72,7 | **parcial** | número grande legível; a legenda repete o mesmo texto; ícone minúsculo; 9,8 s parado | tipografia e legenda dizem a mesma frase ao mesmo tempo | direção/composição | ocultar legenda quando a tipografia escreve a fala |
| Legendas por palavra | todas | **sim** | sincronizadas, contraste bom; colisões em c2 e c3 | — | — | colisão legenda × rótulo do componente no fiscal |
| Som (voz, SFX, master) | todas | **parcial** | −14,6 LUFS; pico −0,1 dBTP no MP4 (master −1,4) | AAC sobe o pico | compositor | ERR-049 (verificado no MP4: −2,4 dBTP, −14,6 LUFS) |
| Fiscal / métricas | — | **parcial** | "demonstra ação" 55,6% contava c5/c6; vazio por blocos escuros erra em foto escura | métrica pela modalidade declarada | métricas | ERR-051: recalculado = **11,1%** (só c8) |

## Ritmo e narrativa

- 72,7 s (alvo 75–90; mínimo operacional 65). 8 cortes (6,6/min), plano médio 8,1 s; 2 planos parados ≥ 9,8 s.
- Progressão coerente (gancho → mapa → altura → história → degraus → mecanismo → gravidade → enchimento → custo), mas
  o meio do vídeo (c5–c7, 38–55 s), onde está a explicação, é justamente o trecho que falhou: o espectador não vê o
  mecanismo funcionando.
- Gancho imediato e correto; payoff (água doce que vai para o mar) sustentado por fonte, mas apresentado só como texto.

## Fatos

Conferidos com a Autoridade do Canal: sem bombas, só gravidade; aquedutos de 18 pés (≈ 5,5 m); Gatún 3 degraus,
Pedro Miguel 1, Miraflores 2. Nenhum erro factual encontrado na narração. O "prédio de 9 andares" é aproximação
declarada (≈ 3 m/andar).

## Custo

Cobrança efetiva US$ 0,00; crédito de assinatura (Claude) US$ 0,13; Gemini 43 chamadas na cota grátis. Direção
reproduzida da execução 43954670866 (sem nova chamada ao diretor). Nenhum provedor pago.

## Corrigido depois desta execução (sem nova execução real)

ERR-048 a ERR-051 com testes de regressão. Status do Revideo no registro de capacidades rebaixado para `falhou_ci`.

## Não corrigido (precisa de decisão ou da sua auditoria)

- Componentes com composição fraca: mapa (rótulos/borda/traço), 3D (enquadramento/rótulos), dados (área útil),
  documento duplicado, tipografia × legenda. São causas gerais de componente; a correção é dirigida pela sua auditoria.
- Métrica de vazio confunde foto escura com fundo.
- Revideo no CI: só a próxima execução confirma a mitigação. Se continuar falhando, o mecanismo 2D precisa de outro
  backend (HyperFrames/GSAP ou Remotion), o que é mudança de arquitetura do componente.
- Vídeo real licenciado do canal: pode não existir nas fontes livres consultadas; nesse caso a cena deve virar
  documento/esquema identificado, não um vídeo de outro lugar.
