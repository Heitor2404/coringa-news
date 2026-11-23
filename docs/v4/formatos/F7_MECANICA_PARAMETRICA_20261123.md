# ATLAS F7 — Biela-manivela paramétrica e núcleo mecânico compartilhado

**23/11/2026 · branch experimental `atlas-direcao-visual-20261118` · QA privado · não publicar.**

## Problema atacado

Na F6, cinco tipos hidráulicos tornaram-se desenho por parâmetros. A F7 buscou a mesma prova para a mecânica: não bastava haver 29 etiquetas de atores do F5. É preciso que raio de manivela, comprimento da biela, diâmetros de polias e tamanhos do pistão mudem a geometria visível sem copiar código por vídeo.

## Código e contratos compartilhados

**`src/v4/formatos/cinematica_biela_manivela.py`** resolve exatamente o elo rígido: posição do pino da manivela `x_e + r sen θ`, `y_e − r cos θ`; cursor `y_p = y_e − r cos θ − sqrt(L² − r² sen² θ)`. A distância Euclidiana entre juntas deve ser sempre `L`. A razão de velocidade para polias ideais é `ω_m / ω_v = R_v / R_m`; sem escorregamento, folgas nem perdas. Este módulo NÃO modela válvulas, termodinâmica ou combustão.

Compressor (`compressor_pv_core.py`) e Otto (`render_reconstrucao_causal_2d.py`) foram migrados para esse único núcleo. O rotor (`render_compressor_conjunto_2d.py`) delega à primitiva genérica com cores, raios e quantidade de hastes originais. Os estados P–V do compressor e a medição da referência Otto permanecem distintos.

**`src/v4/formatos/primitivas_fisicas_parametricas.py`** ganhou rotor, pistao, biela e transmissao_correia. Assim, os cinco tipos hidráulicos da F6 se tornaram **8/13 classes visuais desenháveis**: rotor, piston e transmission novos (biela e correia são variantes de transmission). A correia usa tangentes externas reais para dois círculos com raio parametrizado. Entradas inválidas/cor não hex/NaN/sem tangência/peças fora do viewport bloqueiam, sem placeholders e sem SVG de terceiros.

**`src/v4/formatos/compositor_cinematico_parametrico_2d.py`** monta uma cena a partir de JSON e das mesmas funções; políticas: a câmera fica estática; papéis do grafo causal `slider_crank_parametrico` devem estar presentes; curso do pistão deve caber dentro do cilindro; distância entre polias deve permitir correia; todas as juntas móveis derivam da ÚNICA pose cinemática. Sem uso de modelo externo/3D/licença de imagem presumida. Cabeçalho e rodapé fora da transformação.

**Duas cenas JSON**, sem outro renderizador: `cenas_parametricas/biela_manivela_curso_curto.json` (raio de manivela 46px, curso 92px, L=175px, polia motriz 27px, roda movida 74px); e `biela_manivela_curso_longo.json` (raio de manivela 64px, curso 128px, L=186px, polias 27px / 80px). São escalas didáticas, não dimensões industriais reais.

## QA e prévias REAIS

[GitHub Actions **45117061112**](https://github.com/Heitor2404/coringa-news/actions/runs/45117061112): SUCCESS, **85 testes**, 11 warnings Pillow; inclui regressão do compressor, Otto, F6, eclusa, SceneGraph/câmera e nova cinemática em 216 amostras por rig.

Cada vídeo: **H264 540×960, 24fps, 9 segundos, mudo**. Hash SHA256 de arquivos extraídos e verificados localmente:

- `BIELA_CURSO_CURTO_F7.mp4`: `9dd2ec0e0f58b874f710774c1c4bf7a2dc982c45bcaa6747a0ea1a30367b71e3`.
- `BIELA_CURSO_LONGO_F7.mp4`: `1274cc979c6ae3c349db73902f600e0a0bef3f8fd0ce8fc0daa2d216d0300ef3`.

Artifact **14792495211** (`lab-f7-mecanica-biela-manivela-dois-rigs-privados`) até 28/11/2026 05:20 UTC: vídeos, JSONs, oito PNGs e `COMPARACAO_F7_2_RIGS_8_QUADROS.jpg`. Diferença física comparada no ROI: **18,650 RGB** para curso curto e **20,841 RGB** para longo, não apenas texto animado. Teste inicial 45116857946 (83/85) falhava porque contador correto 01/02 → 02/02 alterava o ROI do rodapé; alterada só a comparação para preservar região imóvel, agora passa.

**Inspeção visual:** no início/segundo quarto/metade/final as partes estão legíveis e biela e pistão acompanham o mesmo virabrequim; linha de correia parece coerente; máquina ocupa boa parte do quadro 9:16, sem os diagramas antigos em fundo grafite. Contudo o estilo ainda é PROTÓTIPO esquemático; não verificamos contra imagem/fotografia de mecanismo real, não certificamos identidade visual nem testamos a UI das redes. Não publicar.

## Limites e próxima fase

**Provado:** reuso da cinemática e dos desenhos entre mecanismos existentes e dois rigs configuráveis; três classes mecânicas de primitives incorporadas; manter câmera travada. **Não provado:** compositor universal que reconstrói qualquer mecanismo, busca automática de referências, 3D, biblioteca licenciada de componentes ou estética pronta para postar. F5 mantém histórico de 29 papéis e 3 famílias certificadas; F7 é laboratório adicional.

**Próximo passo:** catálogo de referência VISUAL licenciada vinculado a cada primitiva e sua âncora real, teste de novos temas em duas famílias distintas sem renderer bespoke, detectar colisões/oclusões/cortes em imagens reais e área segura em interfaces Reels/TikTok/Shorts; evoluir sem reviver layouts rejeitados. Sempre atualizar docs/CONTINUIDADE_PROXIMO_CHAT.md a cada etapa.
