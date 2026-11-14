# Metadados que cada fonte do acervo devolve (condição 5)

**Como foi verificado.** Esta sessão não alcança as APIs: o proxy recusa commons.wikimedia.org, images-api.nasa.gov,
wikipedia, wikidata, openverse e loc.gov. Por isso a verificação usou três coisas:

- a documentação oficial (CommonsMetadata, Template:Information, documentação da API da NASA, mapeamento de campos do Openverse);
- páginas reais de arquivos, por espelhos públicos e pela busca;
- o código atual (`src/acervo.py`, `src/midia.py`).

**Falta conferir.** Uma resposta crua de cada API ainda precisa ser conferida numa coleta de metadados. Ela é grátis e não
usa IA, mas roda num ambiente com rede (o CI). Não executei essa coleta.

Legenda das colunas:

- **Devolve hoje**: vem na resposta da chamada que o código já faz.
- **Guarda hoje**: o que `_cand` mantém (título 120 caracteres, descrição 220 caracteres, ano).
- **Consulta extra**: só com outra chamada (grátis).
- **Não existe**: a fonte não tem esse dado.

## Commons, Wikipédia, Wikidata

Imagens da Wikipédia e da Wikidata são arquivos do Commons e passam por `_commons_infos`.

| Campo | Devolve hoje | Guarda hoje | Observação |
|---|---|---|---|
| `extmetadata.DateTimeOriginal` | sim | só o ano | Vem do campo `date` do {{Information}}: é a data de criação **declarada** por quem enviou. Às vezes é EXIF (`source: mediawiki-metadata`), às vezes é texto como "published 1982" ou "Uploaddate 2010-01-17" (caso real: Tacoma). Pode vir em `<time datetime=…>`. |
| `extmetadata.DateTime` | sim | não | É a data do arquivo ou do envio. **Nunca** situa a imagem no tempo. |
| `imageinfo.timestamp` | só se pedir `iiprop=timestamp` | não | Data do envio. Não situa a imagem. |
| `extmetadata.Categories` | sim | **descartado** | Categorias diretas, curadas por pessoas (ex.: "Apollo 11 Hasselblad film magazine 40"). É o principal sinal da família REGISTRO. |
| Categorias-mãe (ancestrais) | não | — | Consulta extra (`prop=categories` nas categorias), 1–2 níveis. |
| `ImageDescription`, `ObjectName` | sim | 220 caracteres | Descrição multilíngue em HTML. |
| `Artist`, `Credit`, `LicenseShortName` | sim | autor e licença no crédito | — |
| `GPSLatitude` / `GPSLongitude` | quando há | não | Não usado nesta etapa. |
| Dados estruturados (P571 data de criação, P180 "retrata") | não | — | Consulta extra (`wbgetentities` no M-id). Alguns arquivos têm, outros não. |
| Categoria do ACONTECIMENTO e da ENTIDADE | não | — | Consulta extra: artigo da pesquisa → Wikidata → P373 (categoria do Commons). Sem isso, só existe o vínculo fraco por nome. |

## NASA Image Library

| Campo | Devolve hoje | Guarda hoje | Observação |
|---|---|---|---|
| `date_created` | sim | só o ano | Data declarada pela NASA. Às vezes é a de arquivamento: há descrições com "Photo filed 11 July 1969". |
| `keywords` | sim | **descartado** | Palavras-chave curadas (ex.: "Apollo 11", "Apollo 11 50th Anniversary"). A celebração de 2019 também tem a palavra "Apollo 11": por isso palavra-chave nunca prova sozinha. |
| `center`, `photographer`, `nasa_id` | sim | centro no crédito | — |
| `description` | sim | 220 caracteres | — |
| EXIF completo | não | — | Consulta extra (`/metadata/{nasa_id}`). |

## Library of Congress

| Campo | Devolve hoje | Guarda hoje | Observação |
|---|---|---|---|
| `date` | sim | só o ano | Data de criação ou de publicação do item. Precisa ser classificada. |
| `subject` / `subject_headings` | sim | **descartado** | Cabeçalhos de assunto curados (ex.: "Bridge failures--Washington (State)--Tacoma"). |
| `location`, `contributor` | sim | não | — |

## Fontes sem data utilizável

| Fonte | Data | Vínculo possível |
|---|---|---|
| Openverse | **não existe** na resposta da API (o Flickr tem `date_taken`, mas o Openverse não expõe) | etiquetas livres de quem enviou: só vínculo fraco |
| iNaturalist (`taxon_photos`) | não existe | o táxon é o vínculo (entidade) |
| GBIF | `eventDate` existe na ocorrência (o código não guarda) | espécie |
| Pixabay vídeo | não existe | etiquetas livres |
| Met, Art Institute, Cleveland | data da OBRA (`objectEndDate`, `date_end`, `creation_date`) | é obra de arte: nunca prova |
| Smithsonian | `indexedStructured.date`, muitas vezes só a década ("1980s") | `topic` e `place` (descartados hoje) |
| Europeana | `year` | `subject` (descartado) |

## Regras que o código novo aplica a isso

- **Data que situa a imagem:**
  - Só conta a de captura (EXIF) ou a de criação declarada.
  - A de publicação só serve de limite superior: a imagem existia antes dela.
  - A de envio (upload) nunca conta.
  - Data desconhecida não confirma nem contradiz.
- **Mesma família:** categoria, palavra-chave, data e descrição do mesmo registro contam como UMA evidência.
- **Etiqueta livre** (Openverse, JungleDragon, Flickr) vale como descrição, nunca como categoria curada.
- **Erro conhecido (encontrado na avaliação reservada):** o texto real "Uploaddate 2010-01-17" foi classificado como
  criação declarada, porque o padrão exige "upload" como palavra separada. A correção proposta está no documento principal.
  Não foi aplicada, para não usar o conjunto reservado no ajuste.
