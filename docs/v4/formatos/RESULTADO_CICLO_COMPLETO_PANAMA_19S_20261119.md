# Prova de ciclo completo da eclusa — 19 s (19/11/2026)

**STATUS: AGUARDANDO AVALIAÇÃO HUMANA. NÃO PUBLICAR. NÃO PROMOVER PARA O MOTOR PRINCIPAL.**

## Feedback que motivou a intervenção

Na prévia anterior de 7,8 s, o usuário observou que a animação era curta e mostrava praticamente apenas a água subindo, sem explicar o ciclo da eclusa. A auditoria independente também havia detectado um corte de origem e problemas de acabamento. Esta rodada responde especificamente à **ausência de causa, continuidade e consequência** — sem alegar que um esquema 2D resolve a estética do canal.

## O que foi implementado

- Componente isolado `motor4/remotion/src/formatos/LockCausalCycle.tsx` e sua integração estritamente opt-in em `FilmeEditorial.tsx` por `mechanism=lock_cycle`; preserva os mecanismos anteriores `lock_filling` e `lock_causal`.
- Storyboard `docs/v4/formatos/filme_panama_ciclo_19s.json`: 0–1,6 s registro histórico real USNS Comfort (DVIDS 634226, master SHA conhecido e licença domínio público); 1,6–19 s **17,4 segundos de ciclo explicativo** em corte longitudinal, com dissolvência do mesmo master para quadro técnico.
- Sete ações visíveis e dirigidas por eventos do roteiro (não relógio hardcoded no componente):
  1. `enter` t=0: navio entra no nível baixo, portão de entrada aberto e de saída fechado;
  2. `seal` t=2,6: portão de entrada fecha, isolando câmara;
  3. `valves` t=4,6: válvulas liberam água do nível superior pelos condutos;
  4. `rise` t=6,1: água sobe dentro da câmara e casco flutua acompanhando a mesma curva vertical;
  5. `equalize` t=12,2: igualação com nível superior; vazão cessa;
  6. `open` t=14: portão de saída fica aberto somente depois da equalização;
  7. `exit` t=15,6: navio avança da câmara para o trecho mais alto.
- Geometria e portas são **simplificações ilustrativas** (não proporções nem mecanismo de giro exatos). A filmagem DVIDS apresenta a eclusa; a subida está demonstrada no desenho, **não comprovada no clipe**.
- Fato baseado em fontes oficiais: Autoridade do Canal do Panamá, `https://pancanal.com/en/design-of-the-locks/` e `https://pancanal.com/en/history-of-the-panama-canal/`. Água flui por gravidade por condutos (sem bombas). O esquema representa a subida em uma câmara, não todas as etapas de passagem dos dois oceanos.
- Validação `F-CICLO-INCOMPLETO` e manutenção de `F-PONTE-REAL` e `F-MECANISMO-CAUSAL`; testes `tests/test_filme_panama_ciclo_19s.py`. O Telegram privado foi generalizado com nome de arquivo/duração parametrizados, preservando o comportamento padrão do antigo piloto de 7,8 s.
- Workflow isolado `.github/workflows/filme-editorial-panama-ciclo-19s.yml`, disparado por `.github/atlas/filme_panama_ciclo_19s.txt`, que usa o master original curado, remotion em 540×960, sem TTS/IA paga, auditoria temporal de movimento nas regiões reais de cada ação, e envio privado condicionado ao QA.

## Evidência de execução e correções

1. **44536021203 — failure:** incompatibilidade TypeScript: tipagem `Cue.action` ampliada no compositor era incompatível com `EventoEclusa` do componente legado. Corrigido adaptando o tipo ao chamar apenas o componente antigo. Sem vídeo enviado; Telegram recebeu aviso de bloqueio.
2. **44536346964 — failure:** vídeo 19 s renderizado, mas revisão encontrou padrão triangular preto causado por SVG `path` preenchido por default dentro de `pattern`, e colisão de rodapés/captions. QA de saída mediu região inferior da câmara após o navio já estar no nível superior, falseando ausência de movimento. Corrigidos `fill="none"`, rodapés exclusivos do mecanismo e região do detector.
3. **44537374197 — SUCCESS:** 28 testes passaram, compilação TypeScript, validação de mídia, render privado 19.000 s (540×960), comparação de movimento na cena (entrada 59,08; água 60,84; saída na cota elevada 30,96; métrica de diferença média de pixels), diferença luminosa na ponte 2,12; artifact `14537350770` `filme-panama-19s-ciclo-privado`.
4. No mesmo run, **Telegram sendVideo confirmado com retorno positivo**: `{"enviado":true,"destino":"group privado autorizado","arquivo":"prova_ciclo_19s.mp4","anexos":1,"publicado":false}`. Grupo privado, vídeo + contato + mensagem; nenhum post em redes.
5. Revisão final do contato mostra textura normal (sem triângulos), títulos de etapa e créditos sem colisão, navio entrando, subindo e saindo. **Não declarar qualidade artística equivalente às referências**; continua esquema vetorial simples e silencioso, pendente de julgamento humano.

## O que ficou pendente

- A qualidade visual ainda é ilustrativa e não documental cinematográfica. Mais tempo em tela melhora a explicação, mas não resolve realismo/animação de portões em planta, iluminação, cenografia ou câmera. Evitar looping de microcorreções em um piloto específico.
- Depois da reação humana ao MP4, decidir entre direção de arte mais sofisticada para demonstradores técnicos (talvez híbrido vídeo real + composição 3D/documental) ou reduzir animações técnicas a inserções menores em filme baseado principalmente em mídia real.
- Não gerar vídeo longo, narração, gastar Claude/Gemini ou promover compositor para produção sem essa decisão. Nenhuma alteração em `main`, `motor-integral-v4`, NTC, DOSSIÊ; nada publicado.
