# Coringa Explica — Sistema audiovisual V2 (ramo `visual-v2`)

Data: 13/11/2026. Escopo: só o motor documental Coringa Explica; o NTC não foi lido nem alterado.
Nada foi gerado por IA paga. Toda a validação usou dados locais: o diagnóstico do Panamá (execução 43435732255),
recuperado pelo workflow `extrair-auditoria` com chave GPG descartável, e exemplos sintéticos marcados como tal.

> Teste automático não é aprovação visual. Quem aprova é o Heitor, olhando a galeria e as comparações antes/depois.

## 1. Decisão de arquitetura

O motor atual (template HTML + Playwright `seek(t)` + ffmpeg) **continua**. O problema não era a tecnologia de
render, e sim o que se desenhava: um template de 728 linhas com poucos tipos de cena e foto + texto como saída padrão.

A V2 é uma **camada nova ao lado** da antiga:

```
roteiro/dados (motor atual)
   └─ src/v2/montagem.py ──── direção por ACONTECIMENTO (src/v2/capacidades.py)
        │                      precisão factual (src/v2/fatos.py)
        │                      acervo: relevância, duplicatas, recorte, enquadramento (src/v2/acervo_v2.py)
        ▼
   cenas V2 {comp, start, end, params, fundo}
        ▼
   src/render/v2/palco.html + nucleo.js + comp/*.js   (32 composições registradas com metadados)
        │  mesma interface do template: window.DATA, seek(t), READY, inspecionar(t)
        ▼
   src/render/render.py (meta.motor == 'v2') → mesmos quadros, efeitos, mixagem e masterização
        ▼
   src/v2/fiscal_v2.py — bloqueios determinísticos + perguntas subjetivas (sem nota estética automática)
```

- **O pipeline anterior é recuperável.** Sem `meta.motor = 'v2'`, nada muda; `template.html` não foi tocado. A única
  mudança em `render.py` é o desvio para o palco V2 e o parâmetro opcional `nav_args` em `_trecho`/`_montar`.
- **Uma composição é um registro** (`V2.registrar(META, construtor)`). A galeria, os testes, a regressão visual e o
  fiscal leem o mesmo catálogo (`V2.catalogo()`), então não há composição "invisível".

## 2. Inventário das integrações

| Recurso | Uso na V2 | Versão | Licença | Situação |
|---|---|---|---|---|
| HyperFrames (catálogo) | já integrado no main (count-up, chart-story etc.). A V2 **não copia** esses componentes: os 32 novos são próprios, com a tipografia e os tratamentos do Coringa | commit d208281 | Apache-2.0 | mantido no motor antigo |
| GSAP | usado pelos componentes HyperFrames do motor antigo; a V2 não depende dele | 3.14.2 | licença GSAP (gratuita) | mantido |
| **MapLibre GL JS** | mapas V2 (localização, rota, território), câmera determinística por quadro | 5.24.1 | BSD-3-Clause | **novo** |
| **Natural Earth** | países 1:10m e 1:50m (com nome em português), lagos, rios, cidades, mares, regiões | v5.1.2 | domínio público | **novo** (baixado por `scripts/v2_natural_earth.py`, fora do Git) |
| **D3** | escalas, eixos, curvas e áreas (gráficos), centroides e áreas (rótulos de mapa) | 7.9.2 | ISC | **novo** (o d3-geo/d3-array antigos continuam) |
| Source Serif 4 | serifa para arquivo, citação, contexto | @fontsource 5 | OFL-1.1 | **novo** |
| Montserrat, JetBrains Mono | títulos e dados (pesos 500/600 adicionados ao uso) | @fontsource 5 | OFL-1.1 | mantido |
| **Manim Community** | módulo opcional `src/v2/manim_cenas.py` (lançamento oblíquo com vetores) → composição `animacao.quadros` | 0.22.1 | MIT | **novo, opcional** (precisa de Cairo/Pango no sistema) |
| Remotion | protótipo de avaliação em `prototipos/remotion` (dependências só lá dentro) | 4.0.543 | Remotion License | **avaliado, não adotado** |
| Chromatic | avaliado | — | SaaS | **não adotado** |
| Playwright | render, fiscal geométrico, regressão visual, galeria | já instalado | Apache-2.0 | ampliado |
| Wikimedia Commons | o acervo atual (`src/acervo.py`) continua buscando; a V2 decide sobre o que ele trouxe | — | por arquivo | ampliado (`acervo_v2`) |

Nenhuma dependência redundante entrou na raiz: `remotion`/`react` ficam só no `package.json` do protótipo.

## 3. Biblioteca de composições (32)

Cada uma declara: id, nome, tratamento, objetivo, funções narrativas, parâmetros, fundo, regras de layout, paleta,
animação, duração (mín/ideal/máx), limites de texto, legenda, área segura, legibilidade, critérios de rejeição,
transição e um exemplo renderizável. Tudo isso aparece na galeria.

| # pedido | id | tratamento |
|---|---|---|
| 1 | `abertura.pergunta` | documental |
| 2 | `abertura.revelacao` | documental |
| 3 | `banner.discreto` | documental |
| 4 | `banner.importante` | alerta |
| 5 | `lower_third` | documental |
| 6 | `numero.animado` | dado (papel) |
| 7 | `comparacao.grandezas` | dado (papel) |
| 8 | `comparacao.antes_depois` | documental |
| 9 | `mapa.localizacao` | mapa (MapLibre) |
| 10 | `mapa.rota` | mapa (MapLibre) |
| 11 | `mapa.territorio` | mapa (MapLibre) |
| 12 | `linha_tempo.historica` | arquivo |
| 13 | `foto.historica` | arquivo |
| 14 | `foto.sequencia` | documental |
| 15 | `grafico.barras` (D3) | dado |
| 16 | `grafico.temporal` (D3) | dado |
| 17 | `diagrama.explicativo` | ciência |
| 18 | `mecanismo.eclusa` (+ `mecanismo.nivel`) | ciência |
| 19 | `processo.etapas` | ciência |
| 20 | `revelacao.surpresa` | alerta |
| 21 | `fonte.evidencia` | arquivo |
| 22 | `encerramento.editorial` | editorial |
| extras | `titulo.capitulo`, `destaque.palavras`, `citacao`, `proporcao`, `forcas.vetores`, `astronomia.orbita`, `evento.impacto`, `foto.documental`, `animacao.quadros` (Manim) | vários |

### Direção de arte

São seis tratamentos por função narrativa, e não um cartão escuro para tudo:
- **documental**: a foto manda;
- **arquivo**: papel, sépia e carimbo de procedência;
- **dado**: papel claro, tinta escura e um acento, como infográfico de jornal;
- **mapa**: cartografia escura com destaque amarelo;
- **ciência**: prancheta azul-petróleo, grade fina e linhas ciano;
- **alerta**: vermelho e amarelo só para o excepcional.

O amarelo é o acento da marca, não a solução universal.

Tipografia: Montserrat (títulos), JetBrains Mono (dados, rótulos) e Source Serif 4 (contexto, arquivo, citação).

## 4. Legendas (contextuais)

As legendas ficam numa faixa fixa (1180–1440), que não pula entre cenas. A palavra dita fica branca, a atual fica amarela e as futuras ficam translúcidas, então o bloco não "pula".

Cada composição declara `legenda`:
- **livre**: o padrão. A composição não usa a faixa da legenda.
- **integrada**: a tela já escreve a fala (gancho, revelação, citação). A legenda some **só** quando o trecho é redundante, ou seja, quando 60% ou mais das palavras de conteúdo já estão na tela. Se a fala traz informação nova, a legenda fica (há teste disso).

Isso substitui a regra antiga "cena com texto principal esconde a legenda".

## 5. Direção visual por acontecimento

`src/v2/capacidades.py` tem 22 capacidades, como água subindo, elevação vertical, manobra de eclusa, água descendo, explosão, rota, localização, território, escala, comparação, série temporal, sequência histórica, transformação, proporção, número, processo, força, órbita, citação, fonte, pessoa e lugar.

Cada capacidade combina padrões de ação em português (sujeito/objeto + verbo) com os sinais estruturados do roteiro (`bloco.funcao`, `acontecimento.recurso`).

**Um acontecimento crítico sem composição viável vira LIMITAÇÃO explícita** e o fiscal_v2 reprova a cena. Por exemplo: a fala cita uma explosão, mas não há alcances nos fatos. O motor não troca o acontecimento por foto genérica.

A montagem junta as cenas seguidas do mesmo mecanismo numa composição, com as etapas cronometradas pela fala. No Panamá, as cenas de 14,8 a 28,5 s viraram uma eclusa só.

## 6. Precisão factual (`src/v2/fatos.py`)

São cinco regras que bloqueiam a cena:
- **F1**: moeda original.
- **F2**: conversão só com taxa, data e fonte, e a conta é conferida.
- **F3**: fonte obrigatória e presente na lista de fontes do vídeo.
- **F4**: natureza do valor (típico, excepcional, estimativa ou histórico), e o excepcional precisa da palavra que o qualifica.
- **F5**: o rótulo não pode afirmar mais que o contexto.

O "R$ 27 milhões" do Panamá é reprovado em F1, F3, F4 e F5. A versão correta passa e mostra US$ 5,3 milhões com a natureza "LANCE RECORDE EM LEILÃO" e a fonte listada.

## 7. Fiscal V2 (`src/v2/fiscal_v2.py`)

Bloqueios:
- **B1**: acontecimento crítico não representado.
- **B2**: a fala promete mecanismo e a tela mostra foto ou texto.
- **B3**: número não validado.
- **B4**: texto sobre texto ou fora do quadro por 0,75 s ou mais.
- **B5**: revelação fora de sincronia (mais de ±0,4 s).

Avisos: imagem repetida, foto parada por mais de 5 s, plano maior que 8 s, zona da interface, letra pequena, loudness e composições iguais em sequência.

A parte subjetiva é uma lista de perguntas para o Heitor, sem nota.

No vídeo original do Panamá, o fiscal V2 dá **6 bloqueios B2**, um em cada fala de mecanismo mostrada como foto ou tela roxa. O fiscal antigo aprovava esse vídeo. A conversão V2 do mesmo roteiro, com os dois números corrigidos, dá 0 bloqueios.

## 8. Testes e validação

- `tests/test_v2.py`: 28 testes, todos passando localmente. Cobrem:
  - o catálogo e os metadados;
  - o render de todos os exemplos sem erro e sem texto sobre texto;
  - a regressão visual (64 referências, 2 instantes por composição);
  - um teste de que a regressão **detecta** uma mudança real;
  - a legenda contextual;
  - capacidades, fatos e acervo (recorte de cartão, hash perceptual, licença NC/ND, relevância);
  - montagem e fiscal;
  - o render ponta a ponta de um vídeo V2 curto pelo `render.py`;
  - o NTC intocado.
- A suíte antiga continua igual: 408 passam. As 5 falhas que já existiam no main dependem dos prompts do cofre.
- Regressão visual: Playwright + comparação de pixels, sem serviço externo. Referências em `tests/v2_referencias` (WebP sem perda, 144×256, 1,7 MB).
- Workflow `.github/workflows/testes-v2.yml`: roda no ramo `visual-v2` e publica a galeria como artefato.

### Reproduzir

```bash
npm install && pip install -r requirements.txt -r requirements-dev.txt
python scripts/v2_natural_earth.py                 # camadas do Natural Earth (uma vez)
pytest -q tests/test_v2.py
python -m src.v2.galeria --saida saida/galeria_v2  # galeria com prévias
CORINGA_AUDITORIA=<pasta do diagnóstico> python -m src.v2.antes_depois --saida saida/galeria_v2
python -m src.v2.regressao [--atualizar]           # regressão visual
python -m src.v2.manim_cenas lancamento saida/manim/teste --dur 4   # opcional (Cairo/Pango)
```

## 9. Remotion: protótipo e decisão

O mesmo `numero.animado` foi reescrito em React/Remotion (`prototipos/remotion`), com 150 quadros em 1080×1920 nesta máquina de 2 núcleos:

| | Palco V2 atual | Remotion 4.0.543 |
|---|---|---|
| Render | 10,3 s (inclui efeitos sonoros, mixagem e masterização) | 8,1 s, mais 13,4 s de bundle |
| Pico de memória (processos) | ≈ 2,1 GB | ≈ 1,7 GB |
| Qualidade visual | a mesma (os dois desenham no mesmo Chromium) | a mesma |
| Sincronização | `seek(t)` determinístico | `useCurrentFrame()` determinístico |
| Mapas MapLibre | funcionam (espera dos tiles por quadro) | exigiriam `delayRender` por quadro, e não foram testados |
| Integração Python/ffmpeg | nativa | outro runtime (Node/React/webpack) e outro pipeline de áudio |
| Licença | — | gratuita para pessoa física e empresas de até 3 pessoas; acima disso, Company License (a partir de US$ 100/mês para automação) |

**Decisão: não migrar.** Não há ganho visual nem de sincronização. O ganho de velocidade (≈ 20%) não paga a reescrita
das 32 composições nem o segundo runtime. Isso também respeita a regra permanente "sem migração para Remotion".
O protótipo fica no ramo para referência.

## 10. Chromatic: decisão

O plano gratuito tem 5.000 snapshots por mês, só no Chrome. A integração com Playwright passa por um build de
Storybook e os snapshots são tirados na nuvem deles. As composições do Coringa são cenas no tempo (`seek(t)`), não
stories, e os mapas dependem de WebGL e de dados locais. A regressão por Playwright já cobre o caso sem custo nem
conta externa.

**Não integrado.**

## 11. Funcionalidades

**Concluídas, com evidência renderizada:**
- 32 composições;
- mapas MapLibre + Natural Earth;
- gráficos D3;
- mecanismo da eclusa (subir e descer) e mecanismo de nível;
- legenda contextual;
- direção por acontecimento com limitação explícita;
- montagem com continuidade;
- validação factual;
- fiscal V2;
- recorte de cartão de scanner e varredura de panorâmica;
- hash perceptual;
- filtro de licença;
- galeria;
- regressão visual;
- integração ao `render.py`;
- sequências em 5 temas (história, biologia, física, astronomia, geografia);
- módulo Manim opcional.

**Parciais:**
- `acervo_v2` decide sobre o que o acervo atual já baixou, mas **não** refaz a busca no Commons (o Commons é bloqueado neste ambiente). Por isso a relevância foi testada com os metadados do Panamá e com casos sintéticos.
- O foco visual usa energia de bordas, não detecção de objetos ou rostos.
- `capacidades` usa regras em português: é extensível, mas não entende paráfrases que fogem dos padrões.
- A conversão do Panamá ainda tem uma foto repetida (a20), que veio do acervo original.

**Não implementadas:**
- Vídeo real de arquivo (clipes) dentro das composições V2. O motor antigo continua com essa capacidade.
- Escolha automática de `forcas.vetores`/`evento.impacto` a partir só da fala: essas composições pedem dados que o roteiro ainda não fornece (forças, alcances).
- Ligação da V2 ao `main.py`. Está desligada de propósito: só depois da aprovação.

## 12. Limitações conhecidas

- **Resolução das fotos da auditoria.** O diagnóstico guarda miniaturas de 1080 px. A foto de 1913 tem só 110 px úteis de altura, então a varredura fica limitada a 2× e a galeria avisa. No pipeline real, o original do Commons tem resolução muito maior.
- **Narração.** A narração do Panamá ainda diz "R$ 27 milhões". A correção do número precisa voltar ao roteiro e à voz (edge-tts, sem custo) antes de um vídeo novo.
- **Simplificação da eclusa.** As comportas aparecem como de levantar; no Panamá são de duas folhas. É uma simplificação do corte lateral, registrada na composição.
- **Desempenho dos mapas.** Cada quadro de mapa espera os tiles: ≈ 0,2 s por quadro neste ambiente.

## 13. Recomendação sobre a liberação

Não juntar ao main ainda. Próximos passos sugeridos:
1. O Heitor revisa a galeria e as comparações e aprova ou pede ajustes por composição.
2. Com a aprovação, liga-se `MOTOR_VISUAL=v2` no `main.py` só para um vídeo de teste (com nova voz edge-tts, sem custo extra de IA, ou com autorização se houver custo).
3. Mede-se o resultado com o fiscal V2.
4. Só então se junta ao main.
