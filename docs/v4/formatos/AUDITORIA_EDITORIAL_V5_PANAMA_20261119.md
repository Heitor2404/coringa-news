# Auditoria editorial independente — V5 Panamá 12s (19/11/2026)

**Estado:** REPROVADO COMO REFERÊNCIA DE QUALIDADE. Prévia privada; não publicar, não integrar em `main`, `motor-integral-v4`, NTC ou DOSSIÊ.

## Evidência examinada

- Branch `atlas-direcao-visual-20261118`, HEAD documental ao iniciar: `3adcc3887585b92418c47efa07b9e4b9d03c4627`.
- Run `44523312938` (`failure` apenas na etapa final de mux); artifact `14529146959` contém `prova_panama_12s.mp4` (12.000s, 540×960, H264) e `voz.mp3` (12.672s, 24 kHz). `prova_com_voz_12s.mp4` no artifact possui 0 bytes. **Não alegar sucesso do workflow.**
- Reconstrução de escuta/revisão neste atendimento: remux local sem rerender de imagem com `aresample=48000,atempo=1.069,loudnorm=I=-14:TP=-1.5:LRA=9,apad`, `-ar 48000`, AAC mono, saída 12s. O áudio medido desta reconstrução foi ~−14,8 LUFS, true peak −1,4 dBFS, silêncio terminal ~0,80s. Esta versão recomposta localmente não é novo artefato do GitHub Actions.
- 18 quadros verificados manualmente em t=.2,1.2,2.4,2.95,3.02,3.5,4.3,5.3,6.3,6.85,6.95,7.6,8.3,9.3,9.45,10.2,11.1,11.85 s. Cortes secos sem escurecimento artificial em 3.0, 6.9 e 9.4s. 540×960 é **amostra**, não render final.
- Comparação de linguagem com observações preexistentes das referências A/B em `docs/v4/formatos/ENGENHARIA_REVERSA_REFERENCIAS.md` — não afirmar que seus MP4s originais foram reabertos nesta sessão.

## Diagnóstico por trecho

| Trecho | O que o filme mostra | Avaliação |
| --- | --- | --- |
| 0.0–3.0 | Vídeo real da proa do USNS Comfort diante de portões fechados | Primeira imagem concreta, enquadramento e abertura mais fortes que protótipo V3; ainda é perspectiva frontal com navio ocupando o rodapé. |
| 3.0–6.9 | Esquema 2D plano com retângulo da câmara, água e navio transladando para cima | Ação física mínima aparece, mas engenharia de eclusa é simplificada demais; falta ligação de forma/posição entre portão real e esquema; textos grandes repetem a locução e permanecem quase fixos. |
| 6.9–9.4 | Outra tomada do mesmo master com corte mais fechado em direção ao portão | Não comprova por si só a mudança de nível do navio nem mostra claramente saída pós-elevação. Repetição visual de perspectiva exige justificativa narrativa maior. |
| 9.4–12.0 | Foto histórica de Gatún de 1913 | É autêntica e bem proveniente, mas inicia outro assunto (história da obra) no fechamento de uma explicação mecânica; conclusão fica dispersa. |

## Raízes estruturais, não cosméticas

1. O `FilmeEditorial` alterna quatro planos com `headline` estático por tomada; `cues` produzem etiquetas, mas não um encadeamento de objetos revelados e relacionados à voz. Cortes substituem progressão dentro da cena.
2. O mecanismo `lock_filling` é específico e ilustrativo; não há transição didática do portão filmado ao corte transversal e de volta a uma consequência filmada, nem evidência de saída real naquele master.
3. Texto + fonte + cabeçalhos + legenda estática criam aparência de apresentação. Não resolver por tipografia/tintura sem aumentar prova visual.
4. Não foi entregue plano de legenda temporal sincronizada por frase/palavra, sound design e trilha na V5; não chamar isso de acabamento de publicação. TTS Edge é apenas voz de ensaio; Gemini/Charon oficial exige aprovação.
5. O vídeo não demonstra generalização, porque só um mecanismo de eclusa foi programado. Testes técnicos e volume de códigos não substituem essa demonstração.

## Decisão e próximo experimento

**Não disparar render de 60 s, nem promover compositor.** Próximo ensaio deve ser **uma prova de 6–8 segundos** da ligação causal: (A) enquadramento real do portão/câmara, (B) corte/overlay técnico que conserve a geometria reconhecível e revele entrada de água → nível sobe → navio sobe, (C) consequência visual real ou conclusão didática clara que corresponda à locução. Isso precisa ser construído como contrato reutilizável de `objeto/ação/relação/revelação`, não solução `if Panamá`.

Remover o fecho histórico do ensaio de mecanismo: guardar a foto 1913 para episódio de **história das eclusas** se houver contexto. Não afirmar que a filmagem prova subida real quando não mostra mudança objetiva de nível. Se falta filmagem de saída, reconhecer limites e priorizar correspondência honesta em vez de imagem genérica.

**Portão de aceitação para próximo render com narração:** primeiro validar em 2–3 styleframes a legibilidade e o vínculo real→esquema→efeito, depois revisar o movimento no vídeo curto com áudio. Só avançar após avaliação humana explícita de impacto, compreensão, e semelhança de gramática (não cópia) às referências. Segundo tema não hidráulico obrigatório antes de afirmar reuso.

**Sem alterações em código nesta auditoria.** A avaliação só registra defeitos visuais comprovados, para impedir novas microcorreções sem direção.
