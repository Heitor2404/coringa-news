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

## Decisões que não são erro (ficam no projeto do Claude)
- Coringa: linha editorial nova da pauta (perigo, consequência, mistério, absurdo; nicho rebaixado) — cofre e7d8d71.
