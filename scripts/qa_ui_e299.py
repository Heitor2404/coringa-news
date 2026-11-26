"""E299: measure proposed editorial lanes against every configured platform.
A private composition can be attractive while failing the conservative UI model.
Do not change the canonical safety contract or certify actual app pixels.
"""
import json,re,sys
from pathlib import Path
from src.v4.formatos import layout as L
from src.v4.formatos.qa_area_segura import carregar

def diagnosticar():
    code=Path('motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text()
    line=next(s for s in code.splitlines() if s.startswith('const DOC_MEDIA='))
    slots={role:list(map(int,re.search(role+r':\[([0-9,]+)\]',line).group(1).split(',')))
           for role in ('brand','section','subtitle','source')}
    profiles=L.perfis(L.CFG['ativos_seguros'])
    rows=[]
    for name,p in profiles.items():
        for role,(x,y,r,b) in slots.items():
            margins={'left':x-p['esquerda'],'top':y-p['topo'],
                     'right':L.limite_direito(y,b,[name])-r,'bottom':1920-p['base']-b}
            rows.append({'platform':name,'role':role,'rect':[x,y,r,b],'margin_px':margins,
                         'fits_configured_profile':min(margins.values())>=0})
    return {'publish':False,'actual_app_ui_verified':False,'canonical_profile':carregar()['profile'],
            'status':'PRIVATE_UI_RISK' if any(not r['fits_configured_profile'] for r in rows) else 'GEOMETRY_ONLY',
            'checks':rows}

if __name__=='__main__':
    data=diagnosticar()
    Path(sys.argv[1]).write_text(json.dumps(data,indent=2))
    print('E299_UI_DIAGNOSTIC',data['status'],flush=True)
