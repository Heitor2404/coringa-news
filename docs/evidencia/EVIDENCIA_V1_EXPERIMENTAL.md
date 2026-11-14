# Modelo de evidência — fase experimental (V1)

**Ramo:** `evidencia-v1-experimental` (a partir de `visual-v2-3-porteiro-revisao`). Não fiz merge.

**Flag:** `EVIDENCIA_V1`, **desligada por padrão**. Valores:

- vazia: nada muda.
- `sombra`: calcula e grava `<vídeo>-evidencia-sombra.json` ao lado do preparo, sem trocar decisão nenhuma e sem IA.
- outro valor: ignorado. O modo "aplicar" não existe nesta fase.

**Prompts:** versões separadas no cofre, ramo `evidencia-v1` do `coringa-cofre`:

- `PROMPT_CATALOGO_EVIDENCIA.txt`
- `PROMPT_CASAR_EVIDENCIA.txt`

Os prompts de produção não foram tocados e o motor atual não carrega os novos.

## 1. O que foi feito

| Peça | Arquivo |
|---|---|
| Esquema do acontecimento e da imagem, sinais, famílias, decisão, verificação factual, preparo paralelo | `src/v2/evidencia.py` |
| Avaliação offline: cenários de visão e de registro, métricas, reprodução dos pilotos | `src/v2/avaliacao_evidencia.py` |
| Testes (41) | `tests/test_evidencia.py` |
| Casos de desenvolvimento: Ever Given + Santa Helena, 24 casos | `tests/evidencia/desenvolvimento.json` |
| Casos reservados: 8 domínios, 53 casos, 12 decisões por acontecimento | `tests/evidencia/reservado.json` |
| Material do piloto Santa Helena para reprodução | `tests/piloto_santa_helena/` |
| Gancho em modo sombra (só com a flag; dentro de `try`) | `main.py` |
| CI | `.github/workflows/testes-v2.yml` (ramo novo, `test_evidencia.py`) |

O que **não** foi alterado:

- as 33 composições, mapas, centralização, estética, renderização e áudio;
- o porteiro, o fiscal e o preparo V2.3;
- o NTC;
- os prompts em produção.

## 2. As sete condições

### 2.1 Representação × verificação factual

São duas funções separadas.

- **`avaliar()`** responde se a imagem mostra o elemento na ação ou no estado que o tipo exige. Níveis: PROVA, RELACIONADA, CONTEXTO, INCOMPATIVEL.
- **`verificar_afirmacoes()`** confere números, citações, superlativos e causas contra as linhas da pesquisa com fonte.

A imagem nunca entra na verificação factual. Toda avaliação registra em `nao_comprova` as afirmações que a imagem não comprova.

No Santa Helena, a série de Rosenquist vira PROVA da encosta em colapso, mas "magnitude 5,1" continua precisando da linha da pesquisa.

Se uma afirmação de um acontecimento crítico não tem fonte, a decisão ganha `revisao_factual`, mesmo com a foto aceita. Superlativo e causa ficam marcados `nao_verificada_automaticamente`: o código não julga sentido.

### 2.2 Sinais correlacionados

A independência é declarada, não presumida. Há duas famílias:

- **REGISTRO:** categoria, palavra-chave, data, descrição e título do mesmo arquivo contam como **uma** evidência.
- **VISÃO:** catálogo e casamento usam o mesmo modelo, o Gemini. Também contam como **uma** evidência.

**PROVA exige as duas famílias e nenhum veto.** Concordância dentro da mesma família nunca soma. Os testes travam isso:

- registro perfeito sem visão → RELACIONADA;
- visão perfeita sem registro → RELACIONADA.

**Achado:** os prompts atuais **mostram a legenda ao Gemini**.

- O catálogo recebe "o nome do arquivo e a descrição oficial".
- O casamento recebe o texto do catálogo.

A visão de hoje não é independente do registro. O modelo trata essa leitura como "legado" e nunca a conta como confirmação. Por isso os prompts novos são **cegos**: não recebem legenda, nome, data nem fonte.

### 2.3 Testes realmente inéditos

A ordem foi:

1. Regra congelada no commit `b80ba08` (sha256 de `evidencia.py` = `5d6572fc…600ee`).
2. Casos reservados e gabarito criados depois, no commit `f0ee41d`.
3. Avaliação feita uma única vez.

A regra não mudou depois disso. Os erros encontrados estão na seção 4 e **não foram corrigidos**: corrigir exige um conjunto reservado novo.

Limites da reserva:

- **Mesmo autor.** Eu escrevi a regra e os casos. O gabarito precisa da sua auditoria (`GABARITO_RESERVADO.md`). O ideal é você acrescentar casos que eu não vi.
- **25 dos 53 casos usam imagem "hipotética".** É um tipo de arquivo que existe, mas cujo arquivo não conferi. Quase todas as PROVAS esperadas (9 de 10) usam imagens reais e verificáveis.
- **Visão rotulada.** A leitura visual dos casos foi rotulada por mim, a partir do que a fonte verificável diz que a imagem mostra. Os cenários "visão adversária", "legado" e "ausente" medem o que acontece quando a IA erra ou falta.
- **O que não foi medido:** a precisão real do Gemini cego. Isso depende de chamadas de visão (seção 6).

Zero falsas aprovações aqui é critério de aceitação do teste, não garantia para a produção.

### 2.4 Produção preservada

- Ramo isolado.
- Flag desligada por padrão; o teste trava que `aplicar` não liga nada.
- O preparo paralelo não altera o roteiro (há teste para isso).
- Prompts separados num ramo do cofre.
- Nenhuma credencial foi usada ou exposta: o cofre foi clonado com o acesso da sessão.

### 2.5 Metadados disponíveis

Ver `METADADOS_DISPONIVEIS.md`. Resumo:

- **Já chegam e são descartados:** categorias do Commons, palavras-chave da NASA e assuntos da LoC.
- **Precisam de consulta extra:** a categoria do acontecimento e a da entidade (pesquisa → Wikidata → P373).
- **Não existem:** datas no Openverse, iNaturalist e Pixabay.

O código separa captura, criação declarada, publicação (limite superior) e envio (nunca usado). Data desconhecida não confirma.

### 2.6 Rigor sem bloqueio desnecessário

- Uma imagem real com as duas famílias vira PROVA.
- Um sinal só, ou vínculo fraco, vira RELACIONADA: revisão humana se o acontecimento é crítico, uso normal se é de apoio.
- Contexto nunca sobe por semelhança. Os vetos (fase, gênero, documento, monumento, escrita) só rebaixam.

### 2.7 Nada reconstruído

- O preparo paralelo **reaproveita** o preparo V2.3 para tipos, dados e composições.
- Só a decisão de imagem é nova. A ordem de representação é a mesma: composição → prova → editorial → revisão → bloqueio.
- A tabela editorial ganhou `citacao`, só quando a citação tem fonte na pesquisa.

## 3. Resultados

### 3.1 Casos reservados (avaliação final, uma vez) — `AVALIACAO_RESERVADA.md`

| Métrica | Resultado | Critério |
|---|---|---|
| Falsa prova (visão correta) | **0 / 53** | 0 |
| Prova reconhecida | **9 / 10** (90%) | ≥ 80% (amostra pequena) |
| Nível exato | 45 / 53 | — |
| Decisão por acontecimento | 10 / 12 | — |
| Negativos: nunca `foto_prova` | 6 / 6 decisões | 100% |
| Sem visão independente (legado ou ausente): nunca PROVA | ok | invariante |
| Tirar categoria ou data não cria PROVA | ok | invariante |
| Falsa prova com IA mentindo com confiança alta | 3 / 53 (ap-08, bw-05, tn-04) | medida, não critério |

Domínios: espaço, história política, engenharia, biologia (atemporal), clima e três negativos (medicina, arte perdida, esporte).

### 3.2 Desenvolvimento — `AVALIACAO_DESENVOLVIMENTO.md`

- 24 / 24 casos corretos.
- 0 falsa prova.
- 1 falsa prova com IA adversária (geo-03).

Esse conjunto **foi usado para ajustar a regra**. Os três ajustes:

- estado final aceito em tipos de ação;
- placa ou cartaz como documento;
- documento com teto CONTEXTO.

### 3.3 Pilotos: antigo × novo — `PILOTOS_ANTIGO_X_NOVO.md`

| Piloto | Com o que o sistema guarda hoje ("legado") | Com registro completo + visão cega ("rotulado") |
|---|---|---|
| Santa Helena | 3 bloqueios (os mesmos) | **0 bloqueios.** e6 e e7 viram `foto_prova a25` (eram bloqueio falso). e9 vai para revisão. e2 e e5 viram prova. |
| Ever Given | e1 e e4 vão para revisão em vez de `foto_direta`; e3 e e5 bloqueiam | e1 (ISS) e e4 viram `foto_prova`. e9 (navio liberado) **nunca** vira prova. |

**Conclusão importante:**

- **Sem a visão cega e as categorias**, o modelo novo não deve substituir o atual. Ele nunca dá PROVA, então empurra para revisão ou bloqueio decisões que hoje passam.
- **Pior ainda:** no Ever Given ele manda para revisão o e9 (liberação), que o preparo atual bloqueava corretamente. O motivo é que o casamento atual chamou a foto do navio PRESO de "fato".
- **O ganho depende de duas mudanças:** a coleta de metadados e os prompts cegos.

## 4. Erros encontrados nos casos reservados (não corrigidos)

| # | Caso | O que aconteceu | Correção proposta |
|---|---|---|---|
| 1 | tn-03 | O texto real "Uploaddate 2010-01-17" foi lido como data de criação. A foto do colapso caiu para CONTEXTO, e a decisão "tn_queda" virou bloqueio em vez de revisão. | Aceitar "upload" colado em outra palavra (`upload\w*`). |
| 2 | mt-02 | Acontecimento atemporal (metamorfose): categoria curada da espécie + visão deveria ser PROVA, como diz a proposta. A regra pede categoria do acontecimento ou data. | Para acontecimento sem intervalo, categoria curada da entidade conta como vínculo forte. |
| 3 | mt-07, kt-08, es-02 | O registro diz que a imagem é de OUTRA espécie, outro furacão ou outra competição, e o código não percebe a contradição. mt-07 vai para revisão humana; kt-08 e es-02 escaparam só pela data. | Registro com categorias curadas e nenhuma ligada ao acontecimento ou à entidade = contradiz (INCOMPATIVEL). |
| 4 | tn-08, al-03 | Outra ponte e outra biblioteca, sem vínculo, ficam CONTEXTO em vez de INCOMPATIVEL. Em acontecimento de apoio, poderiam aparecer na tela. | CONTEXTO exige algum vínculo de registro. Sem vínculo, é INCOMPATIVEL. |
| 5 | pn-02 | Demonstração moderna (2016) ficou CONTEXTO, não RELACIONADA: o veto de fase agiu. | Gabarito questionável. O resultado é mais rigoroso, não menos seguro. Peço sua decisão. |
| 6 | ap-08, bw-05, tn-04 | Dependência da visão: com registro do acontecimento na fase certa, uma IA que mente com confiança alta produz PROVA (emblema, coletiva, ponte ainda torcendo). | Limite estrutural de duas famílias. Mitigações: gênero pelo registro (pegaria o emblema com "Mission patches"); conferência por amostragem humana; segunda leitura visual só para críticos (chamada extra: **só com autorização**). |

Aplicar 1–4 exige um **conjunto reservado novo** para medir de novo.

## 5. Determinístico × IA

| Parte | Como |
|---|---|
| Datas, fase, origem da data, vínculos de registro, gênero pelo registro, vetos, decisão, verificação de números e citações | determinístico (este código) |
| Natureza visual, texto visível e escrita, se é genérica, qual campo do acontecimento a imagem mostra | IA de visão (prompts cegos novos) |
| Sentido de superlativo e causa | não automatizado: fica marcado para revisão textual |

## 6. O que precisa da sua autorização para continuar

1. **Medir a visão de verdade.** Rodar os prompts cegos (Gemini, plano grátis, nenhuma chamada ao Claude):
   - **Ever Given:** 10 imagens locais → 1 catálogo + 1 casamento.
   - **Casos reservados:** cerca de 28 imagens reais → por domínio, 1 catálogo + 1 casamento (cerca de 16 chamadas).
   - **Comparação:** a resposta da IA com os rótulos.
   - **Pré-requisito:** baixar as imagens (grátis, sem IA). Esta sessão não alcança as fontes, então o download precisaria rodar no CI.
2. **Coleta de metadados reais** (grátis, sem IA, no CI): categorias, datas com origem e categorias do acontecimento via Wikidata, para os casos. Ela substitui os campos "cenário" e as imagens "hipotéticas" por dados conferidos.
3. **Aplicar as correções 1–4** e criar um **conjunto reservado novo**, se possível com casos escritos por você.
4. Só depois: piloto com `EVIDENCIA_V1=sombra`.

Nada disso foi executado.
