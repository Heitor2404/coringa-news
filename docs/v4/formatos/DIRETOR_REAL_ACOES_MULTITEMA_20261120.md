# Direção de imagens de ações reais — contrato transversal V2 → V4

**20/11/2026 • branch experimental** `atlas-direcao-visual-20261118`

## O que mudou no motor

Antes, `diretor_roteiro.py` aceitava mecanismos de animação cadastrados e fotos/vídeos de contexto. Para processos físicos novos, como braço robótico, torno CNC ou encadernação, bloqueava porque não existia renderer específico. A saída correta **não** é criar outro desenho qualquer: poder mostrar a **filmagem da própria ação**, quando houver evidência factual e temporal.

`src/v4/formatos/video_acao_real.py` cadastra provisoriamente **vídeos com ações anotadas**, faz consulta com contrato de acontecimento `src/v2/contrato.py` e só retorna candidato se combinar:
1. `acontecimento.id == evento_origem_id` — o MESMO evento, não só tema parecido;
2. fonte citada no roteiro = página original;
3. `acontecimento.dados.acoes_necessarias` = lista de etapas anotadas no vídeo, com ordem exata;
4. cada etapa tem `at` na janela e `fonte_s == inicio_s+at`, descrição observável e SHA do master original;
5. tempo do roteiro corresponde ao tempo da janela (sem acelerar o master);
6. integridade do master por SHA256 e FFprobe; origem no endereço público oficial;
7. direitos e revisão visual continuam **pendentes**. Só `PROVA_VISUAL_PRIVADA`, publicação false.

Se não existir mecanismo nem fonte factual compatível, `R-SEM-MECANISMO`. Exemplos de negação: vídeo de outro rover, roteiro exigindo a pedra claramente se desprendendo (não visível com segurança nas amostras), ações em ordem errada, janela fora do original, mídia não recuperada, fonte com SHA diferente ou licença promovida sem prova.

## Fonte real NASA Curiosity

A página oficial `https://svs.gsfc.nasa.gov/31397/` descreve Curiosity tentando libertar uma pedra da broca. Arquivo oficial `https://svs.gsfc.nasa.gov/vis/a030000/a031300/a031397/PIA26723_figa_1024p2.mp4`; 24,5 segundos, 1024×1024, 5.145.165 bytes, SHA256 fixado `ec6f31a988fff2a54f69ee9e04efbc77557138a63590a338c6cf4e16d9ca8d40`. Aquisição real pelo runner NASA, sem pagar IA, sem imagens inventadas, sem contornar autenticação.

Contatos 12 quadros gerais e 12 dos 10s iniciais. Nos quadros aproximadamente 4,8–7,9s a ferramenta inicialmente está junto à rocha, o braço muda de posição e termina afastado. Os horários Sol registrados no próprio vídeo avançam entre imagens: **é montagem temporal condensada, nunca 24,5s de vídeo contínuo real-time**. A fonte oficial descreve o resultado final, mas o instante exato do desprendimento da pedra **não foi confirmado visualmente** nesses quadros.

O contrato da janela `VIDEO_ACAO_OBSERVADA_NASA_20261120.json` registra somente ações vistas, de 4,5 a 9,3 segundos do original: `ferramenta_sobre_rocha`, `braco_retrai`, `braco_afastado`. Não incluir `pedra_solta_visivelmente`. É curadoria **ASSISTIDA**, com revisão humana ainda pendente.

## Seleção automática e composição

`QA_ROTEIRO_V2_ACAO_CURIOSITY_20261120.json` declara acontecimento, ações, duração de 4,8s e fonte, **sem shots, arquivo, nome de renderer ou keyframes**. O diretor V2 consulta mecanismos cadastrados, depois gravações do evento com etapas reais. `diretor_hibrido.py` aceita `--videos-acao` para biblioteca privada e usa `video_acao_real.montar_cena`; `filme_editorial.avaliar/preparar` mantém o preflight e a checagem de integridade.

O master é quadrado, então `proteger_fonte_integral` e `FilmeEditorial.tsx` preservam a imagem na vertical em `quadro_integral`, sem zoom e sem cortar pedras, broca, braço ou timestamps. Rótulos editoriais foram direcionados à faixa **abaixo** da mídia para não cobrir a telemetria do original. O compositor conserva indicação de `SEQUÊNCIA TEMPORAL CONDENSADA · NASA/JPL-CALTECH`, que **não é** vídeo de tempo real.

`tempo_natural.validar_progressao_video` confere coerência estrutural das anotações e instantes. Isso não substitui conferência dos pixels, mas evita contar zoom ou imagem congelada como ações.

## Prospecção independente em outros domínios — bloqueada por 429

Duas fontes candidatas Commons em `CANDIDATOS_VIDEO_ACAO_REAL_20261120.json`:
- Torneamento em torno CNC, autor Vandurit inserti, CC BY 3.0;
- Máquina de encadernação com cola, autor Balogic, CC BY-SA 4.0.

O workflow `qa-prospeccao-acao-real-commons.yml` validou offline SHA1 histórico, URL, licenças e política de não publicação. **Ambos downloads originais foram bloqueados por HTTP 429** no GitHub. Não há SHA256 real nem quadros inspecionados deles. O workflow foi alterado para executá-los **somente mediante workflow_dispatch**, e nos pushes roda apenas testes offline, respeitando a limitação de acesso. Não declarar esses processos como comprovados nem liberados.

## Limites reais

- Não resolve busca autônoma de mídia em grande escala e nem inspeciona semanticamente qualquer vídeo desconhecido. Eventos/ações e tempos exigem curadoria humana ou ferramentas semânticas validadas.
- Não cria mecanismo físico novo nem adivinha evento pelas palavras da fala.
- NASA SVS não implica permissão universal de reutilização de qualquer arquivo: direitos específicos e verificação de terceiros/endorsement são portões de publicação. Curadoria segue `REVIEW_PENDING`.
- Amostrar frames não comprova todos os eventos. Resultado e tempo real da rocha não podem ser inventados.
- Um MP4 técnico não aprova estética ou narração; sem Telegram ou publicação.
- CI mede execução e integridade, não entendimento histórico nem licenças.

**Próximas prioridades:** ampliar o acervo com fontes realmente acessíveis e permissões verificadas, extrair ações com revisão por intervalo temporal, ligação semântica entre visual e fala, e testar **três temas independentes com originais inspecionados**. Nunca usar um tema de treino como evidência de autonomia geral.
