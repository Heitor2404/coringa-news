# Ninguém Te Contou — estilo vetorial (decisão de 11/11)

O Heitor escolheu o estilo "boneco de tubo" (como os vídeos de fábula em 2D): tudo desenhado por código em SVG,
personagem articulado de verdade (cabeça, braços com cotovelo, mãos com dedos, pernas com joelho), luz quente, contorno escuro.
Substitui a arte do Flow recortada (a Val em PNG não mexe braço/mão).

`teste_baratas.html` = cena de teste de 5 s aprovada (Val bate o chinelo nas baratas, close com "VOLTA AQUI!").
Abrir com Playwright e chamar `seek(t)` quadro a quadro (mesmo esquema do resto do sistema).

Próximo: transformar em kit (Val como função com poses/ângulos, cenários-modelo, objetos, luz) e ligar ao fabula.py.
