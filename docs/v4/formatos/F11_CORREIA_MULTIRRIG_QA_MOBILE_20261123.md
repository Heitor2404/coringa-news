# F11 — correia multirrig e auditoria real de sobreposição em telas verticais

Data: **23/11/2026 ~03h24 BRT**. Branch exclusivamente experimental `atlas-direcao-visual-20261118`.

**Situação:** F11 APROVADA tecnicamente; segurança de interface e estética **NÃO homologadas**. **NÃO publicar**. Não converter relatório dos perfis conservadores em afirmação sobre UI real exata.

## 1. Implementação comprovada

- A função única `primitivas_fisicas_parametricas.transmissao_correia`, usada no compressor completo F10, agora também é acionada para marcações móveis por `compositor_cinematico_parametrico_2d.frame_svg(...,transmissao_animada=True)`. Dois mecanismos biela-manivela parametrizados via JSON (*curso curto 92 px, curso longo 128 px*) compartilham a mesma primitiva e o mesmo compositor.
- A distância de marca ideal `theta × raio_volante` acompanha as equações de correia sem escorregamento. Física de pressão/combustão não é deduzida dessa marcação. Sem Claude, sem imagem externa, sem duplicar implementação para cada vídeo.
- `--transmissao-animada` opt-in; o modo F7 sem a flag produziu exatamente o **MESMO SHA256 do vídeo F7 original**. Câmera travada sem pan de fase; rotor, pistão, biela, texto e rodapé preservados. A mudança visual é localizada à correia.
- Novo `qa_svg_mobile_f11.py` mede **pixels visíveis** de quatro atores críticos: para cada instante, retira apenas o grupo SVG do papel, renderiza frame de referência/sem papel em memória e mede a diferença. A sobreposição é calculada contra as máscaras de `layout.mascaras` obtidas de `plataformas.json:ativos_seguros`. Não usa a bbox de movimento da câmera como se fosse bbox visual do frame. Cria folhas com imagem original e simulações de interfaces TikTok/Reels/Shorts.
- Novo teste `tests/test_qa_svg_mobile_f11.py` e workflow `.github/workflows/qa-transmissao-multirrig-f11.yml`. Não substituiu modelos rejeitados em `FilmeEditorial`, nem tocou na publicação.

## 2. Evidência GitHub Actions

- **Run F11 FINAL:** https://github.com/Heitor2404/coringa-news/actions/runs/45123709031 — **SUCCESS, 50 testes aprovados**, regressões F10/F7/F2, vídeos renderizados, perfis inspecionados por SVG.
- Regresões F7 e F8 independentes após alteração do compositor: runs `45123521501` e `45123521194` — SUCCESS.
- Artifact privado `lab-f11-correia-multirrig-mascaras-mobile-privado`, ID **14794427961**, expira em **28/11/2026 ~06h24 UTC**. ZIP baixado, vídeos + quadros + JSONs extraídos e prancha visual inspecionada; duração de todos os MP4s 9s, 540×960, 24fps, mudo:
  - `BIELA_CURTO_F7_BASELINE.mp4`: SHA256 **`9dd2ec0e0f58b874f710774c1c4bf7a2dc982c45bcaa6747a0ea1a30367b71e3`**, idêntico à F7.
  - `BIELA_CURTO_F11_CORREIA.mp4`: SHA256 **`13b43cb2a5ef39e53774740b84e9119cf2a489c93ce54c734e8ceb0b96ae9451`**.
  - `BIELA_LONGO_F11_CORREIA.mp4`: SHA256 **`609b9e62ae1f912e7444892ce005747840e89f080d08fe2851167d1d8a3d63e5`**.
- `COMPARATIVO_F7_VS_F11_TRES_RIGS_12_QUADROS.jpg`: inspecionada; o mesmo compositor mostra dois cursos diferentes com conectividade das articulações, sem instabilidade de câmera. Marcas de correia têm efeito VISUAL DISCRETO; é avanço físico/de reuso, NÃO salto de identidade industrial nem nível cinematográfico.

## 3. Achado crítico — safe zones NÃO aprovadas

**O novo QA detectou risco substancial de oclusão de componentes essenciais**, mas pelas máscaras **conservadoras estimadas** no repositório, NÃO pela UI real calibrada dos aplicativos:

| Ator visível | Curso curto: pior fração coberta | Curso longo: pior fração coberta |
|---|---:|---:|
| Pistão | 25,61% | 31,58% |
| Biela | 100% em fase crítica | 100% em fase crítica |
| Volante | 100% | 100% |
| Correia | 100% | 100% |

Os valores máximos foram extraídos de `biela_manivela_curso_{curto,longo}_F11_AUDITORIA.json`, amostragem em **1,1s, 3,6s e 6,7s**. As máscaras simulam a faixa inferior muito conservadora (base de 660–672/1920 px) e coluna lateral de até 300/1080 px, por isso **as polias e correia inteiras no rodapé do SVG entram nas zonas marcadas como cobertas**. Os componentes NÃO foram cortados pelo PNG/MP4 original — a oclusão é uma projeção de UI simulada. Isto NÃO autoriza dizer que desaparecem em 100% dos aparelhos reais.

**Decisão:** bloquear homologação de enquadramento e **não encolher automaticamente a máquina** apenas para zerar esses números. O usuário já rejeitou animações minúsculas e pediu ocupar mais palco, especialmente a parte superior. Próximo experimento deverá usar dois perfis: (a) zonas conservadoras, (b) overlays calibrados por screenshot real da interface, e buscar um enquadramento hero com título/legenda reposicionados em vez de só縮 diminuir o objeto. A prova deve demonstrar visualmente presença/legibilidade das partes físicas em tela de celular, não apenas um passe geométrico.

## 4. Próximo trabalho e limites

1. Escolher/validar política de montagem que mantenha volante, correia e pistão com leitura suficiente no período inteiro, sem pan nervoso; avaliar **uso do espaço vertical alto**, compactação editorial e, se necessário, cortes focalizados MOTIVADOS com câmera estática por tomada, em vez de zoom a cada fase.
2. Cruzar masks conservadoras com capturas reais de Reels/TikTok/Shorts para não sacrificar tamanho sem razão; teste com prévias no dispositivo.
3. Vincular a montagem à identidade visual industrial com referência original verificável; F9 Wikimedia ainda 429, hash ausente. Não usar asset de origem desconhecida nem modelo portátil de outra variante.
4. A F11 NÃO resolve geração 2D/3D livre, nem comprova que o sistema conhece mecanismos inéditos ou que o estilo está pronto para postar. Código ainda só laboratório; `main`, NTC, DOSSIÊ, Telegram e produção intocados.
