# Diretor multitema V2 — mapa, voz natural, progresso global (19/11/2026)

**Branch experimental:** \`atlas-direcao-visual-20261118\`; NTC/DOSSIÊ/\`main\`/produção não modificados. Sem publicação, sem gastar Claude/Gemini. **Visual não homologado**; aprovado somente o preparo e render da amostra.

## Pedido e mudança estrutural

O usuário aprovou a identidade visual dos três filmes narrados (Taiwan/chips, Venezuela, Ever Given), mas criticou voz ruim, mapas sem país destacado ou trajetos, barra de progresso que reinicia a cada imagem, e ausência de direção audiovisual. A orientação é corrigir COMPONENTES REUTILIZÁVEIS, não cada tema isoladamente.

## Implementado no mesmo compositor FilmeEditorial

1. \`motor4/remotion/src/formatos/NarrativeMapStage.tsx\` — mapa SVG D3/TopoJSON com world-atlas/Natural Earth **local, sem tiles ou downloads em render**, país realçado por ISO numérico, pins projetados por coordenadas (longitude,latitude), rota curada (polilinha explicitamente fornecida pelo roteiro), rótulos separados automaticamente por detecção de sobreposição. O caminho não é rastreamento AIS do navio. País/pin/rota precisam ser factualmente curados antes do render.
2. \`motor4/remotion/src/formatos/FilmeEditorial.tsx\` — novo tipo \`map\` e **uma única barra de progresso global** baseada em \`t/duracao\`, nunca reiniciada entre planos. Preservado o estilo grafite, amarelo e tipografia.
3. \`src/v4/formatos/filme_editorial.py\` — \`validar_mapa\` exige país ISO numérico, centro/escala, localização dos pins e geometria declarada quando a intenção é trajeto; mapas são **\`explainer\`**, nunca vídeo literal. Preparo de props mapa não precisa inventar asset de fotografia.
4. \`src/v4/formatos/contrato_visual_comum.py\` — os mapas entram no contrato comum de referente/intenção/evidência/inspeção pendente. \`src/v4/formatos/direcao_eventos.py\` introduziu verificação opt-in: localizar→mapa de país, trajeto→mapa com rota, demonstrar ação não pode usar foto estática, registro não pode ser imagem representativa, fatos duplicados sem justificativa são bloqueados. **Ainda não é uma IA autônoma que escolhe o recurso:** o storyboard precisa fornecer intenções e evidências.
5. \`src/v4/formatos/tempo_natural.py\` e \`scripts/qa_voz_natural.py\` — gerar voz ANTES do vídeo, medir duração de cada arquivo e derivar as durações das cenas (sem \`atempo\`, sem +10%). Quando a fala ultrapassa 3,8s em cena estática, o motor bloqueia e pede divisão/reescrita em vez de acelerar.
6. \`scripts/qa_montagem_multitema.py\` — auditor aceita mapas sem inventar um ID de fotografia e continua registrando diferença de pixels como sinal técnico, **não prova factual**.

## Prova concreta multitema

\`docs/v4/formatos/qa_mapas_eventos_tres_temas.json\` tem 3 cenas no mesmo Remotion: Taiwan (\`158\`, país destacado + pin), Venezuela (\`862\`, mapa país e dois pins Roraima/Salto Ángel) e Suez (\`818\`, rota esquemática e ponto do encalhe). Os três usam o MESMO componente, não geometrias desenhadas à mão para cada vídeo.

- Fonte de coordenada do encalhe do Ever Given: estudo náutico de trajetória com ponto aprox. 30.016933°N, 32.580171°E (Cambridge, Journal of Navigation); rota do canal é esquemática, não navegação AIS.
- Fonte cartográfica offline: world-atlas/Natural Earth. As coordenadas dos pins são dados do roteiro, não interpoladas pelo renderer.
- 47 testes verdes + compilação TypeScript no **run 44575540939 SUCCESS**; prova narrada 10,467 s (540×960, mono 48k AAC, arquivo de vídeo e contato), artifact \`14557021860\` \`qa-diretor-mapas-voz-natural-progresso-global\`. Voz temporária Edge AntonioNeural, +0%, **sem aceleração**: 3,048 s / 3,456 s / 3,216 s, com pausas 0,24 s, resultando em cenas 3,300 / 3,700 / 3,467 s. \`qa_montagem\` sem bloqueios técnicos, **aprovação humana pendente**.
- Três tentativas anteriores são evidência de bloqueio útil: YAML do workflow com dois-pontos sem aspas, mapa de Suez com zoom local fora do antigo limite e duas frases longas que o sincronizador **recusou acelerar**. Correções genéricas; não afrouxar limite de voz.
- Inspeção visual da folha do primeiro render confirmou progresso contínuo, Taiwan destacado, rota Suez desenhada e boa identidade. Detectou **COLISÃO** entre rótulos de dois pins Venezuela; corrigido em \`placeMapLabels\` (alternância vertical determinística).
- **R2 render** no run \`44576552618\` gerou imagem visualmente limpa e passou auditoria de cenas, mas workflow estrito falhou na comparação de áudio: \`ffmpeg -shortest\` descartou um pacote de ~21ms de AAC ao remuxar. Correção reutilizável: remover \`-shortest\` no workflow \`qa-mapa-rotulos-r2.yml\`. Verificação com FFmpeg local juntando o MESMO vídeo novo e o áudio anterior **sem \`-shortest\`** obteve hash de áudio idêntico (MD5 PCM e SHA256 do AAC) e duração intacta. O arquivo final foi entregue na conversa.
- \`qa-diretor-mapa-r2-final.yml\` de recuperação de artefato falhou com \`Bad credentials\` ao baixar artifact de workflow fracassado (embora a recuperação do artifact da execução com sucesso funcione); por isso a validação reprodutível definitiva deve usar o próprio workflow R2 corrigido e a execução disparada por \`.github/qualidade/mapa_rotulos_r2.txt\`.

## Limitações não mascaradas

- O conjunto de mapas é **demonstração técnica de 3 assuntos, não 3 documentários completos** nem seleção autônoma de cenas/filmagens. Falta integrar diretor à geração diária de storyboard, mapear narrativas em fatos reais e comparar com os filmes anteriores (incluindo risco de repetição e falta de ação).
- A velocidade da voz está natural, mas a **qualidade do timbre ainda precisa de escolha humana/A-B**, pois continua sendo AntonioNeural de teste; Charon/voz de produção NÃO foi alterado.
- Os pins agora não se sobrepõem; porém mapas do world-atlas são estilizados e limitados por resolução geométrica do dado. Nenhuma rota foi apresentada como a trajetória real de um navio.
- Não aprovar/publicar/promover motor por testes verdes; revisão real de cenas com som e visual pelo usuário permanece necessária.

## Próximo passo

Após feedback do vídeo curto, selecionar cenas reais usando intenção e evidência, incluir mapa somente quando a narrativa precisa localizar/percorrer, e testar a escolha automática nos três episódios completos. Manter uma barra global, direção visual variada e métricas semânticas. Avaliar alternativas de voz em amostra A/B antes de trocar voz de produção.
