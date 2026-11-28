# F8 — ponte de peça visual SVG auditável (23/11/2026)

**Status: validação técnica concluída. Direção de arte NÃO homologada.**

## Objetivo comprovado

Um compositor de biela-manivela existente passa a montar, em modo **opt-in**, uma carcaça SVG de arquivo separado, validada por SHA256, autoria interna, âncoras e restrições de conteúdo. O caminho é **arquivo → manifesto → validação → peça no SVG do quadro → MP4**. F7 permanece a configuração padrão.

Isto **não é** reconhecimento de um componente numa foto, nem scraping de imagem, nem licença industrial, nem reconstrução automática de máquina nova. A peça de prova é desenhada originalmente pelo laboratório e declarada `identity_match_verified=false`.

## Arquivos

- `src/v4/formatos/pecas_visuais_f8.py`: gate de SHA, XML, atributos, caminhos internos, composição escalável com âncoras.
- `src/v4/formatos/referencias_visuais_f8/manifesto.json`: ator `cylinder`, tipo `chamber`, SHA e direitos internos, publicação bloqueada.
- `src/v4/formatos/referencias_visuais_f8/cylinder_shell_f8.svg`: arte vetorial autoral sem pixel externo.
- `src/v4/formatos/compositor_cinematico_parametrico_2d.py`: parâmetro opcional `visual_parts`, CLI `--visual-f8`; carcaça substituída sem tocar nos movimentos, físico, header e rodapé.
- `tests/test_pecas_visuais_f8.py`, `.github/workflows/qa-pecas-visuais-f8.yml`: testes e vídeos privados; sem Claude, Telegram ou postagem.

## Evidência

- Run F8: https://github.com/Heitor2404/coringa-news/actions/runs/45120024136 — **SUCCESS, 48 testes**.
- Run regressão F7: https://github.com/Heitor2404/coringa-news/actions/runs/45119925085 — **SUCCESS, 85 testes e 11 avisos de Pillow**.
- Artefato de F8 `lab-f8-peca-svg-autoral-tres-mp4s-privados`, ID `14792598868`, retenção até **28/11/2026 ~05h49 UTC**.
- Vídeos (todos 540×960, 24fps, 9 segundos, sem áudio; privados):
  - `BIELA_F7_BASELINE.mp4`, SHA256 `9dd2ec0e0f58b874f710774c1c4bf7a2dc982c45bcaa6747a0ea1a30367b71e3`;
  - `BIELA_CURTO_F8_PECA_INTERNA.mp4`, SHA256 `54cceab2ad52bdae9c0111f0e65dd018dd41c6e99027c97ee4f3fe8aca40cf08`;
  - `BIELA_LONGO_F8_PECA_INTERNA.mp4`, SHA256 `f0d58a3655a15eef0a2f54b93c36f887284a95075651701ad2f6d08ca071fe52`.
- `COMPARATIVO_F7_VS_F8_3_VIDEOS_12_QUADROS.jpg` foi aberto e analisado. Há mudança REAL na carcaça, sobretudo aletas, parafusos e superfície do cilindro; o mecanismo e a câmera seguem. **O impacto visual total é pequeno**. Não é uma melhora cinematográfica significativa.
- Testes negativos verificam recusa de SVG com script/URL, mudança de ator, SHA adulterado, suposta licença, ausência de direitos e publicação. O gate de direitos é intencionalmente restrito a arte interna, não certifica legislação de arquivos externos.

## Não foi feito

- Ingestão de imagem industrial de terceiros ou conferência de sua licença específica.
- Mapeamento automático de peça extraída de fotos para rig físico; reconhecimento de partes.
- Conversão parametrizada de CAD/3D; geometria em unidades físicas; novos mecanismos externos.
- Aprovação de identidade da máquina, experiência em celular, publicação, integração ao `FilmeEditorial`.

## Próximo gate concreto

1. Escolher **uma peça externa** que resolva um problema de identidade do compressor de oficina completo (ex.: cabeçote com aletas) com arquivo transferível e licença de uso/reprodução comprovada. Registrar página, autor, tipo de licença, URL de versão, SHA real e aprovação editorial. **Não copiar com base apenas em página técnica.**
2. Delimitar a montagem física dessa peça: origem, escala, ponto de encaixe e restrições visuais; contraprova com duas cenas do mesmo tipo sem distorcer câmera, pistão ou válvulas.
3. Renderizar prévia privada em condição real de Reels, TikTok e Shorts, auditar visualmente conteúdo e recorte, verificar que a aparência representa corretamente a máquina antes de homologar.
4. Ampliar para outro componente e outra família **somente após** primeira ingestão referenciada, sem criar renderizador por assunto nem assumir qualquer IA gratuita.
5. Manter `F-VISUAL-LEGADO-DESCARTADO`, câmera estável e bloqueio de publicação.

`main`, produção documental, NTC, DOSSIÊ e Telegram foram preservados.
