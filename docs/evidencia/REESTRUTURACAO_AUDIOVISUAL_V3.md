# Coringa Explica — Reestruturação audiovisual (V3) · entrega consolidada

Branch `piloto-v24-lagartixa`. Base auditada: `eb1e983`. Commits deste escopo:
- `9dcb068`: código;
- `.github/experimento/*` e os dois workflows de experimento: narração e regiões, ambos com resultado cifrado.

Nada foi feito em `main`, no NTC nem na produção. Não houve merge, publicação nem envio ao Telegram, e nenhum serviço pago foi contratado.

## Resumo

Na mesma narração e com os mesmos fatos, a nova abordagem foi melhor que a atual nos dois experimentos.
- Na Pompeia, o tempo com imagem parada caiu de 73% para 33%, e o tempo de tela vazia de 54% para 12%.
- No Panamá, o tempo com imagem parada caiu de 53% para 20%.

Os dois vídeos completos offline (57,5 s e 54,9 s) saíram sem nenhum problema geométrico e sem bloqueio do fiscal audiovisual.
**Não é GO para produção automática.** Três motivos:
- os storyboards destes vídeos foram escritos por mim, no papel do diretor; o caminho automático, em que um modelo de linguagem escreve o storyboard (`PROMPT_DIRETOR`), ainda não foi testado com um modelo real;
- o fluxo `main.py` ainda não chama o diretor;
- a aprovação estética é humana.

## 1. Inventário

| Ferramenta | Função | Licença | Custo | Situação | Recomendação |
|---|---|---|---|---|---|
| Playwright + Chromium | palco, com `seek(t)` determinístico quadro a quadro | Apache-2.0 | 0 | em uso | manter |
| FFmpeg | montagem, áudio (loudness/pico) e medição | LGPL/GPL | 0 | em uso | manter |
| GSAP 3.14.2 | animação dos componentes HyperFrames | Standard "No Charge" | 0 | em uso no `template.html` | manter |
| D3, MapLibre, Natural Earth | dados e mapas | BSD/ISC, domínio público | 0 | em uso | manter |
| HyperFrames (5 componentes) | número, gráfico, manchete, marca, vox-annotate | Apache-2.0 | 0 | integrado ao template antigo | manter; reaproveitar padrões (§3) |
| Remotion (protótipo) | React → vídeo | licença de empresa paga acima de 3 pessoas | pode ter custo | protótipo | não migrar (§2) |
| video-use (browser-use) | edição de gravação bruta (corte de fala, cor, legenda) | MIT | exige ElevenLabs (pago) para transcrever | não instalado | não usar: o material não é gravação bruta; aproveito a ideia de autoavaliar o render |
| ffmpeg-skill (kajisho5) | operações FFmpeg para agentes | MIT | 0 | não instalado | dispensável: o pipeline já chama o FFmpeg direto |
| ai-design-skills (elaya) | landing page e Figma | MIT | 0 | não instalado | fora do escopo de vídeo |
| snapcn.dev | biblioteca de motion graphics | não verificada | — | o site está fora da rede deste ambiente | não avaliado |
| Visão do Gemini (`gemini.json_visao`) | localizar regiões de interesse | API, cota gratuita | US$ 0 medido | **novo uso** | manter (com cache) |

Não consegui assistir aos seis vídeos de referência (YouTube não é acessível daqui). As técnicas aplicadas são as
descritas no brief: câmera com intenção, anotação presa ao objeto, coesão de cor e mapa ou animação com ação.

## 2. Arquitetura: A, B ou C

Escolha: **A ampliado**. O renderizador atual continua, e entram uma camada de direção e composições documentais novas.

- **C (Remotion):** usa o mesmo Chromium, então a qualidade visual é a mesma. O benchmark anterior (13/11) mediu ~20%
  de ganho só no render, contra a reescrita de 34 composições, um segundo runtime e licença paga para empresa.
- **B (híbrido):** nenhum motor externo resolve o que faltava. A falta era a **decisão** (o que mostrar, para onde
  olhar, quando anotar), não a capacidade de desenhar.
- **Prova:** sem trocar de renderizador, os experimentos melhoraram os números (§6). O gargalo era a direção.

## 3. Catálogo HyperFrames auditado

Commit `478313ba` (16/11/2026): 456 itens, sendo 210 blocos, 239 componentes e 7 exemplos.

- **Escolhidos como padrão, reescritos em `comp/doc.js`:**
  - `hw-callout-circle`: círculo em dois traços;
  - `yt-feather-highlight`: foco esfumado;
  - `grain-overlay`: granulação de tratamento;
  - `vignette`.
- **Próximos candidatos:**
  - `before-after-wipe`: comparação temporal (arquivo × hoje);
  - `hw-arrow`;
  - `iris-reveal`;
  - `whip-pan-cut`;
  - `split-tilt-cards`.
- **Descartados:**
  - shaders WebGPU/WebGL: GPU no CI não é garantida;
  - `cinemagraph`: inventa movimento em foto;
  - `camera-shake`: movimento sem intenção;
  - carrosséis, mock de interface, cursor, logo e social;
  - estilos de legenda: o canal tem a dele;
  - mapas de EUA e Espanha: específicos demais.
- **Por que não copiei os arquivos:** cada componente é uma composição 1920×1080 com timeline própria e GSAP via CDN.
  A ponte `hf.js` serve ao template antigo. No palco V2 os padrões foram reescritos para o `seek` determinístico, sem
  CDN e sem CSS global. A atribuição está em `src/render/v2/NOTICE.md`.

## 4. O que foi implementado

- **`src/v2/diretor.py`:** contrato de direção, validação e execução, mais o `PROMPT_DIRETOR` e o `storyboard_por_ia`.
  - Enquadramento sempre vertical, sem faixas.
  - Objeto largo aparece inteiro em moldura.
  - Movimento imperceptível é corrigido e registrado.
  - Anotação só entra se a visão localizou o objeto com confiança.
  - Região maior que o quadro vira marcador.
  - Tempos vêm da palavra exata da narração.
  - **Recusa:**
    - fato fora da pesquisa;
    - foto gerada por IA ou sem crédito;
    - REGISTRO com ano incompatível;
    - seta "de direção" sem a palavra "esquema".
- **`src/v2/regioes.py`:** caixa dos objetos pela visão do Gemini, com cache por sha256 e saliência local. A saliência só enquadra, nunca rotula.
- **`src/render/v2/comp/doc.js`:**
  - `doc.plano`: foto, câmera, anotações que acompanham a câmera, tratamento de cor e selo de função documental;
  - `doc.eclusa`: três degraus para o quadro vertical. A câmera segue o caminho da água do lago até a câmara, a câmara fica parada enquanto enche e a comporta só abre com os níveis iguais;
  - `doc.molde`: corpo coberto pela cinza, vazio, gesso, escavação. Rotulado como ESQUEMA.
- **`nucleo.js`:** transição `dissolve`.
- **`src/v2/fiscal_av.py`:** fiscal audiovisual com evidência por segundo: trechos parados, área vazia, repetição, transições, pergunta central e limitações da direção.
- **Workflows de experimento:** gravar uma narração (`experimento-voz.yml`) e localizar regiões (`experimento-regioes.yml`). Os dois cifram o resultado.

## 5. Contrato de direção (cada campo muda a montagem)

| Campo | Efeito na montagem |
|---|---|
| `evento_id`, `fato_id`, `fonte` | rastreio; fato fora da pesquisa = plano recusado |
| `funcao_narrativa` | ritmo e escolha de transição |
| `recurso_visual` | arquivo/composição; IA ou sem crédito = recusa |
| `funcao_documental` | selo na tela (REGISTRO, CONTEXTO, DOCUMENTO, ESQUEMA, RECONSTRUÇÃO, REPRESENTAÇÃO HISTÓRICA) |
| `objeto_principal` | região pedida à visão |
| `regiao_de_interesse` | caixa usada pela câmera e pelas anotações |
| `plano_inicial` / `plano_final` | enquadramentos-chave (geral, contexto, objeto, detalhe, ou outro objeto localizado) |
| `acao_visual` | conferida pelo fiscal (sem trecho parado) |
| `movimento_camera` | revelar, aproximar, localizar, acompanhar, explicar, comparar, fixo |
| `anotacoes` | círculo, contorno, foco, seta, trajeto, marcador, na palavra citada |
| `composicao`, `transicao` | composição e entrada |
| `tempo_inicio` / `tempo_fim` | da narração alinhada |
| `criterio_de_validacao` | registrado e medido pelo fiscal |

## 6. Comparação (mesma narração e mesmos fatos, quadros do MP4 real)

| Medida (fiscal audiovisual) | Pompeia atual | Pompeia nova | Panamá atual | Panamá nova |
|---|---|---|---|---|
| Tempo com imagem parada | 73% | 33% | 53% | 20% |
| Mudança média por segundo | 2,36 | 8,89 | 4,85 | 6,14 |
| Área útil sem detalhe | 54% | 12% | 29% | 33% |
| Cartões de texto | 3 de 3 planos | 0 | 0 | 0 |
| Render (2 núcleos, sozinho) | 42 s | 66–78 s | 39 s | 47–52 s |

**Leitura editorial (minha; a decisão é humana):**
- **Pompeia atual:**
  - foto parada com faixa "CONTEXTO";
  - depois um cartão de texto sobre "fluxo piroclástico";
  - depois um número em fundo bege.
- **Pompeia nova:**
  - a câmera atravessa o depósito até o molde de uma vítima real, circulado na palavra "protegendo";
  - o cume do Vesúvio recua até o fórum, com o trajeto da onda marcado como esquema;
  - as colunas descem até o chão escavado.
- **Panamá:**
  - a versão atual usa o melhor do motor (`mecanismo.eclusa` V2.1): 4 s de foto parada e um esquema com um degrau só;
  - a nova mostra a câmara real marcada na foto e entra no esquema;
  - o esquema segue a água do lago até a câmara, a câmara enche e o navio sobe;
  - no fim, recua para os 3 degraus até o Lago Gatún (+26 m) e os 3 de descida.
- **Onde a nova não ganhou:** área vazia no Panamá. O corte esquemático usa só a faixa do meio da tela.

## 7. Vídeos completos offline

| Vídeo | Duração | Parado | Área vazia | Problemas geométricos | Achados do fiscal audiovisual |
|---|---|---|---|---|---|
| Pompeia (histórico; narração real) | 57,5 s | 21% | 23% | 0 | vazio em 35–39 s (linha do tempo) e no encerramento |
| Panamá (engenharia; narração gravada para o experimento) | 54,9 s | 24% | 21% | 0 | parado em 9–13 s (navios distantes no lago); 4 dissolves seguidos (32–52 s); vazio no encerramento |

- **Áudio:** −14,5 e −14,7 LUFS, pico −1,3 dBFS.
- **Pompeia:**
  - **Corte na narração:** tirei a frase "grande parte dos vinte mil habitantes conseguiu fugir". A pesquisa diz "parcela significativa" de uma população de 10 a 20 mil, então a frase exagera o fato.
  - **Imagem de IA no motor atual:** a foto a25, marcada "ai generated" no Pixabay, foi usada no gancho pelo motor atual. O diretor novo recusa foto de IA.
- **Panamá:** a pergunta central é respondida com o mecanismo inteiro. Nada foi retirado.

## 8. Custos e tempo

- **Gasto em dinheiro:** US$ 0,00. Foram 1 gravação de voz (Gemini TTS, 20 s) e 21 leituras de visão (Gemini, cota gratuita, 12,5 min no Actions, com espera de cota).
- **Render local** (2 núcleos, 7 GB): ~3,7 min por vídeo de 55–57 s.
- **Custo por vídeo em operação, projetado e não medido:** além do que já existe, entram 1 chamada de direção e ~12 leituras de visão. Isso cabe na cota gratuita. Não medi o preço em cota paga.

## 9. Testes

- **Suíte completa:**
  - 782 passaram e 6 falharam;
  - 5 falhas já existiam (cofre privado ou caso polvo);
  - a sexta era a regressão visual das 3 composições novas, sem imagem de referência. Gerei as referências, que são composições novas e intencionais, e depois disso `tests/test_v2.py` passou 28/28.
- **Testes novos:** `tests/test_v3_diretor.py`, 16 testes. O render prova que o círculo acompanha a câmera.

## 10. Limitações

- **Diretor:** o storyboard dos vídeos foi escrito por mim. O `PROMPT_DIRETOR` com um modelo real ainda não foi testado, e o `main.py` ainda não chama o diretor.
- **Visão:** validada em 21 fotos de 2 temas. O cache depende do sha256 da foto.
- **`doc.eclusa`:**
  - mostra as comportas de lado e simplifica as galerias;
  - deixa a metade de baixo da tela vazia, na zona da interface das plataformas.
- **Fotos fracas:** o plano da vitrine (revelação) tem reflexo de vidro, e os navios do Lago Gatún ficam distantes.
- **Sem música** em todas as versões.
- **`doc.molde`:** a silhueta é genérica.

## 11. Recomendação

1. Avaliação humana dos 4 MP4s comparativos e dos 2 completos.
2. Se aprovar: ligar o diretor ao `main.py` (`MOTOR_VISUAL=v3`): storyboard pelo `PROMPT_DIRETOR` antes da narração, regiões pela visão com cache no checkpoint, e o fiscal audiovisual bloqueando a pergunta sem resposta.
3. Rodar 3 pilotos reais (história, ciência, engenharia) com o storyboard feito pelo modelo, uma tentativa cada.
4. Depois: `before-after-wipe`, música licenciada e uma versão do esquema que use a tela inteira.
