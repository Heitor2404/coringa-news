# Livro de erros (Coringa Explica e Ninguém Te Contou)

Todo erro visto num vídeo vira uma linha aqui: o que era, como foi resolvido e o que impede de voltar.
Antes de mexer no visual, ler este arquivo. Erro novo → linha nova (e, se der, um teste).
Status: ✅ resolvido no código · 🧠 depende do prompt no cofre (escolha de imagem/roteiro) · ⏳ a fazer

## Coringa — vídeo "supercomputador do Exército dos EUA" (11/11)
| # | Erro | Status | Como foi resolvido / onde |
|---|---|---|---|
| 1 | Palavras ainda não ditas apareciam apagadas (cinza) — parecia defeito | ✅ | template.html: bloco inteiro em cor cheia |
| 2 | Bloco de legenda curto e solto ("UM CHIP" / "DE SUPERCOMPUTADOR") | ✅ | voz.legendas: bloco de 1–2 palavras junta com o vizinho se couber (~30 letras) |
| 3 | Palavras coladas na legenda ("OSMILITARES") no "pulo" da palavra | ✅ | template.html: espaço real entre palavras + contorno no texto |
| 4 | Mesmo ano 3x na tela (selo "JAPÃO · 2006" + número grande "2006" + legenda) | ✅ | render._numeros: ano nunca vira número grande; número que a cena já escreve também não |
| 5 | Selo digitado letra a letra mostrava "EU"/"J" | ✅ | template.html: selo aparece inteiro, deslizando |
| 6 | Título do gancho cortado nas bordas no 1º quadro | ✅ | template.html: fonte diminui até a maior palavra caber com os 5% de zoom inicial |
| 7 | Pergunta minúscula fixa no topo e créditos ilegíveis | ✅ | pergunta do topo removida; fontes no fim em 30 px, branco |
| 8 | Mesma imagem 3x no vídeo (logo da Força Aérea, chip) | ✅ | main.py: revelação usa a imagem da cena anterior (não a do gancho); fechamento usa a última foto; foto "vizinha" e plano extra só de até 2 ideias de distância |
| 9 | Mesma foto parada 7 s | ✅ | PLANO_MAX 3,5 s (vira corte de câmera) e MESMA_MAX 7 s |
| 10 | Foto que não bate com o fato (PS3 Slim de 2009 no lançamento de 2006) | ✅ | cofre: CATALOGO diz modelo/versão e descarta modelo de outra época; CASAR e FISCAL_FINAL também |
| 11 | Imagem de outra marca (parede da Intel no "1.760 PS3") | ✅ | cofre: CATALOGO/CASAR/FISCAL_FINAL descartam marca de outra empresa |
| 12 | Zoom corta texto/objeto da foto ("RESEARCH LABO", PS3 pela metade) | ✅ em parte | emblema/logo não entra mais (era o caso pior); foto deitada já passeia de um lado ao outro. Ficar de olho |
| 13 | Imagem fantasma (duas fotos misturadas / número atravessando de cena) | ✅ | template.html: troca de cena sem dissolver; número grande some na troca de cena |
| 14 | Mascote aparece 1 s e some | ✅ | template.html: mascote só em cena do gancho com ≥ 2 s |
| 15 | Névoa escura deixando a metade de baixo suja | ✅ | template.html: sombra de baixo mais leve nas fotos (legenda ganhou contorno) |
| 16 | Final repete logo do começo | ✅ | ver item 8 (revelação/fechamento não voltam à imagem do gancho) |
Áudio: volume já normalizado (loudnorm I=-14) no render.

## Ninguém Te Contou — motor vetorial (11/11)
| # | Erro | Status | Como foi resolvido |
|---|---|---|---|
| 1 | 1º quadro com cenário vazio (Val ainda fora, entrando) | ✅ | Val não entra andando na 1ª cena |
| 2 | Balão trocando de lado da cabeça no meio da cena | ✅ | posição do balão fixa por plano; legenda sobe quando há balão |
| 3 | Cena de noite quase igual ao dia | ✅ | camada azul mais forte |
| 4 | Painel grande não aparecia | ✅ | painel por índice de cena |
| 5 | Personagem "duro" (PNG inteiro) | ✅ | trocado pelo boneco articulado vetorial |
| 6 | Fonte do motor (Poppins) só existia na máquina do Claude; no GitHub sairia fonte genérica | ✅ | fabula.py copia Montserrat/JetBrains do node_modules para a pasta do vídeo |
| 7 | Motor com PNG do Flow: 1º quadro errado, Val parada até 9 s, balão a cena toda, baratas da bancada escondidas, pássaro balançando pela cabeça, poeira virando mancha, noite fraca, cenas sem a Val paradas, ratos fora da tela, placa final pequena | ✅ | motor PNG apagado; motor vetorial novo resolve (ver commits 6d3109b em diante) |
| 8 | (vídeo "E se o Sol sumisse", 11/11) Globo de mesa usado como Sol/Terra voando na cozinha; fogo usado como Sol | ✅ | kit novo: sol, terra, lua, vela, lanterna; PROMPT_FABULA: objeto tem que ser o que a frase diz |
| 9 | Val na mesma pose de pânico por ~40 s | ✅ | pose nova "chora"; alternativas sem repetir pânico; prompt: no máx. 2 cenas seguidas com a mesma pose |
| 10 | Metade final do vídeo escura e barrenta (noite + cor sumindo) | ✅ | noite mais leve; cor some até no máx. 70% |
| 11 | Close do rosto cortando o coque / cara gigante | ✅ | close menos fechado (2,0 → 1,6) |
| 12 | Balão em cima do título na 1ª cena | ✅ | balão só depois que o título sai |
| 13 | Planeta/objeto do céu cortado no topo e em cima do painel | ✅ | objeto do céu desce para baixo do painel/legenda, atrás da Val |
| 14 | Cenas longas sem a Val (espaço) paradas | ✅ em parte | prompt: Val em 2 de cada 3 cenas, no máx. 2 seguidas sem ela |
| 15 | (prévia baratas, 11/11) Contador torto: encolhia do meio para o canto e ficava no meio do caminho | ✅ | contador fixo em cima, centralizado, tamanho único; só dá um pulo quando o número muda |
| 16 | Árvores da floresta flutuando (tronco terminava acima do chão) e moitas no ar | ✅ | troncos e moitas descem para dentro do chão |
| 17 | Sacos de lixo/folhas/plantas flutuando no meio da tela (lugar "meio"/"céu") | ✅ | só bicho voador, nuvem, sol, lua, Terra, gota, dinheiro e folhas ficam no ar; o resto vai para o chão |
| 18 | Texto "H2O + CO2 = ?" do quadro-negro brigando com a legenda | ✅ | quadro-negro só com rabiscos, sem texto |
| 19 | Fogo "brochante" (chama pequena e parada) | ✅ | fogo novo: 5 camadas de labareda dançando, faíscas subindo, brilho; rua destruída ganha 2 fogos animados |
| 20 | Ruas e lugares públicos vazios | ✅ | figurantes genéricos (kit_pessoas.js) andando ao fundo; no caos correm com os braços para cima |
| 21 | Val parada no espaço na última cena | ✅ | cenário espaço sem a Val (só o planeta); Terra do fundo desce para não ficar atrás da legenda |
| 22 | (prévia baratas 2) Monte de folhas secas flutuando na altura da cintura da Val na horta | ✅ | folhas saem da lista do que pode ficar no ar (monte de folhas é sempre no chão) |
| 23 | Montes de folhas em fileira certinha, todos iguais | ✅ | objetos repetidos espalhados de forma natural (posição, profundidade, tamanho, ângulo e lado variados) + folhas soltas em volta |
| 24 | Pouco fogo na cena da rua destruída | ✅ | 6 fogos: 2 nas casas ao fundo, 2 médios, 2 grandes na frente nos cantos |
| 25 | (prévia baratas 3) Figurantes pequenos demais (≈ 1/3 da Val) | ✅ | escala 0,42–0,52 → 0,64–0,80 e um pouco mais à frente |
| 26 | Balões ora em MAIÚSCULA, ora em minúscula ("Tá quieto demais…") | ✅ | balão sempre em maiúscula no motor |
| 27 | Cena do hospital falando de "fila" com 1 pessoa só | ✅ | hospital 3 figurantes, mercado 4 |
| 28 | Contador pequeno demais para o vídeo | ✅ | contador em tamanho cheio (escala 0,72 → 1) |
| 29 | (vídeo baratas, 11/11 21h35) Holofote mirando ao lado da Val (ela no escuro) | ✅ | camada do holofote usa coordenadas de tela e segue a cabeça com o zoom |
| 30 | Fogo da frente cobrindo o corpo da Val na rua destruída | ✅ | fogos da frente menores e só nas pontas da tela |
| 31 | Segunda metade escura/marrom (noite + cor sumindo + vinheta) e floresta de noite quase preta | ✅ | cor some até no máx. 55%, noite mais leve, vinheta mais leve, céu da floresta à noite mais claro |
| 32 | (vídeo baratas 21h35, lista do Heitor) Contador fora do centro e pequeno | ✅ | centro exato (left 50% + translate -50%), letras 34/128 px |
| 33 | Gíria "loss" | ✅ | PROMPT_FABULA: proibido, usar "problema" |
| 34 | Celulares em pé no chão "flutuando"; rua só com a Val | ✅ | celular no chão vira gente olhando o celular; mais figurantes (rua 6, destruída 5, mercado 5, praia 5, fazenda 3, hospital 4) |
| 35 | Balão e legenda se batendo | ✅ | balão sempre abaixo da legenda (conferido a cada quadro) |
| 36 | Pássaro em cima do lagarto, os dois colados no canto | ✅ | objetos diferentes em pontos e profundidades diferentes; "esquerda/direita" a 20–40% da tela, não na borda |
| 37 | Som de disco arranhado alto no hospital | ✅ | "scratch" fora da lista de efeitos; efeitos mais baixos (0,55 → 0,38) |
| 38 | Moscas caídas no chão | ✅ | mosca sempre no ar, voando/pairando (pássaro no ar também) |
| 39 | Cidade pegando fogo 2 vezes | ✅ | rua_destruida só no último ato (código troca antes disso por rua normal) + regra no prompt |
| 40 | Figurantes parecendo crianças | ✅ | pernas mais compridas e escala 0,92–1,06 |
Pedido do dono no roteiro: campo ntc = "tema | pedido" (ex.: "E se as baratas sumissem do mundo? | na cena da cidade pegando fogo use a frase ...").
| 41 | Cena sem a Val (horta/floresta) vazia e parada | ✅ | ganha 2 figurantes e 2 pássaros voando |
| 42 | Legenda pulando de cima para baixo no close | ✅ | legenda sempre em cima |
| 43 | Val parada nos últimos segundos (placa da Parte 2) | ✅ | Val dá tchau/chama para a Parte 2 enquanto a placa está na tela |

## Decisões que não são erro (ficam no projeto do Claude)
- Coringa: linha editorial nova da pauta (perigo, consequência, mistério, absurdo; nicho rebaixado) — cofre e7d8d71.
- NTC (11/11 noite): música cômica própria, som do contador, luz por cena (pôr do sol/holofote), closes de mão e olho.
