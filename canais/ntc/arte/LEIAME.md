# Arte do Ninguém Te Contou

Imagens geradas pelo Heitor no Google Flow (Nano Banana), estilo "storybook pintado à mão com contorno preto".
- `cenarios/`: fundos 9:16 sem personagens e sem texto (chão livre no terço de baixo).
- `val/original/`: Valdirene em fundo verde liso, como veio do Flow.
- `val/recorte/`: a mesma Val sem fundo (PNG transparente), feito com `python canais/ntc/recorta.py entrada.jpg saida.png`.

Começo fixo do prompt de cenário:
Vertical 9:16 background for a 2D cartoon animation, hand-painted storybook style, bold black ink outlines,
saturated warm colors, soft depth, cinematic lighting, eye-level camera, empty open floor in the lower third,
no people, no characters, no text, no letters, no watermark. Scene: ...

## Objetos de chão (DE LADO, sem borda) — `objetos/lado/`
Objeto que fica no chão/anda no cenário precisa ser desenhado DE LADO (o cenário é na altura dos olhos) e SEM a borda
branca de adesivo. Gerar no Flow uma folha com vários objetos em fundo verde liso e recortar tudo de uma vez:
`python canais/ntc/recorta_folha.py folha.jpg canais/ntc/arte/objetos/lado barata_lado rato passaro ...`
(nomes na ordem de leitura, linha por linha). O script tira o verde, a borda branca, o branco preso entre pernas/folhas e o halo.
Folha 1 (`objetos/original/folha_lado_1.jpg`): barata_lado, rato, passaro, lixo, folhas, murcha, chinelo, globo.

## O que o vídeo usa (`canais/ntc/fabula.html`)
- Cenários: `cenarios/*.jpg` (preso embaixo, chão sempre aparece; "rua" = rua_normal).
- Val: `val/recorte/` — neutra=frente (perto: tres_quartos), comemora, explica, brava, susto/desesperada=panico; pisca trocando a cabeça (só na frente).
- Objetos: `objetos/usar/` (versão final sem borda). Objeto novo → recortar com `recorta_folha.py`, conferir e copiar para `usar/`;
  colocar a largura em `OBJETOS` e, se o desenho olha para a esquerda, em `OLHA_ESQ` (src/fabula.py).
