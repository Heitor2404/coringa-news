# ATLAS — terceira família: eclusa hidráulica em palco compartilhado (22/11/2026)

**Estado:** LAB experimental; **não** significa aprovação visual ou publicação. Sem Claude/Gemini.

## Sem duplicar a física
O componente `LockCausalCycle.tsx` já executava sete ações com um navio único, altura da água ligada à altura do casco, portões e fluxo por gravidade. `AreaSeguraMovimento.ts` já valida **o ator inteiro**, inclusive durante a saída. Esta rodada não reimplementou hidráulica, não substituiu o renderizador e não moveu cada peça separadamente.

Adicionou-se o modo `privateStageLayout` (desligado por padrão), com uma única transformação sobre a seção física e outro agrupamento editorial, ativado apenas pela composição `ProvaPalcoEclusaHidraulica` em `Root.tsx`. O `FilmeEditorial.tsx` mantém o comportamento anterior sem flag.

## Fonte de configuração
`motor4/remotion/src/formatos/palco-eclusa-hidraulica-lab.json` contém:
- **Canvas:** 1080×1920
- **Caixa física declarada** (inclui recorte): x61..1018, y608..1500
- **Limite editorial**: termina em y435; **início do rodapé**: y1394
- Folgas: superior 18px e inferior 30px
- **Deslocamento vertical máximo 155px**, calculado por `PalcoVertical.deslocar()`, não arbitrário
- Faixa final estimada para cena: y453..1345
- Tipografia privada: kicker y254; título y331; subtítulos y410; rodapé avança 120px para cima
- Sete ações com tempos do catálogo existente `CAPACIDADES['lock_cycle_standalone']`

Todos os pixels de texto/silhueta **não** são automaticamente deduzidos de imagens. A caixa exige anotação semântica confiável pelo renderer. O solver é genericamente geométrico, não uma solução universal de direção de arte.

## Evidência técnica real
[Run 45077175142 — SUCCESS](https://github.com/Heitor2404/coringa-news/actions/runs/45077175142), 13 testes, TypeScript compilado, vídeo real 17,5s 24fps 540×960, 10 quadros, comparação no quadro 9s.

QA de diferença RGB na **região do mecanismo** (não no cabeçalho):
- Entrada: 15,114
- Água elevando o navio: 30,610
- Saída no nível alto: 30,068
- Comparativo posição física antes/depois: 46,286

MP4 SHA256 `aaf25f4c096906bf186511a989c721ff99f91847ab4a56ce54cd9e521c8272fa`.
Artifact **14775911819** até **27/11/2026 22:22 UTC**, nome `lab-terceira-familia-eclusa-palco-vertical`.

**Causas encontradas e corrigidas:** primeiro job sem ffprobe; segundo job tinha ROI da saída focando abaixo do barco, não no barco já elevado. A correção mirou a região física certa sem trocar o teste para aprovar por mera mudança de texto.

## Leitura crítica da imagem
Há melhora objetiva na ocupação do azul escuro superior. Ainda é um desenho esquemático de eclusa, com navio pouco realista, sem a direção visual sofisticada e sem prova de que todos os textos ficam fora da interface real das três plataformas. **Não homologar como arte final.**

## Limite de generalização
Compressor e Otto foram renderizados em SVG Python 540×960; a eclusa em Remotion TS 1080×1920. A união é o **contrato matemático de palco**, não um renderer único de conteúdo nem sistema autônomo de reconstrução. `layout.py`/`plataformas.json` são a fonte real de máscaras de redes sociais; o solver não os substitui.

**Próximo:** diretor causal que localize atores, relações e eventos antes de selecionar capabilities do catálogo e que bloqueie quando a evidência não sustentar o movimento pedido. Teste de legendas e interfaces reais antes de publicar.
