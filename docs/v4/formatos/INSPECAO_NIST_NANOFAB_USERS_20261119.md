# Inspeção de candidato NIST NanoFab — 19/11/2026

**Status: CONTEXTO_VISUAL_CANDIDATO — NÃO HOMOLOGADO.** O mesmo arquivo poderá ilustrar laboratórios de diversas histórias; **não** é filmagem da TSMC e **não** é prova direta de litografia/deposição em andamento.

## Original comprovado (bytes reais)
- Origem oficial: https://www.nist.gov/video/cnst-nanofab-through-users-eyes
- Player Kaltura da página: `kaltura:684682:0_emhevqw5`
- Workflow de aquisição **44617739596**, artifact **14575931753** (retenção 3 dias, NÃO armazenamento remoto durável).
- Original `nist_nanofab_users_2017.mp4`, **28.734.934 bytes**, **1360×720**, **105,05 segundos**, **24 fps**, H.264, áudio AAC embutido.
- SHA-256 calculado no runner e verificado novamente sobre os bytes recuperados para inspeção: `582ee5ea387fae4b424ac08c85a33840fd8a44bc681f136ebbe1f76b8723c474`.
- Registro provisório na Biblioteca V3 de teste: `cm-582ee5ea387f`, `uso_comercial=indefinido`.
- Receita oficial `docs/v4/formatos/CANDIDATOS_VIDEO_NIST_NANOFAB_20261119.json` agora fixa `sha256_esperado`, e `coletar_videos_publicos.py` recusa qualquer arquivo posterior diferente. Não ajustar SHA para encaixar arquivo alterado.

## Revisão visual de amostras reais
Foram inspecionados **42 quadros reais**, extraídos do MP4: 12 amostras distribuídas ao longo dos 105 s e mais 30 amostras concentradas entre 40–90 s. Isso NÃO equivale a inspeção contínua de todos os movimentos ou do conteúdo falado.

| Intervalo aproximado | Conteúdo identificável | Juízo editorial |
|---|---|---|
| 0–15 s | pessoas na sala limpa, fachada do centro | contextual; não demonstra fabricação |
| 20–28 s | câmara, suporte e interior de equipamento | contextual; ação específica não confirmada |
| 30–40 s | capturas de software/apresentação | fraco para documentário visual |
| 41–48 s | equipamentos, painéis, corredor, máquina complexa | contexto de instrumentação, sem comprovação de mecanismo |
| 49–57 s | grupo e depois pesquisadores em sala limpa amarela | bom ambiente e escala, pouca ação nova |
| 58–64 s | pessoa operando estação de computador e microscópio | operador real, mas processo de fabricar wafer NÃO comprovado |
| 65–72 s | portas, avisos, salas e painéis | decorativo, evitar repetição |
| 73–83 s | laboratório com pesquisadores e instrumentos, bancada | potencial B-roll ilustrativo, necessário revisar sequência temporal e recorte vertical |
| 84–90 s | planos de máquinas e do interior das salas | contexto de infraestrutura; sem ação inequívoca |
| >90 s | imagens de encerramento/branding | não representa processo |

**Conclusão:** material mais variado que foto estática e válido como B-roll de laboratório **se** direitos específicos forem resolvidos. Não marcar `prova.acao_ou_relacao_visivel=true` para deposição, EUV, fabricação TSMC ou qualquer processo físico específico com base nestas amostras. Vídeo não resolve os dois clipes independentes de ação exigidos na rubrica antiga; **ainda faltam processos demonstrados**.

**Enquadramento:** original 1360×720 horizontal; cortar automaticamente para 9:16 pode eliminar pessoas e maquinário. Antes de editar, confirmar ROI/enquadramento no FilmeEditorial; não centralizar cegamente.

**Direitos:** o NIST tem política geral de reprodução `https://www.nist.gov/copyrights-disclaimers`, com ressalvas de material de terceiros. Este vídeo inclui depoimentos e áudio; a autorização de uso das imagens específicas, de pessoas e de eventuais trilhas permanece **PENDENTE**. Não promover V3 `uso_comercial` para `sim` por inferência automática.

## Mudança transversal revelada na inspeção
`gate_filme_completo.py` separa vídeo contextual de vídeo demonstrativo:
- `MOSTRAR` pode usar vídeo real com bytes, licença, créditos e correspondência visual comprovados, mesmo sem processo físico demonstrado, mas esse vídeo entra em `videos_contextuais_sem_prova_de_acao` e NÃO eleva `videos_independentes_conferidos`.
- `DEMONSTRAR`, `CONECTAR` ou `REVELAR` continuam exigindo a ação ou relação visualmente comprovada para passar.
- Contadores de ambos os tipos só consideram vídeos com uso comercial verificado, correspondência com mídia, natureza de vídeo e SHA realmente atestado.
- Regressões de geografia, indústria e engenharia impedem contagem falsa de vídeos sem licença, fotos disfarçadas e B-roll contextual.

**Próximo passo:** buscar fonte adicional que mostre um processo físico inequívoco; revisar direitos NIST de forma documentada; adaptar roteiro ao que imagens realmente mostram; verificar verticalização ANTES de render; não chamar Charon sem gate satisfatório.
