# V2.1 — auditoria, correções e validação (ramo `visual-v2-1-refinamento`)

Derivado de `visual-v2` (c9a611c). **Sem merge** em `main` nem em `visual-v2`. Nenhuma chamada paga (IA, imagem, vídeo, áudio). NTC intocado.
Teste automático **não é aprovação visual**: todo estado abaixo é técnico; a aprovação é do Heitor.

## Resumo

- 33 composições auditadas (32 da V2 + `video.documental`, nova): **30 aprovadas tecnicamente, 3 parciais, 0 bloqueadas**.
- Seleção visual: 24/24 casos em 8 domínios e 8/8 negativos (antes das correções: 18/24 e 6/8). **Conjunto de reserva, rodado uma vez e não ajustado: 10/16** — limite real do seletor por padrões (ver §4).
- Fiscal em 3 categorias; banco de defeitos injetados: 12/12 detectados, 0 falso positivo.
- Pipeline experimental (roteiro → … → mp4) com voz local espeak-ng: eclusa, revelação e legenda **sincronizadas e medidas no palco**; fiscal sem bloqueio; vídeo de 51.08 s.
- Testes: `tests/test_v2.py` + `tests/test_v21.py` = 43 passam. Suíte inteira: 5 falhas **pré-existentes e idênticas em `main`** (dependem de prompts guardados no cofre privado; não são do motor visual).

## 1. Matriz de problemas (diagnóstico → correção → teste)

| # | problema | causa | arquivo / função | solução | teste | evidência |
|---|---|---|---|---|---|---|
| 1 | legenda cobria o conteúdo em cenas cheias | faixa fixa 1240 | `nucleo.js` `ocupacao()` | mede a cena a 70% e escolhe 1240/1300/360 e 58/66 px; registra conflito | fiscal D4 | capturas 75% |
| 2 | zonas da interface diferentes por plataforma | constante única | `nucleo.js` `V2.Z`, `PLATAFORMAS` | zonas reels/tiktok/shorts/todas | fiscal D2 | — |
| 3 | texto de 24 px (marca, kicker, fontes) | sem token mínimo | `estilo.css`, `comp/*.js` | token `fs.min` = 26 px | fiscal D3 (0 ocorrências após) | catálogo depois |
| 4 | eclusa sem física e sem planos | desenho estático | `mecanismos.js` | planos A–F; nível (1−k)²; comporta só com Δ<0,3 m; navio na superfície; estado publicado | `test_eclusa_estado_fisico[subir/descer]` | prévia eclusa |
| 5 | rota reta atravessando continente | linha em Mercator | `mapas.js` `densa`; `geo.validar_rota` | círculo máximo; validação de terra | `test_rota_maritima…`; fiscal D8 | tema mapas |
| 6 | rota do Cabo Horn fora do quadro | zoom mínimo vertical do MapLibre (z≈1,9 em 1920 px) | `mapas.js` `motorMapa` | host do mapa encolhe na vertical com esmaecimento quando o enquadramento pede zoom menor | `test_mapa_mundial_cabe_no_quadro…` | tema mapas 17 s |
| 7 | nomes de pino sob o cabeçalho/painel e cruzados | posição fixa acima do pino; vizinhos do quadro anterior | `mapas.js` `animPino` | candidatos acima/abaixo/direita/esquerda; foge do pino vizinho; ordem por quadro | mesmo teste | tema mapas |
| 8 | caixa geográfica além dos polos (página travava) | folga relativa grande | `geo.caixa_de` | limite −80..84 / −180..180 | `test_caixa_nao_passa_dos_polos` | — |
| 9 | equivalência numérica sem cálculo | texto à mão | `unidades.py`, `fatos.para_tela` | cubo de lado calculado + referência real na mesma escala | pipeline (número vem do fato) | numero.animado |
| 10 | gráfico sem conclusão | decorativo | `graficos.js` | `conclusao`, destaque narrado, aviso de eixo | regressão | grafico.* |
| 11 | banners sem saída/categoria | — | `banners.js` | entra/sai, níveis importante/alerta, posição | regressão | banner.* |
| 12 | foto antiga com zoom além da resolução | zoom livre | `fotos.js` foto.historica | dois momentos; zoom ≤ 2× da resolução; alerta | regressão | foto.historica |
| 13 | foto faltante virava ilustração com rótulo "FOTO REAL" | fallback para `fundo_b` | `galeria.midia` | substituto "SEM ACERVO" gerado + aviso | `test_falta_de_foto_vira_substituto…` | — |
| 14 | carimbo cobria a anotação | mesma região | `fotos.js` | carimbo dentro da foto; sai quando a anotação entra | medição (0 choques) | foto.historica_2 |
| 15 | sem vídeo de arquivo | — | `fotos.js` video.documental; `palco.quadros_video` | quadros por ffmpeg, determinístico | catálogo | video.documental |
| 16 | revelação solta da explicação | sem base | `nucleo.js` `sc.base`; `montagem.py` M8 | mecanismo congelado sob a revelação e o fechamento | pipeline experimental | quadro_5/6 |
| 17 | encerramento genérico | variante única | `editorial.js` | conclusão/pergunta/marca/cta | regressão | encerramento |
| 18 | seletor: "percorre", "a" solto, "anos-luz", 1453 | padrões frouxos/estreitos; desistia na 1ª crítica | `capacidades.py` | destino explícito; datas 1000–2099; tenta todas as críticas; requisitos validam coordenadas/valores; capacidade "máquina" | `avaliacao_selecao` | §4 |
| 19 | fiscal misturava bloqueio e gosto | uma lista só | `fiscal_v2.py` | determinístico / semântico / estético, com evidência e solução | `avaliacao_fiscal`; `test_fiscal_*` | §5 |
| 20 | palavra dita com o bloco anterior de legenda na tela | sobreposição de blocos → vencia o primeiro | `nucleo.js` (seleção do bloco) | vence o mais recente | `test_legenda_sobreposta…` (falha com o código antigo) | §6 |
| 21 | erro de sintaxe derrubava 4 composições sem aviso | comentário `//` em linha única | `fotos.js` | `/* */` + teste que compila todo JS e confere o catálogo | `test_todo_js_do_palco_compila…` | — |
| 22 | "80 km" (a fonte citada diz 82) | arredondamento do roteiro | `mapas.js` exemplo; roteiro experimental | 82 km (Wikipedia inglês; Britannica) | — | quadro_1 |
| 23 | "Oceano Pacífico" saía pela borda no mapa mundial (24 medições graves no tema mapas) | visibilidade testava só o centro do rótulo | `mapas.js` `motorMapa.upd` | rótulo de mar preso no quadro pela largura; país só se couber inteiro | medição do tema mapas: 24 → 0 | tema mapas |

## 2. Auditoria por composição

| composição | problema na V2 | correção V2.1 | teste | limitações | estado |
|---|---|---|---|---|---|
| `abertura.pergunta` | mascote não existia; texto sempre no mesmo terço, mesmo com o foco da foto ali | posição adaptativa (texto do lado oposto ao foco); pose de mascote opcional com sombra/contraluz; margem direita 380 com mascote | regressão visual; pipeline experimental (cena 0) | mascote só se houver pose PNG em assets/mascote3d | **aprovado tecnicamente** |
| `abertura.revelacao` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual | — | **aprovado tecnicamente** |
| `banner.discreto` | entrava e ficava; sem saída nem posição alternativa | parâmetros entra/sai; posição "baixo" (1080); saída por cortina | regressão visual | — | **aprovado tecnicamente** |
| `banner.importante` | um só nível (vermelho) para tudo | níveis "importante" (amarelo, ícone de documento) e "alerta" (vermelho); saída deslizando | regressão visual | — | **aprovado tecnicamente** |
| `lower_third` | texto pequeno; sem tipo "história" | tipo "historia" com selo de ano; texto maior; base ancorada em 1185; saída | regressão visual | — | **aprovado tecnicamente** |
| `titulo.capitulo` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual | — | **aprovado tecnicamente** |
| `destaque.palavras` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual | — | **aprovado tecnicamente** |
| `numero.animado` | equivalência solta ("80 piscinas") sem cálculo; cubo pequeno; rótulo encostado no número | equivalência calculada em unidades.py (cubo de ≈ 59 m + referência real na MESMA escala); escala adaptativa até 1200; número desceu 23 px (choque medido) | test_v21 (pipeline: número vem do fato validado); fiscal D9 | equivalência só para volume; outras unidades ficam sem | **aprovado tecnicamente** |
| `comparacao.grandezas` | sem defeito medido | só mudanças globais (G1–G5); referências em capacidades.REFERENCIAS_M | regressão visual | — | **aprovado tecnicamente** |
| `proporcao` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual | — | **aprovado tecnicamente** |
| `grafico.barras` | barras sem conclusão; rótulos pequenos | parâmetro conclusao (caixa após as barras); destaque = categoria narrada; rótulos 34 px, valores 38 px | regressão visual; seleção x7 (valores não numéricos recusados) | — | **aprovado tecnicamente** |
| `grafico.temporal` | eixo podia não começar no zero sem aviso; sem período destacado | conclusao; faixa de período; aviso "EIXO NÃO COMEÇA NO ZERO"; linha termina aos 75% | regressão visual; seleção x6 (série curta recusada) | — | **aprovado tecnicamente** |
| `mapa.localizacao` | pinos e nomes pequenos; câmera chegava tarde | pino 40 px; nomes 38–42 px; câmera chega a ~45%; nomes de pino escolhem posição livre | regressão visual; fiscal D7 (coordenada/país) | depende de scripts/v2_natural_earth.py | **aprovado tecnicamente** |
| `mapa.rota` | rota fina e reta; Cabo Horn saía do quadro; nomes sob o cabeçalho; "80 km" (a fonte citada diz 82) | rotas por círculo máximo, 12 px com brilho; painel de comparação (até 3); host encolhe quando o enquadramento pede zoom menor; nomes evitam cabeçalho/painel/pino vizinho; geo.validar_rota; 82 km | test_v21: rota sobre terra, Cabo Horn no quadro, nomes sem choque; fiscal D8 | zoom mundial ainda deixa NY e SF próximos (nomes legíveis, pinos encostados) | **aprovado tecnicamente** |
| `mapa.territorio` | sem defeito grave medido | só mudanças globais (G1–G5); câmera ~45% | regressão visual | rótulo de mar pode cair sobre o território (Golfo do Panamá no exemplo) | **parcial** |
| `linha_tempo.historica` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual; seleção (datas 1000–2099) | o ano seguinte aparece cortado na borda durante a corrida (intencional?) | **aprovado tecnicamente** |
| `foto.historica` | zoom além da resolução (borrão); carimbo fora da área segura; ilustração substituía a foto faltante com rótulo "FOTO REAL" | momento 1 inteira / momento 2 aproximação limitada a 2× a resolução (ou varredura em panorâmica); alerta de baixa resolução; carimbo dentro da foto e sai quando a anotação entra; substituto "SEM ACERVO" | test_v21 (substituto); medição sem choque | a panorâmica de 1913 tem 91 px de altura útil: vira uma faixa fina, mais fraca que o layout de dois painéis da V2; precisa do original em resolução maior | **parcial** |
| `foto.sequencia` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual | — | **aprovado tecnicamente** |
| `foto.documental` | sem defeito medido | só mudanças globais (G1–G5); recorte/foco "auto" | regressão visual; fiscal D5 (arquivo ausente) | — | **aprovado tecnicamente** |
| `comparacao.antes_depois` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual | — | **aprovado tecnicamente** |
| `video.documental` | não existia | quadros extraídos por ffmpeg (cache), moldura para paisagem / cobertura para vertical, etiqueta, lower third, saída | regressão visual; catálogo | sem vídeo de arquivo real local para teste; licença do vídeo segue a mesma regra das fotos | **parcial** |
| `diagrama.explicativo` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual; seleção (máquina → diagrama) | — | **aprovado tecnicamente** |
| `processo.etapas` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual; seleção b1/t2/r10 | — | **aprovado tecnicamente** |
| `forcas.vetores` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual; seleção f1/f2/r9 | — | **aprovado tecnicamente** |
| `astronomia.orbita` | texto "fora de escala" com 24 px | 26 px (G3) | regressão visual; seleção a1/r11 (ano-luz deixou de virar órbita) | — | **aprovado tecnicamente** |
| `mecanismo.eclusa` | escala pequena; câmera parada; nível linear; comporta abria com desnível; navio flutuava fora da água; rótulos se cobriam | mundo 1480 px com túneis e válvulas; planos A–F; nível (1−k)²; comporta só abre com Δ < 0,3 m; navio na superfície; rótulos com anticolisão; estado físico publicado; tempos amarrados à fala | test_v21: física nos dois sentidos; pipeline experimental (entra/desce/iguala medidos); fiscal S3 | esquema ilustrativo, sem proporção real da câmara | **aprovado tecnicamente** |
| `mecanismo.nivel` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual; seleção n1/n3/r15 | — | **aprovado tecnicamente** |
| `evento.impacto` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual; seleção a3/n2/r12 | — | **aprovado tecnicamente** |
| `revelacao.surpresa` | só sobre foto; classes colidiam com a eclusa quando usada como base | camada base (mecanismo congelado sob a revelação, regra M8); classes rv-; rótulos da base escondidos; gradiente só no topo | pipeline experimental (oculta 0,3 s antes / visível 0,35 s depois da palavra); fiscal D10 | — | **aprovado tecnicamente** |
| `fonte.evidencia` | textos com 24 px | 26 px (G3) | regressão visual | — | **aprovado tecnicamente** |
| `citacao` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual | — | **aprovado tecnicamente** |
| `encerramento.editorial` | bloco de marca grande e genérico, sem relação com o vídeo | variantes conclusao/pergunta/marca/cta; faixa de marca compacta; fontes 1150–1210; sobre a base do mecanismo | regressão visual; pipeline experimental (cena final) | — | **aprovado tecnicamente** |
| `animacao.quadros` | sem defeito medido | só mudanças globais (G1–G5) | regressão visual (pula sem Manim) | Manim precisa de pango/cairo (apt) | **aprovado tecnicamente** |

### `abertura.pergunta` — aprovado tecnicamente

- **funcao**: gancho: pergunta sobre a foto do assunto
- **problema v2**: mascote não existia; texto sempre no mesmo terço, mesmo com o foco da foto ali
- **causa**: layout fixo, sem leitura do foco da foto
- **correcao v21**: posição adaptativa (texto do lado oposto ao foco); pose de mascote opcional com sombra/contraluz; margem direita 380 com mascote
- **arquivo**: comp/aberturas.js abertura.pergunta
- **teste**: regressão visual; pipeline experimental (cena 0)
- **evidencia**: capturas antes/depois em 8/45/75/97% (abertura.pergunta_0..3.jpg)
- **legibilidade**: pergunta 88 px; contexto serifa 40 px
- **hierarquia**: protagonista = pergunta; foto é fundo
- **movimento**: empurrão lento na foto + palavras entram
- **dados fatos**: nenhum número
- **limitacoes**: mascote só se houver pose PNG em assets/mascote3d
- **revisao humana**: a pergunta segura sem a legenda?
- **estado**: aprovado tecnicamente

### `abertura.revelacao` — aprovado tecnicamente

- **funcao**: gancho: título curto sobre detalhe da foto
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/aberturas.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (abertura.revelacao_0..3.jpg)
- **legibilidade**: título 88 px
- **hierarquia**: título
- **movimento**: aproximação do detalhe ao plano geral
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: o detalhe inicial é legível no celular?
- **estado**: aprovado tecnicamente

### `banner.discreto` — aprovado tecnicamente

- **funcao**: contexto curto sem interromper
- **problema v2**: entrava e ficava; sem saída nem posição alternativa
- **causa**: sem parâmetros de permanência
- **correcao v21**: parâmetros entra/sai; posição "baixo" (1080); saída por cortina
- **arquivo**: comp/banners.js banner.discreto
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (banner.discreto_0..3.jpg)
- **legibilidade**: 34 px
- **hierarquia**: secundário (não compete com a legenda)
- **movimento**: entrada, permanência, saída
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: tempo de leitura suficiente?
- **estado**: aprovado tecnicamente

### `banner.importante` — aprovado tecnicamente

- **funcao**: alerta / correção de fato
- **problema v2**: um só nível (vermelho) para tudo
- **causa**: sem categoria
- **correcao v21**: níveis "importante" (amarelo, ícone de documento) e "alerta" (vermelho); saída deslizando
- **arquivo**: comp/banners.js banner.importante
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (banner.importante_0..3.jpg)
- **legibilidade**: título 44 px; corpo 30 px
- **hierarquia**: prioridade sobre a legenda (legenda muda de faixa)
- **movimento**: entra, pulsa uma vez, sai
- **dados fatos**: texto do exemplo vem de fatos.PANAMA_LEILAO
- **limitacoes**: —
- **revisao humana**: o amarelo "importante" se distingue do alerta?
- **estado**: aprovado tecnicamente

### `lower_third` — aprovado tecnicamente

- **funcao**: nome de pessoa/lugar/navio
- **problema v2**: texto pequeno; sem tipo "história"
- **causa**: tamanhos antigos
- **correcao v21**: tipo "historia" com selo de ano; texto maior; base ancorada em 1185; saída
- **arquivo**: comp/banners.js lower_third
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (lower_third_0..3.jpg)
- **legibilidade**: nome 44 px
- **hierarquia**: secundário
- **movimento**: entra/sai
- **dados fatos**: data do exemplo marcada como do arquivo
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `titulo.capitulo` — aprovado tecnicamente

- **funcao**: separador de parte
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/editorial.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (titulo.capitulo_0..3.jpg)
- **legibilidade**: 88 px
- **hierarquia**: título
- **movimento**: número grande ao fundo
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `destaque.palavras` — aprovado tecnicamente

- **funcao**: frase-chave sobre foto
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/editorial.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (destaque.palavras_0..3.jpg)
- **legibilidade**: 72 px
- **hierarquia**: frase
- **movimento**: marca-texto entra por palavra
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `numero.animado` — aprovado tecnicamente

- **funcao**: número grande com contexto
- **problema v2**: equivalência solta ("80 piscinas") sem cálculo; cubo pequeno; rótulo encostado no número
- **causa**: equivalência escrita à mão; escala fixa
- **correcao v21**: equivalência calculada em unidades.py (cubo de ≈ 59 m + referência real na MESMA escala); escala adaptativa até 1200; número desceu 23 px (choque medido)
- **arquivo**: comp/dados.js numero.animado; src/v2/unidades.py; fatos.para_tela
- **teste**: test_v21 (pipeline: número vem do fato validado); fiscal D9
- **evidencia**: capturas antes/depois em 8/45/75/97% (numero.animado_0..3.jpg)
- **legibilidade**: número 230 px; unidade 52 px; fonte 26 px
- **hierarquia**: protagonista = número; cubo explica a escala
- **movimento**: contagem até o valor; cubo cresce
- **dados fatos**: US$ 5,3 mi = lance em leilão por vaga (SK Gas, G. Spirit, 1º/09/2026; pedágio à parte; Revista Oeste); 200 milhões de L (Wikipedia)
- **limitacoes**: equivalência só para volume; outras unidades ficam sem
- **revisao humana**: o cubo ao lado do Cristo Redentor ajuda ou distrai?
- **estado**: aprovado tecnicamente

### `comparacao.grandezas` — aprovado tecnicamente

- **funcao**: altura/tamanho lado a lado
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5); referências em capacidades.REFERENCIAS_M
- **arquivo**: comp/dados.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (comparacao.grandezas_0..3.jpg)
- **legibilidade**: rótulos 28 px
- **hierarquia**: item destacado
- **movimento**: barras/silhuetas crescem
- **dados fatos**: referências aproximadas marcadas
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `proporcao` — aprovado tecnicamente

- **funcao**: parte de um todo (%)
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/dados.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (proporcao_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: percentual
- **movimento**: grade preenche
- **dados fatos**: fonte obrigatória
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `grafico.barras` — aprovado tecnicamente

- **funcao**: comparar quantidades
- **problema v2**: barras sem conclusão; rótulos pequenos
- **causa**: gráfico decorativo
- **correcao v21**: parâmetro conclusao (caixa após as barras); destaque = categoria narrada; rótulos 34 px, valores 38 px
- **arquivo**: comp/graficos.js barras
- **teste**: regressão visual; seleção x7 (valores não numéricos recusados)
- **evidencia**: capturas antes/depois em 8/45/75/97% (grafico.barras_0..3.jpg)
- **legibilidade**: 34/38 px
- **hierarquia**: conclusão
- **movimento**: barras crescem, depois a conclusão
- **dados fatos**: exemplo marcado como DADOS ILUSTRATIVOS
- **limitacoes**: —
- **revisao humana**: a conclusão aparece no tempo certo?
- **estado**: aprovado tecnicamente

### `grafico.temporal` — aprovado tecnicamente

- **funcao**: evolução no tempo
- **problema v2**: eixo podia não começar no zero sem aviso; sem período destacado
- **causa**: —
- **correcao v21**: conclusao; faixa de período; aviso "EIXO NÃO COMEÇA NO ZERO"; linha termina aos 75%
- **arquivo**: comp/graficos.js temporal
- **teste**: regressão visual; seleção x6 (série curta recusada)
- **evidencia**: capturas antes/depois em 8/45/75/97% (grafico.temporal_0..3.jpg)
- **legibilidade**: eixo 28–30 px
- **hierarquia**: linha + conclusão
- **movimento**: linha desenha
- **dados fatos**: exemplo ilustrativo marcado
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `mapa.localizacao` — aprovado tecnicamente

- **funcao**: onde fica
- **problema v2**: pinos e nomes pequenos; câmera chegava tarde
- **causa**: tamanhos antigos
- **correcao v21**: pino 40 px; nomes 38–42 px; câmera chega a ~45%; nomes de pino escolhem posição livre
- **arquivo**: comp/mapas.js
- **teste**: regressão visual; fiscal D7 (coordenada/país)
- **evidencia**: capturas antes/depois em 8/45/75/97% (mapa.localizacao_0..3.jpg)
- **legibilidade**: nomes 38–42 px; atribuição 26 px
- **hierarquia**: pino
- **movimento**: aproxima com leve rotação
- **dados fatos**: coordenadas Natural Earth; atribuição na tela
- **limitacoes**: depende de scripts/v2_natural_earth.py
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `mapa.rota` — aprovado tecnicamente

- **funcao**: trajeto / comparação de rotas
- **problema v2**: rota fina e reta; Cabo Horn saía do quadro; nomes sob o cabeçalho; "80 km" (a fonte citada diz 82)
- **causa**: linha reta em Mercator; zoom mínimo vertical do MapLibre (z≈1,9 em 1920 px); nomes sempre acima do pino; valor do roteiro antigo
- **correcao v21**: rotas por círculo máximo, 12 px com brilho; painel de comparação (até 3); host encolhe quando o enquadramento pede zoom menor; nomes evitam cabeçalho/painel/pino vizinho; geo.validar_rota; 82 km
- **arquivo**: comp/mapas.js motorMapa, animPino, mapa.rota; src/v2/geo.py validar_rota/caixa_de
- **teste**: test_v21: rota sobre terra, Cabo Horn no quadro, nomes sem choque; fiscal D8
- **evidencia**: capturas antes/depois em 8/45/75/97% (mapa.rota_0..3.jpg)
- **legibilidade**: distância 64 px; nomes 42 px
- **hierarquia**: rota
- **movimento**: traço progressivo + bolinha na ponta; contagem da distância
- **dados fatos**: NY–SF 9.500 × 22.500 km (Wikipedia); traçado ilustrativo; Cabral marcado aproximado
- **limitacoes**: zoom mundial ainda deixa NY e SF próximos (nomes legíveis, pinos encostados)
- **revisao humana**: a comparação canal × Cabo Horn convence sem som?
- **estado**: aprovado tecnicamente

### `mapa.territorio` — parcial

- **funcao**: destacar país
- **problema v2**: sem defeito grave medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5); câmera ~45%
- **arquivo**: comp/mapas.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (mapa.territorio_0..3.jpg)
- **legibilidade**: nome 44 px
- **hierarquia**: território
- **movimento**: aproxima; território acende
- **dados fatos**: Natural Earth
- **limitacoes**: rótulo de mar pode cair sobre o território (Golfo do Panamá no exemplo)
- **revisao humana**: o rótulo do golfo sobre o país incomoda?
- **estado**: parcial

### `linha_tempo.historica` — aprovado tecnicamente

- **funcao**: sequência de datas
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/editorial.js
- **teste**: regressão visual; seleção (datas 1000–2099)
- **evidencia**: capturas antes/depois em 8/45/75/97% (linha_tempo.historica_0..3.jpg)
- **legibilidade**: ano 64 px
- **hierarquia**: evento ativo
- **movimento**: trilho corre; evento ativo acende
- **dados fatos**: —
- **limitacoes**: o ano seguinte aparece cortado na borda durante a corrida (intencional?)
- **revisao humana**: o corte do ano seguinte na borda é aceitável?
- **estado**: aprovado tecnicamente

### `foto.historica` — parcial

- **funcao**: foto de arquivo em dois momentos
- **problema v2**: zoom além da resolução (borrão); carimbo fora da área segura; ilustração substituía a foto faltante com rótulo "FOTO REAL"
- **causa**: zoom sem limite; posição fixa; fallback para fundo_b
- **correcao v21**: momento 1 inteira / momento 2 aproximação limitada a 2× a resolução (ou varredura em panorâmica); alerta de baixa resolução; carimbo dentro da foto e sai quando a anotação entra; substituto "SEM ACERVO"
- **arquivo**: comp/fotos.js foto.historica; galeria.midia/_substituto
- **teste**: test_v21 (substituto); medição sem choque
- **evidencia**: capturas antes/depois em 8/45/75/97% (foto.historica_0..3.jpg)
- **legibilidade**: carimbo 30 px; crédito 26 px
- **hierarquia**: foto
- **movimento**: assenta, aproxima/varre, anotação desenha
- **dados fatos**: ano e crédito (Library of Congress, domínio público)
- **limitacoes**: a panorâmica de 1913 tem 91 px de altura útil: vira uma faixa fina, mais fraca que o layout de dois painéis da V2; precisa do original em resolução maior
- **revisao humana**: com esta foto, V2 ou V2.1 fica melhor?
- **estado**: parcial

### `foto.sequencia` — aprovado tecnicamente

- **funcao**: várias fotos do mesmo lugar
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/fotos.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (foto.sequencia_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: foto atual
- **movimento**: troca com movimento
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `foto.documental` — aprovado tecnicamente

- **funcao**: foto real do assunto
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5); recorte/foco "auto"
- **arquivo**: comp/fotos.js; palco.preparar
- **teste**: regressão visual; fiscal D5 (arquivo ausente)
- **evidencia**: capturas antes/depois em 8/45/75/97% (foto.documental_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: foto
- **movimento**: Ken Burns
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `comparacao.antes_depois` — aprovado tecnicamente

- **funcao**: duas fotos, antes × depois
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/fotos.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (comparacao.antes_depois_0..3.jpg)
- **legibilidade**: selos 30 px
- **hierarquia**: divisória
- **movimento**: cortina varre
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `video.documental` — parcial

- **funcao**: trecho de vídeo de arquivo (NOVA)
- **problema v2**: não existia
- **causa**: —
- **correcao v21**: quadros extraídos por ffmpeg (cache), moldura para paisagem / cobertura para vertical, etiqueta, lower third, saída
- **arquivo**: comp/fotos.js video.documental; palco.quadros_video
- **teste**: regressão visual; catálogo
- **evidencia**: capturas antes/depois em 8/45/75/97% (video.documental_0..3.jpg)
- **legibilidade**: etiqueta 26 px
- **hierarquia**: vídeo
- **movimento**: reprodução quadro a quadro determinística
- **dados fatos**: só testado com clipe SINTÉTICO (fractal) marcado na tela
- **limitacoes**: sem vídeo de arquivo real local para teste; licença do vídeo segue a mesma regra das fotos
- **revisao humana**: testar com um trecho real antes de usar
- **estado**: parcial

### `diagrama.explicativo` — aprovado tecnicamente

- **funcao**: nós e setas
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/ciencia.js
- **teste**: regressão visual; seleção (máquina → diagrama)
- **evidencia**: capturas antes/depois em 8/45/75/97% (diagrama.explicativo_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: fluxo
- **movimento**: setas desenham
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `processo.etapas` — aprovado tecnicamente

- **funcao**: etapas em ordem
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/ciencia.js
- **teste**: regressão visual; seleção b1/t2/r10
- **evidencia**: capturas antes/depois em 8/45/75/97% (processo.etapas_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: etapa ativa
- **movimento**: etapas acendem
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `forcas.vetores` — aprovado tecnicamente

- **funcao**: forças sobre um objeto
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/ciencia.js
- **teste**: regressão visual; seleção f1/f2/r9
- **evidencia**: capturas antes/depois em 8/45/75/97% (forcas.vetores_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: vetores
- **movimento**: vetores crescem
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `astronomia.orbita` — aprovado tecnicamente

- **funcao**: órbita
- **problema v2**: texto "fora de escala" com 24 px
- **causa**: tamanho antigo
- **correcao v21**: 26 px (G3)
- **arquivo**: comp/ciencia.js
- **teste**: regressão visual; seleção a1/r11 (ano-luz deixou de virar órbita)
- **evidencia**: capturas antes/depois em 8/45/75/97% (astronomia.orbita_0..3.jpg)
- **legibilidade**: 26 px
- **hierarquia**: órbita
- **movimento**: translação
- **dados fatos**: marcado FORA DE ESCALA
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `mecanismo.eclusa` — aprovado tecnicamente

- **funcao**: eclusa: o navio sobe/desce por gravidade
- **problema v2**: escala pequena; câmera parada; nível linear; comporta abria com desnível; navio flutuava fora da água; rótulos se cobriam
- **causa**: desenho de V2 sem física nem planos
- **correcao v21**: mundo 1480 px com túneis e válvulas; planos A–F; nível (1−k)²; comporta só abre com Δ < 0,3 m; navio na superfície; rótulos com anticolisão; estado físico publicado; tempos amarrados à fala
- **arquivo**: comp/mecanismos.js mecanismo.eclusa
- **teste**: test_v21: física nos dois sentidos; pipeline experimental (entra/desce/iguala medidos); fiscal S3
- **evidencia**: capturas antes/depois em 8/45/75/97% (mecanismo.eclusa_0..3.jpg)
- **legibilidade**: rótulos 30–34 px
- **hierarquia**: navio + nível
- **movimento**: 6 planos de câmera; água, válvulas, comportas
- **dados fatos**: 26 m (Wikipedia); FORA DE ESCALA na tela
- **limitacoes**: esquema ilustrativo, sem proporção real da câmara
- **revisao humana**: entende-se sem som?
- **estado**: aprovado tecnicamente

### `mecanismo.nivel` — aprovado tecnicamente

- **funcao**: nível de água genérico
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/mecanismos.js
- **teste**: regressão visual; seleção n1/n3/r15
- **evidencia**: capturas antes/depois em 8/45/75/97% (mecanismo.nivel_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: nível
- **movimento**: sobe/desce
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `evento.impacto` — aprovado tecnicamente

- **funcao**: explosão/impacto com raios
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/ciencia.js
- **teste**: regressão visual; seleção a3/n2/r12
- **evidencia**: capturas antes/depois em 8/45/75/97% (evento.impacto_0..3.jpg)
- **legibilidade**: rótulos 28 px
- **hierarquia**: centro
- **movimento**: onda expande
- **dados fatos**: raio marcado (≈)
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `revelacao.surpresa` — aprovado tecnicamente

- **funcao**: resposta no instante em que é dita
- **problema v2**: só sobre foto; classes colidiam com a eclusa quando usada como base
- **causa**: sem camada de base; nomes de classe genéricos
- **correcao v21**: camada base (mecanismo congelado sob a revelação, regra M8); classes rv-; rótulos da base escondidos; gradiente só no topo
- **arquivo**: comp/editorial.js; nucleo.js (sc.base); montagem.py M8
- **teste**: pipeline experimental (oculta 0,3 s antes / visível 0,35 s depois da palavra); fiscal D10
- **evidencia**: capturas antes/depois em 8/45/75/97% (revelacao.surpresa_0..3.jpg)
- **legibilidade**: resposta 150 px
- **hierarquia**: resposta
- **movimento**: clarão + resposta bate
- **dados fatos**: —
- **limitacoes**: —
- **revisao humana**: o clarão é forte demais?
- **estado**: aprovado tecnicamente

### `fonte.evidencia` — aprovado tecnicamente

- **funcao**: recorte de fonte citada
- **problema v2**: textos com 24 px
- **causa**: tamanho antigo
- **correcao v21**: 26 px (G3)
- **arquivo**: comp/editorial.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (fonte.evidencia_0..3.jpg)
- **legibilidade**: 26 px
- **hierarquia**: trecho grifado
- **movimento**: cartão entra, grifo corre
- **dados fatos**: exemplo SINTÉTICO marcado (exemplo.invalid)
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `citacao` — aprovado tecnicamente

- **funcao**: fala literal
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/editorial.js
- **teste**: regressão visual
- **evidencia**: capturas antes/depois em 8/45/75/97% (citacao_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: citação
- **movimento**: entra por linha
- **dados fatos**: autor obrigatório
- **limitacoes**: —
- **revisao humana**: —
- **estado**: aprovado tecnicamente

### `encerramento.editorial` — aprovado tecnicamente

- **funcao**: fecho com conclusão e marca
- **problema v2**: bloco de marca grande e genérico, sem relação com o vídeo
- **causa**: variante única
- **correcao v21**: variantes conclusao/pergunta/marca/cta; faixa de marca compacta; fontes 1150–1210; sobre a base do mecanismo
- **arquivo**: comp/editorial.js; montagem.py (fechamento)
- **teste**: regressão visual; pipeline experimental (cena final)
- **evidencia**: capturas antes/depois em 8/45/75/97% (encerramento.editorial_0..3.jpg)
- **legibilidade**: conclusão 70 px; fontes 26 px
- **hierarquia**: conclusão
- **movimento**: mascote entra; marca desliza
- **dados fatos**: fontes do vídeo listadas
- **limitacoes**: —
- **revisao humana**: tem cara de marca sem virar anúncio?
- **estado**: aprovado tecnicamente

### `animacao.quadros` — aprovado tecnicamente

- **funcao**: cena Manim pré-renderizada
- **problema v2**: sem defeito medido
- **causa**: —
- **correcao v21**: só mudanças globais (G1–G5)
- **arquivo**: comp/ciencia.js; src/v2/manim_cenas.py
- **teste**: regressão visual (pula sem Manim)
- **evidencia**: capturas antes/depois em 8/45/75/97% (animacao.quadros_0..3.jpg)
- **legibilidade**: —
- **hierarquia**: animação
- **movimento**: quadros
- **dados fatos**: —
- **limitacoes**: Manim precisa de pango/cairo (apt)
- **revisao humana**: —
- **estado**: aprovado tecnicamente

## 3. Plataformas e zonas seguras

`V2.Z` por plataforma (`meta.plataforma`: reels, tiktok, shorts, todas). Conteúdo em y 330–1215; legenda 1240–1455 (ou 360 quando a cena ocupa a faixa de baixo); coluna direita da interface fora do conteúdo. O fiscal mede D2 (texto na zona) a cada 0,25 s.

## 4. Seleção visual (8 domínios, conteúdo inédito)

`python -m src.v2.avaliacao_selecao` — resultados em `saida/v21/selecao_*.json`.

- Positivos: 24/24 — por domínio {'historia': '3/3', 'geografia': '3/3', 'biologia': '3/3', 'quimica': '3/3', 'fisica': '3/3', 'astronomia': '3/3', 'tecnologia': '3/3', 'fenomenos': '3/3'}.
- Negativos (8/8): mecanismo sem representação → limitação; comparação sem valores e número sem fonte → foto + aviso (sem gráfico inventado); mapa sem coordenadas ou com coordenada fora do globo → limitação; série curta e barras com valores não numéricos → recusadas; elevador ≠ eclusa. Eclusa animada contra a fala é pega no fiscal (S3).
- **Reserva (16 casos escritos depois das correções, rodados uma vez): 10/16.** Falhas, todas para o mesmo lado (acontecimento crítico parafraseado vira foto sem limitação):
  - `r1` "Roma foi fundada em 753 a.C. e caiu em 476." → foto.documental (aceitável: linha_tempo.historica)
  - `r5` "O sangue leva oxigênio dos pulmões até as células." → foto.documental (aceitável: LIMITACAO, diagrama.explicativo, processo.etapas)
  - `r6` "Uma baleia-azul pode ter 30 metros, o tamanho de três ônibus." → foto.documental (aceitável: comparacao.grandezas)
  - `r7` "O ferro enferruja quando reage com o oxigênio e a água." → foto.documental (aceitável: LIMITACAO, comparacao.antes_depois, processo.etapas)
  - `r13` "A fibra óptica leva a luz de um continente a outro pelo fundo do mar." → foto.documental (aceitável: LIMITACAO, diagrama.explicativo, mapa.rota)
  - `r16` "O furacão se formou no Atlântico e seguiu até a Flórida." → foto.documental (aceitável: mapa.rota)

  Conclusão: padrões de texto não generalizam para paráfrases. **Recomendação**: o roteirista passa a declarar o acontecimento de cada cena (`acontecimento.tipo` + dados) — o seletor já aceita sinais estruturados — e os padrões ficam como rede de segurança.

## 5. Fiscal V2.1

Categorias: **determinístico** (D1 sobreposição persistente, D2 zona, D3 letra < 26 px, D4 legenda sem posição, D5 arquivo ausente, D6 limite de texto, D7 coordenada, D8 rota sobre terra, D9 número sem validação, D10 sincronia da revelação, D11 plano longo/loudness), **semântico** (S1 crítico sem representação, S2 fala de mecanismo com foto, S3 eclusa × fala, S4 dados insuficientes), **estético** (observações + perguntas, nunca bloqueia). Cada achado: cena, instante, problema, evidência, gravidade, solução (`fiscal_v2.tabela_md`).

- Banco de defeitos injetados (`python -m src.v2.avaliacao_fiscal`): 12/12 detectados, 0 falsos positivos nas versões corretas.
- Panamá convertido (V2.1): achou 2 bloqueios reais (rótulos da eclusa-base sob a revelação; ambos corrigidos) e 1 aviso (contexto numérico 96 > 70 → limite revisto para 110 após conferir que cabe em 2 linhas, sem mexer no fato). Estado final: sem bloqueio; 1 observação estética (imagem repetida).
- Falsos negativos conhecidos: a medição geométrica só vê texto marcado (`data-txt`, `data-g`); sobreposição de desenho SVG com texto não é medida. O seletor (§4) é a principal fonte de falso negativo semântico.

## 6. Pipeline experimental (integração)

`python -m src.v2.experimental` (`--silencio` sem voz). Isolado: não altera o motor de produção nem o roteirista.

- **Áudio testado**: voz local **espeak-ng** (pt-br), sintetizada palavra por palavra → o instante de cada palavra é conhecido por construção. Voz robótica de propósito: testa sincronia, não qualidade de voz.
- **Não testado**: voz humana/TTS de produção (nenhuma chamada paga); alinhamento forçado de voz real; mixagem com música e loudness de publicação. O áudio antigo do Panamá **não** foi usado: o roteiro corrigido (82 km; leilão de US$ 5,3 mi) não corresponde a ele.
- Eclusa: no instante das palavras *entra / desce / iguala*: navio_em_movimento_ao_dizer_entra, nivel_subindo_apos_dizer_desce, niveis_iguais_ao_dizer_iguala, comporta_abre_logo_apos_iguala, comporta_fechada_antes_de_iguala — todos verdadeiros.
- Revelação: resposta oculta 0,3 s antes e visível 0,35 s depois de "gravidade": True.
- Legenda: 90 palavras; 0 fora do bloco ativo; 49 com a legenda oculta por regra ("redundante com a tela"). Antes da correção (§1 #20) eram 6 palavras fora do bloco.
- Fiscal do vídeo: sem bloqueio; 1 aviso D11 (cena do leilão com 12 s: a voz lenta do espeak alonga a frase).
- Desempenho: render 253.02 s para 51.08 s de vídeo; medição 28.97 s; pico de memória ≈ 0,5 GB; mp4 8.16 MB (1080×1920, 30 fps, AAC).
- Observação para revisão: com a regra de redundância, mais da metade das palavras fica sem legenda (cenas com o texto na tela). É decisão de direção, não defeito técnico.

## 7. Precisão factual

- **US$ 5,3 milhões**: lance em **leilão** por uma **vaga** de travessia (SK Gas, navio G. Spirit, 1º/09/2026); o pedágio normal é cobrado à parte; fonte Revista Oeste. Natureza "excepcional" com a palavra LEILÃO na tela (fatos F1–F5). O "R$ 27 milhões para passar" do roteiro antigo continua bloqueado.
- **82 km**: comprimento do canal pela fonte citada (Wikipedia inglês; Britannica ≈ 82 km). O "80 km" do roteiro antigo era arredondamento.
- **9.500 × 22.500 km** (NY–SF pelo canal × Cabo Horn): Wikipedia (Panama Canal); traçado do mapa marcado como ilustrativo.
- **200 milhões de L ≈ cubo de 59 m de lado** e ≈ 80 piscinas olímpicas (volume nominal 50×25×2 m) — cálculo em `unidades.py`, exibido.
- Rota de Cabral marcada "aproximada · ilustrativo"; dados de galeria marcados "ilustrativos/sintéticos".

## 8. Desempenho

| medida | V2 | V2.1 |
|---|---|---|
| captura das composições (4 instantes + medição) | 91,4 s (32) | 97,2 s (33) |
| mapas (cada) | 16–22 s | 21–26 s (rotas mais densas, MapLibre em SwiftShader) |
| demais composições | ~0,8–1,5 s | ~0,8–1,5 s |
| pico de memória (captura) | — | ≈ 360 MB |
| vídeo integrado (51 s) | — | render 253 s; total 283 s; pico ≈ 0,5 GB; 7,8 MB |
| testes V2 + V2.1 | — | 164 s (43 testes) |
| referências de regressão | — | 66 WebP, 1,7 MB |

## 9. Dependências e licenças

MapLibre GL (BSD-3), D3 (ISC), Natural Earth (domínio público; baixado por `scripts/v2_natural_earth.py`, fora do git), Playwright (Apache-2.0), ffmpeg (LGPL/GPL, ferramenta externa), Manim (MIT, opcional; apt pango/cairo), **espeak-ng (GPL-3, só ferramenta externa para o áudio de teste; nada dele vai ao repositório nem ao vídeo de produção)**. Fotos do exemplo: Library of Congress (domínio público), Wikimedia Commons (licença por arquivo, `acervo_v2.licenca`). Clipe de vídeo de teste: sintético (fractal), marcado na tela. Remotion e Chromatic avaliados na V2 e não adotados.

## 10. Como rodar

```
python scripts/v2_natural_earth.py                 # uma vez (mapas)
python -m pytest -q tests/test_v2.py tests/test_v21.py
python -m src.v2.avaliacao_selecao saida/v21/selecao.json
python -m src.v2.avaliacao_fiscal saida/v21/fiscal.json
CORINGA_AUDITORIA=<pasta> python -m src.v2.antes_depois --saida saida/v21/panama
CORINGA_AUDITORIA=<pasta> python -m src.v2.experimental      # requer espeak-ng (apt) ou --silencio
python scripts/v2_capturar.py saida/v21/depois                # capturas 8/45/75/97%
python -m src.v2.regressao [--atualizar]
```

## 11. Pendente de revisão humana

Aprovação visual de cada composição (perguntas no campo "revisão humana" da §2); `foto.historica` com a panorâmica de 91 px (V2 × V2.1); `video.documental` com vídeo real; rótulo de mar sobre o território; densidade de legenda com a regra de redundância; ritmo da voz de produção sobre a eclusa amarrada à fala.
