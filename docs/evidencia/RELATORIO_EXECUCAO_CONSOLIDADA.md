# Evidência V1 — execução consolidada (coleta real, Gemini real, correções gerais)

Ramo: `evidencia-v1-experimental`.

- `EVIDENCIA_V1` continua desligada por padrão; só existe o modo sombra.
- A produção, os prompts de produção, as composições, a estética, os mapas, a centralização, o áudio e o NTC ficaram intactos.
- Não foi gerado vídeo, não foi feita chamada ao Claude e não houve merge.

## 1. Executado

- **Coleta única no CI** (execução 43631002615): o resultado está cifrado no ramo `evidencia-coleta-resultado`. A cópia sem as imagens está em `tests/evidencia/coleta_real/`, com os registros brutos e as respostas originais do Gemini.
- **Metadados reais coletados para 19 das 45 imagens pedidas.**
  - 20 imagens falharam por **429 do Commons** (limite de pedidos). Não tentei de novo, conforme a ordem.
  - 4 imagens eram hipotéticas ou não tinham fonte acessível.
  - 2 imagens não foram encontradas pela busca.
- **Gemini cego: 12 chamadas de 18.**
  - Os 6 catálogos responderam.
  - Dos 6 casamentos, só 1 respondeu (Katrina). Os outros 5 deram 503/504 (sobrecarga do Google), sem nova tentativa.
  - Geologia e Alexandria ficaram sem imagem, então não houve chamada para elas.

## 2. Gemini real contra o gabarito

- **Catálogo cego, 20 imagens:**
  - A natureza bateu com o rótulo em 20 de 20: foto, satélite, diagrama, pintura.
  - Detectou a escrita árabe como conteúdo e nenhuma imagem como genérica.
  - O conteúdo descrito confere com o gabarito em todas.
  - Detalhe: chamou a foto do NASA nhq2019 de "jovem mexendo em cabos". O gabarito supunha uma celebração. Nos dois casos não é o pouso, e o nível esperado continua certo.
- **Casamento (só Katrina):** fema_15008 → `estado_final`, confiança alta. Bate com o gabarito.
- **Pipeline real completo** (registro real + Gemini real) no único caso possível, kt-01: **PROVA**, correto.
- **Falsas provas com dados reais: 0.** Nos casos sem casamento, a regra caiu para RELACIONADA, CONTEXTO ou INCOMPATIVEL, nunca para PROVA.
- **Não medido:** acerto do casamento em escala. Com 1 resposta, não há amostra.

## 3. Falsas provas e falsas rejeições

- **Falsas provas:** 0 em todos os cenários com visão correta ou dados reais (desenvolvimento, reservado e generalização nova).
- **Falsas rejeições com o registro real** (PROVA esperada que não saiu PROVA): 11 casos.
  - 9 deles não tiveram registro coletado (o 429).
  - **ap-04:** a NASA devolveu a decolagem com o título "APOLLO XI" e **sem palavras-chave**, então não há vínculo de registro. Resultado: RELACIONADA ou CONTEXTO.
  - **tn-01:** a busca achou outro arquivo, um HABS de 7/11/1940, cuja data de registro é "Documentation compiled after 1968". O veto de fase rebaixou. A data verdadeira está no título, não no campo de data.
- **Metadados reais × cenário:**
  - **Contradição detectada só pelo dado real (bw-05):** a coletiva de Schabowski está na categoria "Günter Schabowski's press conference of 9 November 1989", não em "Fall of the Berlin Wall". Com a correção 3, vira INCOMPATIVEL mesmo se a visão mentir.
  - **Homônimo (a10):** a foto de 2011 está em "Ever Given (ship, 1986)", outro navio com o mesmo nome. Hoje é pega só pela data.
  - **O vínculo do acontecimento funciona por nome contido na categoria:** "Satellite pictures of 2021 Suez Canal obstruction" e "Images from FEMA, Hurricane Katrina in Louisiana".
  - **Data de envio:** o ASTER traz "Taken on 4 April 2021" e é classificado certo. Tacoma não tem campo de data nenhum.

## 4. Correções gerais (commit `75db52d` + ajuste final)

Nenhuma lista por assunto: as correções usam só gênero de imagem, gramática e estrutura do registro.

1. **Data de envio:** "Uploaddate…", "Uploaded on…" e "upload date" nunca viram data de captura.
2. **Atemporal:** um acontecimento sem intervalo aceita categoria curada da entidade + visão como vínculo forte.
3. **Outro assunto:** se o registro tem categorias curadas e nenhuma liga ao acontecimento ou à entidade, a imagem é INCOMPATIVEL, por mais parecida que seja (outra espécie, outro furacão, outro dirigível).
4. **Sem vínculo de registro, nunca CONTEXTO:** passa a INCOMPATIVEL.
5. **Ação, estado final e consequência:**
   - "consequência" nunca satisfaz o acontecimento;
   - monumento e documento têm teto CONTEXTO;
   - emblema, insígnia e logotipo valem como ilustração;
   - **ajuste da fase (veio do dado real):** sem leitura visual do estado, vale a fase mais permissiva que o tipo aceita. Antes, a foto do navio preso de 25/03 era vetada como "ação fora do dia".
6. **Confiança não é verdade:** um casamento com confiança alta não confirma se o catálogo (outra chamada) disser genérica, natureza que não prova, ou "nada acontecendo" quando o casamento diz "ação".
7. **Rastreio:** a decisão leva `evidencia`: imagem, fonte, título, página, licença, data e sua origem, famílias e motivos.

Também: o lugar do contrato (`onde`) entra como referência de entidade, só por nome.

## 5. Testes e CI

- `tests/test_evidencia.py`: 56 testes; 15 são de regressão das correções, incluindo ap-08, bw-05 e tn-04.
- Suíte completa local: **177 aprovados** (os 121 de antes + 56 da evidência).
- **Avaliação nova** (`generalizacao_v2.json`):
  - escrita **antes** das correções e não usada para ajustá-las;
  - domínios novos (Hindenburg, Chernobyl, germinação), 17 casos;
  - resultado: 17/17, 0 falsa prova, 3/3 provas, 3/3 decisões. São cenários de regra, não arquivos reais.
- **Reservado original (53):** preservado e não alterado. Depois das correções: 48/53, 0 falsa prova, 10/10 provas.
  - As 5 diferenças são CONTEXTO → INCOMPATIVEL em imagens sem vínculo de registro (correção 4: gravura de outra espécie, produção de 1943, Serapeu, selo).
  - O gabarito antigo previa CONTEXTO nesses casos.
- **Adversários:**
  - **Com só o casamento errando**, nenhuma falsa prova em nenhum conjunto: ap-08, bw-05 e tn-04 estão cobertos.
  - **Com catálogo e casamento errando juntos** sobram bw-05 e tn-04 no cenário montado, e mt-05. bw-05 com o registro real fica INCOMPATIVEL.
  - **Ressalva sobre tn-04:** no rótulo, o catálogo diz "nada acontecendo" para a ponte torcendo. Um Gemini real provavelmente diria "ação em curso", e aí só o casamento errado já passaria.
- **CI:** uma execução final, com a galeria pulada neste ramo, porque renderização e composições não mudaram.

## 6. O que ainda impede a integração

1. **Casamento cego quase sem medição:** 1 resposta de 6. Sem isso não se sabe o acerto real da visão relativa ao acontecimento, e PROVA depende dela.
2. **Coleta incompleta:** o 429 do Commons pede pausa maior entre pedidos ou lotes de 40 títulos por chamada (uma mudança no script, não na regra).
3. **Referências do acontecimento** (categoria P373 e apelidos da Wikidata) ainda não são coletadas. Sem elas aparecem casos como "APOLLO XI" e "Tacoma Narrows Bridge collapsing".
4. **Data verdadeira fora do campo de data** (HABS) e homônimos (Ever Given 1986) só são tratados indiretamente.
5. **Dependência estrutural:** se catálogo e casamento errarem juntos e o registro for do próprio acontecimento, há falsa prova. A mitigação é conferência humana por amostragem ou uma segunda leitura, que seria uma chamada extra.

## 7. Recomendação

**Manter experimental.** A regra está pronta para a próxima fase de medição: 0 falsas provas em todos os conjuntos e com dados reais, correções gerais, catálogo cego confiável. Mas ainda não está pronta para decidir: falta medir o casamento cego em escala, e ele é a metade visual de toda PROVA.

O próximo passo é **uma coleta repetida só para o que falhou por 429/503/504**, com intervalos maiores e lotes. A coleta de imagens e metadados não usa IA. Do Gemini faltam 5 casamentos, dentro do limite que sobrou (6 de 18). Precisa da sua autorização, porque seria uma segunda coleta.
