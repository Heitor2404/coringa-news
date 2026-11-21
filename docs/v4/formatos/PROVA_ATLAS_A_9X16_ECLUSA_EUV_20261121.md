# Prova A no motor Remotion: eclusa e EUV com cena física grande (21/11/2026)

**Status:** laboratório experimental do Coringa documental ATLAS. **SEM publicação**, sem Telegram, sem TTS/legendas finais e sem autorização de integração no `FilmeEditorial`. Não tocar NTC, DOSSIÊ ou `main`.

## Por que foi feita
O usuário **rejeitou explicitamente a direção C** e preferiu A entre os storyboards anteriores. Sua captura real do Reels ilustra que a UI não exige encolher toda a cena; proteger textos importantes e ações essenciais, mas permitir o ambiente ilustrado ocupar a tela. O objetivo é **reproduzir PRINCÍPIOS do visual A dentro do motor**, com ilustração 2.5D original e física conectada, em vez de escolher uma nova direção.

Referência visual da conversa: `Coringa_Storyboard_A_20261121.png`. Trata-se de concept art: inclui números não verificados, representação EUV defeituosa e cenas não prontas para produção; **não se usaram seus pixels como asset de vídeo**, apenas princípios gerais (cores vivas, navio grande, cutaway, tipografia integrada).

## Código IMPLEMENTADO
- `motor4/remotion/src/formatos/AtlasAStudio.tsx`: shell editorial comum das duas famílias. Marca, títulos fortes e etapa/creditos na faixa central conservadora, enquanto o fundo FULL BLEED pertence ao assunto (costa/eclusa vs interior da máquina EUV). SVG vetorial autoral; sem vídeo externo ou importação de imagens do storyboard.
- `motor4/remotion/src/formatos/AtlasAProof.tsx`: duas cenas completas em um mesmo desenho persistente; estados derivados dos **eventos declarados**, não de keyframes independentes. `lockState` calcula `waterY` e `boatShift` do mesmo `fill`; a galeria hidráulica única parte do reservatório e entra na câmara pelo fundo. `euvState` dá progressão de fonte, máscara REFLEXIVA, espelhos e exposição da resina no wafer; raios coloridos são explicativos (EUV real invisível).
- `motor4/remotion/src/formatos/atlas-a-proof.json`: duração 7,8 s, 5 etapas cada, títulos/fonte, papéis de cena e QA `publish:false`, `telegram:false`, `deviceUI:NOT_VERIFIED`.
- `motor4/remotion/src/Root.tsx`: composições `ProvaA-Eclusa` e `ProvaA-EUV`, com IDs sem underscore porque o Remotion rejeita underscores; são **privadas**, não entram no catálogo/produção.
- `tests/test_atlas_a_visual_lab.py`: múltiplos checkpoints de estado físico e limites da UI de `src/v4/formatos/plataformas.json`. Não confundir testes estáticos com a QA visual real.
- `.github/workflows/qa-atlas-a-storyboard-2d.yml`: compila TypeScript, roda pytest, renderiza as duas provas em 540×960 (master declarado 1080×1920), gera folha de 10 quadros e mock de três UIs; guarda MP4s por 5 dias; bloqueia qualquer publicação.

## Iterações da rodada
1. Primeira tentativa confirmou render 2×7,8s, mas o comparativo revelou **objeto pequeno e vazio excessivo no rodapé**, especialmente piso genérico do EUV; não aprovado. Arquivos da conversa `/mnt/data/qa_atlas_a_first/eclusa_A_PRIVADA.mp4`, `euv_A_PRIVADA.mp4`, `contato_inspecao.jpg`.
2. Segundo desenho: cargueiro ampliado horizontalmente por 1,28 e verticalmente por 1,05 **dentro da câmara**, com âncora no nível da água e texto conservado; fundo abaixo da eclusa passou a corte real de estratos do solo com **um único tubo ligado** da fonte ao ponto inferior da câmara, e fundo EUV deixou de usar grid tecnológico, ganhando carcaça de estágio de wafer em plano inferior. É capacidade física ilustrada, não peça copiada de um episódio.
3. Erros de pipeline corrigidos: Remotion não aceita `_` em IDs, teste de “chip pronto” deu falso positivo em comentário explicativo (passou a verificar texto exibido), e workflow precisava instalar `ffprobe`/FFmpeg para gerar contato. Não declarar run final verde até CI realmente concluir.

## Limites assumidos
- Embora seja visual 2.5D e a arte seja autoral, o acabamento pode estar **inferior à concept art A**: aprovar A como referência não significa que nosso desenho SVG já a reproduza com qualidade.
- O design implementa somente duas famílias conhecidas (`gravity_fill` e `reflective_projection`), e não um sistema generativo universal para qualquer mecanismo. O shell é compartilhado; físicas são capacidades separadas. Para temas novos faltam primitivas e fiscal de viabilidade.
- A máscara UI é apenas estimativa; screenshot do editor ou feed não é garantia para qualquer celular/app; atores periféricos podem ficar sob ícones. Teste com legenda/narração real continua pendente.
- A dinâmica EUV é **esquema ilustrativo**; não presume quantidade real de espelhos ou trajetórias internas exatas. “Padrão exposto no wafer” não significa chip pronto após o feixe.
- Água de eclusa sobe por gravidade; os 26m do Lago Gatún **não** são atribuídos à subida de uma única câmara. Sem estatísticas inventadas.

## Gate real
QA do CI + 10 quadros em 5 fases + mock das três redes + opinião estética do usuário **ANTES** de promover um modo visual à produção. Nenhuma entrega posterior é assíncrona. Não substituir a engine ATLAS existente em `main` ou tirar outras provas do repositório.
