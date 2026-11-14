# Evidência V1 — integração experimental Gemini + NVIDIA (só modo sombra)

Ramo `evidencia-v1-experimental`. Os provedores de visão só são chamados com **`EVIDENCIA_V1=sombra` e
`EVIDENCIA_V1_VISAO=1`**, e as duas flags vêm desligadas. Mesmo ligadas, o resultado só é gravado em
`-evidencia-sombra.json` e não troca nenhuma decisão.

## Implementado

| Item | Onde |
|---|---|
| Adaptador comum (Gemini e NVIDIA via OpenRouter): uma chamada por provedor, timeout de 90 s, teto de 4 chamadas por vídeo, sem nova tentativa, JSON tolerante | `src/v2/visao_provedores.py` (`ler`, `Orcamento`, `extrair`) |
| Fallback Gemini → NVIDIA só por 429/5xx/timeout/falta de chave. Outro erro não troca de provedor. Se os dois falham, a leitura é **incerta** | `ler` |
| Dupla leitura só em pares críticos que podem virar prova, ou ambíguos (confiança não alta; "ação" numa imagem parada). Usa o **outro** provedor e só os pares pedidos | `precisa_dupla`, `ler_roteiro` |
| Concordância continua **uma** família (VISÃO). Discordância relevante vira leitura incerta + `discordancia` → revisão humana | `combinar`; `evidencia._visao_ok` |
| Ação × estado resultante × consequência. **Regra:** "ação" sem movimento visível (o casamento diz que está parado, ou o catálogo diz que nada acontece) passa a ser **estado final**, e isso só confirma com **segunda leitura concordante**; sem ela, vai para revisão. **Prompt:** definições explícitas e o campo `movimento_visivel` | `evidencia._semantica`; ramo `evidencia-v1` do cofre (prompt experimental) |
| Vetos de identidade, data, natureza e proveniência intactos. A foto do navio preso não representa a liberação (veto de fase) | testes |
| Registro de provedor, modelo, latência, erro, motivo do fallback, imagens retidas, discordâncias e dupla leitura | `Orcamento.registro`, `ler_roteiro` → `sombra['visao']`; `sinais.visao` em cada avaliação |
| Privacidade: o endpoint grátis da NVIDIA registra o uso e pede para não enviar informação confidencial | `permitido_nvidia` |
| Gancho em modo sombra | `main.py` (dentro do `try` existente) |

**Regra de privacidade** (aplicada em `permitido_nvidia`):

- O catálogo cego roda **só** no Gemini, porque sem catálogo não há como checar privacidade.
- A NVIDIA só recebe imagens cujo catálogo não indica pessoa, rosto, multidão, documento, tela ou texto como conteúdo.
- Imagem sem catálogo não vai para a NVIDIA.
- O prompt é cego: não leva legenda, nome do arquivo, fonte nem autor.

## Testes offline (respostas reais armazenadas, nenhuma chamada)

`tests/test_visao_provedores.py`: 19 testes.

- Contrato único para as respostas reais do Gemini 3.5-flash-lite e da NVIDIA Nemotron.
- **nav-01 (navio preso, i6):** com as duas leituras reais concordantes, **PROVA**; com uma leitura só, revisão.
  Antes da integração era rejeição indevida.
- **Liberação (i14) com a mesma foto:** nunca prova.
- **nav-07 (homônimo de 2011):** Gemini disse "entidade" e NVIDIA disse "ação" → discordância → CONTEXTO, nunca prova.
- **nav-08:** CONTEXTO.
- Katrina com o Gemini real continua PROVA. O colapso de Tacoma, em que o catálogo real diz "ação em curso", não é reinterpretado.
- Fallback, os dois falhando, erro que não é de disponibilidade, teto, privacidade (5 casos) e `ler_roteiro` retendo um retrato.

**Regressão** (gabaritos intocados; cenário "só o casamento erra" = IA mentindo só no casamento, com confiança alta):

| Conjunto | Acerto | Falsa prova | Provas reconhecidas | Falsa prova com só o casamento errando |
|---|---|---|---|---|
| Desenvolvimento | 24/24 | 0 | 7/7 | 0 |
| Reservado (histórico) | 48/53 (igual a antes) | 0 | 10/10 | 0 |
| Generalização v2 | 17/17 | 0 | 3/3 | 0 |
| Validação com dados reais | — | 0 | — | — |

Na primeira versão, a reinterpretação de "ação" em imagem parada abria 2–4 falsas provas no cenário "só o casamento
erra". Exigir segunda leitura concordante fechou essas falsas provas antes do commit.

## Limitações

- O casamento real foi medido em **uma** cena com 4 imagens por provedor (mais o Katrina no Gemini 3.8). As métricas acima testam a regra, não a precisão dos modelos.
- Se catálogo e casamento mentirem juntos e o registro for do próprio acontecimento, ainda há falsa prova no cenário montado (bw-05, tn-04, mt-05, g-gm-03). A dupla leitura reduz esse risco, mas não o elimina: as duas leituras são da mesma família.
- O prompt experimental novo (`movimento_visivel`) não foi testado com chamada real. Os testes usam as respostas antigas, que não têm o campo, e o catálogo cobre essa falta.
- A regra de privacidade usa o catálogo do próprio Gemini: se o catálogo errar, uma imagem com pessoa pode sair para o endpoint grátis. Os termos da NVIDIA e do OpenRouter precisam ser conferidos pelo responsável antes de qualquer uso fora do teste.
- Latência medida: NVIDIA 20,6 s por casamento; Gemini lite 3,5 s.
- O endpoint grátis tem limite de uso e pode ficar mais lento ou indisponível.

## Critérios para uma futura ativação (ainda em sombra)

1. Rodar o casamento real (com `movimento_visivel`) nos domínios reservados que têm imagem, dentro do teto, e conferir: falsa prova = 0, discordância < 20%, e a NVIDIA nunca recebendo imagem retida.
2. Coleta das imagens que faltam (429) e das referências do acontecimento via Wikidata (categoria P373 e apelidos).
3. Uma rodada de piloto com `EVIDENCIA_V1=sombra` e `EVIDENCIA_V1_VISAO=1`, comparando com o preparo atual. Nenhuma decisão é trocada.
4. Só depois avaliar o modo de aplicação, com revisão humana para toda discordância.
