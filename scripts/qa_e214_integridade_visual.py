"""Pixel QA for the E213 common bridge, not an aesthetic certification.
Compare actual output to the exact registered original around the intended local frame.
No crop/stretch or overlays are allowed over the animation's main content.
"""
import json
import subprocess
from pathlib import Path
import numpy as np
from src.v4.formatos.ponte_animacao_editorial import sha

def frames(path):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vf','scale=135:240',
        '-pix_fmt','rgb24','-f','rawvideo','-'])
    return np.frombuffer(raw,np.uint8).reshape(-1,240,135,3).astype(np.int16)

def compare(output,props_path,public_root):
    p=json.loads(Path(props_path).read_text())
    rendered=frames(output)
    if len(rendered)!=round(p['duracao']*30):
        raise ValueError('E214-QUADROS')
    report=[]
    for s in p['shots']:
        if s['type']!='animation_clip':continue
        proof=s['animation_proof']
        source=Path(public_root)/s['asset']
        if sha(source)!=proof['sha256']:raise ValueError('E214-HASH')
        original=frames(source)
        if len(original)!=proof['frames']:raise ValueError('E214-ORIGINAL')
        start=round(s['start']*30)
        # Main image incl. edges; exclude only bottom global progress/footer.
        # Search +/- 2 source frames to account for 24->30 sample cadence.
        rows=[]
        for i in np.linspace(0,len(original)-1,11).round().astype(int):
            t=i/proof['fps']
            j=min(round((s['end']-s['start'])*30)-1,round(t*30))
            actual=rendered[start+j,:220,:,:]
            lo,hi=max(0,i-2),min(len(original),i+3)
            delta=[float(np.abs(actual-original[k,:220,:,:]).mean()) for k in range(lo,hi)]
            rows.append({'source_frame':int(i),'output_frame':int(start+j),'rgb_mae':min(delta)})
        # generous codec tolerance, not a similarity gate for machine identity.
        if max(r['rgb_mae'] for r in rows)>8.0:
            raise ValueError('E214-PIXEL-REGRESSION '+json.dumps(rows))
        report.append({'id':s['id'],'sha256':proof['sha256'],'amostras':rows,'visual_homologado':False})
    if not report:raise ValueError('E214-SEM-ANIMACAO')
    return report

def main():
    root=Path('qa_e213')
    for tema in ('panama','compressor'):
        report=compare(root/(tema+'.mp4'),root/(tema+'.json'),Path('motor4/remotion/public'))
        (root/(tema+'-comparacao.json')).write_text(json.dumps(report,indent=2))
        print('E214-COMPARACAO',tema,report)

if __name__=='__main__':main()
