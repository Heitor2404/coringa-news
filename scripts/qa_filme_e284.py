"""QA técnico de um MP4 renderizado (não é aprovação audiovisual): dimensões, duração, áudio, tipos de cena."""
import hashlib
import json
import sys
from pathlib import Path


def main(root, props):
    root = Path(root)
    p = json.loads(Path(props).read_text()); q = json.loads((root / 'probe.json').read_text())
    v = next(s for s in q['streams'] if s['codec_type'] == 'video')
    audio = any(s['codec_type'] == 'audio' for s in q['streams'])
    dur = float(q['format']['duration'])
    assert p.get('private_review_only') and p.get('preview'), 'escopo privado'
    assert (v['width'], v['height']) == (540, 960), (v['width'], v['height'])
    assert abs(dur - p['duracao']) < .15, (dur, p['duracao'])
    narrado = bool(p.get('scene_narration_asset')) and audio
    qa = {'duration': p['duracao'], 'shots': len(p['shots']), 'types': sorted({s['type'] for s in p['shots']}),
          'sha256': hashlib.sha256((root / 'filme.mp4').read_bytes()).hexdigest(), 'audio': audio, 'narrado': narrado,
          'legendas_medidas': bool(p.get('documentary_captions')), 'origem_legendas': p.get('documentary_caption_origin'),
          'publish': False, 'visual_approval': 'PENDING', 'voice_approval': 'PENDING' if narrado else 'SEM_NARRACAO'}
    (root / 'qa.json').write_text(json.dumps(qa, indent=1))
    print('QA_FILME', json.dumps({k: qa[k] for k in ('duration', 'shots', 'types', 'audio', 'narrado')}))


if __name__ == '__main__':
    main(*sys.argv[1:3])
