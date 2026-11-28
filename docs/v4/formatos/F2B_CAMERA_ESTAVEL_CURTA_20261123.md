# ATLAS F2B — câmera estável em ciclos mecânicos curtos

**23/11/2026 — Correção originada por feedback visual do usuário.** A F2 anterior (8s) criava uma entrada com zoom e leves deslocamentos em cada nova fase: na prática, como a máquina inteira já cabia no viewport, a câmera "flutuava" sem explicar mais nada. Em avaliação humana, isso prejudicou o vídeo.

## Política implementada
`camera_causal_svg.calcular` continua validando o SceneGraph, a ação, os atores, as bboxes curadas e o viewport. Mas para `politica_camera="plano_geral_travado"`, calcula escala e translação **somente pela caixa crítica da máquina inteira**. As saídas `scale`, `tx`, `ty` são independentes de `t`, `inicio_fase_s` e `action`; as ações alteram `active` e `focus_roles`, que seguem presentes para uso por futuros destaques SEM deslocar a câmera. Dois renderizadores Python (compressor de oficina e motor Otto) usam o mesmo algoritmo.

Critérios:
- Máquina inteira dentro do viewport (já incluído cabeçalho/rodapé da prova).
- Sem zoom de entrada, pan por evento ou recorte para "enfatizar".
- Continuar animando fisicamente peças/fases/partículas.
- Ainda que ação mude, transformação SVG idêntica durante o ciclo.
- Tentar alterar `politica_camera` sem nova homologação: `F-CAMERA-POLITICA-NAO-HOMOLOGADA`.
- Em outros tipos de documentário, pan pode ser legítimo **se há mudança real de enquadramento exigida pela narrativa**, não só porque virou a fase. Isso precisa de outro perfil e prova visual explícita.

## Validação
[GitHub Actions 45108070668](https://github.com/Heitor2404/coringa-news/actions/runs/45108070668) — **SUCCESS / 53 testes** e **2 MP4 reais** 8 segundos, 540×960 a 24 fps. Artifact **14788586935**, até 28/11/2026. SHA:
- Compressor `45a848b92ba7da35886590cac856584a1938825875af02a3ca1eeaffa2f4f3a5`.
- Otto `a87764d7d6a4d7cd48df94e8ccec5a4244e67102cda13dde6491be53f591d689`.

A inspeção comparativa de oito instantes do compressor confirmou que motor, tanque e cabeçote mantêm posição na tela. Os detalhes internos continuam animados. Não confundir resultado técnico com aprovação artística final.

**Status:** F2B de câmera estável pronta para revisão privada; não integrada à produção, não publicada.
