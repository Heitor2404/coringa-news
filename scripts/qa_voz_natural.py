"""Voz de ensaio em tempo natural → plano com duração REAL → áudio final por cena.

Diferente da versão anterior NÃO usa atempo nem velocidade +10%.
Preparar ANTES de renderizar: as durações do vídeo respeitam o áudio.
Bloqueia frase longa que excederia o máximo seguro para foto, sem contornar fiscal.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path

from src.v4.formatos.tempo_natural import retemporizar
from scripts.qa_narracao_multitema import sonda, unir

VOZ='pt-BR-AntonioNeural'
RATE='+0%'


async def _gerar(texto: str, destino: Path):
    import edge_tts
    falhas=[]
    for _ in range(2):
        try:
            await edge_tts.Communicate(texto,VOZ,rate=RATE).save(str(destino))
            if destino.stat().st_size<2000:
                raise RuntimeError('arquivo de voz vazio')
            return
        except Exception as e:
            falhas.append(f'{type(e).__name__}: {str(e)[:90]}')
            await asyncio.sleep(2)
    raise RuntimeError('voz de teste indisponível: '+'; '.join(falhas))


def gerar(plano:dict, saida:Path) -> dict:
    textos=(plano.get('auditoria_privada') or {}).get('roteiro_por_cena') or []
    shots=plano.get('shots') or []
    if not shots or len(textos)!=len(shots):
        raise ValueError('deve existir uma fala por cena')
    saida=Path(saida);saida.mkdir(parents=True,exist_ok=True)
    fontes=[];durs=[]
    for i,texto in enumerate(textos):
        if not isinstance(texto,str) or not (6<=len(texto)<=220):
            raise ValueError('fala de teste vazia ou excessiva')
        raw=saida/f'fala_{i+1:02d}.mp3'
        asyncio.run(_gerar(texto,raw))
        dur=sonda(raw)
        fontes.append(raw)
        durs.append(dur)
    # Se a divisão narrativa não couber, interromper AGORA, sem render nem aceleração.
    plano_sync=retemporizar(plano,durs)
    from src.v4.formatos.filme_editorial import avaliar
    qa=avaliar(plano_sync)
    (saida/'preflight_voz_natural.json').write_text(
        json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    if not qa['pronto']:
        raise ValueError('roteiro com voz natural precisa de progressão visual: '+
                         json.dumps(qa['bloqueios'][:6],ensure_ascii=False))
    (saida/'plano_sincronizado.json').write_text(
        json.dumps(plano_sync,ensure_ascii=False,indent=2),encoding='utf-8')
    wavs=[]
    for i,(s,raw) in enumerate(zip(plano_sync['shots'],fontes)):
        dur=float(s['end'])-float(s['start'])
        wav=saida/f'fala_{i+1:02d}.wav'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
            '-i',str(raw),
            '-af',f'aresample=48000,aformat=channel_layouts=mono,apad,atrim=0:{dur:.3f}',
            '-ar','48000','-ac','1','-c:a','pcm_s16le',str(wav)],
            check=True,timeout=45)
        wavs.append(wav)
    args=['ffmpeg','-hide_banner','-loglevel','error','-y']
    for p in wavs:
        args += ['-i',str(p)]
    filt=''.join(f'[{i}:a]asetpts=PTS-STARTPTS[a{i}];' for i in range(len(wavs)))
    filt+=''.join(f'[a{i}]' for i in range(len(wavs)))
    filt+=f'concat=n={len(wavs)}:v=0:a=1[out]'
    final=saida/'narracao.wav'
    subprocess.run(args+['-filter_complex',filt,'-map','[out]','-ar','48000',
                         '-ac','1','-c:a','pcm_s16le',str(final)],check=True,timeout=60)
    if abs(sonda(final)-plano_sync['duracao'])>.12:
        raise RuntimeError('áudio total não corresponde ao tempo dos planos')
    r={'voz_de_teste':VOZ,'rate':RATE,'tempo_audio':1.0,
       'duracoes_naturais':[round(x,3) for x in durs],
       'duracoes_de_cena':[round(x['end']-x['start'],3) for x in plano_sync['shots']],
       'duracao_total':plano_sync['duracao'],
       'sem_atempo':True,'aprovacao_humana':'PENDENTE'}
    (saida/'narracao_qa.json').write_text(
        json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return r


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('plano',type=Path)
    ap.add_argument('saida',type=Path)
    args=ap.parse_args(argv)
    p=json.loads(args.plano.read_text(encoding='utf-8'))
    print(json.dumps(gerar(p,args.saida),ensure_ascii=False))


if __name__=='__main__':
    main()
