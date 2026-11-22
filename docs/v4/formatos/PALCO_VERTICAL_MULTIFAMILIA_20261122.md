# ATLAS — prova geométrica de palco compartilhado em duas famílias

**22/11/2026 · LAB experimental, sem IA, sem publicação.**

## Objetivo e escopo
A translação vertical que corrigiu o compressor não pode permanecer um cálculo `354-12-235-7` escondido em um renderer específico. Criou-se `src/v4/formatos/palco_vertical.py` como pequeno solver de geometria usando caixas fornecidas pelos renderizadores, limites editoriais e rodapé. Não detecta caixas em pixels, nem constitui reconstrução automática de máquinas.

**Entrada genérica:** `largura, altura, caixa(esquerda, topo, direita, base), editorial_termina_y, rodape_comeca_y, folga_superior, folga_inferior`.

**Saída:** deslocamento vertical puro `(0, -subida)`, preservando tamanho; se inválido, `F-PALCO-...`. Não reduz o desenho arbitrariamente, não corta peças para "caber". Segurança externa de Reels/TikTok/Shorts permanece `layout.py` + `plataformas.json`, não duplicada.

## Reuso concreto
| Renderizador | Caixa declarada 540×960 | Editorial termina | Folga topo | Deslocamento |
|---|---|---|---|---|
| Compressor completo | x51..492, y342..900 | 235 | 7 | 100 px |
| Motor Otto 4T | x16..524, y273..888 | 233 | 12 | 28 px |

Essas caixas são **conservadoras e anotadas no componente**, não inferidas por CV2. A translação no Otto engloba dutos, válvulas, ar, pistão, biela e volante; a translação do compressor engloba motor, tanque e fluxo. Nenhum dos dois muda física ou processo.

## Evidência
- `tests/test_palco_vertical_multifamilia.py`, `tests/test_compressor_conjunto_2d.py`, `tests/test_reference_reconstruction_2d.py` → **40 tests passed**.
- [CI 45075498191](https://github.com/Heitor2404/coringa-news/actions/runs/45075498191): SUCCESS, render **dois MP4 reais** 8s, 24 fps, 540×960, mudo, seis PNGs por vídeo e `CONTATO_COMPRESSOR_E_OTTO.jpg`.
- Artifact ID **14774779056** até **27/11/2026 22:04 UTC**, contendo `QA_MULTIMECANISMO.json`. Variação média RGB de cena >0 e integridade de arquivos verificadas. **Diferença de pixels não comprova estética nem semântica**.

## Cuidados para evoluir
1. Não confundir solver de palco com uma solução de todos os mecanismos.
2. Adicionar terceira família com eventos realmente diferentes do movimento de pistão/biela (ex.: eclusa, óptica, fluido) **sem hardcode do tema no solver**, ou bloquear corretamente por capacidade indisponível.
3. Testar interface real e legendas antes de integrar a renderização em publicação.
4. Não mexer em `main`, `motor-integral-v4`, DOSSIÊ, NTC, `FilmeEditorial` sem regressão e aprovação explícita.

**Status:** implementação e QA técnico concluídos, aprovação artística e automação visual universal NÃO concluídas.
