# ATLAS — revisão de enquadramento e aparência após reprovação do 3D

Data: 21/11/2026. **Laboratório privado; não promover à produção nem considerar estética aprovada.**

## Problema reportado

Usuário: "Primeiramente que ficou muito estranho, segundo que agora ta muito baixo, sendo que ta sobrando espaço em cima".

Revisão dos quadros reais do MP4 anterior:
- A máquina começava por volta do terço inferior da tela, cabeça muito abaixo da faixa superior de texto; volante aproximava-se demais do rodapé.
- Argolas decorativas ao redor do cilindro, penduricalhos no corpo, aro turquesa luminoso e oito raios brilhantes faziam o conjunto parecer um brinquedo, não um modelo mecânico de corte.
- Só ampliar ou recolorir a mesma cena não resolve o grau de fidelidade do modelo. A física slider-crank segue válida, mas aparência precisava de correção.

## Implementação (ambas as aplicações com mesmos dados/renderer)

- `CinematicCutaway3D.tsx`: palco ThreeCanvas antes top=685 em canvas 1080×1920, agora controlado por `safeRoles.layout.mechanismTop=505`, **180 pixels mais acima**; textos também ganharam posicão controlada pelo mesmo contrato.
- `editorial-safe-roles-v2.json`: layout compartilhado por papel (arte 3D full-bleed e textos independentes), brandTop=292, headlineTop=350, subtitleTop=515, eventTop=330, mechanismTop=505. Não reduzir mecanismo inteiro para área ad-safe.
- Visual CAD simplificado: removemos torus soltos que atravessavam o cilindro, reduzimos suportes externos e aro luminoso da roda, trocamos raios excessivos por 5 peças metálicas e materiais mais neutros. Removemos oscilação artificial da câmera; a geometria continua ligada a `SliderCrankRig.ts`.
- De propósito NÃO alteramos geometria individual por tema, nem `FilmeEditorial`, main, NTC, DOSSIÊ ou Telegram.

## Resultado testado

- Still QA [44953917074](https://github.com/Heitor2404/coringa-news/actions/runs/44953917074): SUCCESS; TypeScript, testes Python, quatro renderizações 3D e áreas seguras simuladas. Artefato `14726812362`, expira 25/11/2026 21:55 UTC.
- Dois MP4s QA [44953917076](https://github.com/Heitor2404/coringa-news/actions/runs/44953917076): SUCCESS; 8,4 s, 30 fps, 540×960, 1 motor e 1 compressor, áudio ausente. Artefato `14727425121`, expira 26/11/2026 21:57 UTC.
- Resultado: motor SHA-256 `af168b27ff2cea71ac5b80493ef6cd3c0115309db0f84efea18b098ee19a82a9`, delta RGB 16,3; compressor SHA `e9f3d54afccac722a5ee4474cb96dc9f5d43fd89b121487e3b9aad8b6fedc677`, delta RGB 12,52. Métricas de movimento NÃO medem qualidade visual.
- A inspeção dos dez quadros confirmou o mecanismo mais acima, corpo completo em ambos os assuntos, cabeçote legível sem corte, textos sem cruzar com o cabeçote e volante afastado do rodapé.
- Comparativo antes/depois em `/mnt/data/comparativo_posicao_visual_ATLAS_v3.jpg` criado durante o turno, verificar a existência no próximo.

## Avaliação independente

A distribuição vertical foi de fato corrigida. A apresentação metálica está menos ornamentada. **A estética continua conceitual/estilizada**, com peças de geometria primitiva e poucos detalhes funcionais; não afirmar que o usuário gostará, nem que é um modelo CAD realista. Uma direção profissional pode exigir importar geometria 3D editável, com licença comercial conferida, ou escolher outro estilo de motion graphics. Não voltar a polir individualmente cada tema sem critério visual comum.

Próximo portão: aprovação visual do usuário; se ainda estiver estranho, mudar biblioteca de modelos e linguagem visual, não microajustar câmeras para sempre.
