# Coringa Explica — @coringa.explica

Gera **1 mini-documentário de curiosidade por dia** (Reels / TikTok / YouTube Shorts), contado em partes, narrado pelo Coringa,
e manda no Telegram: vídeo + capa + resumo de qualidade + texto pronto de cada rede. A postagem é manual.

## Como funciona (todo dia, sozinho)
1. **Tema**: se tem uma série em andamento (ex.: saiu a parte 1 ontem), faz a próxima parte. Senão pega o próximo tema da
   **planilha** (variável `TEMAS_PLANILHA`) ou, sem planilha, da lista `assets/temas.txt`.
2. **Pesquisa**: Wikipédia PT/EN + Google News; um "garimpeiro" separa os fatos concretos e surpreendentes.
3. **Roteiro**: 2 versões, o editor escolhe; revisão em até 3 rodadas; **3 ganchos** e o editor fica com o melhor;
   120–150 palavras (≈55 s), mini-revelação a cada ~15 s, parte 1 termina em suspense.
4. **Imagens**: uma imagem por ideia (frase longa = 2 planos da MESMA imagem com outro enquadramento). Fotos/filmagens reais
   (Wikimedia Commons, Openverse, Pixabay) conferidas por um fiscal rigoroso (modelo principal do Gemini, sim/não); IA só
   quando não existe imagem real; plano sem imagem certa fica com fundo neutro + palavra-chave (nunca imagem errada).
   Etiqueta "FOTO REAL" vem do próprio arquivo. Mapas com coordenadas do OpenStreetMap. Mesma cor e grão em tudo.
5. **Infográficos** animados (número, linha do tempo, comparação, mapa) no lugar das antigas simulações.
6. **Vídeo**: tudo dentro da zona segura do Reels; 1º quadro já com imagem e título; trilha pelo clima da história.

## Planilha de temas (Google Sheets)
- 1ª linha: `tema` | `status` | `obs`. Um tema por linha. `status` = `feito` ou `pular` faz o sistema ignorar a linha.
- Arquivo → Compartilhar → **Publicar na Web** → escolha a aba → formato **CSV** → Publicar → copie o link.
- No GitHub: Settings → Secrets and variables → Actions → aba **Variables** → `TEMAS_PLANILHA` = o link.

## Rodar na hora
Actions → "Gerar vídeos do dia" → Run workflow:
- tudo em branco → faz o vídeo do dia;
- **Curiosidade** + **Parte** → um tema escolhido;
- **Quantos vídeos de notícia** → notícia (só manual).

## Música
Trilhas CC0 em `assets/musica/` (ver LEIAME.txt). O clima do roteiro (misterioso/tenso/épico/leve) escolhe a trilha.

## Teste no seu computador
`python main.py --teste` (offline, roteiro de exemplo).
