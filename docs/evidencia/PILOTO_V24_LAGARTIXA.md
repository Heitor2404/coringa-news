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

---

# Retomada única — execução 43646047814 (depois das correções gerais, commit 6afff5b)

**Resultado: bloqueado de novo pelo preparo V2.3 antes da narração, desta vez por motivos legítimos. Sem vídeo, como manda a ordem.**
A retomada regenerou o roteiro e o acervo: não existe ponto de retomada no `main.py`, e o acervo da 1ª execução não foi gravado.
Por isso o roteiro saiu diferente. Tempo: 465 s. Custo estimado (assinatura do Claude): USD 0,41, com alerta de custo. Gemini e NVIDIA: gratuitos.

- **e5 (mecanismo, crítico):** "Nessas patas, as *cerdas* criam forças de Van der Waals." O contrato veio **sem dados** (`{}`).
  Nenhuma composição é viável, e nenhuma foto mostra a pata aderida em nível microscópico.
- **e7 (nivel, crítico):** "E ela *some* rápido quando as moléculas se afastam." Só **2 etapas** ("perto: atração", "longe: some").
  A reclassificação nova exige 3 de propósito (é conservadora), e o tipo `nivel` exige `de`/`ate` ou `sentido`.

As correções funcionaram nos casos da 1ª execução (testes `tests/test_preparo_desbloqueio.py`). Mas o roteiro novo trouxe outros contratos sem dados. É o mesmo problema de fundo: **o roteirista declara mecanismos sem os dados que a composição exige.**

## Precisão científica

- **"Sustentar um humano":** a única fonte na pesquisa era uma **manchete** (Portal UAI), insuficiente. O roteiro novo não trouxe a afirmação. Isso não foi forçado: a pesquisa e o roteirista mudaram sozinhos.
- **"A força some":** o roteiro novo ainda diz "*some* rápido". Na pesquisa, a linha certa é "desaparece rapidamente quando as moléculas ficam mais afastadas". A formulação "enfraquece rapidamente" não pôde ser aplicada sem editar o roteiro à mão.
- **Micrografias do NIST:** são de **Stanislas Gorb / Kiel University**, não da NIST, e por isso não estão em domínio público. O resto da página: a ilustração é de Marianne Meijer/Kerncraft, a foto do pé tem CC BY-SA 3.0 e a dos lagartos tem CC0. Sem licença das micrografias, não podem entrar. Também não estão em nenhuma fonte do acervo automático, então nada foi adicionado à mão.

## Evidência V1 (sombra) × preparo V2.3

| | V2.3 | V1 (sombra) |
|---|---|---|
| Bloqueios | e5, e7 | nenhum: e5 e e7 foram para **revisão humana** (fotos ligadas à espécie, sem confirmação dupla) |
| Prova visual | — | e1, e3, e11 (lagartixa no teto / identidade da espécie): categoria curada da espécie + visão cega |
| Composições | e6, e9 processo.etapas | iguais |

**Ressalva:** em e7, a V1 aceitaria uma foto como "relacionada" para uma força que some. É um acontecimento que foto nenhuma mostra. É um ponto fraco da V1 a registrar, porque `nivel` aceita foto de ação.

**Chamadas de visão (3, todas gratuitas):**

| Tarefa | Provedor/modelo | Tempo |
|---|---|---|
| Catálogo | Gemini lite | 13,9 s |
| Casamento | Gemini lite | 12,7 s |
| Dupla leitura | NVIDIA | 12,5 s |

- Uma discordância (e5 × a5), que foi para revisão, e uma concordância (e5 × a26).
- 8 imagens retidas por privacidade.
- Registros reais: 18 do Commons e 7 da NASA (6 legados).
- A Wikidata deu 429 em 2 nomes.

---

**Correção estrutural (V2.4, offline, sem vídeo):** ver [`CORRECAO_V24_CONTRATOS.md`](CORRECAO_V24_CONTRATOS.md) — pré-validação e conserto rastreado dos contratos, checkpoint/retomada por etapa e separação entre evidência visual e ilustração de mecanismo.

---

# Piloto real V2.4 — execução 43654018515 (código 2e43ae3)

**Resultado: `BLOQUEADO_PREPARO`. Sem MP4.** Execução única, sem nova tentativa (como manda a ordem).

**Execução**
- Tempo: 610 s. Pico de memória: 270 MB. Custo: USD 0,00.
  - O **Claude atingiu o limite semanal** da assinatura (volta em 16/11, 05:00 UTC). Roteiro, crítica e conserto saíram do Gemini (reserva).
- Busca na web do Gemini: 429. LoC: 429. Gemini 3.8-flash: um 504.
- Pacote cifrado: ramo `piloto-v22-resultado`, arquivo `piloto-43654018515.tgz.gpg`, para as duas chaves.
- Checkpoint cifrado no cache: chave `piloto-checkpoint-43654018515`. Para retomar: `retomar.txt` = `43654018515 roteiro`.

**Roteiro:** 19 planos, 150 palavras (cerca de 58 s).
- Fala de "atração molecular", dipolo instantâneo, Van der Waals e distância de contato. Não fala em "some".
- **Não menciona cerdas nem espátulas.** Menciona lamelas e "almofadas adesivas".
- Fecha com a NASA/Astrobee (2025) e Suni Williams.
- Imprecisão: "gruda apenas ajustando cargas elétricas moleculares" (revelação).

## Pré-validação V2.4 (funcionou como projetada)

- Uma chamada de conserto para **7 contratos críticos não observáveis** (e4–e10). **7 aceitos**, com todos os itens rastreados na pesquisa.
- Resultado: diagrama.explicativo, processo.etapas e forcas.vetores, todos marcados como **ILUSTRAÇÃO, não é evidência**.
- Nenhum contrato ficou pendente.

## O que bloqueou: 3 mecanismos críticos **observáveis**, que a V2.4 deixa para o acervo

| Ev. | Fala | Contrato (sujeito / mostrar / dados) | Foto no acervo | Por que o preparo recusou |
|---|---|---|---|---|
| e2 | "…usa lamelas nos dedos para se segurar." | Hemidactylus mabouia / "desenho anatômico das lamelas" / `{especie}` | nenhuma das lamelas; a0 é desenho de *Tarentola* | sem composição viável; foto só de contexto (a2) |
| e3 | "…estruturas microscópicas que ampliam o contato." | **"almofadas adesivas"** / "close da sola da pata no vidro" / `{estrutura}` | **a3 = "parte inferior da pata… sobre um vidro" (CC)** | o sujeito "almofadas adesivas" não aparece no catálogo de a3: força 1, só contexto |
| e11 | "Em 2025, a NASA usou essa física no robô Astrobee…" | **"NASA"** / "robô Astrobee manipulando objeto dourado" / `{ano, entidade}` | **a13/a15/a18 = Astrobee com almofadas adesivas (NASA)** | o sujeito "NASA" não aparece nas legendas: força 0,5; troca para a1, que é só contexto |

**Causa técnica.** A avaliação de foto do preparo V2.3 (`preparo.avaliar_imagem`) é lexical:
- exige a palavra do `sujeito` do contrato no catálogo;
- só dá força 3 por grupos de estado herdados do Ever Given (preso, liberado…). Em tema científico, esses grupos nunca casam.

Assim, mecanismo crítico observável só chega a "foto declarada" (força 2) se o roteirista nomear o sujeito com a mesma palavra do catálogo. O e3 e o e11 tinham foto real adequada no acervo e foram bloqueados por isso. O e2 não tinha imagem nenhuma: é um bloqueio legítimo.

**Evidência V1 (sombra):**
- 0 bloqueios. e2, e3, e11 e e12 ficaram como `foto_relacionada`, para revisão humana.
- **Falha da V1:** em e11 ela escolhe a10, uma lagartixa no Kruger, para a fala da NASA/Astrobee. O vínculo "categoria da entidade Hemidactylus mabouia" vale para qualquer acontecimento do vídeo.
- Visão: catálogo e casamento pelo Gemini lite (11 s cada); dupla leitura pela NVIDIA (e2 × a3, concordante).
- 11 imagens retidas por privacidade/texto. Nenhuma discordância.

**Não corrigido nesta execução** (exige mudança na avaliação de foto do V2.3, fora do escopo autorizado):
1. O sujeito visível do contrato (robô, pata) versus a entidade institucional (NASA).
2. Grupos de estado genéricos para fenômenos científicos.
3. O vínculo por entidade da V1 aplicado a acontecimentos de outro sujeito.
