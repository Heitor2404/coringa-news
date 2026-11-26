from src.v4.formatos import replanejamento_e308 as R,reserva_janelas_e313 as J,revisao_documental as V

def need():
    return {'id':'a','fatos':['f1'],'mostrar':'ação específica observável','sujeito':'objeto',
            'necessidade':'registro','evidencia_visual':'movimento','pesquisa':{'consultas_en':['object moving']}}
def task():
    return {'necessidade_id':'a','fatos':['f1'],'mostrar':need()['mostrar'],'motivo':'REVISAR_ACAO_ESPECIFICA','evidencia_visual':'movimento'}
def test_repair_preserves_obligation_and_other_coverage():
    for accept in (True,False):
        old={'necessidade_id':'a','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','old']}
        other={'necessidade_id':'b','estado':'CANDIDATO_PRIVADO_REVISADO'}
        report={'triagem':[need()],'cobertura':[old,other]}
        def prepare(r):
            new=r['cobertura'][0].get('selecionado')==['commons','new']
            if new and accept:return {'a':{'kind':'video'},'b':{'kind':'photo'}},{'capacidade_s':7.6,'pronto_para_tts':True}
            if new:return {'a':{'kind':'video'}},{'capacidade_s':3.8,'pronto_para_tts':False}
            return {'b':{'kind':'photo'}},{'capacidade_s':3.8,'pronto_para_tts':False,'replanejamento_por_fato':[task()]}
        finalized=[]
        def alternative(n):
            assert n==need()
            return {'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','new']}
        logs=R.reparar_acoes(report,prepare,alternative,finalized.append)
        assert finalized==[accept] and logs[0]['cobertura_recusada']==old
        assert report['cobertura'][1] is other
        assert report['cobertura'][0]['selecionado'][1]==('new' if accept else 'old')
        assert not logs[0]['aprovacao_editorial']

def test_motion_need_without_preference_uses_existing_budget_and_never_calls_without_balance():
    def forbidden(*a):raise AssertionError('unexpected call')
    row=R.fila_alternativa(need(),{'pendentes':[{'fonte':'commons','source_id':'v','tipo':'video'}]},forbidden,forbidden,
        pode_buscar=lambda:False,pode_inspecionar=lambda:False,pode_reusar=lambda c:False)
    assert row['estado']=='LACUNA_PENDENTE' and row['tentativas']==0

def test_release_only_own_reservation_preserve_shared_source():
    reservations={'a':{'pagina':'p','sha256':'h'},'b':{'pagina':'p','sha256':'h'},'c':{'pagina':'q','sha256':'i'}}
    pages={'p','q','static'};hashes={'h','i','static'}
    J.liberar_reserva_individual('a',reservations,pages,hashes)
    assert set(reservations)=={'b','c'} and pages=={'p','q','static'} and hashes=={'h','i','static'}
    J.liberar_reserva_individual('b',reservations,pages,hashes)
    assert pages=={'q','static'} and hashes=={'i','static'}

def test_diagnostic_partial_action_is_not_provider_failure_or_absence():
    r=V.diagnostico_cobertura([{'cobertura':{'trilha':[{'decisao':{'estado':'INSUFICIENTE','motivo':'REVISAR_ACAO_ESPECIFICA'}}]}}],'ORCAMENTO')
    assert r['decisoes_por_tipo']=={'ACAO_ESPECIFICA_NAO_DEMONSTRADA':1}
    assert not r['inexistencia_de_midia_comprovada']

def test_failed_alternative_preserves_rejected_receipt_and_rolls_back():
    old={'necessidade_id':'a','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','old']}
    report={'triagem':[need()],'cobertura':[old]}
    def fail(n):raise RuntimeError('offline')
    final=[]
    logs=R.reparar_acoes(report,lambda r:({}, {'replanejamento_por_fato':[task()],'capacidade_s':0,'pronto_para_tts':False}),fail,final.append)
    assert final==[False] and report['cobertura']==[old] and logs[0]['estado']=='FALHA_RECUPERACAO_ACAO'


def test_static_acquisition_without_chapters_does_not_invoke_film_bridge():
    n={**need(),'evidencia_visual':'estatica'}
    old={'necessidade_id':'a','estado':'CANDIDATO_PRIVADO_REVISADO'}
    report={'case':{'necessidades':[n]},'triagem':[n],'cobertura':[old]}
    def forbidden(*args):raise AssertionError('static acquisition cannot invoke action repair')
    assert R.reparar_acoes(report,forbidden,forbidden,forbidden)==[]
    assert report['cobertura'][0] is old
