# INCIDENTE EDITORIAL P0 — ATLAS V2 / Taiwan e chips (19/11/2026)

**Estado: REPROVADO HUMANAMENTE — NÃO PUBLICAR.** A aprovação automática `AGUARDANDO_APROVACAO_HUMANA` não significa qualidade visual aprovada. O usuário viu a prévia de 32,1 s e a rejeitou integralmente por edição, imagens e mapa distantes. **Congelar novas iterações de render desta versão do piloto** até resolver a direção audiovisual; nenhum teste verde reverte esta reprovação.

## Evidências

- MP4 privado do usuário, 32,133 s, 512×910, 30 fps. Temporalidade do render é observada no próprio MP4, não extrapolada dos testes.
- `preflight` 30/30; 21 quadros de QA, 0 bloqueadores; áudio −14,4 LUFS / −2,3 dBTP; 0 janelas de 4 s preto/congelado; maior trecho visual bruto parado 5 s, sem câmera 2 s; 11/32 s parados.
- Branch experimental `atlas-direcao-visual-20261118`, plano `src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json`, render em `motor4/remotion/src/formatos`.
- Referências A (mapa) e B (dossiê) estão decupadas em `ENGENHARIA_REVERSA_REFERENCIAS.md`, e o documento `ESTUDO_REFERENCIAS_E_DIRECAO_ATLAS_V2_20261118.md` **já apontava explicitamente** que falta de máquina EUV/acontecimento físico, fotos pequenas, mapa como substituto de prova e mapa-múndi excessivo seriam falhas. O motor avançou mesmo assim.
- A matriz `MATRIZ_FIDELIDADE_ATLAS.md` já registrava que mapamúndi 9:16 mostra Antártida/Ártico e recomendava limitar escala ao continente. Não implementado no piloto.

## Decupagem do vídeo entregue — falhas observáveis

| Intervalo aproximado | Imagem real | Problema editorial |
| --- | --- | --- |
| 0–2,5 s | Foto de fachada da Fab 18 sobre mapa de Taiwan, rótulo muda | Fachada genérica e pouco impactante; evidência pequena, mapa compete com ela; não demonstra por que Taiwan importa |
| 2,5–7,2 s | Taiwan destacada em mapa regional + pergunta | Não há relação de dependência visual, apenas localização e texto; câmera ocupa tempo sem acrescentar fato causal |
| ~7–15 s | Foto vertical/escura de wafer, letterbox preto, sobre o mesmo mapa | Fotografia de difícil leitura, sem escala ou explicação visual do wafer. Mudar rótulo não explica fabricação |
| ~15–27 s | Mapa-múndi/continentes repetido; pílulas EUA/Holanda/Taiwan | Europa/EUA/Taiwan apenas nomeados; não se veem máquinas, design, fábrica ou fluxo real; Antártida/área vazia consome tela |
| ~27–32,1 s | Mesmo mapa e slogan `UM ELO AFETA TODOS` | Não existe consequência concreta visual, nem revelação final; CTA não resolve a falta de causalidade |

## Causa-raiz (não é sincronização nem codec)

1. **Planejamento invertido:** o roteiro e as 6 composições foram aceitos antes de validar se havia imagens, mecanismos e encadeamento visual que comprovassem cada frase.
2. **Escassez de acervo transformada em aprovação:** o workflow privado exige *exatamente* 2 fotos e 6 beats, e considera suficiente ter hash/licença; não avalia qualidade de enquadramento, relevância nem se a fala exige imagem/máquina adicional. A biblioteca não supre ASML/EUV/projeto de chip. **O correto seria devolver BLOQUEIO_EDITORIAL_SEM_PROVA, não usar o mapa como preenchimento.**
3. **Mapa virou plano-padrão mesmo quando geografia não explica o fato:** 4/6 beats são essencialmente mapa com títulos/etiquetas, e até os 2 planos fotográficos mantêm mapa ao fundo. O cálculo `camera_roi` enquadra ROIs continentais enormes no quadro vertical, apresentando vastas áreas irrelevantes.
4. **Fiscal testa funcionamento, não entendimento:** `F-SEM-PROGRESSAO` conta entradas de rótulo e destaques; o ritmo do MP4 desconta movimento de câmera, permitindo cenas perceptivamente repetidas. Falta teste de se a ação narrada foi representada ou de diversidade semântica apropriada. A aprovação técnica foi comunicada em excesso como avanço de qualidade.
5. **Referências transformadas em parâmetros geométricos, não em direção:** medidas de zoom, slots, cores e tipografia foram copiadas para presets, mas não a sequência `objeto → ação → relação → consequência`. A referência A tem palco persistente, **mas camadas informativas novas a cada 1–2 s**, não mapas vazios com etiquetas. A referência B usa objetos documentais que comprovam a narração; não valida substituir máquina por um card.

## Mudança de abordagem exigida (não iniciar novo render antes)

1. **Reprovar explicitamente o piloto atual.** Não publicar, não usar como base, não ajustar apenas fonte, rótulo, limites de câmera ou animação decorativa.
2. **Inventário de capacidade ANTES do storyboard:** classificar cada frase com `referente físico`, `pergunta visual`, `ação observável`, `evidência exigida`, `asset licenciado disponível`. Sem o mínimo para o fato central: `BLOQUEIO_EDITORIAL_SEM_PROVA`. Não inventar imagens nem licenças.
3. **Roteiro visual antes da narração final**: comparar proposta de 6–8 quadros fundamentais contra as duas referências *pela função narrativa*, e aprovar a variedade de meios motivada pelo tema (foto real em destaque, close-up de chip, mecanismo correto, relação cartográfica concreta, consequência). Não impor número arbitrário de cortes.
4. **Mapa com intenção e enquadramento legível:** use mapa apenas para localizar, mostrar rota/relação real ou consequência espacial. No 9:16, rejeite enquadramentos continentais em que o assunto ocupa pequena fração e polos/área morta dominam; nunca permitir Antártida como elemento principal em vídeo de semicondutores.
5. **Prévia visual curta de baixo custo ANTES do TTS:** usar conteúdo licenciado e quadros de storyboard/animatic sem gerar voz Gemini ou MP4 completo até aprovação humana da gramática. Portões técnicos permanecem, mas são piso, não objetivo.
6. **Portão editorial semântico e humano:** quadro `fala → imagem → o que o público aprendeu`; fotos e fluxos que não demonstram o que foi dito tornam a cena inadequada, mesmo com áudio e geometria perfeitos.
7. **Generalização:** implementar regras e biblioteca de componentes reutilizáveis no ATLAS, não remendos específicos de Taiwan. Preservar `main`, produção V4, DOSSIÊ e NTC.

## Decisão e bloqueio

**P0 de qualidade audiovisual.** Não gerar outra prévia desta configuração, nem tratar `AGUARDANDO_APROVACAO_HUMANA` como "bom". Nenhuma alteração de código ou render foi feita por esta auditoria; documento serve como contrato para a próxima fase. O vídeo de Taiwan apresentado é uma evidência de falha do processo editorial atual, não de validação estética do ATLAS.
