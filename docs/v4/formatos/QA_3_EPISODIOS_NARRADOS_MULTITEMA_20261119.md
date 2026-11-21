# QA multitema — três prévias narradas realmente renderizadas (19/11/2026)

**STATUS:** execução técnica CONCLUÍDA; análise editorial humana PENDENTE; **NÃO PUBLICAR**. Branch experimental `atlas-direcao-visual-20261118`; não alterar main/NTC/motor principal.

## Objetivo e escopo

Após a reclamação de loops sobre Canal do Panamá, testar uma vez o mesmo compositor visual, o mesmo controle de evidência e o mesmo fiscal de montagem em **três assuntos distintos**, com MP4 final contendo voz por cena. Resultado NÃO equivale a demonstrar que um diretor de IA consegue escolher mídia e roteiro sem curadoria. O storyboard e fontes foram selecionados manualmente como regressão controlada.

## Teste final comprovado

**GitHub Actions [44564855342](https://github.com/Heitor2404/coringa-news/actions/runs/44564855342): SUCCESS** (19/11, cerca de 16h23 UTC).

- **43 testes passaram.** `FilmeEditorial` Remotion usado sem ramificações específicas por assunto; TypeScript compilou.
- Três MP4s narrados de **14,8 segundos cada**, quatro cenas por tema; total de 12 cenas. **Voz Edge TTS pt-BR-AntonioNeural de TESTE**, não Gemini Charon final.
- `scripts/qa_montagem_multitema.py` analisou MP4 final com áudio, duração, falta de quadros, níveis de escurecimento, movimento de pixels e quatro quadros por cena, registrou `qa_montagem.json` e `contato_editorial.jpg`. Todos **PRONTO_PARA_REVISAO** tecnicamente, mas **sem revisão semântica da locução × imagem**, sem aprovação estética humana.
- O Telegram privado confirmou `{"enviados":3,"destino":"group privado autorizado","publicados":0,"aprovados_por_humano":0}`: três MP4 e três contatos enviados, nenhuma publicação nas redes.
- Artifact **14551478364**, `qa-3-episodios-narrados-sem-publicar` (~9,9 MB ZIP), inclui vídeos, QA e proveniência.

| Episódio | Cenas verificadas | Verdade das mídias | Limitações visuais observadas |
|---|---|---|---|
| Taiwan/chips | 4 | Mapa real do leste da Ásia, fotomicrografia AMD e wafer D-Wave apenas **ilustrativos**, mapa NASA. Nenhuma mídia foi declarada como prova de produção TSMC/Taiwan | Estética quase só slides com zoom sutil; não demonstra fabricação em Taiwan; última cena informa explicitamente que mapa NÃO prova indústria. Fontes e créditos são pequenos |
| Venezuela | 4 | Roraima/Kukenán reais; Salto Ángel real; **mesma fotografia do Salto Ángel em dois enquadramentos**, declarada; mapa histórico de 1635 não apresentado como fronteira atual | Repetição de foto em sequência e pouca ação; texto compete com a paisagem; não aprovar como capítulo final |
| Ever Given/Suez | 4 | Satélite real do encalhe; NASA real mostrando fila; Ever Given em Roterdã **declaradamente outro local**; outro recorte da mesma foto de encalhe | Visuais fixos / repetição de foto. Há fonte correta, mas falta progressão audiovisual e explicação causal do bloqueio; overlay de manchete grande e créditos pequenos |

**Resultado crítico de generalização:** infraestrutura técnica de render+voz+QA funcionou nos três; **a qualidade visual-editorial ainda NÃO está generalizada**. São vídeos com quatro imagens estáticas e estilo de slide com zoom, distante do documentário desejado. Não afirmar que a presença de narração e 43 testes garante direção audiovisual. Nenhuma integração com seleção autônoma ou revisão VLM em quadros reais foi comprovada nesta rodada.

## Correções reais até a execução verde

1. `44562137474` — 43 testes verdes, **Wikimedia HTTP 429** bloqueou novas imagens. Sem falsa substituição.
2. Alterado conjunto para **fontes locais já preservadas** (chip curado em artifact anterior, NASA/Natural Earth/Commons fixtures, acervo Ever Given), em vez de exigir novos downloads. Os assuntos finais ficaram Taiwan/chips, Venezuela, Ever Given/Suez.
3. `44563805945` — licença `CC BY-SA 4.0` rejeitada no preflight; permitido exclusivamente quando `tipo=PROVA_VISUAL_PRIVADA`, sem autorização de publicação.
4. `44564273596` — JPEGs derivados de scout haviam sido erradamente comparados com SHA dos originais. Corrigido: manter hash da origem + calcular e registrar SHA independente do derivado, sem fingir bytes iguais.
5. `44564714290` — cancelado por novo disparo; o commit seguinte acionou a execução final.
6. `44564855342` — SUCCESS, arquivos entregues ao Telegram privado, 0 publicados.

## Arquivos implementados

- `docs/v4/formatos/qa_episodios_multitema_3.json`: três storyboards de teste com fala, título, identidade das fontes e aviso de imagem meramente ilustrativa.
- `scripts/qa_episodios_multitema.py`: reutiliza acervo local ou curado e faz contrato das três sequências de quatro cenas com SHA da mídia efetivamente usada.
- `scripts/qa_narracao_multitema.py`: grava voz de teste por cena, limita aceleração, sincroniza áudio em WAV/MP4 e registra tempo.
- `scripts/qa_montagem_multitema.py`: mede somente QA técnico e gera contato por cena.
- `scripts/qa_telegram_multitema.py`: envia três vídeos e contatos somente se os três passaram no QA técnico para grupo privado autorizado; bloqueia envio parcial.
- `tests/test_qa_episodios_multitema.py`: regresão sem custo; `.github/workflows/qa-3-episodios-narrados.yml`: pipeline isolado, disparo `.github/qualidade/episodios_narrados_3.txt`.

## Próximo gate — não voltar ao Panamá

- Substituir métricas proxy de pixels por **revisão semântica do MP4 com os quadros reais, locução e evidências**, e medir taxa de falsas aprovações por cena. Usar `revisao_filme_editorial.py` já implementado e revisão humana como referência; não pagar modelo sem autorização.
- Testar **cobertura real de ações** (fazer a imagem demonstrar) em vez de aceitar legenda que afirma. Explicitar e medir repetição do mesmo arquivo de origem mesmo quando o enquadramento muda.
- Integração da busca contextual com a origem/identidade realmente exibida em tela segue pendente; estas três histórias foram curadas manualmente.
- Os filmes não têm a voz de produção, trilha e sincronização de legendas do canal final; ainda são **prévia de QA**. Proibir publicação e alteração do motor principal sem homologação estética e factual.

**Veredito:** não fizemos V6 do Panamá. Conseguimos produzir/testar três amostras distintas e mostrar que o mesmo compositor/QA detecta lacunas estruturais técnicas, mas ainda não atestamos nem construímos qualidade audiovisual generalizável.