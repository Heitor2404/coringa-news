# Protótipo Remotion (Módulo F da V2) — avaliação, NÃO faz parte do pipeline

A mesma composição `numero.animado` da V2 reescrita em React/Remotion, para comparar com o palco atual.

```bash
cd prototipos/remotion && npm install && node render.mjs saida/numero_remotion.mp4   # Remotion
cd ../.. && python prototipos/remotion/comparar.py                                   # palco V2, mesmo trabalho
```
`render.mjs` usa o chrome-headless-shell do Playwright (variável CHROME para outro caminho).

Resultado em 13/11/2026 (2 núcleos, 7 GB, 150 quadros 1080×1920, 2 processos):
- Remotion 4.0.543: bundle 13,4 s + render 8,1 s; pico ≈ 1,7 GB.
- Palco V2: 10,3 s (já com efeitos sonoros, mixagem e masterização); pico ≈ 2,1 GB.

Decisão (docs/V2_ARQUITETURA.md §9): não migrar. Mesmo navegador = mesma qualidade visual; ganho de ~20% no render não
paga a reescrita das 32 composições nem um segundo runtime; licença gratuita só para pessoa física/empresas de até 3
pessoas.
