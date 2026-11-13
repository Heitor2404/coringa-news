# Componentes de terceiros usados pelo template do Coringa

## HyperFrames (HeyGen)

- **Licença:** Apache-2.0. O texto completo está em `LICENSE-HyperFrames.txt`.
- **Origem:** https://github.com/heygen-com/hyperframes, commit `d208281091b1c00db1724a2ee3db0055955eb41b` (13/11/2026).
- **Arquivos copiados de `registry/components/<nome>/<nome>.html`** para `componentes/`:

| Arquivo | Uso no Coringa |
|---|---|
| `count-up.html` | cena `numero` (valor inteiro) |
| `chart-story.html` | cena `comparacao` (2 a 5 valores) |
| `headline-slam.html` | resposta da cena `revelacao` |
| `logo-brand-close.html` | marca no `fechamento` |
| `vox-annotate.html` | frase-chave da cena sem mídia confiável (pendente) |

- **Única modificação no código copiado:** em `count-up.html`, a função `formatValue`:
  - `toLocaleString("en-US")` virou `toLocaleString("pt-BR")`, para mostrar 2.734 em vez de 2,734;
  - um caractere invisível `\u2060` (word joiner) entra no início do número, porque o GSAP lia "3.000" como o número 3.
- **Montagem fora do runtime:** o `hf.js` é um adaptador próprio do Coringa. Ele clona o `<template>` de cada componente, injeta as variáveis e as cores e fontes do canal, e entrega o timeline GSAP de cada componente ao `seek(t)` do template.

## GSAP 3.14.2

- **Arquivo:** `gsap-3.14.2.min.js`, copiado do repositório HyperFrames (que também o distribui).
- **Licença:** GSAP Standard "No Charge" License (https://gsap.com/standard-license). Permite uso comercial. Não é licença OSI. O aviso está em `GSAP-NOTICE.txt`.
