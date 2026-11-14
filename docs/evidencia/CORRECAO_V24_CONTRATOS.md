# Correção estrutural V2.4: contratos visuais, checkpoint e ilustração × evidência

**Ramo:** `piloto-v24-lagartixa` (sem merge). **Escopo:** só com `MOTOR_VISUAL=v2`. Não mexe na produção (`gerar-videos.yml` não define a variável), no NTC nem na identidade visual. Nenhum vídeo foi gerado: tudo foi validado com testes offline.

## O problema de fundo (as duas execuções do piloto)

O roteirista declarava mecanismos sem os dados que a composição exige. Os casos foram:
- e9 (1ª execução): `proporcao` com etapas;
- e5 (2ª execução): `mecanismo` com `{}`;
- e7 (2ª execução): `nivel` com 2 etapas.

O erro só aparecia no preparo, depois de cerca de 460 s de pesquisa, acervo e roteiro. A retomada regenerava tudo, e o roteiro novo trazia outros contratos sem dados.

## 1. Geração e pré-validação dos contratos (`src/v2/contrato.py`, `src/v2/prevalidacao.py`)

### Prompt
- `contrato.bloco_prompt()` acrescenta ao contrato a tabela **DADOS EXIGIDOS POR TIPO**. Ela é gerada da própria `TIPOS`, a mesma tabela que o motor usa. Antes, o roteirista não tinha como saber que `nivel` exige `de`/`ate` ou `sentido`.
- O prompt também ganha o campo `observavel`.
- A produção continua com `BLOCO_PROMPT`, sem mudança (há teste para isso).

### Pré-validação
Roda logo depois de `acontecimentos.normalizar(dividir(...))`, antes do casamento com o acervo, da narração e de qualquer leitura visual. Tem três passos.

**a) Correções sem IA**, que não inventam nada:
- campo sinônimo vira o campo da composição (`passos` → `etapas`);
- tipo dinâmico (`nivel`, `movimento`) que só traz ≥ 2 etapas textuais, sem `de`/`ate`/`sentido`, vira `processo` (é o caso de e7);
- a mesma reclassificação do preparo (`proporcao` com 3 etapas → `processo`, caso de e9). A pré-validação vê o que o preparo vai ver.
- Continua conservador: com o dado do próprio tipo, com uma etapa só, com "etapas" numéricas ou com `comparacao` A × B, nada muda.

**b) Validação contra `TIPOS`.** O resultado é `ok`, `foto` (o acervo decide) ou `invalido`.
- Cena editorial (revelação, gancho, fechamento) não pede conserto.
- Mecanismo **observável** (a pata, a engrenagem) também não: foto real dele é evidência e vale mais que um esquema.

**c) Uma chamada de conserto**, só para contratos **críticos inválidos** (a e5 da 2ª execução). O conserto só é aceito se:
- o tipo novo tem composição viável;
- **cada item dos dados** (etapa, nó, força, número) está numa linha da pesquisa. O rastreio é feito por raízes de palavras; números, pela linha que os contém;
- o tipo novo não é um "não acontecimento" (`pessoa`, `lugar`, `ambiente`, `documento`, `localizacao`, `territorio`, `citacao`, `evento_historico`).

Há também travas que valem em qualquer caso:
- Item sem rastreio → o conserto inteiro é recusado, e o bloqueio continua legítimo.
- Crítico continua crítico (`obrigatoria: true`), seja qual for o tipo novo.
- A IA não consegue rebaixar a importância.
- `observavel` só fica mais restrito.
- IA fora do ar → nada muda (nunca piora).

Tudo fica em `v['_contratos']` e vai para `<nome>-preparo.json` em `contratos`. Cada conserto aceito traz `antes`, `base` e `rastreio`.

## 2. Checkpoint e retomada (`src/v2/checkpoint.py`, `main.py`)

### Etapas gravadas
Ficam em `saida/<dia>/checkpoint/`:

| Etapa | O que guarda |
|---|---|
| `tema` | pergunta e termos |
| `pesquisa` | fatos, fontes, link, dossiê |
| `acervo` | itens + **arquivos de imagem** |
| `roteiro` | tema + `v` completo, com contratos já pré-validados |

### Manifesto
O manifesto guarda o sha256 de cada etapa e de cada imagem, o commit, o pedido e a procedência. Os caminhos são relativos, então o checkpoint é retomável em outra máquina.

### Como retomar
`python main.py --retomar <pasta> [--retomar-etapa roteiro|acervo|pesquisa|tema]` carrega as etapas até a escolhida e refaz só as seguintes.

Na retomada do `roteiro`:
- não roda nenhuma chamada de pesquisa, de acervo nem de roteiro;
- os contratos são conferidos de novo, sem IA se não houver pendência, e daí seguem para o preparo.

### Auditoria de edição à mão
A cópia intocada fica em `.original/`. Se alguém editar o checkpoint (corrigir um contrato, trocar "some" por "enfraquece"):
- a retomada lista cada campo alterado, como `$.v.cenas[0].fala: "…" → "…"`;
- imagem trocada também é detectada;
- tudo é gravado em `v['_checkpoint']` e no relatório do preparo;
- o checkpoint de origem nunca é alterado: a execução nova grava o próprio checkpoint.

### Piloto no GitHub
- O checkpoint vai para o **cache do Actions**, que não é público, ao contrário dos artefatos, com a chave `piloto-checkpoint-<run_id>`.
- Para retomar: em `.github/piloto/retomar.txt`, escreva `<run_id> roteiro` e faça push.
- Retomar não gasta pesquisa, acervo nem roteiro de novo.
- O cache expira após cerca de 7 dias sem uso.

## 3. Evidência visual × ilustração de mecanismo

### Função visual
Cada acontecimento agora sai com uma `funcao` (`contrato.FUNCAO_COMP`):

| Função | O que é |
|---|---|
| **evidência** | foto ou vídeo real que registra o que é narrado; só ela pode ser PROVA |
| **ilustração** | esquema didático de mecanismo (`processo.etapas`, `diagrama.explicativo`, `forcas.vetores`…); explica e **nunca prova**; leva `nao_prova: true` e o rastreio dos dados na pesquisa; se nenhum item aparece nos fatos, vai para revisão |
| **dado** | número, gráfico, mapa, linha do tempo |
| **editorial**, **contexto** | — |

### Observabilidade
Pergunta: o elemento existe numa escala que a câmera registra? O que o roteirista declara vale primeiro. Sem declaração, a regra usa uma lista de **escala física** (moléculas, átomos, elétrons, forças, campos, cargas), igual para qualquer tema.
- "Microscópico" não entra, porque micrografia é registro real.
- `nao`: o sujeito é invisível ("força de Van der Waals").
- `parcial`: o sujeito é visível, mas a ação acontece em escala invisível ("as cerdas criam forças de Van der Waals").
- O Ever Given continua `sim` ("navio empurrado pelo vento").

### Efeito em cada motor
- **Preparo V2.3:** fenômeno não observável nunca vira `foto_direta` nem `foto_declarada`. Sem ilustração, o bloqueio diz exatamente "ILUSTRAÇÃO com dados da pesquisa (fenômeno não observável: foto não mostra)".
- **Evidência V1:** a foto fica no máximo como CONTEXTO, com veto registrado. A decisão vira composição `ilustracao` (`nao_e_evidencia: true`) ou bloqueio. Nunca vira `foto_relacionada`. Isso **corrige a ressalva da retomada** (e7: "relacionada" para uma força que some).
- Fenômeno observável continua podendo chegar a PROVA (há teste).

## Resultado offline sobre os casos do piloto

| Caso | Antes | V2.4 |
|---|---|---|
| e9, 1ª execução (`proporcao` + 3 etapas) | bloqueio no preparo | `processo`, sem IA → ilustração |
| e7, 2ª execução (`nivel` + 2 etapas) | bloqueio | `processo`, sem IA → ilustração |
| e5, 2ª execução (`mecanismo`, `{}`) | bloqueio | 1 chamada de conserto. Com etapas rastreadas → ilustração. Sem dados na pesquisa → **bloqueio legítimo**, já antes do acervo |
| e7 na Evidência V1 | foto "relacionada" (revisão) | CONTEXTO no máximo → ilustração ou bloqueio |
| 1ª execução inteira (com a foto de e4) | 1 bloqueio | 0 bloqueios, 0 chamadas de conserto; e4 = evidência (revisão), e6–e9 = ilustração |

Os casos e5/e7 da 2ª execução foram **reconstruídos a partir deste relatório**, porque o roteiro real está no pacote cifrado. Valem a mesma fala, o mesmo tipo e os mesmos dados declarados.

### Testes
- Novos: `tests/test_v24_contratos.py` (31) e `tests/test_v24_checkpoint.py` (11).
- Suíte inteira: 616 passam e 9 falham. As 9 falhas **já existiam no HEAD `b73d5a0`**: são renderização sem Natural Earth/Playwright e prompts do cofre ausentes. São as mesmas antes e depois da mudança, conferidas por diff.
- Uma falha antiga foi corrigida: `.env.example` não documentava `MOTOR_VISUAL`, `EVIDENCIA_*` e `OPENROUTER_API_KEY`.

## O que continua em aberto

- **Precisão "some" × "enfraquece rapidamente":** agora pode ser corrigida no checkpoint, com retomada auditada. Não há reescrita automática da fala.
- **Micrografias das cerdas:** continuam sem licença livre (Gorb/Kiel). A ilustração não substitui evidência e não é apresentada como tal.
- **Wikidata 429:** a coleta continua sem nova tentativa.
- **Próximo passo:** uma retomada real do piloto a partir de um checkpoint. Ainda não foi feita: espera autorização para gerar vídeo.
