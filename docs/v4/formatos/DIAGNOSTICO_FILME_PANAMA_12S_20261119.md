# Filme Editorial — prova Panamá 12 s (19/11/2026)

**Status: NÃO APROVADO PARA PUBLICAÇÃO OU EXPANSÃO AUTOMÁTICA.**
**Branch isolada:** `atlas-direcao-visual-20261118`. Nenhuma mudança em `main`, NTC ou DOSSIÊ.

## O que foi realmente produzido

Compositor novo `motor4/remotion/src/formatos/FilmeEditorial.tsx`, registrado em `Root.tsx`, desligado do antigo ATLAS de slots/mapas/cartões. Contrato no Python `src/v4/formatos/filme_editorial.py`; mídia com procedência e SHA; storyboard `docs/v4/formatos/filme_panama_12s_prova.json`.

O experimento final teve **12,0 segundos, 540 × 960 pixels (escala 0,5, amostra de qualidade, não formato final), sem áudio, sem Claude, sem APIs de imagens, sem publicação**.
- 0–3s: filmagem U.S. Navy transitando pelo Canal do Panamá (arquivo já versionado).
- 3–6,6s: mecanismo 2D da eclusa. A água entra, o nível da câmara sobe e o navio sobe com ela. **Esquema original ilustrativo, não registro real daquela eclusa.**
- 6,6–9,3s: foto real das eclusas de Gatún, março de 1913, Library of Congress.
- 9,3–12s: timelapse real da passagem pelo Canal do Panamá (arquivo já versionado).
- Fonte visual/página/licença em `tests/midia/*.json` e `motor4/formatos/dados/raster/*.json` para demais mídias. Os clipes utilizados são U.S. Navy domínio público e Morrison Mast CC BY 3.0; foto de 1913 domínio público.
- GitHub Actions `44467983265`: `success`, artefato `filme-panama-12s-prova-movimento-privada` (7 dias). Quadro de auditoria: `contato.jpg`, `props.json`, `midias.json`, `contrato.json`, `prova_panama_12s.mp4`.

## Problemas constatados e corrigidos no próprio turno

1. Primeiro experimento Taipei usava seis fotos e mapa sem ação e falhou ao baixar mídia externa (Wikimedia 429); não insistir.
2. Primeiro teste Panamá renderizou cenas full-bleed e vídeo real, mas **reprovado editorialmente**: grande volume de mar/céu na imagem do navio, mapa genérico e foto histórica sem explicar mecanismo.
3. Segunda prova substituiu mapa por **movimento físico do processo hidráulico**; detectadas sobreposições entre título, legendas explicativas SVG e callouts.
4. Terceira prova `44467983265`: removidas sobreposições e legendas repetidas, padronizada fonte sans na animação; render final da AMOSTRA e QA técnico passaram.

## Veredito editorial atual

**Melhor que slides porque tem movimento causal visível na cena da eclusa, mas ainda NÃO é um documentário no nível dos dois vídeos de referência.** O material do navio é distante e mostra a proa/água, não uma ação de eclusa. Os 12 s não têm narração, sincronização, sound design ou montagem contínua completa; não confundir com episódio aprovado.

**Próximo trabalho correto:** escolher footage onde o evento ocorre visivelmente (eclusa/navio entrando/saindo), ou filmagem equivalente verdadeiramente representativa com identificação honesta; refinar a anatomia física da eclusa e a conexão entre objeto real e esquema; avaliar o filme completo e não apenas contagem de fotos, passes e storyboards. Se não houver mídia adequada, **não renderizar 60s**.

## Princípio de arquitetura

Substituir **somente** a direção/montagem, preservando pipeline funcional de roteiro, voz, licenças, legendas, render e Telegram. O compositor não pode pressupor mapa ou fluxo de cards como template obrigatório. Usa filmagem real, comparação, cenas de foto com eventos e mecanismos de engenharia quando a história exige. Aceita representação autêntica de objetos genéricos, mas não implicação de identidade específica falsa. Não promover como motor produtivo sem passar em **dois temas** e avaliação audiovisual explícita humana.


## 19/11 ~12:17Z — V4 NOVA PREVIA, COM PROVA DE AÇÃO REAL + VOZ

Esta seção substitui a avaliação do artefato V3 anterior **para a nova execução**, sem apagar a história de regressões. A prévia V4 é ainda **privada/pendente de aprovação estética**.

- Pesquisadas fontes externas públicas: Pexels 4K encontrado mas HTTP 403 Cloudflare para ingestão automática — **não tentar burlar nem depender desse serviço**; DVIDS funcionou.
- Scout `44518363127` (primeira seleção) e `44518831321` (cinco trechos PD de GATUN e MIRAFLORES). Revisão visual dos próprios clipes mostrou que só o USNS Comfort DVIDS 634226 gravado em 2018 revela os portões/câmara de forma suficientemente legível em vertical; outros têm mar aberto, noite, créditos ou pouco acontecimento.
- Master de **11s 1920×1080**, recortado do DVIDS `USNS Comfort Transits the Panama Canal` (U.S. Navy / J. Keith Wilson, domínio público) a partir da origem ~27s. Master `comfort-2018-meio.mp4`, SHA-256 `3d21204dc0ff2b45298b341b102f0175f32a8c4838dbed7de4efb24cece5b38d`, preservado no artefato Actions `44519739030` (`filme-panama-eclusa-real-1080p-master`, expira em 7 dias). Origem https://www.dvidshub.net/video/634226/usns-comfort-transits-panama-canal . O subtrecho da fonte derivada em **t=3.0–4.5s tinha efeitos solarizados/flash preto e branco embutidos**; EXCLUÍDOS da montagem por inspeção manual de 22 quadros (a cada 0,5s).
- Novo storyboard `docs/v4/formatos/filme_panama_12s_prova.json`: 0–3.0s filmagem t=4.8–7.8s do master; 3–6.9s animação técnica original com água/navio subindo; 6.9–9.4s filmagem t=8.2–10.7s do master mostrando a travessia; 9.4–12.0s fotografia de Gatún em construção em março de 1913 (Library of Congress, domínio público).
- `src/v4/formatos/filme_editorial.py`: aceita somente arquivo de cena privado `stage_hero/` quando tem origem DVIDS e SHA pinado; evento de ação real pode durar 3.9s se o mecanismo possui duas revelações (não confundir movimento real com fotografia estática); conta momentos reais temporalmente distintos em vez de impor número arbitrário de fotos.
- `.github/workflows/filme-editorial-panama-12s.yml` baixa **o master imutável por Actions** (não rebaixa a URL externa a cada render); gera Edge TTS PT-BR **somente como ensaio** (não substitui motor definitivo Gemini sem avaliação), normaliza a -14 LUFS nominal e força 48 kHz AAC; render 540×960 em amostra.
- Run `44520898331` falhou por limite cego de 3.8s na animação; `44521075441` produziu vídeo+voz porém o comando ffprobe e lista de artefatos estavam errados; corrigido. Run FINAL `44522050547` **SUCCESS**, 10 testes Python passaram, render 12.000s, voz gerada 12.67s com fator atempo1.121, arquivo `prova_com_voz_12s.mp4` + quadros de QA publicados **apenas como artefatos privados** (id `14527704984`, 7 dias). A exportação baixada pelo auditor foi remuxada localmente de 96 kHz para 48 kHz sem alterar a imagem, arquivo `/mnt/data/panama_editorial_previa_narrada_12s.mp4`; audio medido ~-14.96 LUFS e pico ~-1.41 dBTP. Corrigido workflow para futuros arquivos saírem nativamente a 48 kHz. Sem publicação e sem outro motor alterado.
- A nova prévia agora tem **ação real da eclusa**, modelo da água elevando o navio, um outro plano real de portão, arquivo histórico e narração, sem solarização. Ainda não está no nível das referências: a animação é um esquema 2D simples, e a filmagem mostra principalmente a perspectiva do navio, não a medição real do nível da água. **Sem aprovação humana.** Não multiplicar novas métricas ou renderizar longos vídeos até conseguir aprovação visual.

**Critério de continuidade:** após rever a nova prévia, melhorar a fidelidade física/impacto da animação, sincronizar quadro/voz por palavras e validar generalização em outro assunto; não trocar apenas fonte ou cor e chamar de solução.

## 19/11 ~12:25 UTC — V5 com material real novo e narração, avaliação independente

- Fonte substituída por clip real HD 1920×1080 **USNS Comfort nas eclusas do Canal do Panamá**, DVIDS vídeo 634226, U.S. Navy / J. Keith Wilson, domínio público; arquivo master SHA-256 `3d21204dc0ff2b45298b341b102f0175f32a8c4838dbed7de4efb24cece5b38d`, guardado no artifact da execução `44519739030` (`filme-panama-eclusa-real-1080p-master`). O canal de produção não foi alterado.
- Roteiro V5 `docs/v4/formatos/filme_panama_12s_prova.json`: t0–3 navio real, t3–6,9 mecanismo hidráulico, t6,9–9,4 outro momento do mesmo master com foco ampliado no portão, t9,4–12 foto histórica de Gatún (Library of Congress). Foram descartados os frames da origem com solarização e flashes próximos de 3–4,5s de conteúdo do master.
- A composição `FilmeEditorial.tsx` deixou de aplicar `opacity:0` nos cortes, eliminando BLACK FRAME em t0/t3/t6,9/t9,4. A nova filmagem usa enquadramento dirigido nos portões, não zoom automático de mapa.
- Run `44523312938`: render de imagem Remotion **concluído**, geração de voz Edge 24k **concluída**, mas mux FFmpeg falhou com `Cannot select channel layout` pelo segundo `aresample` pós-loudnorm. **Não registrar esta execução como SUCCESS.** A falha foi reproduzida e corrigida removendo o segundo aresample e usando `-ar 48000` no encoder (commit `771f19b57093679a2185ec53b59c583c82d8384e`); mux **executado e validado localmente** a partir do mesmo vídeo e mp3 do artifact `14529146959`, sem novo render.
- Artefato final gerado no ambiente de conversa `/mnt/data/panama_v5/panama_v5_narrado.mp4`: 12,000 segundos, 540×960, vídeo H.264, áudio AAC mono 48kHz, ~1,4MB. Verificados 19 instantes reais com OpenCV; luminância média mínima 32,1 (na animação grafite), e média inicial 67,4 (sem quadro preto). Relatório de QA e grade de quadros: `/mnt/data/panama_v5/contato_qa_v5.jpg`, `/mnt/data/panama_v5/cortes_visuais_local.json`. Áudio termina ~0,8s antes do fim, menor que os 1,4s anteriores.
- **Avaliação editorial:** melhor conexão entre ação real e explicação; ainda não equivale às duas referências de qualidade. Esquema simplificado, não mostra eclusa real enchendo em sincronia com imagem e voz; historicamente relacionado, mas ritmo/aparência ainda precisam passar pelo usuário. **NÃO PUBLICAR** nem promover compositor para main. Próximo passo proporcional: audiência da amostra completa com som, comparar a referência A, corrigir apenas o defeito comprovado, depois testar tema 2.

