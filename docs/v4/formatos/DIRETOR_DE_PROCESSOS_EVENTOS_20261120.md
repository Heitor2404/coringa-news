# Ponte entre direção de acontecimentos e mecanismos — 20/11/2026

## Problema que esta etapa corrige
Até 20/11, `filme_editorial.py` já conseguia selecionar `mechanism: auto` por ações, mas só depois de receber `shots` completos com nome das ações **e segundos de cada cue**. Isso exigia preencher manualmente cada sequência, mesmo com um renderizador e uma máquina de estados já presentes. O antigo `src/v4/formatos/diretor.py` dirige *ATLAS/DOSSIÊ*, não gera esses planos do FilmeEditorial; não foi reutilizado de forma incompatível.

## Implementação
Foi criado `src/v4/formatos/diretor_processos.py`, chamado **pela mesma** função `filme_editorial.avaliar/preparar` quando o JSON contém a chave opcional `eventos_diretor`.

Contrato mínimo de cada acontecimento:
- `id`: identificador único, `duracao_s`: duração dirigida/medida da fala, `lead`, `headline` e `subject`: contexto editorial do referente, fornecido pelo roteiro
- `direcao_evento.intencao = demonstrar_acao`, `fato_id` único e `aprendizado` inequívoco
- `direcao_evento.acoes_necessarias`: identificadores de **ações concretas** em ordem; `fases_necessarias`: macrofases, como origem/transformação/resultado ou entrada/mecanismo/saída

O motor **não** pede `shots`, nome de renderer, `start/end`, `cues`, `tempos` de etapas ou imagens falsas: escolhe a capacidade **real** cadastrada, aplica seu perfil temporal (ajustado à duração informada) e prepara props Remotion. O preflight original verifica novamente ordem, ações, tempos mínimos e prova contextual. Não há chamada externa nem custo por geração.

**Privado apenas:** atualmente exige `tipo: PROVA_VISUAL_PRIVADA`, `publicar: false` e `media: {}` (sem filmagem). Filmes finais têm portões independentes de narração, direitos e aprovação visual. Nunca transformar uma lista de metadados em confirmação de pixels.

## Dois assuntos para testar a mesma ponte
`docs/v4/formatos/DEMO_DIRETOR_EVENTOS_20261120.json` informa dois acontecimentos: projeção EUV com quatro ações (6,9 s) e ciclo completo de eclusa com sete ações (17,5 s). A entrada não determina nome do mecanismo, nem segundo de etapa. A saída do preflight será duas cenas — `optical_projection` e `lock_cycle_standalone` — e uma prévia de 24,4 s, sem áudio/publicação.

## Negativas obrigatórias
Se a pauta trouxer ação indisponível (tornado, triagem logística, outra física), faltar `fato_id`, ação exigida, macrofase, duração, houver duplicação/contradição ou tentativa de publicar sem curadoria, **bloquear** com código `F-DIRETOR-*`. Não substituir automaticamente por animação de palavras, cards ou mapa. A direção editorial deverá buscar gravação real de processo equivalente **verificado**, dividir o beat ou encomendar componente físico com regressão.

## Limites de generalização
1. **Ações estruturadas** precisam ser fornecidas por uma etapa anterior do roteiro: o diretor NÃO compreende por si só texto livre e NÃO verifica os fatos; tampouco criou os objetos e forças para outros assuntos.
2. Os perfis de tempos e rótulos estão cadastrados somente nas capacidades atuais. A duração total do acontecimento continua vindo do roteiro/voz.
3. A área segura está integrada ao ciclo da eclusa por `AreaSeguraMovimento.ts`, mas os demais renderizadores ainda precisam declarar envelope/trajectória para aproveitar a garantia.
4. O vídeo montado continua sujeito à inspeção real e aprovação humana, que um teste de contrato não substitui.

**Decisão técnica:** não trocar de motor, não alterar `main`, NTC ou DOSSIÊ. Somente branch `atlas-direcao-visual-20261118`, sem Claude, Gemini, TTS ou Telegram. O episódio principal segue *Guerra dos Chips EUA × China*; os exemplos são testes de capacidades, não um novo vídeo para postar.
