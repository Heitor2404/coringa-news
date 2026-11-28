# ATLAS — prova F4 da terceira família física: eclusa hidráulica (23/11/2026)

**Status:** MP4 REAL privado gerado. Contrato técnico aprovado; arte **não homologada**.

## Mecânica e direção
Implementação `src/v4/formatos/render_eclusa_hidraulica_2d.py` com base nas sete etapas do grafo `lock_cycle_standalone`. Entrada lateral inferior do cargueiro, isolamento da câmara, abertura da válvula, fluxo por conduto desde a água mais alta, subida da água e do navio com MESMA altitude, equalização, abertura superior, saída completa. Sem fallback para `LockCausalCycle.tsx` legado — o código TS anterior não é importado pelo Python e sua arte rejeitada não é reutilizada.

Visual 9:16, 540×960, cabeçalho azul petróleo + marca amarela, palco hidráulico amplo sobre fundo claro, câmara identificável, duas cotas de nível, conduto com pontos animados e cargueiro ilustrativo. Câmera `plano_geral_travado` (a mesma de compressor e Otto) com 9 bboxes de peças; realce do conduto amarrado ao grafo `valve → conduit → chamber`. Rodapé permanece fixo; testes garantem posição do navio nos limites.

**Atenção à fidelidade mecânica:** representação em **corte lateral esquemático**. A posição dos portões e o desaparecimento de barreiras são abreviações do ato de abrir/fechar, NÃO um modelo de geometria 3D dos portões de mitra ou de operação específica do Canal do Panamá. A função Python `estado()` reproduz a ordem do grafo mas foi reimplementada, não importada do renderizador TS.

## Falha real detectada por inspeção, corrigida
Primeira folha de contato mostrava navio atravessando a parede direita ainda opaca na saída. Adicionadas superfícies de água contínuas ao abrir portões, visibilidade condicionada das próprias barreiras e caminho final do barco após o portão. Teste dedicado `test_portao_superior_aberto_nao_continua_parede_fantasma` protege contra regressão. Os quadros e o vídeo FINAIS já incluem essa correção.

## QA reproduzível
[GitHub Actions 45110717183](https://github.com/Heitor2404/coringa-news/actions/runs/45110717183): SUCCESS, **45 testes** com `tests/test_eclusa_hidraulica_moderna.py`, `tests/test_camera_causal_svg.py`, `tests/test_grafo_causal.py` e `tests/test_realce_causal_svg.py`. MP4 `ECLUSA_HIDRAULICA_MODERNA_PRIVADA.mp4`: 540×960, H.264, 24fps, duração 12.58333s, áudio ausente. SHA256 `f15498d7b6b86834ccd0e186bf4796314a193ade0b46700c886406a67858e322`. Artifact GitHub **14789870582**, expira **28/11/2026 04:16 UTC**. A folha `CONTATO_7_FASES.jpg` e sete frames têm marcos representativos das sete etapas. A diferença de conteúdo físico na câmara é 29.048 RGB em duas fases, sem usar alteração de título como evidência.

## Honestidade de escopo
**Provado:** arquitetura de planejar/validar/salientar atores, relações e enquadramento aplicada a uma terceira família de processo físico, sem voltar ao layout visual antigo.
**Não provado:** criação de 2D/3D a partir de qualquer tema, pesquisa e matching automático de fontes, mecanismo CAD fiel ou estética aprovada em Reels/Shorts/TikTok. Mantida a trava `F-VISUAL-LEGADO-DESCARTADO`. Nenhuma automação de publicação.

**Próxima F5, antes de proliferar renderizadores:** catálogo de primitivos e referências visuais rastreáveis por família + validação de papel e geometria a partir de fontes; evidência visual de que cada ator e mudança de estado aparecem e que portas/objetos não atravessam barreiras. Ajustar estética após avaliação humana, sem fabricar "sucesso" a partir só de testes.
