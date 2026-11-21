# ATLAS / FilmeEditorial — representação de processos equivalentes (19/11/2026)

## Decisão editorial
**Não exigir que toda demonstração seja gravada no local ou empresa narrada.** Uma imagem pode ilustrar um processo técnico equivalente, mesmo produzida por outra entidade, desde que a narração **não a apresente como registro direto do fato**. Preservar identidade original da mídia, créditos e licença, sem tarja decorativa obrigatória. A exceção **não** autoriza trocar imagens de um acontecimento específico por imagens de outro acontecimento (ex.: guerra, acidente, pessoa, desastre).

## Três modalidades
- **Registro real/literal:** imagem do acontecimento/objeto/lugar específico, cuja identidade foi verificada. Não há uso de mídia externa como prova do evento.
- **Ilustração contextual:** fornece contexto, não prova acontecimentos específicos. Origem identificada, licença verificada e sem falsa atribuição.
- **Demonstração técnica equivalente:** imagem real de processo do mesmo tipo, mesmo quando feita em outra instalação. Requer equivalência técnica e ação inspecionada no clipe original, com origem atribuída; jamais transforma o clipe em registro local.

## Contrato implementado nos módulos existentes
Em `qa_video_fontes.decidir_uso`, um campo `representacao` para `uso=demonstracao` ou `ilustracao` permite processo equivalente quando: 
- `tipo=processo_equivalente`, `processo_narrado` e `processo_midia` com identificadores técnicos **iguais**, não apenas similaridade textual vaga;
- `compatibilidade_tecnica_verificada=true` e `evidencia_inspecao` substantiva;
- `fala_atribui_registro=false` (a narração não diz que a filmagem é de uma entidade específica);
- `origem_no_credito` inclui o nome real da fonte, com licença e procedência verificadas;
- `prova_do_fato=false`, `aprovacao_humana=PENDENTE` mesmo quando a classificação estrutural permite.

`contrato_visual_comum.auditar` passa a mesma regra para ATLAS e FilmeEditorial. No `gate_filme_completo`, a cena `DEMONSTRAR` + `identidade=representativa` exige o contrato de substituição no campo `midia.substituicao` e **também** `prova.processo_verificado` equivalente no catálogo curado. Isso impede aprovar a própria alegação do roteiro. Continuam obrigatórios arquivo local com SHA real, licença comercial, inspeção da ação em vídeo, mapa autentico, não repetição e revisão do MP4.

### Exemplo permitido após curadoria verdadeira
Narração: "A deposição de materiais sobre wafers é uma das etapas da fabricação de semicondutores." Vídeo NIST de deposição, identificado no crédito discreto como `NIST · deposição em wafer`. A filmagem do laboratório americano explica o processo, **não** comprova operações dentro da TSMC. Somente liberar depois da verificação dos quadros, compatibilidade e licença específica.

### Exemplos que continuam proibidos
- Vídeo de **litografia por feixe de elétrons (e-beam)** rotulado como demonstração de **litografia EUV** — processos distintos.
- Imagens da Guerra da Síria para ilustrar uma cena apresentada como registro de ataque ocorrido no Iraque.
- Vídeo NIST em que o narrador diga "Essas são as máquinas da fábrica Fab 18" — falsa identidade.
- Vídeo de máquina parada, zoom ou pan apresentado como prova de fabricação ativa sem atividade identificada.
- Arquivos cujo direito de reutilização ainda dependa de revisão, sem bytes ou SHA verificados.

## Estado de implementação
- Código e regressões em `qa_video_fontes.py`, `contrato_visual_comum.py`, `gate_filme_completo.py`; testes multiassunto com um caso NIST hipoteticamente curado e negativos para trocas técnicas/falsas atribuições.
- **CI 44604655724: 62 testes verdes**, mas a montagem completa de Taiwan continua bloqueada por acervo, documentação e WAV.
- Workflow `qa-curadoria-video-processo.yml` busca **apenas em privado** duas fontes NIST/Kaltura, gera SHA/quadros se disponíveis e nunca integra automaticamente ao catálogo, gera TTS, renderiza filme, publica ou envia ao Telegram.
- A aprovação visual humana de todo episódio é indispensável. O programa não consegue inferir por metadados se a fotografia mostra exatamente a técnica prometida.

## Próximo trabalho
Recuperar vídeos NIST; comprovar bytes/origem/licença/trechos com movimento físico; escolher **qual etapa técnica realmente fica clara** nos quadros; adaptar cena/narração de Taiwan antes de chamar Gemini Charon. Não “inventar” identidade/fatos para completar 27,445 s de uma versão antiga. Depois trazer mapa ATLAS já renderizado, montar prévia privada e submeter ao fiscal por cena e à revisão humana. 
