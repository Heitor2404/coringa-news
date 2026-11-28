# F13 — interface orgânica como cenário de evidência, texto lateral sem reduzir máquina

**Data:** 23/11/2026, 10h15 BRT · **Branch:** `atlas-direcao-visual-20261118` · **Status:** etapa técnica CONCLUÍDA, UI específica do usuário **NÃO** homologada, publicação BLOQUEADA.

## 1. Por que a F13 foi necessária

A F11/F12 aplicava os perfis `ativos_seguros` do `plataformas.json` como máscara rigorosa (aprox. topo 240–280/1920, base 660–672/1920, direita 300/1080). O pipeline registrava até 100% de colisão SIMULADA de correia/volante antes da elevação F12. Isso era uma **auditoria conservadora**, e não detecção dos pixels de uma interface real. Não se deve reduzir artificialmente a máquina para obedecer a um molde de publicidade como se fosse o feed orgânico.

A F13 implementa uma **camada de pesquisa de UI com proveniência clara**, sem extrair pixels de terceiros nem declarar screenshot do dispositivo do usuário.

## 2. Referências externas verificadas no navegador em 23/11

Os números abaixo são reportados pelos terceiros indicados, para um canvas **1080×1920**. Não são interfaces oficiais ou calibração do aparelho do usuário:

| Categoria | Referência | Topo | Base | Ação direita | Evidência |
|---|---|---:|---:|---|---|
| Reels orgânico Android | https://pulkitediting.com/blog/instagram-reels-safe-zone/ | 150 | 280 | 190px desde y800 | Medido em um Android em 20/10/2026; ~45px de crop lateral |
| Reels orgânico cruzado | https://myshorts.in/instagram-reels-safe-zone | 220 | 420 | 140px, início y não publicado | Estimativa Android/iPhone nov/2026 |
| TikTok orgânico | https://bannerpeek.com/tools/tiktok-safe-zone | 200 | 600 | 170px, início y não publicado | Medido pelo autor em set/2026; legenda muda área |
| YouTube Shorts orgânico | https://softphoria.com/tools/youtube-shorts-safe-zone | 180 | 190 | 170px desde y1060 | Medido em iPhone 14 Plus e Galaxy A20s em out/2026, auto-captions off |
| Instagram Reels anúncio | https://quelta.ai/tools/safe-zones/instagram-reels/ | 269 | 672 | 65px lateral | Retranscrição do guia **Meta Ads**, 14% topo, 35% base, 6% lados. NÃO é regra de conteúdo orgânico |

O TikTok Ads Manager confirma que a zona de segurança depende de dimensões, extensão da legenda e outros formatos: https://ads.tiktok.com/resources/help/article/tiktok-auction-in-feed-ads . Não aplicar modelos de anúncios universalmente à publicação orgânica, nem supor que o TikTok/YouTube/Instagram possuam exatamente esses perfis em todas as contas. **Nenhum print de aparelho do usuário foi fornecido.**

No perfil em que a fonte não publicou a posição vertical exata da coluna de botões, o laboratório aplicou uma faixa lateral de altura integral para ser conservador e anotou essa extrapolação no manifesto. Isto não constitui medição do botão real.

## 3. Implementações

1. Novo `src/v4/formatos/perfis_ui_evidencia_f13.json`: 4 candidatos de medição orgânica de terceiros + 1 diretriz de anúncios. Fonte, data, dispositivo, dimensões, tier de evidência e gates de não aprovação.
2. Novo `src/v4/formatos/layout_organico_f13.py`: layout opt-in `hero_lateral_f13` SOBRE a F12, com o **MESMO subárvore SVG do mecanismo** preservada byte a byte. Muda somente texto essencial, para bolso lateral superior esquerdo, com quebra por largura real DejaVu, recusando palavras/frases que não caibam. Compacta cabeçalho escuro decorativo de 134 para **105 px** (correção F13b após prévia da primeira versão). Barra progresso acompanha o novo limite. Não usa escala menor nem pan/zoom.
3. `compositor_cinematico_parametrico_2d.py`: flag `--organico-f13`, opt-in, mutuamente exclusiva com `--hero-f12`; F7, F11, F12 e versão default permanecem intactas. `--transmissao-animada` continua compatível.
4. Novo `qa_ui_organico_f13.py`: medição do risco por deltas de pixels SVG de título, fase, explicação, pistão, biela, volante e correia sobre os cinco perfis. Compara F12 vs F13 em três instantes; emite PNGs privados com retângulos de UI simulados, sem reproduzir imagens de terceiros e sem alegar VLM de telas de app.
5. Novo `tests/test_layout_organico_f13.py` e workflow `.github/workflows/qa-ui-organico-f13.yml`: cobertura das fontes, invariância do rig, segurança de texto por cenário, título fora da zona de ads, três MP4s, hash e bloqueio de publicação.

## 4. Validação F13b final

**Run GitHub:** https://github.com/Heitor2404/coringa-news/actions/runs/45181799651 — **SUCCESS: 48 testes aprovados**; renderizações e auditorias de quadros também passaram. A execução inicial F13 `45181092657` tinha 47 testes, mas ao conferir a prancha havia cabeçalho azul escuro grande demais. Alteramos apenas o editorial, repetimos testes com novo gate para altura do cabeçalho. Não confundir run inicial com o final.

**Artifact privado:** `lab-f13-ui-organica-titulo-lateral-evidencias-privadas`, **ID 14821877016**, expira **28/11/2026 13h15 UTC**. Baixado, MP4s conferidos em bytes e folha real de 12 quadros inspecionada. Contém `QA_F13.json`, PNGs individuais, prancha, JSONs de risco e folhas de contato de 6 perfis (imagem original + 5 overlays). Vídeos **9s, 540×960, 24fps, sem áudio, privados**:

- `BIELA_CURTO_F12_BASELINE.mp4` SHA256 `9fa2f51843219339b870b4d69c5312049e30317d1032d03ff802ce20b0693a72` (**idêntico à F12 anterior**).
- `BIELA_CURTO_F13_TITULO_LATERAL.mp4` SHA256 `86bbdabd2a10a0a69753807bd9e332c57dd0908656bf96af91c1309037117d69`.
- `BIELA_LONGO_F13_TITULO_LATERAL.mp4` SHA256 `524c926201bde5e4d81bb2efaa4eb723307db8e85537fa609ff07c13e51c4726`.

**Efeito mensurado nos cinco perfis simulados:** o título da F12 tinha **100% de pixels sob zonas estimadas** nos quatro orgânicos; com F13, nos três instantes estudados e nos dois rigs, título, fase e explicação tiveram **0% de seus pixels de texto nas máscaras cadastradas**. Para Reels de anúncios, o texto F13 também ficou fora da faixa top conservadora; **isso NÃO qualifica automaticamente o vídeo como anúncio apto**.

**Máquina permanece idêntica em pixels/geométria de atores** entre F12 e F13, mas os riscos de oclusão da própria máquina permanecem:
- TikTok orgânico observado por terceiros: no curso curto, volante até **11,91%** e correia até **19,69%**; no curso longo, volante **12,55%**, correia **21,38%**, biela até **3,98%**.
- Reels orgânico Android observado: volante até **1,33%** em curso longo; principal título sem cobertura.
- Diretriz ads de Reels (bem mais restritiva): volante **37–38%**, correia **51–52%** ainda sob zona estimada. **Não reduzir máquina cegamente para zerar diretriz ads**.
- Esses percentuais são contagens dos pixels de cada papel dentro de regiões matematicamente pintadas; não significam que os pixels sumiriam de fato no player.

## 5. Avaliação visual e limites

A prancha F13b mostra cabeçalho escuro menor, título em duas linhas e fases na área vazia à esquerda. O mecanismo ficou do **mesmo tamanho** e com câmera estável. O resultado é mais organizado para orgânico, mas o conteúdo continua com **estética de diagrama educativo**, e cabeçalho/logotipo da parte superior ainda podem ser cobertos pela própria UI. A diferença está no texto essencial, não na fidelidade industrial ou na capacidade de reconstruir outras máquinas.

**Portão F13:** validação técnica OK; UI orgânica no DISPOSITIVO REAL e estética **PENDENTES**. Sem screenshots reais de Reels/TikTok/Shorts em vídeo local e sem validação do conteúdo visual do compressor, NÃO promover a produção. Não afirmar que 0% simulado é garantia.

## Próximo passo sugerido F14

- Preferir a **mesma composição com referência de interface do próprio aparelho**, registrada com plataforma, build, modelo, texto/legenda e data (por um procedimento explícito; não reusar captura de UI de terceiros como oficial). Se possível usar screenshots anônimas em três feeds para calibrar só regiões de interface.
- Enquanto não houver amostras reais, avançar no núcleo de **reconhecimento e montagem por mecanismo/identidade industrial** (dificuldade mais relevante do projeto). F9 Commons original segue sem hash por 429; referência externa nova só com direitos e arquivos rastreáveis. Não multiplicar exemplos iguais de biela como substituto de generalização real.
- `main`, motor documental produtivo, NTC, DOSSIÊ, Telegram e publicação **não foram alterados**.
