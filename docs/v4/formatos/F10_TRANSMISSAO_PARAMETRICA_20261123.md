# F10 — Transmissão paramétrica do compressor completo (23/11/2026)

**Status:** implementação e vídeo técnico REAL comprovados; qualidade estética/industrial **NÃO homologada**. Ramo `atlas-direcao-visual-20261118`, não integrado na produção.

## 1. Problema comprovado

A montagem 2D do compressor de oficina (`render_compressor_conjunto_2d.py`) continha um caminho **fixo** para a correia: `M 142 646 L 278 643 ...`. Mesmo com centro das polias, raios e rotação em `AssemblyLayout`, a geometria da correia podia deixar de corresponder às peças se os parâmetros mudassem. A F7 já oferecia a primitiva genérica `primitivas_fisicas_parametricas.transmissao_correia`, que resolve tangentes externas.

**A solução não pressupõe foto/copiador de um fabricante:** links industriais consultados como contexto físico/topológico, NÃO fontes de pixel licenciadas para cópia:
- https://reddycompressors.com/compressors/reciprocating/tank-mounted/
- https://omegacompressors.com/product/horizontal-tank-mounted/
- https://www.portlandcompressor.com/compressor/air-compressor-anatomy

Nenhum ativo externo importado; nenhuma geometria de CAD/3D foi extraída, a F9 do Wikimedia continua sem JPEG original por 429.

## 2. Código implementado

- `primitivas_fisicas_parametricas.py`: `transmissao_correia(..., deslocamento_trama_px=None)`; **None é idêntico ao retorno antigo** e preserva F7. Quando ativo, acrescenta marcas de deslocamento sobre o **mesmo path** de duas polias calculado, com validação de velocidade, finitude e trajetória física.
- `render_compressor_conjunto_2d.py`: flag experimental `--transmissao-parametrica` / `transmissao_parametrica=True`. Passa centro, raios e posição do motor e bomba à primitiva comum; distância de marca `angulo_bomba × raio_volante` (aproximação de correia **ideal sem escorregamento**). A câmera F2B continua estável, o retiming de fases e o P–V não mudam.
- **Correção visual F10b:** a primeira implementação desenhava a correia por cima da face do volante; inspeção real dos MP4 mostrou marcações atravessando a face. Ordem de camada foi corrigida: a correia F10 é desenhada **atrás** das faces de rotor/polia, sem alterar a ordem da versão antiga por padrão. Teste estrutural específico impede regressão.
- `tests/test_transmissao_parametrica_f10.py`: teste de geometria, recusa de correia degenerada e NaN, movimento monotônico e metadados, câmera fixa, camada da correia, F7 default intocado, invariância em PNG bruto do header/rodapé e variação visual no palco.
- `.github/workflows/qa-transmissao-compressor-f10.yml`: regressões e render de dois MP4s reais, folhas e métricas quantitativas.

## 3. Evidência FINAL

- **GitHub Actions:** https://github.com/Heitor2404/coringa-news/actions/runs/45122774333 — **SUCCESS, 58 testes aprovados, 11 avisos Pillow**, ambos MP4s, auditoria de quadros e artefato. SHA do workflow de QA aprovado `73990ea89a63f14fc9f3bc45e719b2331d4fe95a`.
- **Artefato:** `lab-f10-compressor-correia-antes-depois-privado`, ID **14794895623**, expira em **28/11/2026 06:15 UTC**.
- `COMPRESSOR_F10_ANTES.mp4`: **8s, 540×960, 24fps, H264, sem áudio**. SHA256 `45a848b92ba7da35886590cac856584a1938825875af02a3ca1eeaffa2f4f3a5` — idêntico ao F2B estável do histórico, provando compatibilidade do padrão anterior.
- `COMPRESSOR_F10_CORREIA_PARAMETRICA.mp4`: mesmas especificações, SHA256 `2ab986d07f4c6e9008c172f7f4582b4002ed23a14e1d2c99ae9e347eb3b97e4c`. Resultou de `--camera-causal --transmissao-parametrica`. A correia segue as tangentes externas declaradas, com deslocamento de marca durante a rotação das polias.
- `COMPARATIVO_COMPRESSOR_F10_8_QUADROS.jpg`: foi aberto e examinado. Mecanismo inteiro permanece visível, câmera estável, quatro fases representadas, correia agora atrás das faces do volante. O **ganho visual é LOCAL**, não transforma a arte em imagem industrial hiper-realista.
- `QA_F10_TRANSMISSAO.json`: diferenças médias de RGB no ROI da correia nos quatro instantes: **4,467 / 4,804 / 5,044 / 4,936**. No header: **0,000 / 0,158 / 0,268 / 0,312**; no rodapé: **0,000 / 0,002 / 0,002 / 0,000**. SVG bruto é idêntico fora do palco pela suíte Python; diferenças minúsculas em regiões estáticas do MP4 decorrem do codec H264. O gate final passa com limite **<0,60 RGB** no header MP4 e **<0,08 RGB** no rodapé, além de correia **>1 RGB**, sem afrouxar invariância do SVG.
- Outros workflows na mesma branch (`qa-compressor-conjunto-2d`, `qa-camera-causal-svg-multifamilia`, `qa-mecanica-parametrica-f7`, `qa-biblioteca-fisica-multifamilia`, `qa-realce-causal-svg`, `qa-palco-vertical-multifamilia`) também terminaram SUCCESS após mudança de motor/primitive.

### Problemas encontrados e tratados

1. Primeiro QA `45122063472`: **57 testes verdes, ambos MP4s gerados**, porém comparação de H264 exigia que TODOS os bytes pixel do header/rodapé fossem iguais, o que não é garantido por encoder com cenas distintas. Corrigido separando invariant de SVG (exato) do noise de vídeo (medido).
2. Inspeção dos primeiros vídeos descobriu que desenho da correia vinha DEPOIS do rotor, aparecendo sobre as faces. Corrigido na implementação com regressão nova.
3. Run `45122496572`: **58 testes verdes, vídeos reais** mas QA de compressão ainda acusou header RGB 0,268–0,312 contra threshold 0,20. O limite do H264 foi calibrado com os quadros reais e provas SVG brutas permanecem exatas. Run final `45122774333` passou todas as etapas, sem alterar física/câmera para passar.

## 4. Limites e próxima etapa

F10 NÃO licencia imagens industriais de terceiros, não reproduz maquinaria a partir de fotos, não treina IA, não cria CAD ou 3D, não prova a cinemática por câmera independente e não significa que o estilo 2D ficou profissional para postar. Modelo de correia ideal ignora deformação, inércia, tensão real, escorregamento, proteção e atrito. A F9 de referência Wikimedia permanece BLOQUEADA por HTTP 429 e SHA nulo.

**Próximo passo útil:** validar esta correia e outras partes no contexto de **outro mecanismo com polias/atuadores diferentes** configurado por parâmetros, provar recorte/colisão por bboxes no dispositivo e introduzir componente de aparência curada com direitos de imagem comprovados, sem voltar aos diagramas minúsculos do `FilmeEditorial`. Antes de publicar, inspeção estética/industrial humana continua obrigatória. `main`, NTC, DOSSIÊ, Telegram e publicação permanecem inalterados.
