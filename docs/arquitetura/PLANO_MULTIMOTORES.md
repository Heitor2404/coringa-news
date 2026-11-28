# Plano de arquitetura multimotores — fábrica de canais dark

**Versão de planejamento 1.0 · 18/11/2026.** Documento de referência para execução futura, **não** autorização para modificar motores produtivos.

## Visão e decisão

Construir uma central de produção com um seletor explícito **canal + motor + release/versionamento + tema**. Depois de aprovar o ATLAS, congelar um release e continuar trabalhando em BIO, ASTRO, NTC 2D ou outros formatos sem que alterações afetem o ATLAS estável. A infraestrutura (GitHub Actions, mídia/licenças, TTS, cache, FFmpeg, logs, revisão privada e distribuição) pode ser compartilhada **somente por interfaces versionadas e testadas**.

**Um canal não implica um motor próprio.** Diferentes canais documentais podem compartilhar ATLAS com identidades e vozes diferentes. Biologia animada, simulações astronômicas ou histórias 2D podem justificar motores independentes. O NTC vetorial já possui bases próprias.

## Diagnóstico do repositório atual

Na branch `atlas-direcao-visual-20261118` há separação parcial: catálogo `src/v4/formatos/formatos.json` com ATLAS e DOSSIÊ; perfis em `src/v4/formatos/canais/`; diretor `src/v4/formatos/diretor.py`; pipeline `src/v4/formatos/produzir.py`; renderer `src/render/v2/` e `motor4/remotion/`; NTC em `canais/ntc/vetor/`; workflows em `.github/workflows/`. **Ainda não há isolamento completo de releases imutáveis selecionáveis por canal.** Branches de desenvolvimento, sozinhas, não congelam um motor.

## Arquitetura-alvo

1. **Orquestrador:** recebe `canal, motor, versao, tema, modo, idioma, destinos, limite_custo`; resolve a versão fixada, registra job e escolhe workflow.
2. **Registry de releases:** mapeia combinações permitidas de canal + motor + versão a SHA exato, dependências, ativos, contratos e perfis de identidade.
3. **Motores isolados:** ATLAS, BIO, NTC2D, ASTRO; cada um com prompts, storyboard, componentes, animações, presets, testes e exemplos de referência próprios.
4. **Perfis por canal:** nome, audiência, marca, fontes, voz, legendas, tópicos, CTA, idiomas, destinos e política de aprovação.
5. **Serviços compartilhados versionados:** coleta de mídia/licenças, áudio, legenda, cache, FFmpeg, fiscalização, relatórios, Telegram e publicação. Atualização comum não pode atualizar implicitamente releases congelados.

Exemplo de seleção **ilustrativa, ainda não implantada**:

```yaml
canais:
  coringa_explica:
    motor: atlas
    versao: '1.0.0'
    sha: '<COMMIT_FIXADO>'
    perfil: perfis/coringa_explica.yaml
    ambiente: producao
  canal_biologia:
    motor: bio
    versao: '0.1.0-dev'
    sha: '<COMMIT_BIO_EXPERIMENTAL>'
    perfil: perfis/biologia.yaml
    ambiente: homologacao
```

## Congelamento de um motor

1. Homologar ATLAS com diferentes assuntos, inclusive **um segundo tema a ser decidido com o usuário**, não escolhido automaticamente.
2. Fechar testes unitários, integração, preflight, fiscal factual, imagem, áudio, legendas, créditos e revisão visual em celular.
3. Produzir manifesto: versão, **SHA exato**, fontes e hashes de ativos essenciais, dependências e versões fixas de Python/Node/Chrome/FFmpeg, prompts, catálogo e thresholds.
4. Armazenar vídeos e frames de referência com tolerância visual (hash MP4 pode variar por encoder/timestamps).
5. Criar release `atlas-v1.0.0` apontando ao SHA, proteger referências quando possível; a tag por si só pode ser movida.
6. Reexecutar release em runner limpo e aprovar. Só então mapear `coringa_explica` para o SHA estável.
7. Toda melhoria posterior vira `v1.0.1` ou `v1.1.0`; jamais editar silenciosamente o release estável. Manter rollback.

**Critério de isolamento:** desenvolvimento de BIO não pode alterar o SHA, os pacotes fixados, os golden samples nem a identidade do ATLAS estável. Alterações em serviços compartilhados exigem matriz de compatibilidade de todos os releases consumidores.

## Interruptor e operação

Começar com `workflow_dispatch` no GitHub para canal, motor e versão registrados. Futuramente, construir menu no Telegram ou painel. O registro deve rejeitar valores não autorizados: **não** aceitar `ref`, script, caminho nem comando arbitrário vindo de mensagens externas. Manter segredos segregados por ambiente/canal, logs de custos e estados.

Fluxo: selecionar → validar manifesto → checkout do SHA fixo → preparar dependências do release → carregar perfil → produzir → fiscalizar → enviar prévia privada → aprovação/publicação conforme regras → gravar histórico e custo por job.

## Proteções e testes mínimos

- Testes de direção narrativa, física de mecanismos, continuidade, câmera, legibilidade, áudio, legenda, zonas seguras, fatos/licenças e ritmo.
- Golden samples com pelo menos dois temas distintos e inspeção humana de vídeos reais.
- Regressão cruzada entre motores e integração fim a fim no runner limpo.
- Bloqueio de publicação quando faltarem permissões, fontes, crédito, qualidade, versão homologada ou aprovação exigida.
- Estado `BLOQUEADO` sempre com causas explícitas; rollback rápido para release anterior.
- Logs de canal, motor, versão, SHA, mídia, narração, IA/TTS, tentativas, custos e destino.

## Custos

Priorizar GitHub Actions, FFmpeg, Remotion, bibliotecas SVG/código, cache e mídias com licenças verificadas. Monitorar minutos de CI, armazenamento, transferências, cota de TTS, gastos de IA/API e limites de publicação. **Assinaturas de ChatGPT e Claude não garantem execução ilimitada por API**; os custos e permissões devem ser verificados antes de automatizar em escala. Não prometer produção ilimitada gratuita.

## Roadmap e critérios de avanço

| Fase | Objetivo | Conclusão |
|---|---|---|
| 0 | Finalizar ATLAS | Piloto + segundo tema aprovados; fiscal, narrativa e visual homologados |
| 1 | Congelar ATLAS | Release SHA + manifesto + golden samples + runner limpo + rollback |
| 2 | Interruptor inicial | Seleção `canal + motor + versão` sem vazamento de estilos/componentes |
| 3 | Serviços compartilhados | Dependências fixadas e testes de regressão cruzada |
| 4 | Novo motor | BIO, ASTRO ou outro, escolhido posteriormente, isolado do ATLAS |
| 5 | Escala | Agendamento, revisão e distribuição por canal com custos sustentáveis |

## Decisões já estabelecidas

- Um ecossistema modular, inicialmente **no mesmo repositório**, com isolamento técnico real.
- Não começar BIO/ASTRO antes de homologar o ATLAS e preservar release estável.
- Evitar serviços extras pagos; não assumir custo zero de API/execução.
- O Panamá é teste do motor ATLAS, não projeto de edição caso a caso.
- Não alterar NTC e DOSSIÊ durante correções específicas do ATLAS.
- O usuário escolhe em conjunto o segundo tema de homologação.

## Pendências futuras

Escolha do segundo tema; definição das marcas/canais; quando um canal precisa de novo motor; provedor/cotas de TTS/IA; política de publicação; retenção/backup; desenho final do registry, interface e limites de custo. A versão `atlas-v1.0.0` é **exemplo**, não existe ainda como release homologado.

**Documento completo para download:** `Arquitetura_Multimotores_Canais_Dark.docx` (gerado no chat e entregue separadamente). Este registro no GitHub é o resumo operativo. **Não implantar por leitura automática antes de aprovação da fase ATLAS.**
