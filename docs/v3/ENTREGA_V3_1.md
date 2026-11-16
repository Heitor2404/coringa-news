# Coringa Explica V3.1: diretor automático, biblioteca, memória (entrega de 16/11/2026)

Branch `piloto-v24-lagartixa`. Commit inicial: `c317e1d`. Commits deste escopo: `346e5c8`, `dc147e8`, `719bd13` e o desta entrega.
Nada foi feito em `main`, no NTC ou na produção. Não houve merge, publicação nem envio ao Telegram, e nenhum serviço pago foi contratado.

## Recomendação: GO para piloto supervisionado, NO-GO para produção automática

O storyboard agora é escrito pelo modelo, sem intervenção manual, e é esse storyboard que vai para a montagem. Isso funcionou em 8 de 8 temas: 5 de regressão e 3 inéditos.
- **Fluxo completo:** os 8 chegaram ao MP4 na rodada final.
- **Fiscal:** 4 passaram (Panamá, Pisa, Londres 1666 e Voyager); os outros 4 foram barrados por bloqueio objetivo.
- **Bloqueios:**
  - loudness entre −15,1 e −16,8 LUFS em 3 vídeos;
  - um falso positivo do fiscal no Titanic, já corrigido.
- **Aprovação estética:** é do Heitor.

Ainda não é produção por quatro motivos:
- a masterização falha em 3 de 8 vídeos;
- o custo do diretor é de ≈ US$ 0,23 a 0,31 por vídeo com Claude, acima da meta de US$ 0,30 por vídeo inteiro;
- composições V2 com dados fracos do contrato ainda aparecem (cartão `processo.etapas` com título errado e número sem unidade no Voyager);
- falta a avaliação humana dos MP4s.

## 1–5. Ferramentas e licenças
Ver `docs/v3/INVENTARIO_FERRAMENTAS.md`.
- **Instaladas/integradas:**
  - PySceneDetect (BSD-3) no fiscal;
  - ffmpeg-skill (MIT) como skill de desenvolvimento;
  - transições `whip` e `iris` (padrões HyperFrames, Apache-2.0, atribuição em `src/render/v2/NOTICE.md`);
  - OpenCV contrib (Apache-2.0);
  - SQLite.
- **Rejeitadas:**
  - snapcn: licença não verificável e site inacessível daqui;
  - ai-design-skills: só Figma e landing page;
  - video-use: exige ElevenLabs pago (aproveitei só a metodologia);
  - skills oficiais HyperFrames: servem ao CLI deles, e `media-use` usa HeyGen pago;
  - `before-after-wipe`: já existe `comparacao.antes_depois`.
- **Vídeos de referência:** os do YouTube não abrem deste ambiente e **não foram assistidos**. As técnicas do brief viraram regras verificáveis (tabela no inventário).

## 6. Biblioteca de mídia funcionando (`src/v3/biblioteca.py`)
- **Estrutura:**
  - SQLite com migrações;
  - ID estável `cm-<sha12>` (o `a3` passa a ser alias por vídeo);
  - sha256 + pHash;
  - licença classificada (sim/não/indefinido; indefinido nunca é liberado) e IA marcada;
  - regiões e análises presas ao sha;
  - histórico de uso.
- **Manifesto versionado:** `data/biblioteca/manifesto.jsonl`, com 258 mídias de 8 vídeos.
- **Rodada 1:** o manifesto foi exportado, commitado e importado na rodada 2.
- **Rodada 2 (evidência de reuso entre execuções):**

  | Vídeo | Arquivos reconhecidos pelo sha | Regiões reaproveitadas sem chamar a visão |
  |---|---|---|
  | Pompeia | 29 | 5 |
  | Panamá | 32 | 2 |
  | Pisa | 35 | 5 |
  | Londres | 19 | 2 |

- **Rodada 3:** Titanic com 8 regiões reaproveitadas e 0 novas.
- **Recuperação entre temas diferentes** (mídia de outro vídeo oferecida ao diretor): funciona no teste. Nos 8 temas reais não houve sobreposição de assunto, então ficou em 0. É honesto: os temas não compartilham fotos.
- **Armazenamento:**
  - banco e binários ficam fora do Git;
  - a cópia durável é a URL de origem + sha (`recuperar` baixa de novo e confere o hash);
  - o remoto está **desativado**: não há destino aprovado. Candidato gratuito: Releases do repositório privado `coringa-cofre`, cifrado.

## 7. Biblioteca de direção (`src/v3/receitas.json`, `receitas.py`)
- **Conteúdo:** 14 receitas por função narrativa e tipo de acontecimento: 3 aprovadas, 9 testadas e 2 propostas.
- **Recuperação real:** em todos os vídeos, o prompt recebeu receitas aprovadas, por exemplo `R-MECANISMO-ANIMADO`, `R-APROXIMA-OBJETO` e `R-LOCALIZA-RECUA` (`storyboard_ia.json → contexto_recuperado`). As propostas nunca entram.
- **Aprovação das 3 receitas:** veio da sua frase no brief ("A V3 demonstrou melhoria…"), aplicada aos padrões dos vídeos V3. Se não concordar, é só rebaixar o estado.

## 8. Memória persistente
- **`CLAUDE.md`:** curto, na raiz.
- **`docs/memoria/erros.json`:** 22 erros com ID, causa, arquivos, correção e teste. `python -m src.v3.memoria conferir` garante que cada teste existe.
- **Feedback e regras:**
  - feedback por timestamp: `python -m src.v3.memoria feedback <video> <mm:ss> <categoria> "texto" --direcao direcao.json`, que liga o momento ao plano e à receita;
  - regras com estado proposto → testado → aprovado (aprovar sem testar é recusado);
  - só as aprovadas vão ao prompt.
- **Prova de proteção (ERR-001, ano fantasma):**
  - revertendo as duas camadas da correção (`tempo.js` + `estilo.css`), o teste falha com `['79', '1748']` visíveis;
  - com uma camada só, passa (defesa em profundidade);
  - restaurado, passa.

## 9. Skills
`.claude/skills/coringa-direcao`, `coringa-acervo`, `coringa-edicao`, `coringa-auditoria` e `ffmpeg-skill`.

## 10. Diretor automático integrado
- **Ativação:** `MOTOR_VISUAL=v3` em `main.py` aproveita a pesquisa, os contratos e o checkpoint do v2 e entrega a direção a `src/v3/pipeline.py`.
- **Chamadas:** 1 chamada + no máximo 1 correção dirigida pelo validador, mais 1 correção se a prévia mostrar texto sobre texto. Depois disso, bloqueia.
- **Tempos:** vêm da fala alinhada.
- **Modelos:** Claude por padrão. Na rodada 3, o limite de 5 h do Claude estourou e o diretor caiu sozinho para o Gemini grátis (céu azul e Voyager). O Voyager dirigido pelo Gemini passou no fiscal, o que abre a opção de custo zero.
- **Auditoria por vídeo:** `storyboard_ia.json` guarda o prompt, a resposta original, as correções e o consumo.

## 11. Fiscal integrado (`src/v3/fiscal_editorial.py`)
- **Técnico:** resolução, duração, áudio, loudness/pico e cortes reais × planejados (PySceneDetect).
- **Editorial:**
  - pergunta central;
  - um mecanismo crítico precisa ser demonstrado;
  - o id no storyboard não comprova cobertura;
  - objeto localizado;
  - plano sem direção de atenção;
  - rótulo que repete a fala;
  - número fora da pesquisa;
  - monotonia e cara de slideshow.
- **Classes de achado:** bloqueio / revisão / estética.
- **Calibração do PySceneDetect** (Pisa real, 12 transições planejadas):

  | Limiar | Recall | Inesperados |
  |---|---|---|
  | 12 | 0,75 | 6 |
  | 27 | 0,33 | 2 |

  Fica 27: dissolve, íris e deslize são graduais. A detecção serve para achar a mudança inesperada dentro de um plano, não para medir a qualidade.

## 12. Testes
- **V3.1:** `tests/test_v3_*.py` com 47 testes, todos passando, mais o `test_v3_diretor` (16).
- **Suíte inteira:** 789 passaram, 12 falharam e 13 foram pulados. As 12 falhas são de ambiente ou anteriores a este escopo:
  - Natural Earth ausente nesta máquina (v21/v22);
  - prompts do cofre privado;
  - caso polvo;
  - matriz v25.
  As duas falhas causadas por esta entrega foram corrigidas: `.env.example` e um teste que conferia o texto exato da condição do motor.

## 13–15. Execuções reais (GitHub Actions, uma tentativa por caso)

| Tema | Grupo | Rodada | Resultado | Planos | Parado | Vazio | Anotações | LUFS |
|---|---|---|---|---|---|---|---|---|
| Panamá | regressão | 2 | **aprovado pelo fiscal** | 11 | 26% | 33% | 6 | −14,6 |
| Pisa | regressão | 2 | **aprovado pelo fiscal** | 15 | 24% | 19% | 10 | −14,5 |
| Londres 1666 | **inédito** (fluxo completo) | 2 | **aprovado pelo fiscal** | 16 | 27% | 28% | 10 | −14,4 |
| Voyager 1 | **inédito** (fluxo completo) | 3 | **aprovado pelo fiscal** (diretor Gemini) | 14 | 40% | 43% | 7 | −14,6 |
| Pompeia | regressão | 3 | MP4, bloqueado: loudness | 18 | 30% | 35% | 8 | −15,3 |
| Titanic | regressão | 3 | MP4, bloqueado: "04" de 10/04/1912 (falso positivo do fiscal, **corrigido depois**) | 14 | 38% | 41% | 6 | −15,0 |
| Lagartixa | regressão | 3 | MP4, bloqueado: loudness | 14 | 52% | 46% | 4 | −16,8 |
| Céu azul | **inédito** (checkpoint nunca usado na V3) | 3 | MP4, bloqueado: loudness | 13 | 61% | 52% | 4 | −15,1 |

Referência V3 manual (Pompeia): 33% parado, 12% vazio.
- **Fotos reais:** os automáticos com mais foto real (Pisa, Panamá, Londres) chegam perto: 24–27% parado.
- **Esquemas:** os de ciência com esquema (lagartixa, céu azul) ficam muito mais parados.

As **três rodadas** acharam 7 defeitos gerais, corrigidos com teste:
- ERR-017: data, hora e "nós" viravam números;
- ERR-018: `ate_desvio: true` derrubava a montagem;
- ERR-019: OpenCV sem saliência;
- ERR-020: tempos em formato que a composição não lê e 5,5° exibido como "6";
- ERR-021: vídeo apontando para o quadro;
- ERR-022: mecanismo sem dados não tinha saída; agora o diretor escreve o esquema (`mecanismo.estados`), conferido por código;
- o falso positivo de data também no fiscal.

Nenhuma correção foi específica de um tema.

## 16. Custos (dinheiro gasto: US$ 0)
- **Diretor:**
  - Claude Sonnet pela assinatura: US$ 0,23–0,31 por vídeo, sempre 2 chamadas porque a primeira resposta tem algum erro;
  - Gemini: US$ 0.
- **Pesquisa e roteiro de tema novo:** ≈ US$ 0,63 em crédito da assinatura (Voyager, rodada 1). Na rodada 3 foi reaproveitada do checkpoint cifrado: US$ 0.
- **Visão:** cota grátis do Gemini (chave principal esgotou e o modelo lite assumiu).
- **Tempo por vídeo no Actions:**
  - diretor: 1–1,5 min;
  - visão: 1–6 min (cai com o reuso);
  - render: 2,6–6 min.
- **Total por tema novo com Claude:** ≈ US$ 0,9 de crédito. Acima da meta.

## 17. Problemas não resolvidos
1. **Loudness** fora da meta em 3/8 (−15 a −16,8). A causa provável é a mistura com música ou a voz lite. Precisa de diagnóstico no `render.py`.
2. **Composições V2 alimentadas por contrato pobre:**
   - `processo.etapas` com título tirado do campo "mostrar" ("Gravura de 1674 de contexto");
   - número sem unidade no cartão do Voyager (`25,9`).
   Causa: o contrato do roteirista.
3. **Vazio e parado** altos nos temas de ciência; os esquemas usam só o meio da tela.
4. **Imagem duvidosa:** o diretor ainda escolhe imagem fraca às vezes (pôster tipográfico "One Light Day" como CONTEXTO no Voyager).
5. **Custo do diretor com Claude acima da meta.** Testar o Gemini como padrão está alinhado ao resultado do Voyager.
6. **Biblioteca remota:** desativada até você aprovar um destino.

## Onde está tudo
- **Resultados cifrados:** ramo `v3-validacao-resultado` (execuções 43811511302, 43818596529 e 43827356241).
- **Chave privada descartável:** só na máquina de análise (`~/.piloto_gpg_v3`).
