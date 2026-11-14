# Piloto V2.4 — "Por que as lagartixas conseguem andar no teto sem cair?" (execução 43643345166)

**Configuração:** `MOTOR_VISUAL=v2`, `EVIDENCIA_V1=sombra`, `EVIDENCIA_V1_VISAO=1`. Uma geração, sem aprovação e sem Telegram.
**Pacote cifrado:** ramo `piloto-v22-resultado`, arquivo `piloto-43643345166.tgz.gpg`.

## Resultado: **bloqueado pelo preparo V2.3 antes da narração**. Sem vídeo (não contornado, como manda a ordem).

- **e9:** fala "Só que essa força some quando as moléculas se *afastam*."
- O roteirista declarou o tipo **`proporcao`**, mas mandou dados de **etapas** ("moléculas próximas", "moléculas se afastam", "atração desaparece").
- A única composição de `proporcao` exige `pct`. A reclassificação da V2.3 não converte "proporção com etapas" em processo, então o preparo bloqueou.
- **A Evidência V1, em sombra, concorda: também é bloqueio.**
- Tempo: 491 s. Custo estimado (assinatura do Claude): USD 0,44, com alerta de custo. Gemini e NVIDIA: gratuitos.

## Outros achados (registrados, não corrigidos)

- **e4 (lamelas):**
  - A V2.3 mandou para revisão por "foto de 2009, acontecimento de 2026".
  - O acontecimento é atemporal, e a data de 2026 veio da época geral do roteiro.
  - É um erro de data do preparo V2.3. A Evidência V1 trata acontecimentos atemporais sem data.
- **Acervo sem microscopia:** nenhuma imagem de setas ou espátulas. As buscas no Smithsonian voltaram vazias.
  - Os mecanismos (e6–e8) foram para as composições `processo.etapas`.
  - Não houve nenhuma PROVA visual de estrutura microscópica, porque não havia imagem dela.
- **Afirmação "sustentar até um humano" (e3):** a imagem nunca verifica afirmação. A verificação factual da V1 a marca à parte.

## Evidência V1 (sombra) × preparo V2.3

- **Mesmos 13 acontecimentos.** Mesmo bloqueio em e9 e mesmas composições em e6–e8.
- **Mais rigor nas fotos:**
  - e2, e4 e e5 ficaram como RELACIONADA (revisão) em vez de foto declarada ou contexto.
  - O vínculo é a categoria da espécie (*Hemidactylus mabouia*, via Wikidata P373), sem leitura visual que confirmasse a ação.
- **Nenhuma PROVA concedida.**
- **Metadados:** 9 registros reais do Commons, 6 da NASA e 10 legados. A Wikidata deu 429 em 3 nomes, sem nova tentativa.

## Chamadas de visão (3, todas gratuitas)

| Tarefa | Provedor/modelo | Tempo | JSON |
|---|---|---|---|
| Catálogo cego | Gemini 3.5-flash-lite | 16,0 s | ok |
| Casamento cego | Gemini 3.5-flash-lite | 7,9 s | ok |
| Dupla leitura (e4 × a3) | NVIDIA Nemotron VL | 16,1 s | ok, concordante |

- **Fallback:** nenhum. O Gemini lite respondeu às duas chamadas.
- **Discordâncias:** nenhuma.
- **Privacidade:** 13 imagens retidas e **não enviadas** à NVIDIA (pessoa ou mão, texto como conteúdo, diagramas com rótulos).
- **Fora da Evidência:** o casamento da produção (`gemini-3.8-flash`) deu 503 uma vez e seguiu pela reserva já existente.
