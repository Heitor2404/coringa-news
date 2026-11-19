# ATLAS V2 — Integração audiovisual P1, usando o que já existia
**19/11/2026 — branch experimental `atlas-direcao-visual-20261118`**
**Estado:** implementação + testes técnicos de contrato; sem aprovação estética, sem gerar novo vídeo público, sem merge em `main` ou `motor-integral-v4`, sem alterações no DOSSIÊ/NTC.

## Por que essa implementação é pequena e não duplicada
Antes: `src/v4/episodio.py` já renderizava vídeo real via `src/v4/backends/legado.py::render_video` (FFmpeg, recorte 9:16 estático, sem áudio, sem esticar clipe curto, máx. ampliação 2,6×). Porém o `src/v4/formatos/produzir.py` do ATLAS só aceitava `PIL.Image.open`, convertia tudo a JPEG e o catálogo de formatos só liberava `mecanismo.eclusa` como clipe. Resultado: não havia forma de registrar e montar MP4 documental como cena dominante.
Agora: **REUTILIZAMOS** o backend de vídeo V4; nenhuma implementação nova de decoder, FFmpeg, banco de mídia ou fornecedor externo.

## Código alterado
1. `src/v4/formatos/formatos.json`: adicionou `registro.video` como clipe ATLAS; foto editorial `atlas.provaVisual` + composição `atlas.prova` com slot protagonista, mapa apenas como contexto de cena. **Nenhum componente novo para DOSSIÊ.**
2. `motor4/remotion/src/formatos/Primitivas.tsx`: `ProvaVisual` desenha foto REAL licenciada em grande formato e sem cartões/pinos decorativos, permite `enquadramento` 'conter'/'cobrir' e `foco` do acervo; rodapé de atribuição vem do motor, não de CSS ad hoc.
3. `src/v4/formatos/produzir.py`: `assets_do_plano()` inclui arquivos citados em `registro.video`. `ativos()` baixa/copia origem de mídia aprovada, checa SHA256 de origem, exige `natureza: video`, `uso_comercial: sim` e hash obrigatório, confere largura/altura/duração com `src.v4.util.sondar`; guarda vídeo original `.mp4/.webm/.mov` no mesmo `motor4/remotion/public/_formato` e em `saida/ativos`. O preflight exige clipe real, duração válida e licença/crédito comprovados; `_clipe()` chama diretamente `src/v4/backends/legado.render_video` com foco padrão central. O vídeo **não traz áudio original**, só áudio/narração master do Coringa.
4. `src/v4/formatos/plano.py`: valida tipo, duração e início do vídeo; **impede camadas documentais escondidas** durante o intervalo substituído pelo clipe. Fotos protagonistas requerem asset e crédito. `P._creditos()` inclui fotos protagonistas no rodapé cartográfico. `P.props_camada()` recebe `imagens` e credita MP4 com selo `REGISTRO`, não `ESQUEMA`.
5. `motor4/remotion/src/Camada.tsx`: aceita `credito_caixa` na faixa de atribuição já reservada **abaixo da legenda**, sem elevar os créditos para onde estavam antes. `scripts/formatos_validar.py` usa `imagens` também na prévia de quadros, e não apenas no MP4.
6. `src/v4/formatos/diretor.py`: prompt oferece foto grande e vídeo real somente se constarem do inventário comprovado; proíbe substituir processo crítico por mapa e usar vídeo genérico como prova de instalação identificada.

## Contrato de vídeo comprovado (exemplo de estrutura; não é um ativo real)
Um curador/adaptador aprovado deve registrar uma entrada em `src/v4/biblioteca_comprovada.json` ou via futura ponte segura à biblioteca V3:
```json
{
  "id": "arquivo:video-livre-especifico",
  "natureza": "video",
  "url": "<URL DIRETA DO VÍDEO; ou página da origem SOMENTE com cache por SHA256 e arquivo_ext>",
  "pagina": "<página onde se verifica a licença e o autor>",
  "titulo": "<assunto realmente filmado>",
  "credito": "Autor original · CC BY 4.0",
  "licenca": "CC BY 4.0",
  "uso_comercial": "sim",
  "sha256_origem": "<64 caracteres hexadecimais do arquivo REAL>",
  "prova": {"midia_corresponde": true, "metodo": "<verificação registrada de identidade e correspondência>"}
}
```
**Não inventar** URL, hash, autor, licença, cena, correspondência ou interpretação de licença. Arquivos originais não são redistribuídos no repositório público. Para vídeo baixado **manualmente** do Pexels, a pasta `CORINGA_MIDIA_LOCAL` pode apontar para mídia armazenada com nome `<sha256>.mp4` ou equivalente; não se automatiza scraping nem se contorna a API suspensa. Se a URL registrada for a **página do vídeo no Pexels** (sem sufixo `.mp4`), registrar também `"arquivo_ext": ".mp4"` no manifesto. Esse modo **só funciona com o cache já existente** e SHA256 conferido; se o arquivo não tiver sido baixado legitimamente ou não estiver disponível localmente, a importação falha. Nenhuma página é raspada. O uso comercial depende também das condições específicas de licença, direitos de terceiros, pessoas e marcas.

O storyboard cita:
```json
{
  "t0": 12.5, "t1": 16.5,
  "componente": "registro.video",
  "params": {"asset": "arquivo:video-livre-especifico", "inicio": 0.5}
}
```
Esses tempos são ilustrativos; o clipe deve começar **após o gancho cartográfico obrigatório** no ATLAS V1. Duração do recorte <= original. Sem camada editorial que desapareça sob o vídeo.

Para fotografia real, uma camada dentro do beat com `composicao: "atlas.prova"` usa:
```json
{"id": "fabrica-real", "componente": "atlas.provaVisual", "slot": "prova",
 "t0": 7, "t1": 11,
 "p": {"asset": "commons:id-foto-real", "meta": "Autor · CC BY 4.0", "enquadramento": "conter", "rotulo": "Instalação identificada"}}
```
**Exemplos não entram em produção** sem arquivos realmente cadastrados, direitos e imagem corretos.

## Verificações
- `tests/test_atlas_integracao_p1.py` contém testes offline sem serviços externos: catálogo ATLAS/DOSSIÊ separado, falhas por vídeo ausente/tipo errado/duração insuficiente, colisão com camada oculta, créditos/attribution, SHA256, licença e origem, `ffprobe` de um vídeo sintético criado durante o teste, reuso do backend real.
- `.github/workflows/atlas-validacao.yml` roda V1, P0 e P1, mais JS/TypeScript; é um teste técnico isolado, não uma prévia de qualidade.
- Execução `44429572086`: **sucesso, 108 testes Python + TS/JS** (antes da adição do smoke real FFmpeg).
- Teste FFmpeg real: `test_ativos_reutiliza_hash_origem_e_probe_v4`, que gera original de 0,8 s e usa **de fato** `src.v4.backends.legado.render_video` para recortar e normalizar segmento de 0,45 s em 1080×1920, verificando duração e ausência de áudio original. É **verificação de segmento**, não comprovação de direção audiovisual final.
- Execução **`44430232954`**: **success, 108 testes Python passaram**, incluindo recorte real FFmpeg sintético, verificações JS/TypeScript verdes. Execução final após suporte ao Pexels manual **`44430724950`**: **success, 108 testes Python passaram**, incluindo importação manual com cache SHA e o mesmo smoke FFmpeg; TypeScript/JS também verdes. 
- Execução `44429900573`: falhou **ANTES dos testes**, na action externa `FedericoCarboni/setup-ffmpeg@v3` com erro `Failed to read version from readme`. A dependência da action foi removida **só** da validação ATLAS; reexecução `44430232954` comprovou o código P1 verde.

## Lacunas e próximos passos sem falsa aprovação
1. **Biblioteca V3 integrada em modo opt-in:** implementada a ponte `ponte_biblioteca.py` abaixo; exige manifesto explícito de aprovações, DB e arquivos V3 acessíveis. Ainda falta provisionar/persistir essa mídia no runner da produção e habilitar o manifesto de curadoria real. Não criar novo banco.
2. **Mídia do tema:** ainda NÃO foi cadastrado vídeo EUV/TSMC realmente identificado e licenciado. Não gerar preview Guerra dos Chips com vídeo genérico fingindo ser uma instalação específica.
3. **Preflight e performance:** fotos protagonistas e crédito de vídeo ganharam contratos; precisam ser testados em render REAL visual com licença. O Remotion ainda renderiza o palco base durante intervalos substituídos por vídeo — **otimização potencial** antes de YouTube longo.
4. **Direção automática:** a ponte V3→ATLAS P0 é opcional e não está ligada a um orquestrador completo; a seleção automática dos componentes recém adicionados precisa ser exercitada com roteiro diferente, não hardcode de chips.
5. **Experimento decisivo:** curta vertical 20–30s com narrador Gemini/Charon confirmado e mídia pertinente; comparar vídeo contra roteiro pelo olho humano. Só depois começar perfil horizontal 1920×1080 de 90–120s com lógica de capítulos.
6. **Risco de créditos:** renderizar e conferir a fonte em celular, sobreposições reais das três plataformas e licença específica do clipe; dados técnicos verdes não significam permissão legal nem resultado editorial.


## Ponte V3→ATLAS sem banco paralelo (implementada após os testes P1 iniciais)

Código experimental: `src/v4/formatos/ponte_biblioteca.py`. Não executa pesquisa online nem grava uma segunda base de mídia. **Fonte dos binários e IDs:** `src/v3/biblioteca.py::Biblioteca` (SQLite, cache local e arquivos por SHA256), existente antes do P1.

**Como ativar só quando houver curadoria e arquivo acessível ao runner:**
- `BIBLIOTECA_DB` → caminho do banco global V3, com `BIBLIOTECA_ARMAZEM` → diretório de bytes originais endereçados por SHA256. Ausente/alterado ⇒ **BLOQUEADO**.
- `CORINGA_ATLAS_APROVACOES_V3` → manifesto JSON **privado/versionado para os autorizados**, apontando para IDs estáveis `cm-...` e hash completo. Sem essa variável, o ATLAS continua lendo **só** `src/v4/biblioteca_comprovada.json`, sem regressão dos pilotos.
- Formato do manifesto (valores ilustrativos, NUNCA substituem verificação factual/real de direitos):
```json
{
  "versao": 1,
  "aprovacoes": [{
    "midia_id": "<ID REAL cm-... do banco V3>",
    "sha256": "<SHA256 ORIGINAL VALIDADO>",
    "prova": {
      "midia_corresponde": true,
      "revisor": "<identificação da revisão efetuada>",
      "evidencia": "<observação/registro da correspondência imagem/acontecimento>",
      "acontecimento": "<ação específica demonstrada>",
      "licenca_evidencia": "<link/registro dos direitos conferidos>",
      "licenca_exata": "<licença e versão verificadas; ex.: CC BY 4.0 (não copiar classificação genérica)>"
    }
  }]
}
```
- A licença exata declarada pelo revisor deve concordar com a categoria da V3. **CC BY 4.0** não é **CC BY-SA 4.0**; versão e créditos são preservados na montagem.
- A biblioteca V3 também precisa ter `uso_comercial=sim`, ausência de indicação de IA, **autor, licença e comprovação, página de origem**, arquivo original presente e identidade binária intacta. Mesmo hash já cadastrado no catálogo V4 não gera duplicata. Item rejeitado falha explicitamente, sem procurar substituto genérico.
- `produzir.ativos` e `produzir.preflight` agora chamam **esse catálogo opt-in**, e `produzir._origem` lê bytes V3 **locais por SHA**, sem fazer requisição a páginas HTML do Pexels. `diretor.prompt(..., inventario=None)` recebe apenas mídias aprovadas com pertinência textual mínima `SCORE_MIN` da V4. Conteúdo com só 1 palavra genérica em comum não é indicado.
- **Importante:** pesquisa de texto não comprova identidade de uma fábrica. Curadoria/validação por acontecimento continua obrigatória; o teste de relevância é **filtro conservador**, não reconhecimento factual. O motor não pode apresentar mídia genérica como se fosse de instalação nomeada.
- `tests/test_atlas_ponte_v3.py` prova ingestão V3 com arquivo sintético, manifesto aprovado, ligação ao catálogo, uso dos bytes corretos, expiração/alteração de SHA, banco ausente, falta de prova de licença, ausência de duplicata e filtro factual. CI foi incluído em `.github/workflows/atlas-validacao.yml`.
- **Atenção infraestrutura:** GitHub Actions é efêmero. Sem banco V3 e bytes armazenados de forma durável e disponibilizados **com autorização**, o modo V3 ficará desligado. Não colocar vídeos baixados de terceiros brutos em repositório público nem presumir permissão de sublicenciamento.
- Nesta entrega **não** foi gerada nova narração/episódio e **não** há anúncio de que novas mídias já foram curadas para chips.

**Próxima prova:** curar 2–3 ativos específicos (com direitos e ação registrada), produzir uma mini-sequência vertical privada de 20–30 s com voz Gemini/Charon, mostrar em dispositivos e fiscalizar ritmo, correspondência imagem/fala, créditos e interesse humano. Vídeo horizontal longo continua fase posterior, sujeito a 16:9 e direção por capítulo.


## Resultado da integração V3 após regressões (CI final)

- Actions **44431917824**: `success`, 114 testes Python, JS/TypeScript aprovados; confirma a ponte de mídia V3 para ATLAS com manifesto, banco único e bytes por SHA.
- Actions **44432458299**: 116 testes passaram e **1 teste falhou por uma expectativa incorreta** sobre a forma de representar a licença: a V3 resume `CC BY 4.0` como `CC BY`. O problema de fidelidade foi resolvido exigindo `prova.licenca_exata` no manifesto e conservando a licença/versão no catálogo e nos créditos.
- Actions **44433077213**: **SUCCESS — 118 testes Python passaram**, com testes JS/TypeScript também verdes. Abrange vídeo sintético recortado com FFmpeg real, biblioteca V3, manifesto curado, SHA/proveniência, categoria × versão de licença, duplicidade e filtro de pertinência. Testes **offline**, sem Claude/Gemini nem render audiovisual de episódio.
- Nenhuma mídia TSMC/EUV foi efetivamente cadastrada ou revista por humano. Não existe prévia nova da Guerra dos Chips homologada nesta rodada.

<https://github.com/Heitor2404/coringa-news/actions/runs/44433077213>
