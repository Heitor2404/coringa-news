# Prova causal de eclusa — 7,8s (19/11/2026)

**Status editorial: AGUARDANDO_AVALIAÇÃO_HUMANA; NÃO PUBLICAR E NÃO PROMOVER A PRODUÇÃO.**
**Escopo:** experimento isolado em `atlas-direcao-visual-20261118`; `main`, `motor-integral-v4`, NTC, DOSSIÊ e vídeo V5 não foram alterados.

## Entrega real

- Cena 0–1,65s: vídeo U.S. Navy/DVIDS 634226 `comfort-2018-meio.mp4`, master SHA256 `3d21204dc0ff2b45298b341b102f0175f32a8c4838dbed7de4efb24cece5b38d`, origem 4,8–6,45s, antes do corte interno embutido do fornecedor.
- Cena 1,65–7,8s: componente isolado `LockCausal.tsx` e storyboard `docs/v4/formatos/filme_panama_8s_causal.json`, corte ilustrativo com cinco estados cronológicos: câmara fechada → entrada de água por duto inferior → elevação do casco → equalização com nível superior → portão pode abrir. **Esquema e portão são simplificações ilustrativas, não filmagem real nem reprodução exata da comporta.**
- Uma imagem real do master é congelada em t6,45s e dissolvida no diagrama, evitando a troca interna de tomada vista nos testes; não há segunda mídia disfarçada. Aplicado o mesmo tratamento de luminosidade do vídeo durante a transição para evitar flash.
- Fonte e SHA conferidos antes do preparo; nenhuma voz, Claude, Gemini, Telegram, postagem ou roteiro longo gerados. Artefato privado de 7 dias.
- `src/v4/formatos/filme_editorial.py` ganhou a validação `F-MECANISMO-CAUSAL` (ordem e intervalo) e `F-PONTE-REAL` (arquivo e timestamp da fonte), sem alterar o comportamento da V5, além de preparar o quadro derivado.
- `FilmeEditorial.tsx` aplica o mecanismo somente quando a composição o solicita e não impõe gradiente escuro aos rótulos; demais composições continuam intactas.
- `tests/test_filme_panama_causal.py` cobre coerência, ausência de falsas provas, manutenção da V5, limite de tempo e ponte verdadeira.

## Execuções e avaliação independente

- `44529565906`: sucesso técnico; a primeira amostra revelou rótulos encobertos pelo gradiente do compositor.
- `44530638832`: sucesso técnico; corrigiu legibilidade, mas apresentou salto de trecho no clipe de origem e mudança de exposição na transição.
- `44531518899`: sucesso técnico; corte da fonte removido com quadro congelado, ainda houve flash de luminosidade na troca.
- **`44532194366`: SUCCESS**, contrato Python, TypeScript, mídias SHA, render **7,800s, 540×960**, contato de 7 frames, QA de exposição e artifact `14533737677` (`filme-panama-8s-causal-privado`). O teste incluiu diferença de brilho do céu nos quadros t1,60 e1,70 menor que 32 pontos; revisão local deu ~121,7 e 120,0. Não equivale a auditoria estética humana.
- O trecho completo V4 foi inspecionado por imagens e pela transição. A nova versão **comunica visualmente água e casco subindo** com mais consistência, mas o diagrama ainda é vetorial simples, sem detalhamento técnico/fotográfico próximo das referências. Não declarar filme profissional nem homologação de novo motor; foi só prova curta e silenciosa.

## Decisão de próximo passo

Mostrar ao usuário o MP4 curto silencioso e os quadros do último artifact. Se ele **reprovar artisticamente**, parar e reavaliar o conceito de direção/animação, sem repetir microfixes. Se a comunicação e o visual forem aceitos **como base**, integrar narração e movimento vinculados às palavras, sound design e testar o mesmo compositor em tema não hidráulico, sem programar um novo mecanismo para cada episódio. O motor produtivo permanece protegido.
