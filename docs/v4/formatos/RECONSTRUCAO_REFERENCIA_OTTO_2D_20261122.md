# Reference-first — primeira reconstrução 2D original baseada em movimento MEDIDO

**Data:** 22/11/2026 · **Branch:** `atlas-direcao-visual-20261118` · **Escopo:** laboratório privado. Não publicar; não integrar ao motor de produção; não usar Claude.

## Por que foi necessário

O `CinematicCutaway3D` deixava compressor e motor quase iguais. A física do mecanismo slider-crank foi implementada, mas a geometria era inventada, válvulas não demonstravam os processos corretamente, e o acabamento 3D foi rejeitado. A solução anterior "usar GIF licenciado como footage" também não era reconstrução. Esta fase implementa uma cadeia concreta, embora PARCIAL, de **arquivo de referência real → rastreamento do movimento → geometria calibrada → vídeo vetorial com desenho próprio**.

## Fonte real e medição não sintética

Fonte: [4-Stroke-Engine-with-airflows.gif](https://commons.wikimedia.org/wiki/File:4-Stroke-Engine-with-airflows.gif), Wikimedia Commons; créditos da página indicam UtzOnBike, Cuddlyable3 e Jahobr, CC BY-SA 3.0 (verificar obrigações antes de publicar qualquer derivação). Original preservado fora do repositório GitHub.

- Origem SHA-256: `ec9238971e2b213b240ca1a707430bf3690a23c1153088cdc22debbe5e672d69`.
- GIF: 48 quadros em 4,8s, duas revoluções do virabrequim.
- Algoritmo genérico em `src/v4/formatos/rastrear_movimento_referencia.py`: template matching OpenCV numa região anotada em `docs/v4/formatos/reference_first/otto_48f_tracker_config.json`. Acompanha pino do pistão em todos os 48 quadros; rejeita arquivo com hash diferente, baixa correlação, pista horizontal incoerente, estático ou movimento incompatível com biela/manivela.
- Marcador ROI anotado **manualmente para esta referência** (bbox 116,154,138,175). Isto não é ainda detecção automática de objetos.
- Correlação mínima observada **0,7940**, média **0,8902**.
- Ajuste geométrico com mínimos quadrados: raio ~**20,6112 px**, biela ~**82,6874 px**, fase ~**0,261799 rad**. Erro médio **0,2265 px** e máximo **0,4526 px** sobre a posição do marcador, em coordenadas da imagem original 265×369. Esses números medem somente a **trajetória do pistão**, não a semântica do mecanismo todo.
- Medição e procedência registradas em `docs/v4/formatos/reference_first/otto_48f_measured_motion.json`; o arquivo registra `valvulas_validadas:false` e `reconstrucao_original:false` porque é rastreamento, não o vídeo final.

## Reconstrução própria e grafo causal

Renderer **novo** `src/v4/formatos/render_reconstrucao_causal_2d.py` (Pillow + SVG CairoSVG + FFmpeg), com geometria autoral do cilindro, pistão, cabeça, biela, rodas, dutos, válvulas e visualização didática dos gases. Renderiza 540×960, 24 fps e 8 segundos (192 quadros), sem áudio. **Não reutiliza os pixels do GIF**.

O mesmo `pose(t,medicao)` deriva ângulo, raio, comprimento de biela e fase calibrados pela imagem real e mantém os pinos conectados; as válvulas e o estado das partículas vêm de **eventos declarativos**, não da mesma timeline mecânica genérica.

`otto_48f_causal_reviewed_scene.json` documenta quatro eventos **REVISADOS MANUALMENTE**, ligados a quadros de comprovação da fonte:
1. 0–11: `admissao_mistura` (válvula de entrada + fluxo);
2. 12–23: `compressao_mistura` (ambas fechadas + volume diminuindo);
3. 24–35: `ignicao_expansao` (faísca no ponto alto + gases expandindo);
4. 36–47: `escape_gases` (válvula de saída + partículas de escape).

**Não fingir que as válvulas foram aprendidas automaticamente:** o mecanismo é reconstruído com trajetória medida e estados revistos manualmente. O contrato no renderer bloqueia `compressor_alternativo` com os 48 quadros e o grafo Otto; compressor precisa **outra referência** contendo seus três eventos corretos e uma revolução do eixo.

## Evidência de execução no GitHub

[GitHub Actions run 45064850172](https://github.com/Heitor2404/coringa-news/actions/runs/45064850172): **SUCCESS**. 

- `tests/test_reference_reconstruction_2d.py`: **10 testes** de fonte, SHA, proporção, 192 estados, conservação de distância de biela, fases e rastreio, rejeição de impostor compressor, frames renderizados e invariantes.
- Arquivo gerado pela própria CI: `MOTOR_OTTO_2D_RECONSTRUCAO_PRIVADA.mp4`. `ffprobe` confirmado 540×960, 24 fps, 8,0s, sem áudio; SHA-256 `e868a5eb0c5cb52d1139195ebe270896c20d2bf96a675270375ad33d0f4a384d`.
- Artefato `14771080933`, nome `lab-otto-48f-reconstrucao-original-2d-privada`, expira 27/11/2026 20h10 UTC.
- Contato de oito frames no artifact: `contato_8_eventos_2d.jpg`.
- Produção em container local também conferida e renderizada. O comparativo lado a lado referencia real vs desenho próprio está em `/mnt/data/reference_first_v2/comparativo_referencia_real_vs_reconstrucao_2d.jpg`. Em nova conversa **verificar caminhos antes de linkar**.

## O que ainda NÃO está resolvido

- Nenhuma IA viu a referência e produziu as quatro fases sem revisão manual; a tentativa anterior de Gemini visual estourou 3 minutos sem resultado e foi desligada por padrão. As relações/valvulação desta prova foram revisadas por pessoa.
- Rastreamento genérico funciona com marcador/ROI anotado, não detecção automática de todos os atores. Não há inferência de topologia de malhas 3D, nem importação de asset 3D de alta qualidade.
- O SVG em si é uma **biblioteca desenhada/procedural de slider-crank**, não desenho autônomo de máquina arbitrária. Não chamar de motor universal.
- Visual técnico 2D foi revisado internamente; **usuário ainda não aprovou estética e usabilidade**. Não publicar ou promover `FilmeEditorial`.
- Não existe ainda referência animada válida de **compressor** analisada com a mesma profundidade. Sem isso, motor deve bloquear e não trocar título no motor Otto para fingir compressor.
- Articulações são calibradas pela trajetória, mas há simplificações de geometria do cabeçote, fluxo gasoso, pressão termodinâmica, momento da ignição, e espessuras das partes; não é simulador de engenharia.

## Próxima execução recomendada

1. Buscar referência ANIMADA de compressor alternativo com válvulas e partículas visíveis (não arquivo Commons estático de 1 quadro); separar prova da peça/ator da prova dos três eventos.
2. Analisar fases por VLM eficiente ou por sinais de imagem com controle independente. Gerar `reference-first-reviewed-scene-v1` automaticamente apenas como **rascunho privado**, com gate físico e semântico.
3. Trocar ROI manual por seleção automática + correlação multiobjeto para válvula, entrada, saída e ignição. Exigir correspondência antes/depois e verificar não associação equivocada de um processo.
4. Renderizar compressor no **mesmo motor 2D**, mas com seu próprio ciclo, grafos e trajetória. Comparar com referência real e não declarar melhoria só por testes sintéticos.

**Importante:** nenhum código tocou na produção `main`, `FilmeEditorial`, NTC ou DOSSIÊ; todas as mudanças são na branch experimental.
