# F9 — evidência externa de aparência + confronto com compressor (23/11/2026)

## Situação

**PARCIAL / NÃO HOMOLOGADO.** A pesquisa na Wikimedia Commons encontrou a ilustração estática `Portable Single Stage Air Compressor.jpg` de Brian S. Elliott, 2018, com licença declarada **CC BY-SA 4.0** na página de origem. Trata-se de uma **ilustração técnica da máquina completa**, não foto industrial nem esquema animado/CAD.

- Página de origem: https://commons.wikimedia.org/wiki/File:Portable_Single_Stage_Air_Compressor.jpg
- Licença e atribuição: https://creativecommons.org/licenses/by-sa/4.0/
- Autor: Brian S. Elliott
- Tipo: compressor portátil de estágio único, motor elétrico e reservatório horizontal; carenagem cobre a transmissão.
- Dimensões anunciadas na página: **2100×1500 JPEG**. O arquivo ORIGINAL **NÃO foi ainda hash-validado** pelo motor.

### Bloqueio real

A execução inicial **45120918588** completou **50 testes** (11 avisos Pillow), mas a solicitação do JPEG ao host oficial recebeu **HTTP 429 Too Many Requests**; o passo de aquisição falhou e **NENHUMA foto original foi baixada e NENHUM vídeo de comparação foi criado por essa execução**. Não se deve usar miniatura alternativa, imagem externa rehosted ou SHA inventado como se fosse o original.

O workflow foi corrigido para tratar 429 como estado **BLOQUEADO_EXTERNO**, com JSON explícito, mantendo QA estrutural local. Verificar resultado da próxima execução antes de alegar sucesso.

## Arquitetura implementada

1. `referencias_visuais_f9/compressor_elliott_2018.json`: contrato de um candidato externo com fonte, direitos, papéis visíveis (8 caixas manualmente aproximadas), papéis ocultos (4), `industrial_identity_certified=false`, `publication_allowed=false` e `expected_sha256=null` até verificar os bytes.
2. `referencia_evidencia_f9.py`: ingestor de JPEG com limite de tamanho, host permitido (`upload.wikimedia.org`), sem redirect, SHA fixado antes de render MP4, validade da imagem, atribuição, comparação com um frame do **renderizador verdadeiro** do compressor, e gate de publicação fechado. PDF/GLB/3D e fotos sem licença não entram.
3. `auditoria_alinhamento_f9.py`: compara papéis declarados no candidato contra `role-...` efetivamente presentes no SVG do motor; **não** lê pixels da imagem nem afirma ter testado seu funcionamento interno. Produz quadro local de quatro fases do compressor, independentemente da aquisição Commons.
4. `test_referencia_evidencia_f9.py`, `test_auditoria_alinhamento_f9.py` e `qa-referencia-compressor-f9.yml`: testes offline, CI e relatório privado (sem Claude, sem publicar).

## Resultado de correspondência esperado do QA SEMÂNTICO

Os 8 papéis visíveis **declarados manualmente** na ilustração cobrem, no nosso código, 6 papéis presentes: `receiver_horizontal`, `electric_motor`, `compressor_head`, `intake_filter`, `discharge_pipe` e manômetro (`tank_pressure_gauge` do desenho → `receiver_gauge` do código).

Dois elementos são **diferença de variante**, NÃO BUG automaticamente: `wheel` e `belt_guard`, que não aparecem no SVG de oficina. A referência é portátil, mas nosso protótipo é um compressor de oficina com transmissão visível e desenho em corte. O interior da correia, o pistão, as válvulas e a manivela **não estão visíveis nessa referência externa**, não podendo ser tratados como prova da cinemática.

Essa é uma correspondência de NOMES/PAPÉIS declarados, não uma verificação visual por IA. O índice 6/8, se obtido na CI, **não significa precisão visual de 75%**, nem confiabilidade de identificação.

## Próximos gates

- Retentar aquisição do ORIGINAL apenas quando permitido pelo host e fixar **SHA256 real**; não contornar rate limiting.
- Após SHA, produzir MP4 comparativo privado e inspecionar composição, tipo de máquina, coerência da geometria e ações com o original visível; manter atribuição, licença e aviso de alterações.
- Escolher referência EXATA para o subtipo que o motor vai desenhar (compressor de oficina com corte) e definir critérios de visibilidade; não copiar rodas/carenagem do portátil por pressão estética.
- Somente com evidência de correspondência e direitos, considerar tradução para peças vetoriais genéricas. **Não** incorporar imagem estática no rig como se fosse animação 2D/3D.
- Não promover a `main`, não publicar e manter o gate de legado descartado.


## Validação técnica final do checkpoint F9b

**GitHub Actions:** https://github.com/Heitor2404/coringa-news/actions/runs/45121238521 — **SUCCESS, 54 testes aprovados, 11 avisos Pillow**, na implementação commit `b151558f`. O resultado verde certifica APENAS código e matriz local. A fonte Commons **continuou bloqueada por HTTP 429**, registrado como `BLOQUEADO_HTTP_429_LIMITE_WIKIMEDIA` no JSON, sem baixar original e sem fixar SHA e SEM produzir vídeo comparativo de fonte externa.

**Artefato real:** `lab-f9-referencia-compressor-real-privado`, ID **14793354589**, expira em **28/11/2026 06:01 UTC**. ZIP foi baixado e inspecionado. Contém `AUDITORIA_SEMANTICA_F9.json`, `BLOQUEIO_FONTE_429_F9.json` e `MAQUINA_EXISTENTE_4_FASES_SEM_REFERENCIA_EXTERNA.jpg`. A prancha **é o render SVG próprio** do compressor em quatro etapas: reexpansão residual, admissão, compressão e descarga. NÃO contém o JPEG de Brian S. Elliott.

**Análise:** a arte do compressor do Coringa mantém o conjunto grande em tela clara, motor, correia, câmara/pistão em corte, saída, manômetro e tanque horizontal. É uma ilustração didática de mecânica: não há semelhança homologada com modelo industrial de fabricante nem reconstrução a partir da referência externa. O relatório semântico fez a correspondência 6/8 de PAPÉIS declarados, não de PIXELS: seis nomes presentes no código; `wheel` e `belt_guard` pertencem à variante portátil e não devem ser adicionados automaticamente ao nosso subtipo de oficina. A correia sob carenagem e interior do pistão não são observáveis na imagem externa, portanto NÃO demonstram seu movimento.

**Próximo:** manter o candidate externo fechado até o limite de requisições do provedor permitir o ORIGINAL; não procurar proxy que altere hash. Em paralelo, refinar o CONTRATO DE VARIANTE e diferenciar fonte para compressor com correia exposta e bomba em corte, validando objeto protagonista sem que o render dependa de supor que páginas de manual liberam imagens. Necessário QA visual humano no dispositivo antes de qualquer publicação.
