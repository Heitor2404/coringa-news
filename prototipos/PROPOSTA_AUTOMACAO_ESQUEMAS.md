# Proposta: gerar especificações de ESQUEMA a partir do plano editorial (não implementada)

**Situação:** proposta para aprovação, 13/11/2026.

**Objetivo:** cada vídeo explicativo deve obter seus esquemas sem programação manual por episódio. As condições são três:
- nenhum desenho afirma algo fora dos fatos coletados;
- as primitivas e as receitas já aprovadas são reaproveitadas;
- o custo incremental fica perto de zero.

## 1. Onde isso entra no fluxo atual

```
fontes → acervo → viabilidade → roteiro (+ campo "esquema" por cena) → editorial.preparar → storyboard
      → resolucao.resolver ──(cena esquema_pendente)──► ESQUEMATIZADOR ──► spec validada ──► render (seek t)
                                                         │ falha
                                                         └──► continua pendente (alerta P0/P1, como hoje)
```

O esquematizador só atua quando o resolvedor da Etapa 2/3 já decidiu que **nenhuma mídia real representa o fato**. Se existe evidência real (por exemplo, um vídeo do polvo mudando de cor), ela continua tendo prioridade.

## 2. Peças

### a) Biblioteca de receitas

Uma receita é uma spec parametrizada, escrita e aprovada uma única vez por tipo de explicação. Ela declara:
- os **papéis** (slots), por exemplo `agente`, `estrutura`, `efeito`, `observador`;
- as primitivas permitidas para cada papel;
- a coreografia (passos e tempos relativos);
- o layout (zonas onde cada papel vive na tela de 1080×1920).

Receitas iniciais, tiradas dos protótipos:

| Receita | Serve para | Exemplo testado |
|---|---|---|
| `zoom_macro_micro` | estrutura vista de perto e o efeito visto de longe | cromatóforo, micro-ondas |
| `cadeia_causal` | clímax: causa → mecanismo → efeito visível | clímax do polvo |
| `onda_e_meio` | luz ou som atravessando um meio e interagindo com partículas | céu azul |
| `campo_e_dipolo` | campo que oscila e moléculas que respondem | micro-ondas |
| `processo_em_etapas` | sequência linear de 3 a 5 estados | genérica |

Primitivas novas só entram na biblioteca por aprovação humana. A IA nunca desenha SVG livre.

### b) Preenchimento (uma só passagem de IA, dentro de uma chamada que já existe)

O `PROMPT_ROTEIRO_EXPLICA`, que já roda hoje, ganha um campo opcional por cena:

```json
"esquema": {"receita": "zoom_macro_micro",
            "papeis": {"estrutura": "cromatoforo", "efeito": "pele"},
            "passos": [{"fato": "F3", "rotulo": "músculos contraem"}, {"fato": "F4", "rotulo": "pigmento se espalha"}]}
```

- A saída extra fica em torno de 150 a 300 tokens, dentro da mesma chamada. **Não é uma chamada nova.**
- Os `fatos` (F1…Fn) são os que o roteiro já recebe das fontes. Cada um carrega sua origem.
- A resposta passa por `extrair_json` com um validador de esquema, como na Etapa 1. Se vier inválida, o campo é descartado e o roteiro segue normalmente.
- **Plano B sem IA:** escolher a receita por regra (`acontecimento.recurso == 'esquema'` mais palavras-chave do mecanismo) e usar como rótulos as raízes dos fatos citados na fala da cena.

### c) Validação factual (sem IA, determinística)

Uma spec só é renderizada se passar em todos os pontos abaixo:
1. Todo passo cita um `fato` que existe na lista coletada.
2. Todo rótulo tem pelo menos uma raiz (`editorial.raizes`) em comum com o fato que cita. Números, datas e nomes próprios do rótulo precisam aparecer no texto do fato.
3. Só são usadas primitivas e papéis declarados pela receita, e o motor já rejeita tipos e propriedades desconhecidos.
4. Os rótulos têm no máximo 4 palavras por linha e no máximo 2 linhas.
5. A geometria passa nos mesmos testes dos protótipos: rótulos dentro de x 50–930 e y 270–1150, corpo de pelo menos 24 px e nenhuma colisão.
6. Se a cena é central (P0) e a validação falha, a cena **não** vira esquema inventado. Ela volta para o resolvedor como pendente, com alerta.

### d) Layout e tempo automáticos (o que falta construir no motor)

- **Posicionador de rótulos:** escolhe a âncora e o lado de cada rótulo, evitando colisões com a forma e com os outros rótulos. Hoje essas posições estão escritas à mão nas specs. Esse posicionador é a peça mais importante a implementar.
- **Tempo:** os `de/ate` de cada passo saem dos tempos das palavras da narração (a TTS já devolve isso). O passo começa quando a palavra-chave do seu fato é dita.
- **Escala:** a receita define a zona; o motor escala a primitiva para caber nela.

### e) Reaproveitamento e cache

- Uma spec aprovada é guardada por **mecanismo** (por exemplo, `mecanismo:cromatoforo_neuromuscular`), não por assunto do vídeo. Um vídeo sobre lulas reaproveita o mecanismo, porque o fato é o mesmo. Um vídeo sobre camaleões **não** reaproveita, porque o mecanismo é outro e o validador barra.
- O mesmo mecanismo em outro vídeo custa zero: só os textos e os tempos mudam.

## 3. Custo incremental estimado

| Item | Custo por vídeo |
|---|---|
| Campo `esquema` dentro da chamada de roteiro | Cerca de 300 tokens de saída a mais na chamada já paga. Não é chamada nova |
| Plano B por regra | 0 |
| Validação, layout e tempo | 0 (código local) |
| Render | 0 a mais: o mesmo Chromium e o mesmo `seek(t)`. Esquemas com filtros de SVG podem deixar o quadro um pouco mais lento; isso ainda não foi medido no Actions |

## 4. Fases sugeridas, uma de cada vez e com aprovação entre elas

1. **Fase 1, sem IA:**
   - posicionador de rótulos;
   - tempos tirados da narração;
   - extração de 3 receitas a partir dos protótipos;
   - validador factual;
   - testes com os 4 casos atuais e 2 casos negativos (rótulo sem fato; mecanismo sem receita).
2. **Fase 2:** campo `esquema` no prompt do roteiro (cofre) e plano B por regra. Medir quantas cenas pendentes passam a ser resolvidas.
3. **Fase 3:** integração ao template (nova camada de cena) e ao fiscal de tela. Só depois disso, um vídeo real autorizado.
4. **Fase 4:** crescimento da biblioteca. Cada nova receita ou primitiva entra só por aprovação visual.

## 5. Riscos

- **Receita errada para o mecanismo:** mitigada pela validação por raízes e pela regra "na dúvida, pendente".
- **Excesso de esquemas genéricos:** a receita só existe se demonstrar o mecanismo; não haverá receita do tipo "caixas e setas".
- **Fatos insuficientes:** a cena fica pendente. Nenhum detalhe anatômico ou numérico é inventado.
