"""Auditoria individual das composições (V2.1): 15 campos por composição e estado final.

Estado final (técnico — NÃO é aprovação visual; quem aprova é o Heitor):
  'aprovado tecnicamente' = testes e medição sem defeito conhecido;
  'parcial'               = funciona, com limitação conhecida registrada;
  'bloqueado'             = não deve ir a vídeo até resolver.

Mudanças GLOBAIS (valem para todas, além das específicas):
  G1 tokens (V2.T) e zonas seguras por plataforma (V2.Z: reels/tiktok/shorts/todas);
  G2 legenda adaptativa por cena (mede o que a cena ocupa a 70% e escolhe 1240/1300/360 e 58/66 px);
  G3 texto mínimo 26 px (token fs.min); G4 marca some quando a cena tem kicker; G5 cenas ocultas por visibility.
"""
from __future__ import annotations

CAMPOS = ['id', 'funcao', 'problema_v2', 'causa', 'correcao_v21', 'arquivo', 'teste', 'evidencia', 'legibilidade', 'hierarquia',
          'movimento', 'dados_fatos', 'limitacoes', 'revisao_humana', 'estado']

_G = 'só mudanças globais (G1–G5)'


def _a(id, funcao, problema, causa, correcao, arquivo, teste, legib, hier, mov, dados, lim, rev, estado):
    return dict(zip(CAMPOS, [id, funcao, problema, causa, correcao, arquivo, teste, f'capturas antes/depois em 8/45/75/97% ({id}_0..3.jpg)',
                             legib, hier, mov, dados, lim, rev, estado]))


AUDITORIA = [
    _a('abertura.pergunta', 'gancho: pergunta sobre a foto do assunto',
       'mascote não existia; texto sempre no mesmo terço, mesmo com o foco da foto ali', 'layout fixo, sem leitura do foco da foto',
       'posição adaptativa (texto do lado oposto ao foco); pose de mascote opcional com sombra/contraluz; margem direita 380 com mascote',
       'comp/aberturas.js abertura.pergunta', 'regressão visual; pipeline experimental (cena 0)', 'pergunta 88 px; contexto serifa 40 px', 'protagonista = pergunta; foto é fundo',
       'empurrão lento na foto + palavras entram', 'nenhum número', 'mascote só se houver pose PNG em assets/mascote3d', 'a pergunta segura sem a legenda?', 'aprovado tecnicamente'),
    _a('abertura.revelacao', 'gancho: título curto sobre detalhe da foto', 'sem defeito medido', '—', _G, 'comp/aberturas.js',
       'regressão visual', 'título 88 px', 'título', 'aproximação do detalhe ao plano geral', '—', '—', 'o detalhe inicial é legível no celular?', 'aprovado tecnicamente'),
    _a('banner.discreto', 'contexto curto sem interromper', 'entrava e ficava; sem saída nem posição alternativa', 'sem parâmetros de permanência',
       'parâmetros entra/sai; posição "baixo" (1080); saída por cortina', 'comp/banners.js banner.discreto', 'regressão visual', '34 px', 'secundário (não compete com a legenda)',
       'entrada, permanência, saída', '—', '—', 'tempo de leitura suficiente?', 'aprovado tecnicamente'),
    _a('banner.importante', 'alerta / correção de fato', 'um só nível (vermelho) para tudo', 'sem categoria', 'níveis "importante" (amarelo, ícone de documento) e "alerta" (vermelho); saída deslizando',
       'comp/banners.js banner.importante', 'regressão visual', 'título 44 px; corpo 30 px', 'prioridade sobre a legenda (legenda muda de faixa)', 'entra, pulsa uma vez, sai',
       'texto do exemplo vem de fatos.PANAMA_LEILAO', '—', 'o amarelo "importante" se distingue do alerta?', 'aprovado tecnicamente'),
    _a('lower_third', 'nome de pessoa/lugar/navio', 'texto pequeno; sem tipo "história"', 'tamanhos antigos', 'tipo "historia" com selo de ano; texto maior; base ancorada em 1185; saída',
       'comp/banners.js lower_third', 'regressão visual', 'nome 44 px', 'secundário', 'entra/sai', 'data do exemplo marcada como do arquivo', '—', '—', 'aprovado tecnicamente'),
    _a('titulo.capitulo', 'separador de parte', 'sem defeito medido', '—', _G, 'comp/editorial.js', 'regressão visual', '88 px', 'título', 'número grande ao fundo', '—', '—', '—', 'aprovado tecnicamente'),
    _a('destaque.palavras', 'frase-chave sobre foto', 'sem defeito medido', '—', _G, 'comp/editorial.js', 'regressão visual', '72 px', 'frase', 'marca-texto entra por palavra', '—', '—', '—', 'aprovado tecnicamente'),
    _a('numero.animado', 'número grande com contexto', 'equivalência solta ("80 piscinas") sem cálculo; cubo pequeno; rótulo encostado no número',
       'equivalência escrita à mão; escala fixa', 'equivalência calculada em unidades.py (cubo de ≈ 59 m + referência real na MESMA escala); escala adaptativa até 1200; número desceu 23 px (choque medido)',
       'comp/dados.js numero.animado; src/v2/unidades.py; fatos.para_tela', 'test_v21 (pipeline: número vem do fato validado); fiscal D9', 'número 230 px; unidade 52 px; fonte 26 px', 'protagonista = número; cubo explica a escala',
       'contagem até o valor; cubo cresce', 'US$ 5,3 mi = lance em leilão por vaga (SK Gas, G. Spirit, 1º/09/2026; pedágio à parte; Revista Oeste); 200 milhões de L (Wikipedia)',
       'equivalência só para volume; outras unidades ficam sem', 'o cubo ao lado do Cristo Redentor ajuda ou distrai?', 'aprovado tecnicamente'),
    _a('comparacao.grandezas', 'altura/tamanho lado a lado', 'sem defeito medido', '—', _G + '; referências em capacidades.REFERENCIAS_M', 'comp/dados.js', 'regressão visual', 'rótulos 28 px',
       'item destacado', 'barras/silhuetas crescem', 'referências aproximadas marcadas', '—', '—', 'aprovado tecnicamente'),
    _a('proporcao', 'parte de um todo (%)', 'sem defeito medido', '—', _G, 'comp/dados.js', 'regressão visual', '—', 'percentual', 'grade preenche', 'fonte obrigatória', '—', '—', 'aprovado tecnicamente'),
    _a('grafico.barras', 'comparar quantidades', 'barras sem conclusão; rótulos pequenos', 'gráfico decorativo', 'parâmetro conclusao (caixa após as barras); destaque = categoria narrada; rótulos 34 px, valores 38 px',
       'comp/graficos.js barras', 'regressão visual; seleção x7 (valores não numéricos recusados)', '34/38 px', 'conclusão', 'barras crescem, depois a conclusão', 'exemplo marcado como DADOS ILUSTRATIVOS',
       '—', 'a conclusão aparece no tempo certo?', 'aprovado tecnicamente'),
    _a('grafico.temporal', 'evolução no tempo', 'eixo podia não começar no zero sem aviso; sem período destacado', '—', 'conclusao; faixa de período; aviso "EIXO NÃO COMEÇA NO ZERO"; linha termina aos 75%',
       'comp/graficos.js temporal', 'regressão visual; seleção x6 (série curta recusada)', 'eixo 28–30 px', 'linha + conclusão', 'linha desenha', 'exemplo ilustrativo marcado', '—', '—', 'aprovado tecnicamente'),
    _a('mapa.localizacao', 'onde fica', 'pinos e nomes pequenos; câmera chegava tarde', 'tamanhos antigos', 'pino 40 px; nomes 38–42 px; câmera chega a ~45%; nomes de pino escolhem posição livre',
       'comp/mapas.js', 'regressão visual; fiscal D7 (coordenada/país)', 'nomes 38–42 px; atribuição 26 px', 'pino', 'aproxima com leve rotação', 'coordenadas Natural Earth; atribuição na tela',
       'depende de scripts/v2_natural_earth.py', '—', 'aprovado tecnicamente'),
    _a('mapa.rota', 'trajeto / comparação de rotas', 'rota fina e reta; Cabo Horn saía do quadro; nomes sob o cabeçalho; "80 km" (a fonte citada diz 82)',
       'linha reta em Mercator; zoom mínimo vertical do MapLibre (z≈1,9 em 1920 px); nomes sempre acima do pino; valor do roteiro antigo',
       'rotas por círculo máximo, 12 px com brilho; painel de comparação (até 3); host encolhe quando o enquadramento pede zoom menor; nomes evitam cabeçalho/painel/pino vizinho; geo.validar_rota; 82 km',
       'comp/mapas.js motorMapa, animPino, mapa.rota; src/v2/geo.py validar_rota/caixa_de', 'test_v21: rota sobre terra, Cabo Horn no quadro, nomes sem choque; fiscal D8',
       'distância 64 px; nomes 42 px', 'rota', 'traço progressivo + bolinha na ponta; contagem da distância', 'NY–SF 9.500 × 22.500 km (Wikipedia); traçado ilustrativo; Cabral marcado aproximado',
       'zoom mundial ainda deixa NY e SF próximos (nomes legíveis, pinos encostados)', 'a comparação canal × Cabo Horn convence sem som?', 'aprovado tecnicamente'),
    _a('mapa.territorio', 'destacar país', 'sem defeito grave medido', '—', _G + '; câmera ~45%', 'comp/mapas.js', 'regressão visual', 'nome 44 px', 'território', 'aproxima; território acende',
       'Natural Earth', 'rótulo de mar pode cair sobre o território (Golfo do Panamá no exemplo)', 'o rótulo do golfo sobre o país incomoda?', 'parcial'),
    _a('linha_tempo.historica', 'sequência de datas', 'sem defeito medido', '—', _G, 'comp/editorial.js', 'regressão visual; seleção (datas 1000–2099)', 'ano 64 px', 'evento ativo',
       'trilho corre; evento ativo acende', '—', 'o ano seguinte aparece cortado na borda durante a corrida (intencional?)', 'o corte do ano seguinte na borda é aceitável?', 'aprovado tecnicamente'),
    _a('foto.historica', 'foto de arquivo em dois momentos', 'zoom além da resolução (borrão); carimbo fora da área segura; ilustração substituía a foto faltante com rótulo "FOTO REAL"',
       'zoom sem limite; posição fixa; fallback para fundo_b', 'momento 1 inteira / momento 2 aproximação limitada a 2× a resolução (ou varredura em panorâmica); alerta de baixa resolução; carimbo dentro da foto e sai quando a anotação entra; substituto "SEM ACERVO"',
       'comp/fotos.js foto.historica; galeria.midia/_substituto', 'test_v21 (substituto); medição sem choque', 'carimbo 30 px; crédito 26 px', 'foto', 'assenta, aproxima/varre, anotação desenha',
       'ano e crédito (Library of Congress, domínio público)', 'a panorâmica de 1913 tem 91 px de altura útil: vira uma faixa fina, mais fraca que o layout de dois painéis da V2; precisa do original em resolução maior',
       'com esta foto, V2 ou V2.1 fica melhor?', 'parcial'),
    _a('foto.sequencia', 'várias fotos do mesmo lugar', 'sem defeito medido', '—', _G, 'comp/fotos.js', 'regressão visual', '—', 'foto atual', 'troca com movimento', '—', '—', '—', 'aprovado tecnicamente'),
    _a('foto.documental', 'foto real do assunto', 'sem defeito medido', '—', _G + '; recorte/foco "auto"', 'comp/fotos.js; palco.preparar', 'regressão visual; fiscal D5 (arquivo ausente)', '—', 'foto',
       'Ken Burns', '—', '—', '—', 'aprovado tecnicamente'),
    _a('comparacao.antes_depois', 'duas fotos, antes × depois', 'sem defeito medido', '—', _G, 'comp/fotos.js', 'regressão visual', 'selos 30 px', 'divisória', 'cortina varre', '—', '—', '—', 'aprovado tecnicamente'),
    _a('video.documental', 'trecho de vídeo de arquivo (NOVA)', 'não existia', '—', 'quadros extraídos por ffmpeg (cache), moldura para paisagem / cobertura para vertical, etiqueta, lower third, saída',
       'comp/fotos.js video.documental; palco.quadros_video', 'regressão visual; catálogo', 'etiqueta 26 px', 'vídeo', 'reprodução quadro a quadro determinística',
       'só testado com clipe SINTÉTICO (fractal) marcado na tela', 'sem vídeo de arquivo real local para teste; licença do vídeo segue a mesma regra das fotos', 'testar com um trecho real antes de usar', 'parcial'),
    _a('diagrama.explicativo', 'nós e setas', 'sem defeito medido', '—', _G, 'comp/ciencia.js', 'regressão visual; seleção (máquina → diagrama)', '—', 'fluxo', 'setas desenham', '—', '—', '—', 'aprovado tecnicamente'),
    _a('processo.etapas', 'etapas em ordem', 'sem defeito medido', '—', _G, 'comp/ciencia.js', 'regressão visual; seleção b1/t2/r10', '—', 'etapa ativa', 'etapas acendem', '—', '—', '—', 'aprovado tecnicamente'),
    _a('forcas.vetores', 'forças sobre um objeto', 'sem defeito medido', '—', _G, 'comp/ciencia.js', 'regressão visual; seleção f1/f2/r9', '—', 'vetores', 'vetores crescem', '—', '—', '—', 'aprovado tecnicamente'),
    _a('astronomia.orbita', 'órbita', 'texto "fora de escala" com 24 px', 'tamanho antigo', '26 px (G3)', 'comp/ciencia.js', 'regressão visual; seleção a1/r11 (ano-luz deixou de virar órbita)', '26 px', 'órbita',
       'translação', 'marcado FORA DE ESCALA', '—', '—', 'aprovado tecnicamente'),
    _a('mecanismo.eclusa', 'eclusa: o navio sobe/desce por gravidade', 'escala pequena; câmera parada; nível linear; comporta abria com desnível; navio flutuava fora da água; rótulos se cobriam',
       'desenho de V2 sem física nem planos', 'mundo 1480 px com túneis e válvulas; planos A–F; nível (1−k)²; comporta só abre com Δ < 0,3 m; navio na superfície; rótulos com anticolisão; estado físico publicado; tempos amarrados à fala',
       'comp/mecanismos.js mecanismo.eclusa', 'test_v21: física nos dois sentidos; pipeline experimental (entra/desce/iguala medidos); fiscal S3', 'rótulos 30–34 px', 'navio + nível',
       '6 planos de câmera; água, válvulas, comportas', '26 m (Wikipedia); FORA DE ESCALA na tela', 'esquema ilustrativo, sem proporção real da câmara', 'entende-se sem som?', 'aprovado tecnicamente'),
    _a('mecanismo.nivel', 'nível de água genérico', 'sem defeito medido', '—', _G, 'comp/mecanismos.js', 'regressão visual; seleção n1/n3/r15', '—', 'nível', 'sobe/desce', '—', '—', '—', 'aprovado tecnicamente'),
    _a('evento.impacto', 'explosão/impacto com raios', 'sem defeito medido', '—', _G, 'comp/ciencia.js', 'regressão visual; seleção a3/n2/r12', 'rótulos 28 px', 'centro', 'onda expande', 'raio marcado (≈)', '—', '—', 'aprovado tecnicamente'),
    _a('revelacao.surpresa', 'resposta no instante em que é dita', 'só sobre foto; classes colidiam com a eclusa quando usada como base',
       'sem camada de base; nomes de classe genéricos', 'camada base (mecanismo congelado sob a revelação, regra M8); classes rv-; rótulos da base escondidos; gradiente só no topo',
       'comp/editorial.js; nucleo.js (sc.base); montagem.py M8', 'pipeline experimental (oculta 0,3 s antes / visível 0,35 s depois da palavra); fiscal D10', 'resposta 150 px', 'resposta', 'clarão + resposta bate',
       '—', '—', 'o clarão é forte demais?', 'aprovado tecnicamente'),
    _a('fonte.evidencia', 'recorte de fonte citada', 'textos com 24 px', 'tamanho antigo', '26 px (G3)', 'comp/editorial.js', 'regressão visual', '26 px', 'trecho grifado', 'cartão entra, grifo corre',
       'exemplo SINTÉTICO marcado (exemplo.invalid)', '—', '—', 'aprovado tecnicamente'),
    _a('citacao', 'fala literal', 'sem defeito medido', '—', _G, 'comp/editorial.js', 'regressão visual', '—', 'citação', 'entra por linha', 'autor obrigatório', '—', '—', 'aprovado tecnicamente'),
    _a('encerramento.editorial', 'fecho com conclusão e marca', 'bloco de marca grande e genérico, sem relação com o vídeo', 'variante única', 'variantes conclusao/pergunta/marca/cta; faixa de marca compacta; fontes 1150–1210; sobre a base do mecanismo',
       'comp/editorial.js; montagem.py (fechamento)', 'regressão visual; pipeline experimental (cena final)', 'conclusão 70 px; fontes 26 px', 'conclusão', 'mascote entra; marca desliza',
       'fontes do vídeo listadas', '—', 'tem cara de marca sem virar anúncio?', 'aprovado tecnicamente'),
    _a('animacao.quadros', 'cena Manim pré-renderizada', 'sem defeito medido', '—', _G, 'comp/ciencia.js; src/v2/manim_cenas.py', 'regressão visual (pula sem Manim)', '—', 'animação', 'quadros', '—',
       'Manim precisa de pango/cairo (apt)', '—', 'aprovado tecnicamente'),
]


def resumo() -> dict:
    est = {}
    for a in AUDITORIA:
        est[a['estado']] = est.get(a['estado'], 0) + 1
    return {'composicoes': len(AUDITORIA), 'estados': est}


def markdown() -> str:
    linhas = ['| composição | problema na V2 | correção V2.1 | teste | limitações | estado |', '|---|---|---|---|---|---|']
    for a in AUDITORIA:
        linhas.append(f"| `{a['id']}` | {a['problema_v2']} | {a['correcao_v21']} | {a['teste']} | {a['limitacoes']} | **{a['estado']}** |")
    detalhe = []
    for a in AUDITORIA:
        detalhe.append(f"\n### `{a['id']}` — {a['estado']}\n")
        for c in CAMPOS[1:]:
            detalhe.append(f"- **{c.replace('_', ' ')}**: {a[c]}")
    return '\n'.join(linhas) + '\n' + '\n'.join(detalhe)
