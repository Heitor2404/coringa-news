# Vídeo real no diretor híbrido V2 → biblioteca V3 → FilmeEditorial V4

**Data:** 20/11/2026 • **Branch:** `atlas-direcao-visual-20261118` • **Situação:** QA privada, sem licença comercial liberada.

## Por que esta etapa existe

A etapa anterior renderizou **foto autenticada do Commons → mecanismo EUV**. O próximo gargalo era a seleção de um trecho real de vídeo, sem repetir a falha clássica: inserir um clipe institucional de outra instalação e fazê-lo parecer comprovar o fato ou processo da história.

A fonte pré-existente na V3 é `nist_nanofab_users_2017`: vídeo NIST (Kaltura oficial, original de 105,05s, 1360×720, SHA `582ee5ea387fae4b424ac08c85a33840fd8a44bc681f136ebbe1f76b8723c474`). Autorias/terceiros/direitos do item **PENDENTES**; origem institucional não significa livre reutilização comercial. Documentado desde 19/11 em `INSPECAO_NIST_NANOFAB_USERS_20261119.md`.

## Como o motor agora usa a fonte

1. O arquivo `src/v4/formatos/inspecionar_janelas_video.py` parte dos bytes originais e exige SHA igual ao acervo. Gera quadros com timestamps reais e simulação de crop **central não aprovado**; isso é prova de que o corte foi observado, não confirmação de ROI/habilidade do processo.
2. O novo `src/v4/formatos/video_contextual_v3.py` lê um inventário **separado do roteiro** (`VIDEO_CURADO_PRIVADO_NIST_20261120.json`) contendo ID do acervo, página de origem, direitos, SHA real, janela temporal original e ROIs observadas. Confere original via SHA e FFprobe. Permite provedores institucionais cadastrados (NIST/Kaltura, DVIDS), mas sem fingir que um download indisponível está disponível.
3. Esse inventário gera um candidato **somente em memória**, sem promover sua licença na Biblioteca V4: `prova.midia_corresponde` identifica visualmente o referente NIST, **não** comprova a ação narrada e **não** prova direitos.
4. `diretor_hibrido.py` recebe opcionalmente `--videos-curados`, consulta o catálogo agregado por **sujeito do contrato V2**, e monta `photo | video | mechanism` no **mesmo** FilmeEditorial. O roteiro original não informa o arquivo, o nome do renderer, o tempo de origem nem o bbox.
5. O preflight `filme_editorial.py` reaproveita `planejar_enquadramento_video`: valida que a área essencial observada cabe no 9:16; compara SHA da ROI com o vídeo; verifica que cada `fonte_s` corresponde ao mesmo instante da origem; rejeita zoom que cortaria o referente; checa a janela temporal (não pode avançar além do master).
6. O arquivo original é ingerido em `stage_documental/` **somente na QA**, por `coletar_videos_publicos.baixar_fonte`, usando Kaltura/portal institucional já homologados como origem. Não modificar, recodificar ou trocar SHA para fazer o teste passar.
7. O render lê o clipe original e o exibe **mudo**, com rótulo de laboratório independente. Direitos continuam `REVIEW_PENDING`; não há publicação ou Telegram. A aprovação factual/visual humana permanece pendente.

## Teste multiformato sem pré-seleção no roteiro

`QA_ROTEIRO_V2_HIBRIDO_NIST_20261120.json` tem 3 cenas:
- Fab 18: foto real contextual autenticada do Commons, mostra **fachada em Taiwan**.
- NIST NanoFab: vídeo real de trabalhador em estação/laboratório nos EUA, janela inspecionada no original, **não é TSMC nem demonstra EUV**. A origem precisa aparecer nitidamente como NIST.
- Mecanismo óptico: ilustração EUV original, com fonte ASML. A ilustração não é continuação da filmagem institucional e não prova equipamento naquela sala.

A transição é **contextual**, não uma tentativa de fazer parecer que vemos a máquina da TSMC. Quando os elementos/tempos do processo não correspondem ao filme de origem, **não criar correspondência falsa com zoom ou morph**.

## Bloqueios que devem permanecer

- Original ausente/diferente: `V-CURADORIA-AUSENTE`, `V-CURADORIA-SHA`.
- Direitos fora de `REVIEW_PENDING`: `V-CURADORIA-DIREITOS`.
- Proveniência ou quadro não identificado: `V-CURADORIA-ORIGEM`, `V-CURADORIA-QUADROS`.
- Janela/ROI inválidos: `V-CURADORIA-JANELA`, `V-CURADORIA-ROI`, ou preflight `F-ROI-NAO-CABE`.
- Duração maior que trecho curado: `H-VIDEO-JANELA`.
- Vídeo repetido fingindo nova prova: `H-VIDEO-REPETIDO`.
- Registro histórico só com contexto de outro acontecimento: `H-VIDEO-REGISTRO-ESPECIFICO`.
- Qualquer tentativa de publicação sai bloqueada antes de render.

## Limitações reais da arquitetura

- Cenas físicas ainda dependem de **mecanismos implementados**. O motor não cria física para qualquer assunto novo.
- Seleção do candidato por sujeito não substitui curadoria das **janelas originais e dos direitos**; a janela foi inspecionada, não gerada semanticamente a partir da fala.
- A biblioteca de vídeos por ação ainda é pequena e sem aprovação comercial. Não afirmar "vídeos reais curados para postar" por termos e SHA.
- A composição ainda não dispõe de ponte audiovisual semântica plenamente automatizada, nem narração sincronizada. Isso é um QA técnico.
- A política de não cortar sujeitos opera com ROI declarada e rejeita bboxes que não cabem; a presença/posição real nos pixels exige revisão humana.
- Não modificar main/NTC/DOSSIÊ; nem chamar Claude/Gemini.

**Próximo grande passo:** provar em múltiplos provedores/temas a classificação de cenas V2 + descoberta de clipes adequados + direitos + seleção de momento + ROI + continuidade editorial, sem falsa equivalência de eventos. Até lá, os candidatos com direitos pendentes permanecem restritos à prévia privada.
