# ATLAS — Reference First (22/11/2026): pesquisa, quadros, processo, fallback licenciado

**Branch experimental:** `atlas-direcao-visual-20261118`. Sem Claude, sem Telegram, sem publicação, sem promoção ao FilmeEditorial. Esta implementação é parcial e não é um motor universal de replicação.

## Diagnóstico confirmado

O visual antigo `CinematicCutaway3D` trocava título, cor, portas e uns elementos, porém compartilhava a mesma cinemática de pistão-biela-virabrequim. Não demonstrava válvulas/fluxo completos de compressor ou motor Otto 4 tempos (duas revoluções e ignição). Portanto motor e compressor tinham, de fato, praticamente o mesmo vídeo. Bloquear esse renderer para ambos os processos integra o novo contrato e é mais honesto do que apresentá-lo como solução.

## Componentes executáveis

- `src/v4/formatos/garimpo_reference_first.py`: reaproveita `referencias_mecanismos.descobrir()` (acervo V4, Commons, Sketchfab) mas procura por PROCESSO, não só 'piston'; filtros fracos de título eliminam Minecraft, diesel confundido com Otto, elétricos, corações; sinaliza licença NC/ND, modelos 3D sem malha/rig e mantém todos os candidatos como NÃO INSPECIONADOS. CLI com `--rede`, sem chamadas automáticas na importação.
- `src/v4/formatos/referencia_temporal.py`: aceita arquivo GIF, MP4, WebM ou MOV LOCAL. Exige 10 a 20 amostras, por padrão 12; GIF com poucos frames/repetido bloqueado; para vídeo usa ffprobe/ffmpeg. Salva SHA-256 da origem e de cada JPEG, tempos/ordem, verifica tudo novamente antes de usar visão.
- `src/v4/formatos/reference_first.py`: dois contratos diferentes. Compressor: ar entra, pistão comprime válvulas fechadas, ar sai por válvula de descarga; motor Otto: admissão de mistura, compressão, ignição/expansão, escape, com sinais de válvulas. Quando só houver pistão e biela, NÃO classificar como processo completo. Produz grafo causal provisório (atores, juntas, ordem, evidências antes/depois) sem gerar geometria. A IA NÃO aprova a cena; a revisão humana e capacidade renderer continuam pendentes.
- A visão (`src.gemini.json_visao`, já presente) requer **opt-in** CLI `--usar-gemini`, nunca é executada silenciosamente só porque existe uma chave; agora consolida 12 frames em UMA prancha visual numerada para reduzir chamadas. Resposta VLM incompleta, 429, cota ou latência = bloqueio.
- `src/v4/formatos/render_referencia_licenciada.py`: **modo de fallback editorial** que adapta GIF já licenciado como clipe 9:16 com capítulos e créditos a partir de dados (não há posições por episódio). Requer hash da origem, título, autores, licença permissiva conferida manualmente, eventos ordenados e `publicar=false`. Esta saída é adaptação de mídia existente, não reconstrução original 2D/3D; marca como privada e grava créditos completos em arquivo lateral.
- `tests/test_reference_first.py`, `tests/test_garimpo_reference_first.py`, `tests/test_render_referencia_licenciada.py`: verificação offline de mídia adulterada, ausência de frames, falsa identificação de motor/compressor, valvulação/fluxo, engine diesel confundido, licença NC, e vídeo privado com áudio ausente.

## Prova com fontes externas reais

**Compressor:** [Compresor alt frig1.gif](https://commons.wikimedia.org/wiki/File:Compresor_alt_frig1.gif) de Miguel Rodriguez Sanmartin, declarado domínio público. Download da origem funcionou, mas o arquivo é GIF com **1 quadro**, não animação! Foi corretamente REJEITADO. Relatório `comprovacao_fonte_real.json`, run 45060056512.

**Motor Otto:** [4-Stroke-Engine-with-airflows.gif](https://commons.wikimedia.org/wiki/File:4-Stroke-Engine-with-airflows.gif) — UtzOnBike, Cuddlyable3 e Jahobr; CC BY-SA 3.0 e histórico GFDL. Arquivo ORIGINAL 48 frames de 4,8s, SHA-256 `ec9238971e2b213b240ca1a707430bf3690a23c1153088cdc22debbe5e672d69`. Download funcionou no run [45060221935](https://github.com/Heitor2404/coringa-news/actions/runs/45060221935); **12 JPEGs reais e 11 intervalos com mudança visual**. Inspeção humana destes quadros identificou admissão amarela, compressão, ignição vermelha/expansão e escape, além das válvulas e biela; o material é uma referência mais apropriada que nossos vídeos procedurais bugados.

A chamada à visão Gemini desse run **EXCEDEU TIMEOUT DE 3 MINUTOS**, portanto NÃO houve resultado semântico de IA. O job geral foi verde porque a tarefa de visão foi marcada `continue-on-error`. Não contabilizar como 'Gemini comprovou 4 tempos'. A nova entrada compacta e opt-in foi feita para evitar novo consumo involuntário.

Foi produzido no ambiente da conversa um **vídeo privado de 7,67s** (540×960, sem voz) adaptando esse GIF real com fases legíveis e marcação de licença. Arquivo `/mnt/data/reference_first_otto_referencia_privada_20261122.mp4`. Esta é referência adaptada, NÃO criação de uma animação nova. Dados de origem e quatro etapas em `docs/v4/formatos/reference_first/otto_48f_prova_privada.json`. Checar existência do sandbox path em outro turno antes de linkar.

## Uso futuro

```bash
# 1. Busca remota (status candidato, não prova)
python -m src.v4.formatos.garimpo_reference_first compressor_alternativo saida/busca.json --rede

# 2. Amostra local de uma referência realmente ANIMADA (12 quadros + SHA)
python -m src.v4.formatos.reference_first amostrar arquivo.gif saida/frames --referencia-id exemplo-01

# 3. Visão opt-in, via Gemini + caixa, nunca automaticamente
python -m src.v4.formatos.reference_first inspecionar saida/frames compressor_alternativo saida/relatorio --usar-gemini

# 4. Caso asset esteja licenciado e aprovado manualmente, fallback 2D licenciado privado
python -m src.v4.formatos.render_referencia_licenciada arquivo.gif plano_revisado.json saida/preview.mp4
```

## Próximos portões e limites

1. Encontrar referência genuinamente animada de COMPRESSOR, com válvulas e admissão/descarga VISÍVEIS (o 1-frame Commons não serve), direitos claros. Não supor que modelo Sketchfab baixe/tenha rig.
2. Obter análise multimodal que funcione com prancha curta, testar contra anotações humanas e eventos temporais reais. A IA ainda não foi validada em vídeo externo.
3. Criar operador `scene-graph -> objetos / valvulas / fluxos` para um 2D realmente bonito e confiável, ou importar modelo 3D adequado, rigorosamente diferenciado do motor Otto; QA de estados + motion antes/depois.
4. Comparar referência real e reconstrução própria em vídeo, na mesma escala, com áreas seguras por papel. Se referência não cobre etapas, BLOQUEAR.
5. Licença CC BY-SA exige atribuição e compartilhamento de adaptações nos mesmos termos; não publicar a prévia sem conferência jurídica/editorial. Nenhum material de terceiros foi mesclado na produção.

**Critério:** códigos e testes verdes indicam que o fluxo não mente sobre o que sabe. Ainda falta a etapa central de RECONSTRUÇÃO automática 2D/3D a partir da referência. Não confundir o fallback licenciado com esse objetivo.
