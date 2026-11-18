# GUIA VISUAL OFICIAL — ATLAS / CORINGA EXPLICA
**Versão:** 1.0 — direção estética aprovada em 18/11/2026; conformidade dos renders ainda sujeita a aprovação humana.
**Escopo:** apenas ATLAS, motor `motor-integral-v4`. Não altera DOSSIÊ, NTC ou `main`.
**Referência:** gramática audiovisual da Referência A (68,223 s), com fontes próprias/licenciadas, sem copiar ativos de terceiros.

## 1. Assinatura editorial
**Mapa editorial premium + briefing estratégico + explicação técnica limpa.**
A geografia e o acontecimento narrado são protagonistas. A composição precisa ser inteligível no celular, não parecer apresentação escolar, infográfico genérico ou colagem com efeitos.
O mesmo conjunto de componentes se aplica a qualquer história; mudam apenas assunto, dados, lugares, mídias e direção da câmera.

## 2. Paleta SEMÂNTICA (não escolher cores livremente por episódio)
| Papel | Cor oficial | Aplicação |
|---|---|---|
| Fundo noturno | `#05080F` | transições e profundidade |
| Fundo técnico | `#070B14` / `#0E1828` | mecanismos, diagramas |
| Papel | `#F2EDE3` | cartão editorial e rótulos |
| Texto principal | `#FFFFFF` | legenda/títulos em mapa |
| Tinta | `#0B0F17` | número e texto sobre papel |
| Assinatura/amarelo | `#FFD21F` | um foco/etapa/CTA, não preencher a cena inteira |
| Água | `#2F8FD8` / `#5AB4F0` | água, canos e nível |
| Ciano | `#3FD0E0` | fluxos tecnológicos e conexões |
| Alerta | `#E5483A` | bloqueio, risco, sanção ou perigo |
| Foco territorial editorial | `#A8392B` | país explicitamente protagonista na cartografia |
Proibido: degradês neon decorativos, arco-íris, grade verde, cores inventadas por episódio.

## 3. Tipografia
- Manchetes/números: Montserrat (800–900), hierarquia alta, espaçamento consistente.
- Dados técnicos, fontes, créditos e labels: JetBrains Mono, discreta.
- Serifa Noto (quando o documento/licença pede aparência documental), **nunca** fonte aleatória.
- Nada de corpos em pixels arbitrários dentro do plano do episódio: dimensões vêm dos tokens do canal.
- O editorial ATLAS usa caixa normal em legendas, sem karaoke palavra a palavra.

## 4. Três contextos visuais aprovados
### A. MAPA HERO — geografia
Base satélite/relevo licenciada, raster cobrindo a área e com resolução suficiente; textura real, zoom dirigido, país ou rota destacados quando relevantes. Pin/foto protagonista grande, rotulado e ancorado no território.
Nunca substituir um mapa físico por desenho vetorial chapado nem por grade técnica. Crédito da fonte cartográfica obrigatório.

### B. MAPA TÉCNICO — mecanismo / estrutura
Fundo grafite-azulado `#070B14`, grade muito discreta (principal 170 px), textura topográfica quase invisível; estrutura legível em azul-ardósia; água azul, movimento/fluxo amarelo; cartões off-white. Sem verde, neon, falsa perspectiva ou slide cheio de caixas. Só para um mecanismo ou estrutura que esteja sendo explicado.

### C. CARTÃO EDITORIAL — número / dado / documento
Papel off-white, texto escuro, fio ou acento amarelo, sombra curta, borda discreta, cantos pouco arredondados. **Zero rotação**. Centralizar exatamente no slot autorizado, sem ocupar o território principal sem necessidade. Campo de fonte factual pequeno no rodapé do cartão; não misturar com crédito cartográfico.

## 5. Sistema de cartões (único para todos os episódios)
- Número: tamanho-alvo 112 px com ajuste automático até 60 px para caber.
- Título: 26 px; legenda do valor: 32 px; fonte factual: >=18 px.
- Unidade menor (aprox. 46% da altura do número) e alinhada ao valor.
- Um cartão para 26 m; outro para 101 mil m³; outro para 197 milhões de litros; nunca confundir unidades.
- Tipos: numérico, comparação, processo e alerta. Todos compartilham o mesmo acabamento de papel/tinta/acento/espessura.
- Não inventar inclinação para “dar estilo”, nem trocar fontes/cores por episódio.

## 6. Fotografia de pinos
- FOTO real devidamente licenciada, com atribuição; pessoa real quando o fato pede uma pessoa.
- Pino protagonista: maior que o secundário, sem colisão com rótulo, texto, legenda ou ícones das plataformas.
- Círculo, anel quente discreto, pulso breve e rótulo preso ao mapa; cresce e fixa. Nada de círculos minúsculos para o objeto principal.
- Lugar geograficamente correto; deslocamento em tela feito pela câmera/composição, não falsificando coordenadas.
- O crédito da foto entra na faixa de créditos quando visível.

## 7. Legenda, créditos e áreas seguras
**Master:** 1080×1920, 30 fps. **Plataformas:** TikTok, Reels e Shorts com união dos perfis ativos em `plataformas.json`.
- Legenda: branco com sombra, caixa normal, até 3 palavras por grupo e preferencialmente 1 linha, 56 px (mín. 44), sincronizada com pausas da voz; nunca ocupar o crédito.
- Fontes/créditos cartográficos: faixa própria **abaixo** da legenda, junto ao rodapé visível de todas as plataformas. Não esconder licença nem permitir overflow sobre a legenda.
- Na configuração atual de segurança, limite inferior comum é y=1440, não y=1920. A referência original põe créditos mais baixos, mas esses pixels podem ficar encobertos pela interface. Segurança e legibilidade vencem deslocamento literal.
- Marca fixa sobre o ATLAS desativada: foi cortada em 40/40 quadros e, ao ser movida, colidiu com o gancho. A marca aparece no CTA e nos canais/perfil; identidade nos componentes.
- Validação em 1080×1920 e também com simulação das interfaces das três plataformas, incluindo recorte 4:5 de feed.
- Legenda × fonte factual × crédito visual são três funções diferentes.

## 8. Gancho (0–3 segundos)
**Pergunta/tensão + mapa + prova grande.** Preferencialmente geografia desde o primeiro quadro; primeira mudança de informação deve ocorrer antes dos 3 s. Abertura deve suscitar a pergunta antes de explicar o funcionamento.
Não usar quatro segundos de fundo parado; não esconder a prova atrás de cartão ou introdução do canal.
No Panamá: mapa + navio/eclusa em foto grande + questão visual; mecanismo completo entra como explicação, não como slide genérico.

## 9. CTA final
Mensagem curta, visual limpa: `SIGA` + `@coringa.explica` (ou variante temática aprovada).
Reservar **1,2 a 2,2 s**, preferencialmente depois da revelação final, sobre mapa hero, sem interromper a conclusão nem forçar alongamento vazio.
Se a história não reservar espaço, o **storyboard** deve ser sinalizado para revisão antes de render; não suprimir o CTA silenciosamente e chamar de aprovado.
CTA nunca deve tapar fonte, legenda ou informação factual.

## 10. Controle de ritmo e som
- Nova informação visual no máximo a cada 3 s; câmera sozinha não vale como nova informação.
- Trocas de legenda no tempo real da fala; blocos legíveis, sem flash ou palavra solta de 0,1 s.
- Som master alvo ~−14 LUFS, pico verdadeiro <=−1 dBTP; SFX somente em acontecimentos.
- Gráficos e acontecimentos têm timing narrativo; sem efeito apenas para encher a tela.

## 11. Política de qualidade / portões
1. **Contrato editorial:** referência A define linguagem; o canal define tokens; episódio só escolhe conteúdo e acontecimentos.
2. **Preflight:** licença e origem dos assets; mapa visível e nítido, coordenadas, unidades, textos, hierarquia, zonas de identidade, CTA planejado, gancho visual, progressão.
3. **Prova visual barata:** quadros 1080 + celular + trecho curto de animação, comparados à referência; corrigir antes do render inteiro.
4. **Render final** somente após validação técnica e sinalização humana do padrão.
5. **Regressões:** todo erro recorrente vira teste automatizado nomeado (com ID de execução).
6. **Cache:** reutilizar mídia, voz e renders que tenham os mesmos hashes de entrada. Nunca confiar somente no nome do arquivo.
7. **Entregas:** status técnico distinto de aprovação estética. 62 testes passando não significam que a edição foi aprovada.

## 12. Faça / não faça
| FAÇA | NÃO FAÇA |
|---|---|
| Base de mapa satélite com textura e créditos | Vetor pastel / grade genérica como substituto |
| Cartão reto, centralizado, coerente | Cartão torto, flutuando ou sem hierarquia |
| Fundo técnico marinho sutil | Quadriculado verde/neon |
| Pino protagonista grande e correto | Retrato pequeno ou troca de pessoa por prédio |
| Legenda acima dos créditos, ambos legíveis | Fontes sobre a fala ou no espaço da interface |
| Primeiros 3 s com acontecimento | Logo/intro vazia ou mapa imóvel |
| CTA reservado no storyboard | CTA sumir porque não coube |
| Teste visual antes de render completo | 51 min de render só para ver erro antigo |

**Critério final:** aprovado pelo responsável humano em referência lado a lado e em assunto novo; sem aprovação automática por testes verdes.
