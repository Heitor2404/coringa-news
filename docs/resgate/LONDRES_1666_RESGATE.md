# Resgate audiovisual V3.1: Londres 1666 (produção de referência supervisionada, 16/11/2026)

**Ramo:** `piloto-v24-lagartixa`, a partir de `d40a89b`. Os commits desta etapa estão no fim do documento.
**Regras respeitadas:** sem merge, sem publicação, sem Telegram, sem serviço pago.

**Situação do vídeo: aguarda avaliação humana. Não o declaro pronto.**
O MP4 tem 64,6 s, 1080×1920, −14,5 LUFS e pico de −1,7 dBTP. O fiscal final dá 0 bloqueios, 1 revisão e 4 achados estéticos. A seção 4 lista o que ainda acho ruim.

## 1. Diagnóstico: causas confirmadas no código

| # | Problema apontado | Confirmado em | Causa |
|---|---|---|---|
| 1 | Direção subordinada ao roteiro | `pipeline.PROMPT` (antigo): "um plano por trecho, cobrindo TODOS os trechos" | A narração era definitiva antes de decidir o que podia ser mostrado. O modelo preenchia frases com a mídia que tinha: placa moderna por 6 s, retrato do rei para o padeiro, título interno, mapa parado. |
| 2 | Fiscal editorial insuficiente | `fiscal_editorial.py`: `E-MECANISMO` aceitava a composição por nome; não havia revisão por sequência | Os achados técnicos, semânticos e estéticos ficavam misturados. Movimento e mecanismo eram julgados por um quadro só. |
| 3 | Degradação silenciosa | `diretor.montar`: objeto não localizado, anotação retirada, percurso lateral inventado, palavra não achada. `pipeline`: plano descartado com o vizinho esticado, vídeo virando foto, corte por tempo igual | Tudo virava texto em `limitacoes` e o vídeo seguia aprovado. |
| 4 | Receitas "aprovadas" | `receitas.json`: 3 receitas com `aprovacao` = uma frase genérica do brief | `receitas.problemas()` aceitava qualquer texto. |
| 5 | Loudness fora da meta (3 de 8 na V3.1 e 1ª render de Londres) | `render.final_medido` | Ganho subindo e limitador por amostra (48 kHz) descendo ao mesmo tempo. O limitador não via os picos que o AAC cria entre amostras. A **última** tentativa era gravada mesmo quando era a pior (lagartixa: −14,7 → −16,8). |

Os problemas 3, 4 e 5 se resolveram com mudanças pequenas e localizadas. O problema 1 exigiu mudar o fluxo; isso foi feito sem novo módulo de planejamento, reaproveitando o contrato e o plano V2. O problema 2 exigiu um módulo novo: `revisao_multimodal.py`.

## 2. Arquivos e funções corrigidos

**`src/v3/plano_av.py` (novo)**
- `fichas()` monta, para cada acontecimento: sujeito, estado inicial, ação, transformação, consequência, representação necessária, mídia e composições disponíveis, evidência, critério visual e status.
- A base é o contrato do roteiro e o `sb` da V2; não é um planejamento paralelo.
- `validar_ajustes()` confere as mudanças de narração propostas pelo diretor: nenhum número fora da pesquisa e tamanho entre 60% e 140% do trecho.

**`src/v3/pipeline.py`**
- Prompt em 3 passos: **demonstrações** → **ajustes de narração** → **planos por demonstração** (um plano pode cobrir vários trechos).
- Os ajustes aceitos mudam as falas **antes** da gravação da voz. É o roteiro definitivo depois do plano visual.
- `aplicar_tempos()` reescrita: planos contíguos por construção, corte na palavra; sem a palavra, o corte é registrado como revisão.
- Agregação das degradações:
  - perda essencial (`bloqueio`) entra no replanejamento, que já existia com limite de 1 correção, e bloqueia se persistir;
  - `revisao` vira `revisoes_obrigatorias`.
- A revisão multimodal entra depois do MP4.

**`src/v2/diretor.py`**
- `degradar()` registra impacto, código, texto e se o elemento era essencial. Objeto não localizado em plano crítico vira bloqueio.
- Movimento sem percurso perceptível vira **plano fixo** (antes: percurso lateral inventado).
- Novos recursos genéricos, todos sincronizados na palavra:
  - `camera_chaves`: a câmera muda de enquadramento na palavra;
  - `t1_palavra`: a anotação sai na palavra;
  - `avanco`: a área é revelada em etapas, cada uma na palavra.
- Palavra composta alinhada como um token ("segunda feira") passa a ser encontrada.

**`src/render/v2/comp/doc.js`** — `avanco` em `doc.plano`: revela a imagem em cor a partir de um ponto, em etapas, com base derivada. O anel da frente só aparece enquanto a etapa avança.
- É a menor solução reutilizável para propagação, expansão ou inundação sobre um mapa ou registro **que já mostra a área final**. Não é componente exclusivo de Londres.

**`src/v3/derivados.py` (novo)** — `apagar_cor()` gera uma cópia do mapa com a cor da legenda (área queimada) em cinza, preservando a legenda. Só a área que o próprio mapa marca ganha cor.

**`src/render/v2/nucleo.js` + `estilo.css`** — legenda com placa escura sobre `doc.*`, legível sobre gravura clara.

**`src/render/render.py`** — `final_medido()`: ganho linear + limitador a 192 kHz (aproxima o pico verdadeiro), compensação medida depois do AAC e **melhor** tentativa gravada.

**`src/v3/fiscal_editorial.py`**
- Cada achado tem `dimensao`: técnica, semântica ou estética, com resumo por dimensão.
- Corte detectado durante movimento, anotação ou avanço **planejado** é explicado, não acusado. Na 1ª render de Londres, os 4 "cortes inesperados" eram movimentos pedidos.

**`src/v3/revisao_multimodal.py` (novo)**
- Por plano: tira de 4 quadros em ordem de tempo + narração do trecho + ficha do acontecimento → modelo de visão (cota grátis do Gemini).
- Devolve diagnóstico: `M-NAO-DEMONSTRA`, `M-MIDIA-DIVERGE`, `M-MAPA-DECORATIVO`, `M-TEXTO-INTERNO`, `M-ILEGIVEL`, com o quadro onde aparece e a correção sugerida.
- Sem modelo disponível, registra `M-NAO-REVISADO`: nunca aprova por omissão.

**Receitas** — `receitas.json`: as 3 aprovadas voltaram a `testado`, com histórico. `receitas.py`: `aprovado` exige `FB-xxxx` existente ou `humano:<nome>:<data>:<video>:<t>`.

**`src/v3/supervisionado.py` (novo)** — executa um storyboard escrito à mão pelo **mesmo caminho** do diretor automático (`aplicar_tempos` → `diretor.montar` → palco → render → fiscal). Tem prévia por quadros, trecho animado e render completo.

**Memória** — `docs/memoria/erros.json`: ERR-023 a ERR-026, cada um com teste de regressão.

## 3. Storyboard usado (`docs/resgate/londres_storyboard.json`)

Narração reescrita a partir dos fatos da pesquisa, **depois** de decidir o que mostrar: 14 falas, 64,6 s, Gemini TTS (voz Charon).

| Plano | Tempo | Mídia | Câmera / elementos | Por quê |
|---|---|---|---|---|
| 0 | 0–7,4 | Pintura c. 1675 | Do fogo para a cidade inteira | O acontecimento numa imagem de época; a pergunta cai sobre a escala |
| 1 | 7,4–12,3 | Mapa da City (base cinza) | Aproxima até a Pudding Lane; ponto e a 1ª brasa no nome da rua | Onde começou, na geografia real; prepara o mapa da propagação |
| 2 | 12,3–15,3 | Placa na Pudding Lane (2011) | 3 s nas linhas "Thomas Faryner, the King's Baker" | Prova escrita da fala; curta (falha 5–11 s); nenhum retrato de outra pessoa (falha 12–15 s) |
| 3 | 15,3–21,4 | Xilogravura de 1612 | Da casa em chamas até os homens com o gancho; círculo na palavra "derrubar" | A técnica mostrada por registro, não por cartão (falha 30–34 s) |
| 4 | 21,4–25,3 | Gravura vitoriana | Da fumaça para a cidade sob ela | Sem retrato de Bloodworth no acervo; mostra o fogo crescendo enquanto ninguém age |
| 5 | 25,3–29,7 | Xilogravura de 1612 (2º uso) | Dos homens puxando até a casa já em chamas | A ordem chega com o telhado queimando |
| 6 | 29,7–33,7 | Gravura de 1811 | Segue as labaredas deitadas pelo vento | A palavra "vento" tem imagem |
| 7 | 33,7–47,0 | Mapa (2º uso), **avanço** | Brasa → norte até o centro (segunda) → quase toda a City (terça) → oeste além da muralha → Smithfield. A câmera segue a frente | O mapa **demonstra** a propagação (falha 40–48 s); selo "ordem aproximada do avanço" |
| 8 | 47,0–49,3 | Golden Boy (2007) | Da inscrição de 1666 para a estátua | O marco do ponto onde o fogo parou |
| 9 | 49,3–57,6 | O Monumento (foto de 2013) | Do pedestal à urna; na palavra "metros", a coluna inteira com a seta de 61,5 m | O número preso ao objeto que ele mede; não é o encerramento (falha 58–65 s) |
| 10 | 57,6–64,6 | Pintura c. 1675 (2º uso) | Percorre a margem em chamas, da Torre ao centro do fogo | A resposta sobre a imagem mais forte, em laço com a abertura |

## 4. Auditoria do MP4 por timestamp (o que ainda está ruim)

Fiscal final: 0 bloqueios; 1 revisão (`E-PARADO` 40–43 s); 4 estéticos (planos longos de 7–13 s).
- **Revisão multimodal:** não rodou com o Gemini nesta máquina (sem chave aqui). As 11 tiras de quadros foram revisadas por mim nesta sessão; o módulo ficou testado com resposta simulada.

**Problemas por timestamp:**

| Tempo | Problema | Gravidade |
|---|---|---|
| 7,4–12,3 | A aproximação do mapa acelera muito no meio (~11 s) | Ritmo |
| 21,4–25,3 | Bloodworth é só nome na narração: a gravura mostra o incêndio, não a hesitação | Semântica fraca; limite do acervo |
| 25,3–29,7 | Mesma xilogravura 10 s depois do plano 3 (enquadramento oposto). Funciona como continuidade, mas repete | — |
| 29,7–33,7 | A gravura de 1811 mostra margem de papel e a legenda impressa embaixo | Parece página escaneada |
| 33,7–47,0 | A propagação é um esquema circular a partir da Pudding Lane: honesto (selo diz "aproximada"), mas não é a frente histórica dia a dia. 40–43 s: mapa parado durante "dentro da antiga muralha romana". Pye Corner não está marcado no mapa (só "perto de Smithfield", e o marcador aparece em < 1 s). Os rótulos do próprio mapa são pequenos. O selo no alto cruza nomes do mapa | — |
| 47,0–49,3 | Foto do Golden Boy de baixa resolução (480×640): fica macia | — |
| 25–30 | A legenda quebrou "em grande / escala" entre dois blocos (quebra automática das legendas) | — |
| Vídeo todo | Sem efeitos sonoros. A música ("hidden-truth", CC0) foi escolhida por mim e não foi avaliada esteticamente | — |
| Vídeo todo | 8 de 11 planos são aproximação ou revelação. Há variedade de intenção, mas o vocabulário de câmera é pequeno | — |

## 5. Testes executados

- `tests/test_v3_resgate.py`: 18 testes, todos passando. Cobrem:
  - críticos preservados e ausência de degradação silenciosa;
  - sincronia de corte, anotação, câmera e avanço;
  - objeto não localizado e vídeo indisponível;
  - receitas, plano audiovisual e revisão multimodal;
  - geometria e textos, áudio de crista alta e melhor tentativa.
- `tests/test_v3_*.py`: 65 testes, todos passando.
  - 2 asserções antigas foram atualizadas porque o comportamento mudou de propósito: não há mais receita aprovada.
- Suíte inteira: 815 passaram, 12 falharam, 13 pularam. As 12 falhas são as mesmas de antes desta etapa e vêm do ambiente: Natural Earth ausente nesta máquina, prompts do cofre privado, caso polvo e matriz v25. A única falha nova (`.env.example` sem `REVISAO_MULTIMODAL`) foi corrigida.

## 6. Consumo e custo

| Recurso | Uso | Cobrança |
|---|---|---|
| Gemini TTS (narração) | 1 gravação de 14 falas | Cota grátis: US$ 0 |
| GitHub Actions | 2 execuções (material + narração ≈ 4 min; mídia ≈ 3 min) | Cota grátis: US$ 0 |
| Wikimedia Commons | 5 arquivos (licenças CC BY-SA 2.0/3.0/4.0, registradas) | US$ 0 |
| Claude (direção supervisionada) | Esta sessão de Claude Code. **Nenhuma** chamada de modelo dentro do pipeline: storyboard e regiões feitos à mão | Crédito da assinatura, não cobrança |
| Visão (regiões) | 0 chamadas: caixas marcadas pelo diretor | — |
| Renders locais | 4 prévias por quadros, 1 trecho animado de 13 s, 3 MP4 completos (≈ 6 min cada, em 2 núcleos) | US$ 0 |

Dinheiro gasto: **US$ 0**.

## 7. O que o diretor automático pode reaproveitar

1. **Formato do storyboard.** O deste episódio é o mesmo que o modelo produz, mais `avanco`, `camera_chaves` e `t1_palavra`. Depois da aprovação humana, vira **exemplo aprovado** concreto para receitas (`R-DESLOCAMENTO` com avanço; `R-APROXIMA-OBJETO` com prova escrita), com `aprovacao` = `humano:...`.
2. **Ordem demonstrações → ajustes de narração → planos.** Já está no prompt e no fluxo real (`MOTOR_VISUAL=v3`).
3. **Degradação com impacto, replanejamento e bloqueio.** Vale igual para o automático: nada mais some em silêncio.
4. **`avanco` + `apagar_cor`.** Qualquer propagação ou território sobre um mapa que já marca a área final.
5. **Revisão multimodal por tira de quadros.** Fica pronta para a cota grátis do Gemini no fluxo automático.
6. **Áudio.** A masterização corrigida vale para toda render.

**Falta para automatizar este padrão:**
- regiões vindas da visão no lugar das caixas manuais;
- o modelo escolher `avanco` e `camera_chaves` (o contrato já os descreve);
- aprovação humana deste episódio para promover as receitas.

## Commits

Ver `git log d40a89b..HEAD` no ramo `piloto-v24-lagartixa`.
