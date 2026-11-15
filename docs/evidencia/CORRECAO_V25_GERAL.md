# V2.5 — Generalização e estabilização do motor (ramo `piloto-v24-lagartixa`)

Sem merge, sem alteração de main, produção, NTC ou identidade. Nenhuma publicação, nenhum envio ao Telegram.

## 1. Matriz de capacidades (auditoria RENDERIZADA — `python -m src.v2.auditoria_capacidades`)
Cada composição: exemplo da galeria + contrato bem formado + contrato "como o roteirista escreve", pelo caminho real
(contrato → seletor → montagem → palco), medindo erro de render, texto fora/sobreposto, área vazia, mudança visível
(média e fração de pixels), ocupação da área útil, e se o fiscal bloqueia quando o dado não serve.

| Estado | Composições |
|---|---|
| **FUNCIONAL** — demonstra acontecimento | mecanismo.estados, mecanismo.nivel, astronomia.orbita, evento.impacto, forcas.vetores¹ |
| **FUNCIONAL** — dado/lugar/registro | mapa.rota, mapa.localizacao, mapa.territorio, grafico.barras, grafico.temporal, comparacao.grandezas, proporcao, numero.animado, linha_tempo.historica, foto.documental, foto.historica, lower_third², fonte.evidencia, citacao |
| **FUNCIONAL** — editorial/apoio (sem tipo de acontecimento) | abertura.pergunta, abertura.revelacao, revelacao.surpresa, encerramento.editorial, banner.*, destaque.palavras, titulo.capitulo, foto.sequencia |
| **LIMITADA** | processo.etapas e diagrama.explicativo (só escrevem; mecanismo crítico só com rótulos curtos), comparacao.antes_depois (exige par de fotos do mesmo lugar), video.documental (exige vídeo licenciado), mecanismo.eclusa (só eclusa) |
| **NÃO FUNCIONAL** | animacao.quadros — sem Manim no CI a tela sai VAZIA; agora o seletor recusa (limitação + bloqueio) |

¹ era NÃO FUNCIONAL (objeto parado, seta solta, 1,4% da área) → corrigido. ² pessoa com nome virava foto sem identificação → corrigido.
Fallbacks silenciosos no caminho real: **0** (todo crítico sem composição capaz termina em limitação + bloqueio do fiscal).

## 2. Problemas estruturais encontrados → correções gerais
| Problema | Correção |
|---|---|
| Seletor aceitava dado que "existe" mas não desenha (frase no lugar de número, item sem valor, anel sem raio, força sem sentido, país inexistente) → tela degradada sem bloqueio | esquema ÚNICO de campos (`capacidades.ITEM/ESCALAR`): o que não desenha vira limitação explícita |
| Composições quebravam com dado parcial (órbita sem raio: Sol sumia; diagrama com string: erro JS) | padrões desenháveis e coerção de tipos no renderizador |
| Validação só geométrica | **cobertura semântica** (`src/v2/cobertura.py`): afirmação × elementos necessários × representados × mudança exigida/produzida × fonte → aprovado/revisão/bloqueio, com 1 alternativa entre as composições capazes |
| Prévia não media objeto pequeno nem movimento de objeto pequeno | fração de pixels alterados e ocupação da área útil |
| Sequências de cartões / monotonia | D17 (3 cartões de texto seguidos = bloqueio), E-seq (≥ 5 cenas iguais = revisão humana) |
| Roteirista não conhecia o formato dos campos (esquema, forças, itens…) → mecanismos em frases, números sem valor (piloto 1) | `contrato.FORMATO_CAMPOS` no prompt do roteiro e do conserto |
| Checkpoint perdia as imagens após vídeo pronto; imagem ausente virava "foto vizinha" | limpeza nunca apaga `<checkpoint>/arquivos`; imagem ausente interrompe a retomada; verificação no workflow antes da retomada e antes do cache |
| Pessoa com nome só no sujeito | `dados.nome` derivado do sujeito (sem inventar) |

## 3. Testes
- Suíte completa: 748 testes; as falhas restantes são as **5 antigas** da linha de base (polvo, lote, fase3), nenhuma nova.
- `tests/test_v25_matriz.py`, `test_v24_previa.py`, `test_v24_correcao_visual.py`: regras novas, retomadas sucessivas, áudio medido no MP4.

## 4. Cobertura por nicho (matriz offline, `src/v2/matriz.py`, 49 cenários)
| Grupo | DEV | VAL (inéditos, expectativa escrita antes) |
|---|---|---|
| ciência/mecanismos invisíveis | 5/5 | 3/3 |
| natureza/animais | 1/1 | 3/4 |
| história | 1/1 | 4/4 |
| geografia | 2/2 | 3/3 |
| espaço | 1/1 | 3/4 |
| engenharia | 2/2 | 3/4 |
| números/estatística | 2/2 | 4/4 |
| pessoas/biografias | 1/1 | 3/3 |
| mistos | 1/1 | 3/4 |
| **total** | **16/16** | **29/33** |
VAL não foi ajustado: as 4 diferenças são **revisões humanas conservadoras** (nenhuma aprovação indevida): rota com nome de
lugar que a fala não diz (2) e ilustração cujos dados não estavam nos FATOS do cenário (2 — a regra de rastreio funcionando).
Dois defeitos GERAIS de render achados pela VAL foram corrigidos (rótulo de anel fora do quadro; rótulo de força no título).
Casos negativos (imagem enganosa, anacrônica, de outra pessoa, mídia ausente, dado inválido, tipo desconhecido): **nenhum aprovado**.

## 5. Ensaio integrado (`src/v2/ensaio.py`, código real do checkpoint ao MP4; só a voz simulada)
| Cenário | Resultado |
|---|---|
| checkpoint íntegro + edição | MP4, 0 bloqueio, preparo = render (0 divergência), −14,1 LUFS / −2,5 dBTP, checkpoint novo com 21/21 imagens |
| imagem apagada do checkpoint | para na verificação, nomeando o arquivo (sem MP4, sem foto substituta) |
| IA indisponível com contrato pendente | sem exceção; bloqueio no preparo com o que falta |
| retomadas A→B→C com limpeza pós-vídeo | imagens preservadas (teste) |

## 6–7. Pilotos reais (1 geração por assunto, sem repetição)
| # | Assunto | Resultado | Causa objetiva |
|---|---|---|---|
| 1 | Por que o céu é azul? (ciência, inédito) | BLOQUEADO_PREPARO, sem MP4 | roteirista não conhecia o formato do esquema/números → 5 críticos sem dados. **Corrigido** (FORMATO_CAMPOS) |
| 2 | Naufrágio do Titanic (história, inédito) | BLOQUEADO_PREPARO, sem MP4 | esquema e números OK após a correção; 4 momentos históricos sem foto que os mostre (manobra de Murdoch, iceberg avistado, inspeção de Andrews, destroços 1985) — bloqueio correto, nenhuma foto genérica aceita como prova |
| 3 | Por que a Torre de Pisa é inclinada? (engenharia/geologia, inédito) | ver anexo da entrega | |

## 8. Limitações remanescentes
- **História**: depende do acervo ter a foto do MOMENTO narrado; quando não tem, o vídeo é barrado (seguro, mas a taxa de
  aproveitamento é baixa). Falta uma representação documental alternativa (mapa do lugar + linha do tempo + foto do
  objeto identificada como contexto) acionada automaticamente para momentos sem registro.
- Cobertura semântica por palavras: sinônimos e topônimos (Abrolhos ≠ "Brasil") geram revisão humana.
- animacao.quadros sem Manim; antes/depois e vídeo dependem de insumo raro.
- Ritmo: vídeos de mecanismo tendem a muitas cenas de esquema seguidas (E-seq → revisão humana).
- Estética só se avalia assistindo; a automação prova ausência de defeitos objetivos, não qualidade.

## 9. Categorias prontas
- **Prontas para piloto supervisionado** (não para publicação automática): ciência/mecanismos com esquema; números e
  comparações com fonte; geografia/mapas; espaço (órbitas, impactos).
- **LIMITADAS**: natureza/animais (dependem de foto do comportamento), engenharia (máquinas sem esquema → barradas),
  biografias (dependem de retrato real).
- **NÃO SUPORTADA para automação**: história de momentos sem registro fotográfico no acervo.

## 10. Recomendação
**NO-GO para ativar a V2 em produção automática.** GO para pilotos supervisionados nas categorias "prontas", sempre com
avaliação audiovisual humana (o fiscal nunca aprova sozinho: ilustração e monotonia exigem revisão). Próximo passo
estrutural: representação documental alternativa para momentos históricos sem foto.
