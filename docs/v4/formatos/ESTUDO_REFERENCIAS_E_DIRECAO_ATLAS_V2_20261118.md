# ATLAS — Estudo de referências e proposta de direção audiovisual V2
**Data:** 18/11/2026  
**Status:** PROPOSTA EDITORIAL, não implementação nem alteração das regras já aprovadas.  
**Ramo:** `atlas-direcao-visual-20261118`. **Escopo:** ATLAS/Coringa; não toca produção `motor-integral-v4`, DOSSIÊ ou NTC.
**Motivação:** revisão humana do piloto privado Guerra dos Chips (58,862 s): inteligível mas monótono, fotos pequenas, mapa zenital repetido, cartões inadequados ao assunto, narração Edge não aprovada. O fiscal marcou `BLOQUEADO` por congelamento 36–40 s, embora o GitHub Actions tenha concluído com sucesso.

## 0. Método, evidência e limite do estudo
Este é um **estudo de linguagem editorial**, confrontando **fontes dos próprios criadores**, episódios identificados, documentação de produção, relatos e um estudo externo de montagem com o código ATLAS. Não é uma afirmação de ter baixado e decupado, quadro a quadro, os seis vídeos originais; a decupagem por quadro feita nesta conversa foi **do MP4 próprio da Guerra dos Chips**, não dos vídeos de terceiros.
- **Primárias:** neo FAQ e portfólio; Branch Education vídeos/about; fern website/FAQ e vídeo dos bastidores; Johnny Harris “How I Make My Maps”; CNBC vídeo e descrição; Wendover episódio e entrevista pública de Sam Denby.
- **Complementares:** Nieman Journalism Lab sobre Vox Borders; levantamento de planos de ReelPantry (amostra de 8 vídeos fern, trechos amostrados, portanto números NÃO universais); artigo ACM MapStory sobre processos de animadores cartográficos.
- **Licenciamento:** observar referências para aprender gramática, **não** importar fotogramas, trechos de vídeo, músicas, marcas, materiais Getty, imagens Bing/Google, gráficos nem modelos 3D de terceiros para o Coringa sem licença específica.

## 1. Conclusão central
**ATLAS = geografia editorial com acontecimentos físicos e evidências reais**, não uma sequência de apresentações sobre mapa. A narração faz uma promessa; a imagem demonstra a promessa. Movimento de câmera, legenda, transição ou cartão **não** substituem acontecimento ou prova. Um vídeo pode ser tecnicamente válido e editorialmente reprovado.

Preservar o DNA já aprovado em `GUIA_VISUAL_ATLAS_V1.md`: mapa/relevo escuro licenciado; grafite `#05080F`/`#070B14`; papel off-white `#F2EDE3`; acento amarelo `#FFD21F`; cards retos; tipografia Montserrat/JetBrains; legenda branca com no máximo uma palavra amarela por bloco; créditos separados abaixo da legenda; fontes e áreas seguras. O estudo **não** autoriza copiar estética alheia nem modificar esses tokens.

## 2. Seis referências — mecanismo narrativo, adaptação e limite

### 2.1 neo — mapa explica uma ação situada
**Exemplo:** “How One Ship Caused a Global Traffic Jam” (Ever Given / Suez, 31/03/2021). **Método declarado do criador:** After Effects + GeoLayers sobre dados OSM/Bing Satellite para mapas 2D; Blender para 3D.
- **Princípio extraído:** câmera acompanha uma relação geográfica específica: **onde** algo ocorre → **qual trajeto/área muda** → **qual consequência territorial aparece**. É diferente de um mapa que apenas localiza países citados.
- **Para ATLAS:** nova composição cartográfica deve ter `evento_geografico` explícito (aproximar, bloquear, percorrer, isolar, expandir, comparar). Uma rota só é permitida quando mostra deslocamento ou dependência real que o espectador compreende. Mapas podem alterar escala e perspectiva, mas cada mudança precisa revelar um fato novo.
- **Não copiar:** estética/plug-in/tiles proprietários; não fazer inclinação 3D falsa com fronteiras erradas. Testar uma câmera de relevo oblíqua com datasets licenciados e geometria verificada.
- **Teste Guerra dos Chips:** Holanda → Taiwan só ganha valor se ligar **a máquina física demonstrada** à produção industrial, não apenas a duas etiquetas.

### 2.2 Branch Education — o objeto físico muda de estado
**Exemplo:** “How are Microchips Made?”; a produção declara 1300 h de pesquisa, roteiro, modelagem, animação e edição; usa narração humana e verifica fidelidade técnica.
- **Princípio:** começar pelo **objeto**, abrir sua estrutura, seguir a transformação de uma peça e recuperar o contexto. A câmera acompanha peças e fluxos que o narrador cita. A demonstração não desaparece para mostrar cards no meio do processo.
- **Para ATLAS:** contrato `explicacoes` existente deve ser expandido para um pequeno catálogo de mecanismos frequentes, NÃO um 3D específico por episódio. Ordem sugerida: objeto real → corte didático → ação/fluxo → consequência. Usar 2.5D/SVG/Blender pré-renderizado quando isso bastar.
- **Não copiar:** horas de modelagem por vídeo, modelos originais de terceiros, diagramas que insinuem exatidão física não comprovada. Cada reconstrução técnica deve ser marcada como esquema quando simplificada.
- **Teste Guerra dos Chips:** wafer/placa real → esquema correto de fotolitografia EUV (luz, padrão, wafer; simplificado e validado) → máquina real ou foto licenciada correspondente. **Atualmente não existe mecanismo EUV aprovado**, logo há bloqueio de capacidade, não autorização para substituí-lo por rota.

### 2.3 Wendover Productions — uma tese causal, não uma lista
**Exemplo:** “How Taiwan is Preparing to Get Invaded” (08/08/2026). Entrevista pública com Sam Denby destaca execução narrativa do conceito e planejamento de produção.
- **Princípio:** pergunta com consequência → componentes de um sistema → dependência/gargalo → resposta. O mapa é usado para mostrar a operação do sistema; números só entram quando mudam a inferência.
- **Para ATLAS:** cada história deve ter `pergunta`, `tese`, `tensao`, `virada` e `resposta`, com 3–5 causas importantes. Números precisam responder “por que isso importa?”, não criar uma interrupção estética.
- **Não copiar:** velocidade e tempo de construção de vídeos de 18–25 min para Shorts de 60 s; nem transmitir certezas sobre temas geopolíticos em evolução.
- **Teste Guerra dos Chips:** não começar enumerando EUA, China, Holanda, TSMC, Nvidia e datas. Mostrar **uma dependência concreta**, revelar que não é apenas fabricação, depois ampliar para a disputa.

### 2.4 CNBC — evidência industrial real
**Exemplo:** “Why AI Chips Made In The U.S. Are Being Sent To Taiwan — Creating A Major Bottleneck” (08/04/2026). A produção relata entrevistas com TSMC e visita a uma unidade de packaging da Intel.
- **Princípio:** o mundo físico prova que o setor existe: fábrica, processo, máquinas, engenheiros e componentes; gráfico contextualiza, não finge documentar.
- **Para ATLAS:** onde a fala menciona máquina/fábrica/produto, a primeira opção é imagem/vídeo real, específico e licenciado. O mapa entra depois para situá-lo. Criar `prova_visual` diferenciando `imagem_real`, `video_real`, `esquema`, `reconstituicao`, `grafico`.
- **Não copiar:** usar reportagem CNBC, B-roll comercial ou still do vídeo sem licença; imagens genéricas de sala limpa **não** podem ser apresentadas como interior da TSMC.
- **Teste Guerra dos Chips:** prioridade de pesquisa audiovisual = máquina EUV e wafer, não mais fotos de mapa.

### 2.5 Vox Borders / Johnny Harris — tornar o território concreto
**Exemplo:** “Divided island: How Haiti and the DR became two worlds” e “How I Make My Maps”. Reportagem do Nieman Lab documenta o uso de fontes locais e a conexão entre cartografia e vivência.
- **Princípio:** zoom do mapa para lugar/evidência/cotidiano → volta ao mapa com significado novo. Uma fronteira é uma explicação da vida real, não um traçado decorativo.
- **Para ATLAS:** usar mapas em **três escalas funcionais**: global (relação), regional (decisão) e local (prova). Quando mostrar fotografias reais, enquadrá-las como objeto principal e creditar corretamente. Não esconder o assunto em pinos circulares pequenos.
- **Não copiar:** colagem documental como fantasia, imagens de cidadãos sem contexto, ou elementos de produção audiovisual de campo inexistentes.
- **Teste Guerra dos Chips:** localização Taiwan → fábrica grande e identificável, com o mapa recuando para pano de fundo; não uma miniatura de foto sob um selo.

### 2.6 fern — cinema de investigação e mudanças de linguagem
**Exemplos:** vídeo oficial “The Truth About fern” (22/07/2026) e decupagem independente ReelPantry. FAQ oficial: equipe de animadores 2D/3D, IA generativa usada seletivamente em tarefas auxiliares.
- **Princípio:** uma cena concreta abre a questão, depois alterna planos de escala/tipo (objeto, ambiente, mapa, arquivo, reconstrução), usando som e composição para criar expectativa; os planos têm função narrativa diferente.
- **Amostra externa, não regra universal:** ReelPantry analisou 8 vídeos e trechos selecionados, relatando aproximadamente um novo plano a cada 2,8 s. A própria amostragem impede impor esse número a todos os temas, especialmente Shorts.
- **Para ATLAS:** roteirizar **variação de modalidade com motivo**: objeto ↔ geografia ↔ processo ↔ evidência ↔ consequência. Sons discretos nas ações; evitar câmera perpetuamente flutuante e cortes frenéticos sem revelação.
- **Não copiar:** visual de bonecos/figurinos, reconstituições cinematográficas não verificáveis nem tom investigativo dramático para assuntos que não sustentam tensão.
- **Teste Guerra dos Chips:** a troca de mapa para máquina real deve ser percebida como **revelação**, não como elemento decorativo sobre o mesmo mapa.

## 3. Estado ATUAL do motor e lacunas concretas
Inspecionados `src/v4/formatos/diretor.py`, `src/v4/formatos/formatos.json`, `docs/v4/formatos/CONTRATO_DIRECAO_VISUAL_ATLAS.md`, `src/v4/formatos/canais/coringa.json`.
- **Já existe:** seleção de `prova` por beat, escolha de composição do catálogo, `explicacoes` para mecanismos, tokens de identidade, testes de tipografia/colisão/progressão, mapa/pino/cards e reuso de `dossie.documentCard` em ATLAS.
- **Limitação decisiva:** `formatos.json → formatos.atlas.clipes` só autoriza `mecanismo.eclusa`. **Não há mecanismo de semicondutor**. O mapa e o card tornam-se substitutos involuntários para explicações físicas.
- **Composições disponíveis:** `atlas.abertura`, `atlas.protagonista`, `atlas.escada`, `atlas.painel`, `atlas.tecnica`, `atlas.manchete`. Palcos = `mapa`, `tecnico`; não há atualmente um plano de prova real dominante com contrato audiovisual próprio.
- **Regra atual da abertura:** mapa hero desde o primeiro quadro, sem animação técnica no gancho. **Preservar nesta proposta**: abrir com mapa e uma **prova física grande e licenciada sobreposta** (chip/wafer/fábrica), depois entrar no mecanismo. Revisar regra de abertura só mediante teste A/B e aprovação explícita.
- **Voz:** workflow privado dos chips desativou `GEMINI_API_KEY` e recorreu ao Edge TTS; isso é **voz provisória para teste**, não novo preset aprovado. O estado `BLOQUEADO` do MP4 de 58,862 s não pode ser apresentado como render editorial aprovado.
- **Créditos:** `A-CREDITO-RODAPE` persiste e deve ser resolvido para exibição nas 3 plataformas, sem elevar cegamente a faixa que o usuário aprovou.

## 4. Gramática original proposta do ATLAS: seis verbos, uma identidade
Cada beat deve ter um verbo dominante e uma evidência observável:

| Verbo | Promessa ao espectador | Modalidade correta | Falha típica |
|---|---|---|---|
| **LOCALIZAR** | onde e em que escala? | mapa com território e câmera factual | mapa exibido só porque um país foi citado |
| **MOSTRAR** | o que é essa coisa? | foto/vídeo real **grande**, com procedência | foto minúscula em pino ou banco genérico |
| **DEMONSTRAR** | o que se move/muda? | mecanismo, antes/depois, corte técnico | carta de texto no lugar da ação |
| **CONECTAR** | quem depende de quem e por quê? | fluxo ou mapa, com vínculo verificável | linha entre países sem objeto causal |
| **COMPARAR** | qual diferença muda a conclusão? | gráfico ou um card editorial decisivo | várias caixas consecutivas de números/datas |
| **REVELAR** | o que o espectador agora compreende? | consequência visual ou retorno a cena anterior | slogan final sem consequência visível |

**Regra essencial:** alternância não deve ser mecânica. O diretor escolhe a modalidade pelo verbo da fala; mapas podem voltar várias vezes quando a relação geográfica mudou de fato. Cartões continuam parte do DNA, mas somente quando a informação os justifica. Nenhum teto arbitrário global para quantidade de fotos, mapas, cortes ou cards.

### Esquema editorial PROPOSTO (não implementado)
Antes de formar `beats` reais, o diretor redigiria uma `ficha_cena` com:
```json
{
  "id": "chips-asml-euv",
  "fala": "A Holanda produz máquinas fundamentais para fabricar chips avançados.",
  "pergunta_visual": "Que máquina é essa e o que ela faz?",
  "verbo": "DEMONSTRAR",
  "referente_concreto": "scanner de litografia EUV",
  "evidencia_necessaria": ["foto_real_licenciada_euv", "mecanismo_euv_aprovado"],
  "acao_observavel": "o processo simplificado de exposição transfere um padrão ao wafer",
  "depois_o_publico_sabe": "por que um equipamento holandês é essencial à fabricação em Taiwan",
  "estado_capacidade": "BLOQUEADO_ATÉ_EXISTIR_COMPONENTE_E_MÍDIA",
  "credibilidade": "esquema didático, não filmagem de máquina real"
}
```
A `prova` de hoje é texto livre; a ficha proposta explicita o vínculo **fala → objeto → ação → aprendizado → asset**. Não forçar todo campo como teste programático: o que exige julgamento humano/semântico fica no checklist editorial, e não vira falso “teste verde”.

## 5. Sequência piloto: 22–25 segundos para validar direção antes de novo episódio completo
**Tema:** Guerra dos Chips. **Aprovação:** prévia privada, nunca publicar automaticamente.

| Tempo orientativo | Cena / o que MUDA | Aprendizado | Recurso |
|---|---|---|---|
| 0–3 s | Mapa Taiwan desde o 1º quadro, **chip/wafer real grande** surge em primeiro plano, pergunta direta | existe um objeto e uma ilha ligada a ele | cartografia aprovada + foto macro licenciada |
| 3–8 s | Camera desce para Taiwan; **fábrica TSMC real ocupa a cena**, não um pino de 100 px | produção concentrada em um lugar concreto | foto real licenciada e verificada |
| 8–12 s | Comparação essencial: **74% da receita de wafers da PRÓPRIA TSMC em 2025 vem de tecnologias avançadas**, se o dado continuar verificado | magnitude da especialização interna | 1 card reto/indicador, não 3 cards |
| 12–20 s | Mostra **máquina EUV** real e uma **demonstração simplificada**, com clareza de que é esquema | o papel do equipamento holandês | mídia EUV + mecanismo novo aprovado ou BLOQUEAR |
| 20–25 s | Volta ao mapa com **objeto causal** “equipamento Holanda → fábrica Taiwan” | um elo da cadeia pode afetar o resto | mapa/rota factual sincronizada |

**Bloqueios reais:** atualmente não há foto EUV comprovada nem mecanismo EUV no catálogo ativo. Não fingir que o trecho já pode ser renderizado como planejado. Alternativa para teste V0: foto licenciada validada de máquina + movimento gráfico básico de duas etapas rotulado “esquema”, **somente após verificar precisão técnica**. Se não houver ativos válidos, não usar foto de sede da ASML como se fosse a máquina.

**Narração:** reutilizar **o timbre/preset editorial previamente aprovado**, mantendo origem, parâmetros e hash rastreados; não impor Edge por conveniência de custo. Testar qualidade auditiva com 2–3 frases antes de gastar no render integral.

## 6. Mudanças de engenharia — prioridade e custo
**P0 — apenas editorial/dados (baixo custo, sem render caro):**
1. Gerar `fichas_cena` antes do JSON. Para cada frase factual: verbo, referente visível, ação, prova, fonte. Se inexistente, registrar `MÍDIA/CAPACIDADE INDISPONÍVEL` em vez de escolher rota/cartão por padrão.
2. Criar checklist de revisão humana `fala_ou_acontecimento_visual`: avaliar **relevância visual**, não só frequência de pixels novos.
3. Bloquear substituição silenciosa de voz; travar preset de narração aprovado por ID/versão, com diagnóstico claro de indisponibilidade, sem fallback editorial não autorizado.
4. Corrigir resultado de workflow: `estado=BLOQUEADO` deve resultar em **status editorial explícito** de bloqueio no Telegram e, conforme política do job, conclusão não verde da etapa de gate; entrega de prévia bloqueada só para diagnóstico, com etiqueta evidente.

**P1 — composições reutilizáveis (custo médio, testes por componente):**
5. Novo plano ATLAS de **prova visual dominante** (foto/vídeo real em enquadramento grande), mantendo legenda/crédito/safe area, sem virar paleta DOSSIÊ.
6. Capacidade de transição semântica **mapa → prova física → mapa**, sem usar foto pequena presa ao pino em todos os casos.
7. Animação de processo **2.5D** com `focos` semânticos e estados; primeira candidata semicondutores **somente se prevista para uso recorrente**. Manter `mecanismo.eclusa` como regressão.
8. Estudar câmera de mapa com perspectiva oblíqua verdadeira e relevo, testando geometria, noções de distorção, crédito e framerate; fallback continua mapa plano dinâmico, não falsa perspectiva.

**P2 — validação audiovisual e generalização (depois de P0/P1):**
9. Render privado de 22–25 s com voz aprovada, avaliar no celular: curiosidade, compreensão, consistência, ritmo, legibilidade, precisão, som. Se falhar, reescrever cenas, não adicionar zoom por reflexo.
10. Só após aprovação, montar 60s. Testar as **mesmas regras de direção** em segundo assunto não industrial (ex.: rota de comércio, fronteira ou infraestrutura), para evitar overfit da Guerra dos Chips.
11. Resolver créditos/captions por plataforma antes de publicação; as licenças de origem governam a forma de atribuição.

## 7. Gates de aceitação PROPOSTOS
**Automáticos possíveis:** asset inexistente/licença incompatível, referente de mídia/objeto não cadastrado, voz diferente do preset aprovado, componente de mecanismo sem contrato, texto fora de área segura, sincronização, áudio, estado `BLOQUEADO`, render sem mudança visual. **Não** prometer detecção automática de compreensão humana, verdade factual ou interesse do espectador.
**Aferição humana obrigatória (registro sim/não por cena):**
- Dá para apontar **o que mudou na história**, não apenas texto/câmera?
- A imagem é pertinente ao **substantivo e verbo narrados**?
- Prova real está suficientemente grande e autêntica? Reconstrução é rotulada?
- O mapa explica geografia ou está enchendo espaço?
- Os números são indispensáveis e corretamente qualificados?
- O ritmo dá tempo para entender a ação, sem trechos vazios?
- A voz é a aprovada e a trilha não compete?
- O final entrega uma consequência, não só uma frase de efeito?

**Regra de aprovação:** CI `success` = a automação executou; `fiscal: BLOQUEADO` = não aprovado; `aprovacao_humana` é campo separado. Testes verdes nunca significam publicação liberada.

## 8. Critérios para NÃO diluir o estilo ATLAS
- A identidade não será “um terço neo, um terço fern”: apenas **lógica narrativa** é combinada; paleta, fontes, legendas, créditos e design são originais do Coringa.
- ATLAS continua **cartográfico**: se a história não tem papel causal de geografia, escolher outro motor ou reprovar pauta.
- Sem introdução, CTA, efeito ou transição por obrigação; sem personagens 3D genéricos, documentários falsos ou mapas 3D com limites inventados.
- Nenhuma nova arquitetura de síntese generativa cara, troca de fornecedor de TTS ou mudança de branch produtiva apenas para maquiar um episódio.
- Novas capacidades ampliam o catálogo **de forma genérica**, com testes e amostras em mais de uma pauta; não embutir regras hardcoded por país, tempo ou nome do roteiro.

## 9. Fontes verificadas (consulta pública em 18/11/2026)
- neo — canal/portfólio: https://neoproductions.com/ ; **FAQ técnica:** https://neoproductions.com/faq ; vídeo: https://www.youtube.com/watch?v=8RxmRw1kCrc
- Branch Education — vídeo: https://www.youtube.com/watch?v=dX9CGRZwD-w ; método: https://www.branch.education/about ; catálogo: https://www.branch.education/videos
- Wendover — Taiwan: https://www.youtube.com/watch?v=2iHPVsyv4GU ; entrevista Sam Denby: https://thetranscriptdesk.two-lambda-ai.com/transcripts/sam-denby-wendover-productions-oxford-union/
- CNBC — packaging: https://www.youtube.com/watch?v=a0uQ1ZxfxfQ
- Johnny Harris/Vox — Borders: https://www.youtube.com/watch?v=4WvKeYuwifc ; “How I Make My Maps”: https://www.youtube.com/watch?v=GsojLuJpe_0 ; cobertura de produção: https://www.niemanlab.org/2018/08/explanatory-video-engagement-how-voxs-borders-series-is-humanizing-the-map-and-building-local-source-networks/
- fern — bastidores oficiais: https://www.youtube.com/watch?v=TlioXObelHU ; FAQ: https://www.watchfern.com/contact ; análise amostral independente: https://www.reelpantry.com/teardown/fern-tv-youtube-long
- Pesquisa de processo de produção de mapas (ACM UIST 2025): https://doi.org/10.1145/3746059.3747664

**Próxima etapa recomendada:** aprovar **direção e storyboard de 22–25s** primeiro; confirmar voz e mídia válida; implementar componentes novos **apenas na branch experimental**; mostrar vídeo real ao usuário. Este documento não modifica código, não renderiza e não publica.
