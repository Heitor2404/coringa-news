# Enquadramento vertical por área essencial — contrato compartilhado
**19/11/2026 · ATLAS / FilmeEditorial · branch experimental**

## Por que isto existe
Uma filmagem horizontal 1360×720 perde cerca de **70,2% da largura** ao preencher um vídeo 1080×1920 com `object-fit: cover`. No quadro NIST NanoFab ~78s o operador e o painel de operação cabem juntos num recorte estreito; o grande equipamento à esquerda NÃO cabe ao mesmo tempo. Zoom adicional piora. Fundo desfocado não resolve uma relação causal que a imagem vertical deixou de mostrar.

Esta melhoria é **do FilmeEditorial**, reutilizável em qualquer documentário, não uma exceção de Taiwan/NIST. O código segue no montador existente `src/v4/formatos/filme_editorial.py` + `motor4/remotion/src/formatos/FilmeEditorial.tsx` e a mesma regressão multitema, sem outro diretor/fiscal/montador.

## Como declarar o ROI numa tomada (exemplo ilustrativo)

`plano.media[asset]` já contém a origem curada, dimensões e hash:
```json
{
  "media": {
    "laboratorio": {
      "media_type": "video",
      "width": 1360, "height": 720,
      "expected_sha256": "<sha256_64_caracteres_do_original>",
      "local_source": "<arquivo_autenticado_no_workspace>",
      "page": "<pagina_da_fonte>",
      "license": "<licenca_verificada>",
      "credit": "<credito_original>"
    }
  }
}
```

Na cena `shots[*]`:
```json
{
  "id": "operador-controle",
  "type": "video", "asset": "laboratorio",
  "start": 0, "end": 2.6,
  "source_in_seconds": 78.0,
  "video_framing": {
    "modo": "roi_observada",
    "sha256_origem": "<mesmo_sha256_original>",
    "inspecao": "Quadros reais revisados na origem; a área destaca operador e painel",
    "pontos": [
      {"at": 0.0, "fonte_s": 78.0, "area_essencial": [0.45, 0.32, 0.68, 0.88]},
      {"at": 1.4, "fonte_s": 79.4, "area_essencial": [0.47, 0.32, 0.70, 0.88]}
    ]
  }
}
```

Campos `area_essencial` são **[esquerda, topo, direita, base] normalizados em 0..1 no frame ORIGINAL**. São medidos/inspecionados, **não inventados**. `at` é relativo ao início do plano; `fonte_s = source_in_seconds + at` identifica o frame real. O hash é do MP4 original, e o uso comercial continua condicionado à prova de licença e curadoria do catálogo.

## Funcionamento técnico
1. `filme_editorial.planejar_enquadramento_video` recebe as dimensões reais, calcula a janela visível de `object-fit:cover` em 9:16 e a posição que contém a área declarada com margem (3% do recorte nos eixos cortados).
2. Se a região essencial não cabe, dá **`F-ROI-NAO-CABE`** e exige outra filmagem ou composição — não usa blur/card/zoom para esconder a falha.
3. Se o SHA não corresponde à mídia, o ponto sai da cronologia do original, há bbox inválida ou falta declaração de inspeção, o preflight BLOQUEIA.
4. No `preparar`, `ffprobe` confere largura/altura reais do MP4 e rejeita discrepância com a ROI calculada; os `framing_positions` chegam ao **mesmo** compositor.
5. Remotion interpola as posições para acompanhar o sujeito/ação sem trocar clipes. Esse deslocamento da câmera **não é computado como progresso de conteúdo** pelo fiscal.
6. Para filme final, vídeo horizontal sem enquadramento explícito e origem dimensionada é bloqueado. Pilotos técnicos antigos mantêm compatibilidade legada.

**Importante:** a geometria prova que a BBOX declarada cabe nos frames amostrados. Ela **não prova** que os quadros correspondem à ação narrada, que a trajetória entre amostras fica sempre visível, ou que o MP4 final é bonito. Isso continua sujeito à inspeção de quadros contínuos / revisão humana antes de qualquer publicação.

## Prova com material real, sem nova publicação
- Quadro autêntico do NIST NanoFab, vídeo horizontal 1360×720, perto de **78s**, foi examinado na própria sessão. ROI escolhida ~x=0.45–0.68 preserva operador e painel; o equipamento maior à esquerda fica fora e **não pode ser apresentado como mecanismo completo** com esse recorte.
- Gerada prova visual privada de fonte + retângulos + recorte correspondente em `/mnt/data/atlas_roi_prova_nist_78s.png` (arquivo da sessão, NÃO salvo no GitHub).
- O MP4 NIST segue candidato com direitos específicos pendentes, **NÃO** fonte curada para produção e **NÃO** comprova fabricação da TSMC.

## Testes e próximos critérios
- `tests/test_video_framing_multitema.py`: 12 testes novos, quatro tipos de história, impossibilidade geométrica, SHA de outra mídia, cronologia incorreta, zoom extra, ausência em filme final, e ponte `preparar` com **fixture MP4 real 1280×720** no repo.
- **CI Python 44624251846 SUCCESS: 164 testes**, mapa ATLAS 1 autenticado, duas fotos 2/3, Taiwan histórico ainda com 9 bloqueios.
- **CI TypeScript 44624493717 SUCCESS**: `npm ci` e `tsc --noEmit` para Remotion, sem render nem Gemini.
- Próximo passo audiovisual: usar ROI de ação em trechos demonstrativos realmente homologados, inspecionar **MP4 vertical renderizado**, verificar se operador E ferramenta continuam visíveis durante toda a explicação; caso sejam espacialmente incompatíveis com 9:16, escolher shot alternativo ou composição específica. **Não** criar novo sistema, depender exclusivamente de metadados inventados ou fazer outro piloto de 20s só para mostrar testes verdes.
