# Último checkpoint real do compressor de oficina — 23/11/2026

**Origem:** vídeo MP4 enviado pelo usuário nesta conversa sob nome `COMPRESSOR_CONJUNTO_2D_PRIVADO(5).mp4`. O vídeo foi efetivamente inspecionado: 8s, 512×910, 30 fps, H.264, sem som. Essas características são da **cópia enviada**, não necessariamente da saída original do GitHub. Não anexamos o arquivo privado ao repositório.

## Identidade visual que deve ser preservada

A animação apresenta **conjunto de compressor de ar**, e não apenas um mecanismo biela-pistão genérico: motor elétrico e correia à esquerda, bomba/cilindro em corte à direita, filtro e entrada no topo, descarga até reservatório horizontal grande embaixo, manômetro, luzes/cores de pressão e movimento no ciclo. Fundo claro quadriculado, cabeçalho azul grafite com marca amarela e título, peças grossas e de alto contraste.

A **imagem histórica** do renderizador `render_compressor_pv_2d.py` (seção 109) serviu de referência editorial para objeto principal grande; **não é o último teste**. A referência mais atual de composição e máquina é `src/v4/formatos/render_compressor_conjunto_2d.py`, cuja família visual equivale à enviada. Não inferir identidade byte a byte sem confirmação.

## Auditoria breve do vídeo recebido

Ao longo de 12 amostras de 0.10 a 7.60s, observam-se etapas:
- expansão residual, com câmara e pressão variando;
- admissão com entrada de ar;
- compressão com volume e pressão mudando;
- descarga pressurizada ao reservatório.

O conjunto é persistentemente visível e domina a região clara da tela, diferentemente do visual antigo de diagrama minúsculo suspenso em tela azul escura. **Ainda não há validação estética final**: necessidade de conferir temporização e legibilidade do resultado em celular, com atenção à curta janela de descarga e à área do cabeçalho. A adequação mecânica industrial ainda é um protótipo ilustrativo, não CAD nem referência automaticamente reconstruída.

## Próxima prova de motor

Fazer `SceneGraph.eventos[].camera.alvos` realmente acionar foco do mecanismo em design contemporâneo equivalente, mantendo o contexto físico e bboxes (filtro, válvulas, câmara, motor, tanque) e bloqueando quando faltarem papéis/ativos. Mesmo critério de proporção, contraste, continuidade e recorte deve funcionar em **outra família física**, sem copiar geometrias do compressor. Não ressuscitar `OpticalProjection`/`LockCausalCycle` como estilo aprovado. Manter `F-VISUAL-LEGADO-DESCARTADO` ativo.

**Fonte de verdade:** upload visto pelo usuário + código atual no ramo de laboratório. **Sem publicação**.
