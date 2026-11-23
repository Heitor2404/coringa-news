# F17 — ligações mecânicas com evidência individual e plano de lacunas de núcleo

**Data:** 23/11/2026, 11h44 BRT  
**Estado:** F17 VALIDADA tecnicamente no ramo \`atlas-direcao-visual-20261118\`. **Nenhum renderer novo, nenhuma visualização industrial ou publicação.**

## Escopo entregue

A F16 confirmava três trechos de texto por documento e escolhia um padrão rígido por conjunto de frases. A F17 adiciona o módulo \`src/v4/formatos/relacoes_com_evidencia_f17.py\`, que transforma **cada trecho técnico comprovado** em nenhuma ou uma relação candidata. Cada aresta informa \`from\`, \`to\`, \`joint\`, \`supported_span_ids\`, \`matched_phrase\` e \`direction_confirmed\`. A fonte e os trechos continuam sob o downloader HTTPS allowlisted da F16, com hash real dos bytes da página.

O classificador não utiliza nome do documento nem URL para escolher a topologia: lê apenas relações e tipos detectados. Aceita um **pequeno vocabulário de expressões mecânicas e sinônimos**; não é reconhecimento linguístico geral nem pesquisa livre. Menções de duas peças no mesmo parágrafo **não viram articulação por inferência**. Uma frase negada não confirma ligação.

### Validação real

**GitHub Actions FINAL:** https://github.com/Heitor2404/coringa-news/actions/runs/45196795461 — **SUCCESS, 49 testes aprovados** (F17 + regressões F16/F15 selecionadas). O workflow produziu relatório de quatro fontes e exigiu que cada ligação tivesse pelo menos um identificador de citação. Não usou Claude, IA paga, imagens externas nem FFmpeg.

**Artifact:** \`lab-f17-arestas-com-citacoes-e-plano-hidraulico-privado\`, ID **14827908061**, expira **28/11/2026 ~14h41 UTC**. ZIP \`F17_PROVAS_E_PLANO_HIDRAULICO.zip\` efetivamente baixado e aberto. Arquivos:
- \`QA_F17.json\`
- \`par_engrenagens_educacional_F17_RELATIONS.json\`
- \`biela_cinematica_parcial_F17_RELATIONS.json\`
- \`plataforma_tesoura_fonte_alternativa_F17_RELATIONS.json\`
- \`plataforma_tesoura_hidraulica_F17_RELATIONS.json\`

### Resultados de auditoria da página (novamente verificados via HTTPS nesta CI)

| Fonte | Prova HTTP | Relações citadas | Resultado |
|---|---|---|---|
| Applied Mechanics — engrenagens | CONFIRMADA, SHA \`9ce7ac...fe8b\` | \`gear_1 meshes_with gear_2\`, citação **g2** | Estrutura reconhecida, mas **qual eixo é entrada/saída não foi comprovado**; F15 não compila automaticamente nesta fase |
| Mechanic — biela | CONFIRMADA, SHA \`4b67df...d897\` | \`piston slides_in chamber\`, citação **b3** | Não inventa juntas não demonstradas entre manivela/haste/pistão nem polias/correia; **BLOQUEADO** |
| Hydra Products — tesoura | CONFIRMADA, SHA \`b0259e...b175\` | \`electric_motor drives hydraulic_pump\` (**h1**), \`hydraulic_pump fluid_to hydraulic_cylinder\` (**h2**), \`hydraulic_cylinder pushes scissor_arms\` (**h3**) | **BLOQUEADO: sem kernel hidráulico/tesoura**, mesmo com três relações suportadas |
| AHydraulics — página original | NÃO CONFIRMADA nesta execução, HTTPError | Nenhuma | **BLOQUEADO**, nenhum falso positivo |

O dicionário de fontes e hashes completos está nos JSONs do artifact. Os nomes \`pushes\` e \`fluid_to\` são **normalizações de linguagem técnica em relações abstratas**, não determinação de forças, pressão, posição de pinos ou circuito hidráulico de uma máquina particular.

## Plano de implementação gerado da tesoura

\`plataforma_tesoura_fonte_alternativa_F17_RELATIONS.json\` inclui o campo \`capability_gap\`, com quatro capacidades **a desenvolver, não concluídas**:

1. **\`scissor_linkage_kinematics_2d\`**: braços, comprimento, articulações, bases fixas, plataforma e fechamento de pivôs, sem atravessamentos.
2. **\`cylinder_to_scissor_constraint\`**: montagem fixa e móvel do cilindro, comprimento retraído, curso, alturas mínima e máxima; verificação de poses possíveis.
3. **\`hydraulic_power_and_control\`**: reservatório/retorno, vazão, área do cilindro, limites de pressão e válvulas. Não inferir segurança funcional a partir de desenho didático.
4. **\`licensed_machine_visual_reference\`**: subtipo exato, referência geométrica, autorização de uso de mídia, atribuição e inspeção visual humana.

Referências complementares da literatura — **contexto de engenharia, não páginas automaticamente ingestas nem prova de medidas do objeto**: https://jtambg.eu/papers/2024/JTAM2024_2_232-241.pdf (posição do atuador e características geométricas) e https://www.ahydraulics.com/en/about-us/frequently-asked-questions/frequently-asked-questions-about-scissor-lifts/which-hydraulic-components-are-used-in-a-scissor-lift/ (subsistemas hidráulicos). Não atribuir ao documento Hydra Products dados geométricos ou especificações dessas fontes adicionais.

## Limites e decisão

A F17 entrega **rastreabilidade por aresta** e um **diagnóstico de capacidades faltantes**. Não aprende a reconstruir geometria a partir de vídeo, não interpreta qualquer texto livre, não extrai atributos físicos numéricos da imagem, não possui kernel de tesoura, não possui referência visual industrial licenciada e **não produziu nenhum MP4**. Sua saída não libera automaticamente o compilador F15, a produção ou postagem.

**Próximo gate F18:** adquirir especificação geométrica de um subtipo definido de tesoura e desenvolver um **núcleo mínimo paramétrico de linkage** com teste de fechamento de pivôs, colisões, extensão do cilindro e mudança de altura; só depois criar montagem SVG privada. Integrar fluidos/pressão apenas quando parâmetros e limites forem sustentados. Rejeitar supor uma máquina de fabricante por analogia com um diagrama genérico.

**Produção:** \`main\`, NTC, DOSSIÊ, Telegram, publicação e rotas produtivas intactos. Gates visual/industrial/segurança mobile permanecem fechados.
