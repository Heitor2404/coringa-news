# Comparativo de direções A × C: Coringa Motion 2D

**Data:** 21/11/2026  
**Escopo:** somente escolha estética e auditoria preliminar. **NÃO é render do motor**, NÃO foi enviado ao Telegram, **NÃO publicar**. Branch `atlas-direcao-visual-20261118`; `main`, NTC, DOSSIÊ e `FilmeEditorial` não foram alterados.

## Motivo

O usuário disse explicitamente: **“Eu preferi a opção A, mas tbm achei elas praticamente o mesmo estilo”**. Isso invalida a comparação A/B anterior como disputa de direções de arte. A ficou preferida **entre duas variações próximas**, não foi homologada como identidade definitiva. Foi solicitado “Prossiga” e esta rodada produziu uma opção *gráfica genuinamente distinta* para avaliação estética.

## Materiais realmente produzidos nesta conversa

| Entrega | Caminho na conversa | Observação |
|---|---|---|
| Referência existente A: eclusa/EUV renderizados como concept art | `/mnt/data/Coringa_Storyboard_A_20261121.png` | Já era a opção preferida do usuário; visual volumétrico ilustrado, cobalto/amarelo |
| **C: eclusa vetorial expressiva** | `/mnt/data/Coringa_Storyboard_C_Eclusa_20261121.png` | 5 quadros originais, rosa-coral/turquesa/roxo, silhuetas recortadas e títulos cinéticos; criada imagem estática, NÃO SVG do motor |
| **C: EUV desenho vetorial 2D** | `/mnt/data/Coringa_Direcao_C_EUV_VETOR_20261121.png` | 5 quadros com fonte, máscara reflexiva, espelhos, wafer e padrão exposto; desenhado programaticamente em SVG didático, **não escala nem geometria exata do equipamento** |
| Fonte SVG do EUV editável | `/mnt/data/Coringa_Direcao_C_EUV_VETOR_20261121.svg` | Arte de conceito programática local; não integrada ao Remotion |
| Comparativo eclusa com duas ações iguais | `/mnt/data/Coringa_Comparativo_Real_A_vs_C_Eclusa_20261121.jpg` | Entrada de água, navio subindo; dimensões igualadas por resize proporcional, sem chamar as composições de idênticas |
| Comparativo EUV por componente | `/mnt/data/Coringa_Comparativo_A_vs_C_EUV_20261121.jpg` | Fonte, espelhos e wafer: os componentes são os mesmos, **mas os enquadramentos e o detalhe didático diferem**, não é rigoroso A/B frame-a-frame |
| Mock de interfaces para C/eclusa | `/mnt/data/Coringa_C_Mock_3_Redes_20261121.jpg` | Perfil conservador do projeto, visualização **simulada** em canvas 1080×1920 por resize proporcional de um painel; NÃO tela oficial/validação final |

**Nota operacional:** as imagens raster foram entregues como artefatos da conversa, não enviadas ao repositório. Os caminhos acima são da sessão, não URLs permanentes do GitHub. Houve gerações experimentais extras que repetiram o Canal do Panamá quando o EUV era solicitado e incluíram números incorretos; foram **descartadas** e não fazem parte do conjunto de aprovação.

## Diferença VISUAL real

| Critério | A: ilustrado técnico | C: vetor gráfico expressivo |
|---|---|---|
| Acabamento | Volumetria, luz/gradientes, quase 3D | Manchas de cor, contornos grossos, sensação de animação editorial/cartum 2D |
| Paleta | Azul/ciano + amarelo/laranja | Roxo-escuro + coral + turquesa + creme |
| Estrutura da eclusa | Componentes e cortes técnicos dispersos por cada frame | A mesma câmara + tubulação + cargueiro aparecem conectados durante as cinco etapas |
| Informação | Etiquetas e métricas frequentes, nem todas validadas | Mensagens curtas por acontecimento, sem números |
| Escalabilidade automática | Exige muitos assets com profundidade/artes refinadas | Formas planas são mais viáveis em SVG e geometria por estado, porém qualidade de ilustração/continuidade ainda requer biblioteca |
| Maior risco | 3D ilustrativo genérico e números automáticos | Ilustração pode ficar infantil ou simples demais; balões/títulos grandes podem devorar área útil |

**Parecer técnico independente:** a C representa uma direção **substancialmente diferente** da A na eclusa. **Entretanto**, a versão vetorial didática do EUV ficou mais esquemática do que a eclusa e NÃO comprovou consistência de acabamento entre temas. Não declarar vitória, nem afirmar que o SVG de EUV já é um módulo universal. O usuário não avaliou C nesta rodada.

## Física e procedência — portões de segurança

- **Eclusa:** referência do Canal do Panamá `https://pancanal.com/en/design-of-the-locks/`. A água passa por galerias e válvulas por gravidade, elevando o navio que flutua. Evitar representar água empurrando o casco, elevar o navio acima da superfície ou atribuir 26m a uma única câmara. O painel C não traz valores de altura, deliberadamente.
- **EUV:** referência ASML `https://www.asml.com/en/careers/technical-fields/optical-engineering-jobs`. Fonte → iluminador → máscara **reflexiva** → espelhos de projeção → exposição no wafer. Os raios luminosos desenhados são marcações DIDÁTICAS; a luz EUV não é visualmente roxa/amarela para o olho humano. O resultado é **padrão exposto na resina**, não um chip completo.
- Ambos são STORYBOARDS ARTÍSTICOS, não simulação geométrica final; não usar essas imagens como afirmação de posição exata dos órgãos dentro de máquinas reais.

## Safe area testada apenas como MOCK

Usamos perfis `src/v4/formatos/plataformas.json`, `ativos_seguros` da branch experimental:
- `instagram_reels_multiplataforma`: topo270, base672, margem esquerda70, coluna direita300 desde y840.
- `tiktok_multiplataforma`: topo240, base660, esquerda120, direita300 desde y840.
- `youtube_shorts_multiplataforma`: topo280, base660, esquerda110, direita300 desde y840.

Resultados visuais: no quadro C “NAVIO SOBE”, **a marca no topo fica parcial ou totalmente sobreposta ao envelope de interface e a ligação do duto inferior avança para a faixa coberta**. A leitura principal do navio é relativamente robusta, mas isso **não homologa** as conexões e a legenda. A máscara foi aplicada a um painel proporcionalmente adaptado a 1080×1920, não nativo. Precisamos de templates verticais originais com camadas semânticas e teste no app antes de publicar. A foto do editor do Instagram do usuário não define os limites oficiais de Reels publicado.

## Próximo gate — uma escolha, não dois motores

1. O usuário vê o novo C/eclusa e o EUV C (este último mais esquemático), comparando com A, e responde se prefere o impacto de A ou a linguagem gráfica de C. **Não forçar a C só por ela ser mais fácil de automatizar.**
2. Caso prefira C, elevar **a qualidade ilustrativa do EUV ao mesmo nível da eclusa**. Caso prefira A, propor uma implementação 2D com aparência de profundidade leve, sem 3D pesado.
3. Fixar UM storyboard com 5 eventos/mesma geometria para duas famílias independentes, em nativo 1080×1920, com sobreposição realista das três UIs, fonte e legenda legíveis.
4. Só então autorizar um clipe curto no motor Remotion; derivar `actors`, `connections`, `events` e registrar capacidades ausentes em vez de inventar imagens.
5. Não publicar até teste completo com áudio, fact-check, licenças e visual em apps.

**Conclusão:** esta etapa efetivamente produziu uma alternativa estética nova e comparativos inspecionáveis. **Não produziu uma animação nova** nem demonstrou um compositor universal.


## Decisão posterior explícita do usuário — C REJEITADA (21/11, 13:42)

Após ver o storyboard C e enviar captura de um Reels para ilustrar o uso do espaço, o usuário declarou expressamente: **“Nao gostei da direção C”**. Qualquer interpretação anterior de “Gostei” como aprovação da C estava ERRADA: a captura era uma observação sobre a UI ocupar pouco espaço impeditivo na prática, e **não endossava C**.

**Decisão válida:** A continua como referência estética principal (preferência previamente expressa), embora A NÃO esteja aprovada para produção ou com física/safe homologadas. A versão C é **REPROVADA ESTETICAMENTE**, não deve ser promovida, recomendada como padrão ou confundida com preferência do usuário. Preservar somente como artefato de estudo e comparativo.

**Próximo passo:** desenvolver a linguagem A em 9:16 nativo, com mecanismo maior, ambiente visual impactante, textos e conectores causais essenciais protegidos por zonas de UI dependentes da altura. A imagem do Reels enviada é evidência de que não se deve encolher tudo; não representa medida oficial universal de máscaras. Não adicionar mais um estilo D nem repetir A/B de renders quase iguais. Primeiro uma prova curta e fiel à A em duas famílias, com checagem técnica EUV reflexiva e eclusa por gravidade. Nenhuma alteração da produção autorizada pela preferência estética.
