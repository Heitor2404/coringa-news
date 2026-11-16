# Linguagem visual do Coringa Explica (regras e componentes reutilizáveis)

Uma identidade só. As quatro referências entram como **técnicas**, não como estilos misturados — nada de copiar
material, marca, personagem ou projeto.

| Referência | Técnica adotada | Onde está no motor |
|---|---|---|
| Zack D. Films | gancho visual imediato; progressão de acontecimentos; cada cena acrescenta informação; retenção pela narrativa | regra GANCHO/PROGRESSÃO (`linguagem.REGRAS`); validador recusa recuo no gancho; fiscal `F-GANCHO-PERDE-IMPACTO` (bloqueio) |
| Vox Atlas | mapa que ensina (lugar, rota, avanço); rótulos legíveis; composição editorial; registro real + explicação gráfica | forma `mapa`; composição `editorial` (visão geral + detalhe); `avanco` no doc.plano; fiscal `F-MAPA-ILEGIVEL` |
| Primal Space | mecanismo explicado em 2D/2.5D: partes, estados, movimento, resultado | forma `esquema` obrigatória quando a ação é o essencial; `mecanismo.estados`, `doc.eclusa`, `forcas.vetores`…; fiscal `F-ACAO-SEM-ESQUEMA` |
| Kurzgesagt | inserção explicativa simples quando a foto não mostra o processo — pontual | forma `esquema` só para o acontecimento que precisa; o resto do vídeo segue registro real (o canal não vira animação vetorial; isso é do NTC) |

## Decisão, nesta ordem

1. **Forma pelo acontecimento** (`src/v3/linguagem.py`): registro, mapa, esquema, documento, comparação, tipografia —
   pelo tipo do contrato, composições viáveis e natureza da mídia (mapa/documento/gravura/pintura/foto/vídeo, lida do
   título e descrição). Sem cota de recursos. Outra forma só com `justificativa_forma`.
2. **Composição** (`src/v3/decisao.py`): vertical que preserva o importante → outra mídia (`alternativas`) →
   **editorial** para documento/mapa/arte → revisão/bloqueio. Não existe mais cartão sobre fundo escuro automático.
3. **Câmera**: fixa por padrão; aproximar só até o objeto principal; recuo só com `revela` e quadro cheio no fim.

## Medidas (fiscal de decisão, `fiscal_editorial.decisoes`)

Calibradas em 13 vereditos do Heitor (`tests/dados/londres_decisoes_humanas.json`): aprovados mantêm ocupação 1,00;
reprovados ficam entre 0,31 e 0,65. Limites de trabalho, não verdade universal: ocupação < 0,80 por ≥ 0,5 s = revisão;
< 0,55 por ≥ 1 s = bloqueio; queda > 0,15 = revisão (bloqueio no gancho); mapa < 0,8 px/px por ≥ 1,5 s = revisão.
O que não se prova por geometria (o recuo acrescentou informação? a imagem é boa?) fica como revisão ou nota — nunca
aprovação automática.
