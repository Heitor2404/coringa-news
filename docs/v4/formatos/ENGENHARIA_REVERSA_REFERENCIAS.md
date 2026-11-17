# Engenharia reversa das referências A (mapas) e B (dossiê)

Análise dos MP4s originais do Heitor (720×1280, 30 fps), feita em 17/11 com `scripts/analisar_referencia.py`
(PySceneDetect, limiar 27; mudança por segundo SÓ na zona de conteúdo, 8–62 % da altura, separada da faixa de legenda;
loudness EBU R128) e com grades densas de quadros. Os vídeos e quadros **não** entram no repositório (material de
terceiros). Copiamos a gramática observável, não identidade, artes, narração ou paleta.

## Medidas

| | A — mapas (68,2 s) | B — dossiê (176,7 s) |
|---|---|---|
| Trocas de tomada | **0** (o único corte, aos 68,0 s, é o cartão final) | **10** (tomada média ≈ 16 s) |
| Mudança na zona de conteúdo (p10 / p50 / p90) | 1,4 / 6,8 / 22,5 | 0,8 / 6,4 / 32,0 |
| Maior trecho sem mudança de conteúdo | **2 s** | **1 s** |
| Brilho médio (0–255) | 77 (mapa claro/satélite) | 45 (mesa escura com objetos claros) |
| Áudio no MP4 | −14,2 LUFS · TP −2,5 dBTP · LRA 1,9 | −14,2 LUFS · TP −1,2 dBTP · LRA 4,2 |
| Legenda | 2–4 palavras, branca, sem caixa, ≈ 77 % da altura | caixa alta, palavra-chave em cor de destaque, ≈ 73 % |
| Zona dos objetos | 8–62 % da altura, centrados | 10–60 %, um objeto principal por vez |

**Conclusão central:** os dois quase não cortam. A sensação de ritmo vem de **elementos que entram e saem sobre um palco
persistente**, sincronizados com a palavra que os pede. Cortar mais não resolveria; o que falta ao nosso motor é progressão
por camada.

## Beat sheet A (ATLAS)

| Tempo | Função | Palco | O que entra (prova visual da fala) |
|---|---|---|---|
| 0–2 | gancho | mapa continental, país em destaque | região colorida + retrato circular com etiqueta |
| 2–7 | tensão | mesmo mapa | cédula de papel "cai" sobre o mapa; palavra-gancho gigante ("COMO?") |
| 7–12 | escala | troca para a cidade (satélite) | escada de 5 níveis no topo; cartão de número grande (≈ 1.260) com gráfico de assentos |
| 12–20 | prova numérica | mesmo palco | cartão com semicírculo que se preenche e contador (0 → 2.952) |
| 20–30 | estrutura territorial | mapa político por divisões | a escada persiste e acende nível por nível; pílula "27 PROVÍNCIAS" na base |
| 30–37 | regra | mapa de relevo | figura humana, rótulos de voto direto/indireto sobre a escada |
| 37–48 | estrutura abstrata | **mapa técnico escuro** (contorno + grade) | blocos empilhados (Estado / Partido) — a hierarquia vira objeto |
| 48–55 | quem manda | mesmo palco | pirâmide numérica (7 / 24 / ≈200 / ≈100 mi) + retrato que sobe ao topo |
| 55–68 | síntese | **retorno ao mapa inicial** | escada inteira + barra de deputados; cartão final |

Funciona porque: (1) o mapa nunca some, só troca de escala/estilo quando a explicação muda de nível; (2) cada número tem
objeto e unidade; (3) a escada é um **componente persistente** que acumula significado; (4) o abstrato ganha palco próprio
(técnico) em vez de foto genérica. Não funciona/evitar: texto minúsculo em cartões (lê mal no celular); tiles de satélite de
terceiros (licença — usamos Natural Earth/OSM).

## Beat sheet B (DOSSIÊ)

| Tempo | Função | Palco | O que entra |
|---|---|---|---|
| 0–15 | gancho investigativo | mesa escura | ficha de procurado + checklist marcado + carimbo "NÃO EXISTE" |
| 15–30 | identidade | mesa | retrato com legenda de fonte, nome em tipografia grande, dados com ícones |
| 30–50 | contexto | mesa | documento oficial com sublinhado; pastas com aba de ano ligadas por linhas (organograma) |
| 50–80 | cronologia | mesa | caixa de entrada, contador "062 dias", calendário que vira páginas, datas grandes |
| 80–115 | dinheiro/propagação | mesa + filme real dessaturado | ordem de pagamento, cifra grande, grade de pedidos, impressora, alerta de resgate |
| 115–155 | comparação | mesa | ficha × foto ("VERDADEIRO"), documento judicial, novos nomes/pastas |
| 155–176 | síntese | mesa | pastas reunidas com carimbos, pergunta final, cartão de fecho |

Funciona porque: (1) fundo escuro **com objetos informativos** (não é blackout); (2) cada objeto tem proveniência visível
(foto: fonte, documento: órgão/data); (3) carimbos/sublinhados apontam a evidência já presente; (4) números e datas viram
objetos grandes; (5) um objeto principal por vez. Evitar: paleta e identidade vermelhas da referência.

## Regras comuns e diferenças → o que o motor implementa

| Regra observada | Onde está no motor |
|---|---|
| palco persistente; progressão por camadas, não por cortes | `Formato.tsx` (palco + camadas); `plano.validar` F-SEM-PROGRESSAO (≤ 4 s; as referências ficam em 1–2 s) |
| posições previsíveis (objeto no meio, base para pílulas) | slots fixos em `formatos.json`; F-COLISAO calculada antes do render |
| número sempre com unidade/objeto | `editorial.statCard` (valor + unidade + rótulo; contagem real) |
| hierarquia/escada persistente que acende | `editorial.hierarchy` (escada ou perfil, níveis ativos por tempo) |
| abstrato em palco técnico | palco `tecnico` (grade + planta do assunto) |
| retorno ao palco inicial no fecho | plano ATLAS (keyframe final = câmera do gancho) |
| proveniência visível | `dossie.documentCard` (cabeçalho, data, crédito/licença obrigatórios no preflight) |
| evidência apontada, não inventada | `dossie.evidenceHighlight` (carimbo/sublinhado/círculo sobre parte de um objeto já presente) |
| legenda curta e sincronizada | camada global `Camada.tsx` (palavra a palavra; caixa alta) |
| −14 LUFS, pico < −1 dBTP | `compositor.final` + `corrigir_pico_aac`; portão no MP4 final |
| ATLAS: mapa/escala/territórios · DOSSIÊ: mesa/documentos/datas | presets em `formatos.json` (componentes e palcos permitidos por formato) |
