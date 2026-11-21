# Inspeção visual preliminar — NIST (19/11/2026)

**Projeto:** ATLAS/FilmeEditorial, piloto Taiwan. **Este não é um vídeo da TSMC.**

## Arquivo real e proveniência
- Fonte oficial: https://www.nist.gov/video/inside-instrument-nist-center-nanoscale-science
- Player original: Kaltura partner 684682, entry `1_k2iydnt5`; obtido pelo workflow privado `qa-curadoria-video-processo.yml`, run **44604866932**.
- Candidato baixado `nist_deposicao.mp4`: **9.725.710 bytes**, **720×1280**, **11,833333 s**, 30fps, H.264/AAC.
- SHA-256 do MP4: `9d5d908e11af8af44c45c151db7abc67930c786e81f3e81fed9956d1f1200854`.
- Artefato GitHub Actions **14570545070**, retenção **3 dias**, não é armazenamento permanente da biblioteca.
- O site do NIST explica que o equipamento adiciona camada de metal vaporizado a wafer de silício e que o mecanismo interno gira para uniformizar a deposição. Isso é **descrição da fonte**, não verificação de deposição acontecendo durante todo o vídeo.

## Inspeção independente do arquivo REAL
O MP4 do artifact foi recuperado e conferido em **24 quadros** distribuídos em intervalos de aproximadamente 0,49 s. O contato grande foi analisado visualmente.

- **0–4,7 s:** pesquisadora em traje limpo diante da máquina, com movimentos pequenos. Muito tempo quase igual e texto embutido identificando pesquisadora.
- **~5–8 s:** equipamento aberto, movimento de porta e transição de câmera para o interior. **Mostra claramente a instalação e a abertura da câmara**, não deposição química observável.
- **~8–11,83 s:** componentes dentro do equipamento, com peças em suportes circulares e alumínio nas paredes. As amostras não comprovam diretamente vapor sendo depositado nem demonstram inequivocamente toda a rotação.
- Legendas e textos originais já estão **gravados no próprio vídeo**, inclusive títulos escuros grandes sobre a parte inferior, portanto não é um b-roll limpo para reaproveitar com legendas do Coringa.
- O MP4 contém áudio original; **não reutilizar trilha/som automaticamente**. Direitos específicos, principalmente eventuais músicas, ainda requerem revisão.

## Decisão de curadoria
- **Pode ser considerado como contexto de laboratório real (com fonte explícita NIST)** ou introdução visual de equipamento, após confirmação da licença do arquivo específico e estratégia de enquadramento para texto embutido.
- **NÃO APROVADO** como prova audiovisual de `deposicao_metalica_em_wafer` acontecendo ao vivo. O material parece mais explicativo do que demonstrativo. Não marcar `prova.acao_ou_relacao_visivel=true` nem `prova.processo_verificado` sem visão adicional mais conclusiva.
- Não é TSMC, não demonstra EUV da ASML e não comprova elos comerciais Taiwan–Europa.
- Não passar diretamente para `ponte_biblioteca.catalogo()`. **Estado: CANDIDATO_REAL_INSPECIONADO_PARCIALMENTE / NAO_HOMOLOGADO**, sem render/TTS/Telegram.

## Próxima busca
Obter outra tomada de wafer **em processo observável** (movimento relevante, ação concreta) com licença confirmada. A narração pode dizer "a deposição é uma etapa da fabricação", enquanto o vídeo NIST exibe equipamento como **contexto**, mas não afirmar "agora veja o metal sendo depositado" sem imagem correspondente. Recuperar o vídeo e-beam em resolução reduzida (run posterior) para comparar utilidade; nunca confundir e-beam com EUV.
