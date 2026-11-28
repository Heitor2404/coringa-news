from scripts.qa_ui_e299 import diagnosticar

def test_private_editorial_risks_are_not_certification():
    r=diagnosticar()
    assert len(r['checks'])==12
    assert r['actual_app_ui_verified'] is False and r['publish'] is False
    assert r['status']=='PRIVATE_UI_RISK'
    assert all(not c['fits_configured_profile'] for c in r['checks'] if c['role'] in ('subtitle','source'))
    assert all(c['fits_configured_profile'] for c in r['checks'] if c['role'] in ('brand','section'))
