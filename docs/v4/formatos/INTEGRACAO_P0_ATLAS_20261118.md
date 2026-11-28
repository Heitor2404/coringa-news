# ATLAS V2 — Integração P0 (implementada em branch experimental)
**18/11/2026 | Somente `atlas-direcao-visual-20261118` | Sem publicação, geração por IA ou merge**

## Diagnóstico que motivou estas mudanças
A auditoria de reuso mostrou que as capacidades de direção já existem no V2/V3/V4, mas o ATLAS de formatos é uma integração parcial. Não foram criados diretor, acervo ou fiscal novos. **Esta entrega implementa três adaptadores/portões pequenos; não equivale à correção visual do piloto Guerra dos Chips nem libera vídeo para publicação.**

## 1. Bloqueio de voz diferente da aprovada para o ATLAS
- **Fonte de verdade:** `src/v4/formatos/canais/coringa.json → narrador`, com o **Gemini/Charon** já configurado historicamente em `config.json`; modelo e estilo de origem são conservados. O timbre final exige uma nova aprovação auditiva humana. O arquivo cifrado já existente é **preservado**, mas não se assume que seu timbre esteja homologado sem escuta.
- **Caminho específico:** `src/v4/formatos/produzir.py::narrar` injeta `cfg` e `exigir_gemini=True` **somente** para nova geração de ATLAS. `src/voz.py::narrar` ganhou parâmetro **opcional**, default `False`; ele lança erro quando a chave falta ou o Gemini falha, sem invocar Edge. A geração de DOSSIÊ/NTC/legado mantém o comportamento preexistente.
- **Rastreabilidade:** `narracao.json` registra voz/configuração (ou preservação cifrada) e SHA-256 dos bytes de `voz.wav`; não guarda chave de API.
- **Custo:** nenhuma chamada ao Gemini foi executada por esta implementação/teste. Na produção futura a geração Gemini precisa de cota/chave válida — não prometer custo zero; falha explicitamente quando indisponível.

## 2. Portão editorial V3, distinto do CI e de publicação
- **Reuso:** `src/v4/formatos/estado.py` usa `src/v3/estado_final.py::decidir` em vez de definir outra máquina de estados.
- **Validação de verdade:** não confia em `resultado['estado']` sozinho; exige `nao_publicado=True`, MP4 presente e não vazio, nenhuma janela congelada/preta, `audio_ok`, `ritmo_ok`, `legenda_ok` e nenhum motivo de bloqueio.
- **Saída:** `estado_editorial.json` é `BLOQUEADO` ou `AGUARDANDO_APROVACAO_HUMANA`; **nunca** `APROVADO_HUMANO` automaticamente. Revisão multimodal não realizada consta como pendência. O envio privado Telegram usa esse estado conferido.
- **Operação:** `python -m src.v4.formatos gate <plano.json> <pasta_saida>`; exit code 1 em bloqueio/ausência de resultado. Adicionado ao workflow `formatos-piloto.yml` **após** o envio diagnóstico ao Telegram e **antes** do arquivamento cifrado (que permanece `if: always()`). Assim, o job termina vermelho quando o MP4 for BLOQUEADO.
- **Limite:** este workflow `formatos-piloto.yml` não é o mesmo workflow específico `atlas-chips-previa-privada.yml` da branch isolada Chips; não alegar que um piloto anterior foi alterado retroativamente ou que qualquer pipeline em `main` mudou.

## 3. Ponte opcional de direção V3 → ATLAS
- **Reuso real:** `src/v4/formatos/diretor.py::fichas_do_v3(contexto)` chama diretamente `src/v3/plano_av.py::fichas` e seu `texto_prompt`. O chamador fornece `{roteiro, acervo, fatos, eventos}` V3 com fatos e metadados já verificáveis.
- O `prompt` do diretor ATLAS e `pedir` aceitam `contexto_v3` **opcional**. Quando existe, o diretor recebe as fichas/representações antes de escolher mapa, card, foto ou mecanismo; pede que o beat declare `evento_id`.
- A validação `_violacoes` exige beat vinculado a cada acontecimento crítico e recusa mecanismo V3 sem componente **de fato homologado no catálogo ATLAS** (`F-MECANISMO-FORA-ATLAS`), impedindo usar um mapa ou card para encobrir o processo que falta.
- **Limite fundamental:** o pipeline de produção de `formatos-piloto.yml` ainda é **baseado em JSON de storyboard existente**. Não existe nesta entrega orquestração automática de roteiro V3 até o ATLAS; a ponte só funciona quando o chamador passa `contexto_v3`. Não anunciar um diretor genérico de episódios novos já funcional.

## Testes e escopo do que foi validado
- `tests/test_atlas_integracao_p0.py`: testes novos offline para falta de chave, Gemini indisponível, compatibilidade de fallback legado, preset, hash, estado falso, janela/ritmo bloqueado, ausência de MP4, não-publicação e ponte V3/mecanismo fora do catálogo.
- `.github/workflows/atlas-validacao.yml` compila os arquivos modificados e roda `tests/test_formatos.py` + `tests/test_atlas_integracao_p0.py`, além de Node/TypeScript. Disparo exclusivo pela trilha `.github/atlas/validacao.txt`; **sem execução do motor, render ou APIs de IA**.
- Primeiro CI `44427175545` (voz/gate antes da ponte V3): **success; 96 testes Python passaram**, compilação TypeScript e checagens JS verdes.
- Segundo CI `44427556402` (ponte V3 incluída): **SUCCESS; 98 testes Python passaram**, verificações JavaScript e compilação TypeScript também concluídas. É validação offline do contrato, **não** avaliação de qualidade audiovisual nem ensaio fim-a-fim.
- Não houve inspeção de execução final com Gemini real, Telegram real, documento real licenciado, nem Render 20–30s; esses itens requerem prévia privada futura.

## Próxima etapa executável (P1)
1. Conectar a chamada do diretor automático aos fatos/acontecimentos V3 via `contexto_v3` com contrato de entrada/saída versionado; sem hardcode de Taiwan/TSMC.
2. Reusar `registro.video`/FFmpeg do V4 integral e os ids/licenças da biblioteca global, estendendo o ATLAS para **fotos e vídeos reais de destaque** (não criar novo downloader).
3. Resolver crédito/legendas em áreas seguras; manter mapas/cartos subordinados ao que o roteiro pede; nunca fabricar prova.
4. Testar **20–30s de Guerra dos Chips** em privado com narração Gemini/Charon e mídia comprovada, liberar apenas após avaliação humana; depois estudar perfil 16:9 de 90–120s, não alongar 9:16.

**Política de merge:** nenhum merge/push em `main`/`motor-integral-v4`/`atlas-piloto-chips-20261118` nem alteração NTC/DOSSIÊ. Regressão e aprovação humana primeiro.
