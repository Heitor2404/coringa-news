# E3 — ponte de evidência por junta entre F16/F17 e solver comum E1/E2

**Data:** 23/11/2026 · **Branch:** `atlas-direcao-visual-20261118`
**Resultado:** 62 testes no CI, três fontes técnicas recuperadas **LIVE**, 0 mecanismos inéditos automaticamente especificados, 0 renders neste experimento, 0 publicação.

## O que mudou

Após E2 demonstrar um terceiro mecanismo via solver comum com parâmetros **MANUAIS**, E3 introduziu `src/v4/formatos/ponte_evidencia_solver_e3.py`. Ela usa:
1. **F16** — downloader HTTPS com lista de URLs exatas, recusa redirecionamentos, confirma que cada fragmento citado existe no HTML retornado, calcula SHA.
2. **F17** — extrai relações pontuais **com regras léxicas curadas**, cada aresta com `supported_span_ids`. O extrator NÃO é LLM, OCR, VLM nem compreensão irrestrita de engenharia.
3. **E3** — transforma arestas sustentadas em **esboços de juntas** do solver comum e verifica a procedência de cada `joint_index` declarado em uma `MechanismSpec` escrita manualmente. A relação `hinged_to` pode sustentar junta `pin`; `slides_in` pode sustentar `slider`. `meshes_with`, `drives`, `fluid_to` e `pushes` ainda NÃO são juntas equivalentes já disponíveis em E1/E2. O fato de F14 possuir um kernel de engrenagens separado não prova suporte genérico a `meshes_with`.

Para uma junta ser considerada sustentada, a proposta precisa citar uma **aresta realmente extraída**, com ID de trecho, tipo mecânico compatível e endpoints mapeados para corpos concretos; `slides_in` respeita direção pistão→guia. Relacionamentos sem citação, alterações de tipo, corpo trocado, reutilização de aresta, fonte errada, URL desviada e texto sem âncora válida são **bloqueados**.

Mesmo quando todas as relações de uma eventual proposta tiverem fonte, as coordenadas locais, raio, comprimento, seed, eixo, restrições de movimento e aparência exigem comprovação **adicional**. Nesta versão todas são declaradas manualmente, sem licença de mídia externa nem prova CAD. A E3 **NUNCA** habilita render/publicação: ela é uma etapa de QA antes de qualquer promoção.

### Arquivos criados

- `src/v4/formatos/ponte_evidencia_solver_e3.py` — descoberta de candidatos por relações e verificação de claims do solver.
- `benchmarks/bindings_e3/biela_parcial_f17_e3.json` — binding de papéis de fonte para corpos E1, deliberadamente parcial e rotulado `manual_prototype`.
- `tests/test_ponte_evidencia_solver_e3.py` — adversariais de origem, falso span, papel, junta, indexação, contrato e direitos; fixtures nunca contam como download público.
- `.github/workflows/qa-ponte-evidencia-solver-e3.yml` — regressões F16/F17/E1/E2 e três GETs live controlados, entrega JSON auditável sem MP4.

## Execução real conferida

**Run final:** https://github.com/Heitor2404/coringa-news/actions/runs/45212820200 — **SUCCESS, 62 testes aprovados**, passos de acesso live, teste de recusa e upload do artifact verdes.

**Artifact:** `lab-e3-relacoes-fonte-viva-e-contraprovas-privado`, ID **14836667890**, expira **28/11/2026 16:07:26 UTC**. ZIP baixado e os **4 arquivos JSON** inspecionados, incluindo `QA_E3_SOURCES.json`.

### Resultado das 3 fontes HTTPS

1. **Biela parcial**, `https://jd-jones-ases.github.io/Mechanic/things/slider-crank/`, SHA do HTML **`4b67df19838531d3afc8065806d36c9ce9d76adfb151c299ed4e942b2aa3d897`**. Os fragmentos F16 foram confirmados live. F17 dá a relação explícita `piston slides_in chamber` do trecho **b3**. Binding manual para spec E1: pistão=corpo `slider`, câmara=`ground`, junta índice 3. **Apenas 1 das 4 juntas** recebeu vínculo evidencial; três articulações não demonstradas pelos trechos continuam **NÃO SUSTENTADAS**. A geometria da `MechanismSpec` foi obtida do oráculo/protótipo E1, NÃO da fonte; os 33 estados desse modelo matemático prévio passam, mas isso NÃO substitui as três provas faltantes. Status **`BLOCKED_UNPROVEN_JOINTS`**.
2. **Par de engrenagens**, `https://mechanics.ju.se/MachineElements/spur-gears.html`, SHA **`9ce7ac8639bfbfe7f3ebdc8fa45e7e68a66cbd33dae5e5ca5d2294efb9fffe8b`**. A relação `gear_1 meshes_with gear_2`, trecho **g2**, foi confirmada, mas o solver E1/E2 NÃO tem `meshes_with` como junta genérica; F14 é kernel separado. Entrada/saída, dentes, módulo e referências visuais continuam pendentes. Status **`STRUCTURE_RECOGNIZED_DESIGNER_BINDING_REQUIRED`**, sem Spec automática nem vídeo.
3. **Plataforma tesoura**, `https://hydraproducts.co.uk/hydraulic-power-packs/power-pack-applications/commercial-systems/scissor-lift/`, SHA **`b0259e470995a0cd1655b8f9fd92058ab961244843216ee2faebc1dab298b175`**. Relações confirmadas separadamente `motor→bomba` (**h1**, drives), `bomba→cilindro` (**h2**, fluid_to) e `cilindro→braços` (**h3**, pushes). Não há dados geométricos da tesoura nem solver hidráulico/forças. Status **`BLOCKED_NO_KERNEL`**, sem Spec automática nem vídeo.

**O que foi efetivamente automatizado nesta fase:** obtenção HTTPS **dos URLs já permitidos**, correspondência exata de trechos curados, extração léxica restrita, sugestão de tipo de junta quando a relação é suportada, verificação de binding por corpo/junta e recusa de lacunas. **Não** há descoberta autônoma de URLs inéditos, geração de parâmetros, otimização de seeds, interpretação de imagem/vídeo ou uso de Claude/LLM. Nenhum custo de LLM foi incorrido pelo código E3; custos de GitHub Actions não quantificados.

## Escore honesto

Benchmark congelado permanece inalterado. E2 havia resolvido **3 topologias** em specs manuais (quatro barras, Scotch yoke, pinhão-cremalheira). E3 **não tenta um 4º mecanismo** e **não adiciona acerto em benchmark**: 3 fontes vivas checadas, 1/4 juntas da biela sustentada nos trechos, 0 specs completas geradas de fontes, 0 aprovações visuais, 0 modelos 3D, 0 publicações.

**Próximo ciclo recomendado (E3b/E4):** capacidade de descobrir documentos técnicos relevantes sem lista de URLs fixa, extrair relações e dimensões com indicação da citação de origem e avaliar a confiabilidade por junta; testar contra conjunto de fontes rotulado previamente, com limites de custo e revisão humana. Mesmo com especificação completa, só liberar render privado se validação geométrica e visual independente comprovarem coerência. O motor não pode retornar ao padrão de um renderer hardcoded por máquina ou aos diagramas pequenos rejeitados.

**Segurança e isolamento:** `main`, produção, NTC, DOSSIÊ, Telegram, dados privados e publicação NÃO modificados. Documento de continuidade deve receber seção 131.
