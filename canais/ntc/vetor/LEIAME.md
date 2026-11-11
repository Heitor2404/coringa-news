# Ninguém Te Contou — motor vetorial (estilo "boneco de tubo", decisão de 11/11)

Tudo desenhado por código em SVG; o `src/fabula.py` copia estes arquivos para a pasta de trabalho e o Chrome
fotografa quadro a quadro com `seek(t)`.

- `kit_base.js` — cores, contorno, degradês e padrões (DEFS), utilidades.
- `kit_val.js` — a Valdirene articulada: braços com cotovelo, mãos (aberta / punho / apontando), pernas com joelho (anda, agacha),
  cabeça que gira, olhos (normal, feliz, arregalado, olhando para cima, piscando), sobrancelhas, bocas, suor, lágrima.
  Poses do roteiro: neutra, comemora, explica, susto, brava, desesperada; cada uma tem uma ALTERNATIVA que entra nos planos
  ímpares (pensa, comemora2, explica2, brava2...) para ela não ficar parada.
- `kit_cenarios.js` — 12 cenários (cozinha, sala, lab, mercado, hospital, rua, rua_destruida, floresta, horta, fazenda, praia,
  espaco), com versão noite. Chão começa em y=1340; a Val pisa em y=1720. `BANCADAS` = tampos onde objetos podem ficar.
- `kit_objetos.js` — 16 objetos/bichos (todos virados para a direita, largura nominal 100), alguns com partes animadas
  (patas da barata/rato/lagarto, asa do pássaro/mosca, fogo).
- `fabula.html` — o motor: planos de câmera (geral/rosto/objeto/meio a cada ~2,3 s), Val entrando andando quando muda de
  cenário, troca de pose com mola, aceno da cabeça a cada bloco da narração, balão em cima da cabeça, painel que aparece
  grande e encolhe para o canto (como placar), legenda, título, placa final, confete, poeira, folhas/poeira no ar.
- `teste_baratas.html` — a cena de teste aprovada (não é usada pelo sistema).

Coisa nova (cenário, objeto, pose): desenhar UMA vez aqui e, se o roteiro puder pedir, pôr o nome na lista do
`src/fabula.py` (CENARIOS / OBJETOS+PROPORCAO / POSES). O teste `tests/test_fabula.py` confere se os dois lados batem.
