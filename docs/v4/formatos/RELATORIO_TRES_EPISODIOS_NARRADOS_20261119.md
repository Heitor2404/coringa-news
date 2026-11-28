# Regressão com três episódios narrados — 19/11/2026

## Objetivo e restrições

O usuário pediu que correções e métricas comprovassem generalização em vídeos completos, não só no Panamá. Esta etapa usou 3 filmes efetivamente montados e narrados no **mesmo compositor**, com cenas reais de acervos e quatro planos de 3,7s, sem gasto Claude/Gemini, sem postagem pública. Rodada no branch \`atlas-direcao-visual-20261118\`, sem alterar \`main\` ou NTC.

### Fontes dos três pilotos (curadoria existente)

1. \`taiwan_chips\` (indústria): quatro cenas, mapa Natural Earth do leste asiático, imagem macro AMD curada, wafer D-Wave curado, imagem NASA Blue Marble. Todas classificadas como **representativas**, jamais “registro TSMC”. O esquema é de evidência genérica, não narração forte de uma história sobre Taiwan.
2. \`venezuela_paisagens\` (geografia): foto Monte Roraima, Salto Ángel, **outra variante da mesma foto Salto Ángel**, mapa histórico Blaeu 1635. A repetição foi deliberadamente declarada no plano para testar o fiscal.
3. \`ever_given_suez\` (história): imagem do navio encalhado, imagem NASA satelital com fila de embarcações, foto do Ever Given em Roterdã explicitamente identificada como **outro porto**, segundo recorte do **mesmo evento-foto** usado na abertura.

Fontes/autor/licença explícitos nos planos JSON. Derivados do garimpo visual anterior **não possuem o mesmo SHA dos originais**: o catálogo registra SHA256 da origem, enquanto a prévia JPEG preservada foi submetida a uma checagem SHA própria; jamais alegar bytes idênticos. Acesso direto ao upload Wikimedia retornou HTTP 429 na primeira tentativa, por isso reaproveitamos arquivos curados de artefatos Github e fotos locais do repositório.

## Pipeline implantado

- \`docs/v4/formatos/qa_episodios_multitema_3.json\` — manifesto curado de três assuntos com falas e provas explícitas por cena.
- \`scripts/qa_episodios_multitema.py\` — preparação SHA-256 e storyboard compartilhado; \`src/v4/formatos/filme_editorial.py\` validou o plano e Remotion produziu os clipes.
- \`scripts/qa_narracao_multitema.py\` — voz temporária Edge TTS AntonioNeural; frases por plano, áudio AAC no MP4 e alinhamento temporal dentro do limite. **Não confundir com Charon de produção** nem com áudio homologado.
- \`scripts/qa_montagem_multitema.py\` — captura 4 frames por cena, checa áudio, duração, pretos e variação de pixels; **não** avalia se o assunto narrado de fato aparece.
- \`scripts/qa_telegram_multitema.py\` — enviou 3 filmes e folhas de quadros no Telegram privado autorizado; sem publicar.
- Workflow \`.github/workflows/qa-3-episodios-narrados.yml\` e gatilho \`.github/qualidade/episodios_narrados_3.txt\`.

## Resultado do primeiro fiscal e erro de interpretação

O workflow **44564855342 terminou SUCCESS**: 43 testes passaram, três clipes MP4 narrados de **14,8s cada**, 12 cenas no total, todos com áudio e preflight técnico verde. Artefato **14551478364** \`qa-3-episodios-narrados-sem-publicar\` guardou os MP4, folhas e relatórios. Logs confirmam \`{"enviados": 3, "destino": "group privado autorizado", "publicados": 0, "aprovados_por_humano": 0}\`.

**Inspeção VISUAL DO RESULTADO REAL (folhas 4×4)**:
- Todos os três filmes parecem apresentações de quatro fotografias com zoom suave e títulos, pouco ritmo visual. **A aprovação técnica não é aprovação editorial.**
- \`taiwan_chips\`: as imagens de chip/wafer são reais e o mapa é identificado, mas a progressão não mostra a fabricação ou o argumento de por que Taiwan importa. Falta ligação causal entre fala, indústria e território.
- \`venezuela_paisagens\`: utiliza duas variantes da **mesma fotografia** do Salto Ángel em cenas sucessivas; não adiciona prova nova. Mapa histórico e paisagem são reais, mas há pouca direção de câmera.
- \`ever_given_suez\`: primeira cena de satélite mostra navio encalhado, outra imagem NASA mostra escala da fila de forma pouco legível em tela pequena, terceiro plano é navio em Roterdã corretamente rotulado, quarto reutiliza a foto de abertura. A ideia de um episódio sobre Suez termina repetindo a imagem, sem payoff.

## Correção do erro GENERICAMENTE, sem mudar nenhum dos vídeos antigos

Novo \`src/v4/formatos/fiscal_progressao.py\` reutilizável, chamado pelo preflight \`filme_editorial.py\` em **qualquer tema**:
- \`F-SEM-PROGRESSAO-INFORMACIONAL\`: cena de **fotografia** dura mais de 2,8s depois do último marco/acontecimento visual declarado. Movimento de zoom/pan não conta como informação nova. Heurística de risco; não é julgamento humano.
- \`F-FONTE-VISUAL-REPETIDA\`: duas cenas fotográficas reaproveitam a mesma página de origem ou SHA original, mesmo com outro ID/nome/crop. **Não** tratar como material novo. Não bloqueia comparações propriamente declaradas nem vídeo documental só por duração.
- \`tests/test_fiscal_progressao.py\` verifica casos positivos e negativos independentes do tema; \`tests/test_qa_episodios_multitema.py\` agora exige que os **mesmos vídeos tecnicamente verdes** sejam bloqueados pelo fiscal mais forte (em vez de perpetuar teste permissivo).

Workflow \`.github/workflows/qa-reavaliar-tres-narrados.yml\` recuperou **exatamente o artefato do run 44564855342**. **Run 44566545483 SUCCESS, 45 testes, nenhum render e nenhum custo IA.** Comparação:

| Filme | Antigo | Novo | Bloqueios |
|---|---|---|---:|
| Taiwan | PRONTO_PARA_REVISAO | BLOQUEADO_POR_QUALIDADE_VISUAL | 4 (fotos sem novidade) |
| Venezuela | PRONTO_PARA_REVISAO | BLOQUEADO_POR_QUALIDADE_VISUAL | 5 (4 fotos + 1 fonte repetida) |
| Suez | PRONTO_PARA_REVISAO | BLOQUEADO_POR_QUALIDADE_VISUAL | 5 (4 fotos + 1 fonte repetida) |

Artifact do relatório comparativo **14552202526**, \`qa-comparativo-falsos-positivos-3-temas\`. A reprovação é repetível e vem da regra comum, **não de regras específicas para Panamá/Venezuela/Irã**.

## Limites e próximo passo correto

- Esta métrica só confirma sinal de risco informacional por tempo de foto e identidade de origem. **Ainda não avalia qualidade da narração, legibilidade minuciosa, veracidade factual, ritmo musical nem entendimento do espectador.** Dois títulos diferentes ou maior variação de pixels não demonstram dois acontecimentos reais. O bloco multimodal \`src/v4/formatos/revisao_filme_editorial.py\` já existe, mas a execução real de 12 revisões por IA foi deliberadamente evitada nesta rodada.
- O fiscal novo atua **no formato FILME EDITORIAL**. Deve ser integrado ao adaptador de planos ATLAS depois de confirmar o mapeamento de seus beats e camadas; não afirmar que o gate anti-repetição já roda em todos os motores da produção.
- **Não gerar automaticamente outras versões dos três filmes** sem corrigir a seleção de mídia e a direção: cenas precisam ter mudança informacional real, não simplesmente mais pan, cards, rótulos ou fotografias repetidas.
- Próxima meta: aplicar uma direção narrativa movida por provas e construir de forma genérica novos eventos visuais (nova mídia comprovada, mapa contextual útil, demonstração, comparação real) durante a montagem. Julgamento humano por cena deve medir falsos positivos/negativos da IA antes de liberar produção.

**Estado final:** \`main\`, NTC, motores diários sem alterações. Os três MP4s foram enviados como *TESTE* no Telegram e agora constam **REPROVADOS para publicação**. Não enviar novo MP4 sem uma melhoria transversal demonstrada.
