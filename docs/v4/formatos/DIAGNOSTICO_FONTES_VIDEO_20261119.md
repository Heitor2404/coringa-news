# Diagnóstico de aquisição de vídeos institucionais — 19/11/2026

**Regra do motor:** fonte institucional não vira prova audiovisual só por ter título, descrição, domínio público declarado ou arquivo decodificável. O acervo V3 registra candidatos com SHA e verificação de integridade. Curadoria de acontecimentos, direitos específicos, seleção de trechos e revisão humana continuam separadas.

## Tentativa executada: DVIDS
Fontes verificadas publicamente:
- Tobyhanna Army Depot, **Microelectronics**, vídeo 1029228 (104 s), Ryan Beilman, https://www.dvidshub.net/video/1029228/microelectronics
- DARPA, **NGMM**, vídeo 995636 (109 s), Tom Shortridge, https://www.dvidshub.net/video/995636/ngmm-next-generation-microelectronics-manufacturing
- Aviso de direitos https://www.dvidshub.net/about/copyright: páginas marcadas PUBLIC DOMAIN, mas direitos de terceiros, imagem e voz de pessoas, marcas, símbolos, proibido implicar endosso e advertência específica permanecem relevantes. Nem toda obra DVIDS é automaticamente reaproveitável sem revisão.

**Run 44616948714 SUCCESS como teste do coletor, mas nenhuma mídia recuperada:** dois downloads 1280×720 retornaram **403 Forbidden** (`download/videofile/10494611` e `download/videofile/10069508`). `baixados=0/2`, `aprovados=0`, `publicados=0`. Artefato 14574434558 guarda somente relatório e banco vazio; **não** contém MP4. Não reexecutar o mesmo acesso esperando sucesso. Não tentar contornar autenticação do DVIDS. Sem arquivo, sem SHA do conteúdo, sem inspeção de quadros.

## Alternativa oficial: NIST/Kaltura
- Página de origem https://www.nist.gov/video/cnst-nanofab-through-users-eyes
- Player oficial público `https://www.kaltura.com/p/684682/embedPlaykitJs/uiconf_id/55674542?entry_id=0_emhevqw5&iframeembed=true`, obtido a partir do vínculo da página NIST.
- Vídeo institucional de 2017 com entrevistas e imagens sobre NanoFab. Ainda não se sabe se mostra equipamentos trabalhando de modo adequado para explicar fabricação de chips.
- Política NIST https://www.nist.gov/copyrights-disclaimers: regra geral sobre conteúdos do governo com ressalvas para materiais de terceiros. Depoimentos e áudio/trilha precisam revisão específica.
- Receita versionada `docs/v4/formatos/CANDIDATOS_VIDEO_NIST_NANOFAB_20261119.json`. Teste de recuperação via `yt-dlp` no Kaltura oficial iniciado; **não declarar aprovação nem dizer que recuperou até ter relatório e SHA reais**.

## Mudança reutilizável do motor
- Novo `src/v4/formatos/coletar_videos_publicos.py` implementa **etapa de prospecção** com provedores explicitamente validados: DVIDS e NIST/Kaltura, origem HTTPS institucional, identificador original, fluxo sem IA, teto de download, `ffprobe`, folha de 12 quadros, SHA-256 real e entrada candidata na **Biblioteca V3 existente** (não um segundo acervo). Nenhum sinalizador `acao_fisica_comprovada` ou `publicado` pode ser `true` automaticamente.
- `tests/test_coletar_videos_publicos.py` verifica erros de origem, direitos, cache/duplicação por SHA, HTTP 403 e apresentação negativa em vários temas, além do adaptador NIST.
- `.github/workflows/qa-coleta-videos-institucionais.yml` usa a mesma etapa para qualquer provedor/tema. A execução escolhe uma fonte por receita sem uma versão por episódio. O primeiro ajuste de seleção quebrou o YAML do workflow (jobs vazios); o arquivo foi **reescrito** no commit 4dfdc61444e201c00b566f3330f9fa42d6e6b7f1 e relançado.
- **CI principal 44617523766 SUCCESS: 132 testes**, mapa original 1, fotos Commons 2/3, Taiwan com 9 bloqueios, nenhum vídeo de ação curado.
- Nenhuma alteração em `main`, NTC, DOSSIÊ. Nenhum custo Gemini, Charon, render final, Telegram ou publicação.

**Próximo aceite:** um MP4 ORIGINAL recuperado (SHA real), folhas de contato legíveis e seleção manual de trechos que demonstrem movimento físico adequado; depois validação dos direitos específicos. Sem isso, os vídeos não entram no catálogo comprovado e o gate mantém o bloqueio.
