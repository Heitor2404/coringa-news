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
- `kit_pessoas.js` — figurantes genéricos (5 tons de pele, roupas e cabelos variados); entram sozinhos em rua, rua_destruida, mercado, praia, fazenda e hospital (MULTIDAO).
- `fabula.html` — o motor: planos de câmera (geral/rosto/objeto/meio a cada ~2,3 s), Val entrando andando quando muda de
  cenário, troca de pose com mola, aceno da cabeça a cada bloco da narração, balão em cima da cabeça, painel que aparece
  grande e encolhe para o canto (como placar), legenda, título, placa final, confete, poeira, folhas/poeira no ar.
- `teste_baratas.html` — a cena de teste aprovada (não é usada pelo sistema).

Coisa nova (cenário, objeto, pose): desenhar UMA vez aqui e, se o roteiro puder pedir, pôr o nome na lista do
`src/fabula.py` (CENARIOS / OBJETOS+PROPORCAO / POSES). O teste `tests/test_fabula.py` confere se os dois lados batem.

## Som, luz e closes (11/11 noite)
- Música: `canais/ntc/musica/trilha_1..5.mp3`, trilhas cômicas GERADAS por código (`gerar.py`: oom-pah de tuba, bumbo/caixa, melodia de pizzicato ou xilofone) — sem licença de terceiros. Trocar por outras = pôr .mp3 na pasta.
- `sfx/contagem.wav`: tic-tic-tic acelerando + "pum", toca quando o contador muda.
- Campo `luz` por cena: dia, por_do_sol (tom laranja), noite, holofote (só a Val iluminada, segue a cabeça dela).
- Planos de detalhe: no 3º plano de uma cena sem balão, close da MÃO (cenas pares) ou do OLHO (ímpares), medidos na tela.

## Juninho (11/11 noite)
- `kit_juninho.js`: segundo protagonista, caipira de ~20 anos (chapéu de palha, camisa xadrez vermelha, jeans, botina, sardas). Mesmo esqueleto/classes da Val — a classe `Val` anima os dois (`new Val(g, PERSONAGEM_SVG.juninho())`).
- Escolha: no campo ntc, começar com "Juninho:" (ex.: `Juninho: E se parasse de chover por 1 ano?`). Sem prefixo = Val.
- `src/fabula.py` troca o parágrafo PERSONAGEM do PROMPT_FABULA e os nomes (Valdirene → Juninho); bordão "NINGUÉM ME CONTOU, SÔ!".
- Cenário novo `sitio` (casa de roça, poço, árvore, cerca; chão racha quando a cor some = seca). Cozinha sem "BOLOS DA VAL" quando é o Juninho.

## Regiões do cenário e medidor (12/11)
- `regioes.json`: lugar ÚNICO onde cada cenário diz onde fica o céu livre (+ faixas de legenda, painel e título, e o lugar do sol/lua do cenário). `src/fabula.py` põe tudo que é "do céu" inteiro dentro dessas caixas. Cenário sem céu à vista = lista vazia.
- Mudou um cenário? Rode `pytest tests/test_ntc_geometria.py`: o teste desenha cada cenário no Chrome e acusa se uma casa/árvore/morro entrar no céu declarado.
- `ceu({semAstro: true})`: o cenário não desenha o sol/lua dele (o roteiro trouxe o próprio).
- Diagnóstico completo (sem IA, sem vídeo): `PYTHONPATH=. python -m tests.ntc_geometria docs/RELATORIO_GEOMETRIA_NTC.md` (~25 min).
