"""Pilot visual reconstruction: verified evidence, deliberate shots, no global maps.

Temporary human-auditable animatic, NOT a new fixed pattern for future topics.
Only reuses old verified factual narration and the licensed media from scouting.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.v4.formatos import triagem_editorial

ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / 'src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json'


def montar(catalogo: dict, original: dict | None = None) -> dict:
    old = original or json.loads(ORIGINAL.read_text(encoding='utf-8'))
    aprovados = {
        q['id']: q['asset'] for q in catalogo.get('relatorio') or []
        if q.get('estado') == 'CANDIDATO_VERIFICADO' and q.get('asset')
    }
    # Ser honesto com a prova: macro e wafer são imagens ilustrativas, NÃO
    # filmagens das instalações da TSMC nem da máquina ASML.
    exigidos = ('chip-macro', 'wafer-visivel')
    if any(x not in aprovados for x in exigidos):
        raise ValueError('SEM_PROVA: falta mídia real do chip ou wafer')
    foto = old['beats'][0]['camadas'][0]
    fab = {
        'id': 'fabrica-real',
        'componente': 'atlas.provaVisual', 'slot': 'prova', 't0': 0,
        't1': '@max(2.5,@por-0.12)', 'p': {
            **foto['p'], 'rotulo': 'TSMC FAB 18', 'rotulo2': 'FÁBRICA REAL · TAIWAN',
            'enquadramento': 'cobrir', 'foco': '50% 50%'}}
    wafer = {
        'id': 'wafer-real', 'componente': 'atlas.provaVisual', 'slot': 'prova',
        't0': '@observe-0.12', 't1': '@mas-0.9',
        'p': {'asset': aprovados['wafer-visivel'],
              'meta': 'Wikimedia Commons · licença conforme catálogo privado',
              'rotulo': 'WAFER REAL · FOTO ILUSTRATIVA',
              'rotulo_t': '@wafer', 'rotulo2': 'CIRCUITOS NO SILÍCIO',
              'rotulo2_t': '@formam', 'enquadramento': 'cobrir'}}
    chip = {
        'id': 'chip-real', 'componente': 'atlas.provaVisual', 'slot': 'prova',
        't0': '@2:se-0.12', 't1': '@fim',
        'p': {'asset': aprovados['chip-macro'],
              'meta': 'Wikimedia Commons · licença conforme catálogo privado',
              'rotulo': 'MICROCHIP REAL · FOTO ILUSTRATIVA',
              'rotulo_t': '@consequência', 'enquadramento': 'cobrir'}}
    def beat(bid,comp,t,verb,question,ref,learning,provas,fatos,camadas,**extra):
        return {'id': bid,'composicao':comp,'t':t,'movimento':'fixo',
                'fatos':fatos,'camadas':camadas,'direcao_visual':{
                    'verbo':verb,'pergunta':question,'referente':ref,
                    'aprendizado':learning,'provas':provas},**extra}
    b1 = beat('nova-01-fab18','atlas.prova',0,'MOSTRAR',
              'Qual é a fábrica real citada na abertura?',
              'Exterior da instalação TSMC Fab 18, fotografada em Taiwan',
              'A indústria dos chips tem fábricas físicas identificadas e reais',
              ['fabrica-real'],['f-fab18'],[fab])
    title={
        'id':'pergunta-regional','componente':'editorial.titleOrPayoff','slot':'pergunta',
        't0':'@max(2.5,@por)','t1':'@observe-0.12','entrada_apos_voo':True,
        'p':{'linhas':[{'texto':'POR QUE','t':'@max(2.5,@por)'},
                       {'texto':'TAIWAN?','t':'@importa','destaque':True}]}}
    b2=beat('nova-02-local-taiwan','atlas.abertura','@max(2.5,@por-0.12)','LOCALIZAR',
            'Onde fica Taiwan em relação à região asiática?',
            'Ilha de Taiwan e sua posição geográfica na Ásia Oriental',
            'Taiwan está localizada com destaque geográfico regional legível',
            ['mapa'],['f-fab18'],[title],roi=[116.3,20.4,125.0,27.2],movimento='aproxima')
    b3=beat('nova-03-wafer-real','atlas.prova','@observe-0.12','MOSTRAR',
            'O que exatamente é o wafer real mencionado na narração?',
            'Wafer físico de silício com circuitos integrados observáveis',
            'Os circuitos são formados sobre wafers de silício reais',
            ['wafer-real'],['f-wafer'],[wafer])
    flow={'id':'cadeia-industrial','componente':'editorial.flowConnections','slot':'corpo',
          't0':'@mas-0.9','t1':'@2:se-0.12',
          'p':{'fluxo':True,'nos':[
              {'rotulo':'PROJETOS','sub':'EMPRESAS AMERICANAS','t':'@mas-0.12'},
              {'rotulo':'EQUIPAMENTOS','sub':'FORNECEDORES EUROPEUS','t':'@cadeia'},
              {'rotulo':'FABRICAÇÃO','sub':'FÁBRICAS EM TAIWAN','t':'@europeus','destaque':True}]}}
    b4=beat('nova-04-cadeia-causal','atlas.tecnica','@mas-0.9','CONECTAR',
            'Como diferentes etapas da indústria dependem umas das outras?',
            'Três etapas reais da cadeia: projeto, equipamento e fabricação',
            'Fabricar chips integra projeto nos Estados Unidos, equipamentos europeus e fábricas em Taiwan',
            ['cadeia-industrial'],['f-cadeia'],[flow],funcao='estrutura')
    b5=beat('nova-05-chip-real','atlas.prova','@2:se-0.12','MOSTRAR',
            'Qual é o objeto real produzido por essa cadeia industrial?',
            'Microchip real fotografado em macro com ligações e circuitos visíveis',
            'O produto final físico depende de uma rede internacional de etapas',
            ['chip-real'],['f-cadeia'],[chip])
    new = {**old, 'video_id':'atlas-chips-evidencias-v3-privado',
           'titulo':'Por que Taiwan é importante para os chips? (reconstrução visual)',
           'beats':[b1,b2,b3,b4,b5]}
    new['destaques']=[{'fonte':'paises','nome':'Taiwan','cor':'destaque',
                       't0':'@max(3.5,@por+0.4)','t1':'@observe-0.62'}]
    new['rasters']=[{'nome':'ne2_asia_leste','de':0}]
    new['clipes']=[]
    new['rotas']=[]
    new['rotulos']=[]
    return new


def main(argv=None):
    import sys
    args=argv if argv is not None else sys.argv[1:]
    if len(args)!=2:
        print('uso: python -m src.v4.formatos.roteiro_visual_curado catalogo.json plano.json',file=sys.stderr)
        return 2
    cat=json.loads(Path(args[0]).read_text(encoding='utf-8'))
    p=montar(cat)
    from src.v4.formatos import ponte_biblioteca
    rep=triagem_editorial.avaliar(p, ponte_biblioteca.catalogo())
    if not rep['pronto']:
        print(json.dumps(rep,ensure_ascii=False))
        return 1
    Path(args[1]).parent.mkdir(parents=True,exist_ok=True)
    Path(args[1]).write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('STORYBOARD_CANDIDATO',args[1])
    return 0

if __name__=='__main__':
    raise SystemExit(main())
