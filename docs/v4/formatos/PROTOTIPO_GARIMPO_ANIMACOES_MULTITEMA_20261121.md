# ATLAS — Referencias animadas: prototipo de descoberta multitema

**Escopo:** laboratorio isolado, sem publicacao/Telegram/TTS nem alteracao de
FilmeEditorial, NTC, DOSSIÊ ou main.

## O que existe de verdade

- Python: src/v4/formatos/referencias_mecanismos.py.
- Recupera candidatos de **video** a partir de src/v4/acervo_v4.py (nao duplica
  Commons/Archive/Pixabay) de GIFs/vídeos animados no Wikimedia Commons (inclusive baixas resoluções
  para estudo) e de **modelos 3D** via pesquisa publica de metadados
  Sketchfab (nao baixa modelos). Sem cota Claude.
- Gera referencia id, titulo, pagina, meio, declaracao de fonte e marca
  CANDIDATO_SEM_INSPECAO.
- Somente admite planejamento de mecanismo quando existe observacao **em dois
  ou mais quadros** de referencia com lista ordenada de acoes/fases visiveis.
- O planejamento de reaproveitamento usa src/v4/formatos/catalogo_mecanismos.py.
  Se a capacidade nao existe, sinaliza lacuna, sem fabricar objeto SVG ou
  declarar video aprovado.
- A funcao extrair_quadros opera em arquivo de video LOCAL, usando ffmpeg/
  ffprobe para gerar cinco stills com hash de origem. Esses quadros **ainda
  precisam ser interpretados por um revisor de visao**; esse modulo nao diz
  que detectou uma sequencia de acontecimentos sozinho.

## Executar o garimpo

python -m src.v4.formatos.referencias_mecanismos docs/v4/formatos/briefs_referencia/motor_pistao.json saida_referencia/pistao
python -m src.v4.formatos.referencias_mecanismos docs/v4/formatos/briefs_referencia/circulacao_cardiaca.json saida_referencia/coracao

O comando faz busca real, registra candidatos e gera planejamento.json:
normalmente REFERENCIA_SEM_INSPECAO. Isso é CORRETO: achar um video pelo titulo
nao prova a operacao. Sem rede: use --sem-rede.

## O que ainda nao existe (nao fingir)

- Captura automatica de todos os candidatos em 2D/3D com uso verificado.
- Analise multimodal em lote que transforme frames em eventos auditados.
- Importacao/rigging de modelos 3D e animacao controlada deles.
- Compositor causal universal 2D/3D e avaliacao automatica de qualidade.
- Uma animacao final de pistao ou coracao, montada sem novo codigo.
- Resultado visual 9:16 novo ou prova de retorno financeiro.

**Proxima entrega de engenharia:** conectar triagem multimodal a extracao
de quadros, salvar observacoes verificaveis (evidencias com timestamps) e
gerar planejamento de cenas compatível com o diretor existente. So depois
testar reconstrucao automatica da primeira familia com dois assuntos
diferentes, sem editar TSX por episodio.

Fontes de pesquisa: Commons/Archive ja existentes no acervo V4.
Sketchfab Data API /v3/search (metadados); downloads exigem autorizacao/
autenticacao quando aplicavel. NASA 3D Resources e Smithsonian Open Access
sao alternativas de catalogo 3D a integrar apos prova de busca.

## Revisão após primeiro teste de rede

No primeiro run live, a pesquisa original retornou 0 candidatos para pistão
 e 1 vídeo histórico para circulação cardíaca, 0 modelos 3D. Isso mostrou que o
acervo V4 prioriza footage documentário e perde animações técnicas curtas.
A revisão adiciona MediaWiki Commons (GIF/WebM/Ogg/MP4) sem filtro de resolução
para USO COMO REFERÊNCIA e encurta termos Sketchfab por ator relevante.
A busca real precisa ser reexecutada; nem GIF nem modelo localizado significa
reconstrução validada.

## Resultado do segundo experimento com rede (21/11, run 44940270620)

**CI SUCCESS**, 9 testes sem rede mais pesquisas reais sem Claude/Gemini. Artifact privado
`14721114225`, expiracao `2026-11-24T19:19:25Z`.

- **Pistão:** 8 candidatos: 2 GIFs de Wikimedia Commons (Denis Papin piston anim.gif e Cshaft.gif) e 6 modelos Sketchfab. O primeiro e piston historico a vapor, **nao comprova ciclo de quatro tempos**; modelos como Sticky Piston Minecraft são resultado irrelevante. **Nenhum item validado semanticamente.**
- **Coração:** 8 candidatos: 1 video historico do Internet Archive (Heart and Circulation), 1 GIF Commons (Real Human Heart Turntable.gif) e 6 modelos Sketchfab. O GIF e uma rotacao de modelo anatômico, **nao prova movimento do sangue pelas valvulas**; varios itens 3D com palavra heart no titulo nao sao anatômicos. **Nenhum item validado semanticamente.**
- A busca foi ampliada com Commons GIF/WebM/Ogg/MP4 e palavras-chave 3D curtas. Isso **melhorou descoberta, nao a qualidade nem a capacidade de render**.

**Proximo portao real:** salvar quadros amostrados dos GIFs/clipes, analisar as imagens/etapas com revisao visual e classificar `RELEVANTE_COMPROVADO`, `PARCIAL`, `IRRELEVANTE` por acoes observadas; nunca selecionar modelo so pela palavra heart/piston. Depois testar reconstrucao via operador reusavel/asset validado. Nao publicar; nenhuma animacao nova do motor foi produzida nesta etapa.
