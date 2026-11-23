# Referência de apresentação visual: compressor P–V de tela cheia

**Recebida do usuário em 23/11/2026** por screenshot de vídeo que contém:
- Cabeçalho grafite-azulado, logo amarelo CORINGA EXPLICA.
- Textos "COMPRESSOR DE AR", "O VOLUME DIMINUI", "As duas válvulas ficam fechadas".
- Faixa superior editorial; abaixo, corte claro e GRANDE do conjunto pistão-biela, volante e válvulas, linhas grossas/metálicas e contraste com fundo azul muito claro.
- Indicadores físicos como "ENTRADA", "SAÍDA" e "PRESSÃO 1.4×"; rodapé técnico, sem caixas genéricas competindo com o desenho.
- Mecanismo ocupa a maior parte da região útil, diferentemente dos 16 frames EUV+eclusa do FilmeEditorial antigo.

## Fonte reproduzível no próprio GitHub

`src/v4/formatos/render_compressor_pv_2d.py` usa o estado `COMPRESSAO_AR` e `SIZE=(540,960)`. Código e geometria originais permanecem acessíveis. A imagem anexada é uma referência de observação; o arquivo de screenshot não foi copiado para o repositório.

**Não confundir** com `src/v4/formatos/render_compressor_conjunto_2d.py` que melhorou a configuração industrial, nem com `OpticalProjection.tsx`/`LockCausalCycle.tsx` cujos frames pequenos e fundo vazio foram rejeitados.

## Regra transversal — apresentação, não máquina fixa

1. A prioridade visual é um mecanismo reconhecível, grande e em destaque, com estados e relações que o movimento realmente explica.
2. Compartilhar regra de ocupação, escala, câmera, hierarquia de textos e proteção de cortes; não compartilhar coordenadas/peças específicas de compressor para outros assuntos.
3. Quando a fidelidade exigir mais peças (motor, correia, tanque horizontal), mantê-las; não regredir à máquina didática simplificada para copiar estética.
4. Não aprovar porque 39/41 testes passaram; é indispensável conferir ação e composição em quadros reais, na tela de celular.
5. `plano_causal.eventos[].camera` deve passar a controlar enquadramento real dos renderizadores, respeitando áreas de UI das plataformas.

**Status:** benchmark visual identificado no repositório; direção final continua pendente. Não publicar automaticamente e não tratar como novo vídeo aprovado.
