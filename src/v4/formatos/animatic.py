"""ATLAS — animatic visual no renderizador REAL, SEM pagar/gerar voz nem MP4 final.

Reaproveita exatamente o compositor de quadros Remotion e a biblioteca atual.
A ordem dos beats e o estilo são fiéis; os tempos de fala são PROVISÓRIOS
e serão resolvidos novamente pelo áudio real depois.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from src.v4.formatos import plano as P, produzir, triagem_editorial


def palavras_provisorias(texto: str, palavras_por_s: float = 2.7) -> dict:
    if not 1.5 <= palavras_por_s <= 4:
        raise ValueError('cadência provisória fora dos limites')
    words = re.findall(r'\S+', texto)
    if not words:
        raise ValueError('narração vazia')
    dur = round(len(words) / palavras_por_s + .6, 3)
    pal = [{'w': w, 's': round(i / palavras_por_s, 3),
            'e': round((i + 1) / palavras_por_s, 3)}
           for i, w in enumerate(words)]
    return {'palavras': pal, 'duracao': dur, 'origem': 'SIMULACAO_VISUAL_SEM_VOZ',
            'aviso': 'tempos de narração provisórios; não mede legenda real nem áudio'}


def preparar(pl: dict, saida: Path, catalogo: dict | None = None, recolher=True) -> dict:
    if catalogo is None:
        from src.v4.formatos import ponte_biblioteca
        catalogo = ponte_biblioteca.catalogo()
    tri = triagem_editorial.avaliar(pl, catalogo)
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'triagem_editorial.json').write_text(json.dumps(tri, ensure_ascii=False, indent=2), encoding='utf-8')
    if not tri['pronto']:
        return {'pronto': False, 'etapa': 'triagem', 'bloqueios': tri['bloqueios']}
    meta = palavras_provisorias(pl['narracao']['texto'])
    resolvido = P.resolver_tempos(pl, meta['palavras'], duracao_audio=meta['duracao'])
    erros = [x for x in P.validar(resolvido) if x['gravidade'] == 'erro']
    if erros:
        return {'pronto': False, 'etapa': 'plano', 'bloqueios': erros}
    (saida / 'narracao.json').write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
    (saida / 'plano_resolvido.json').write_text(json.dumps(resolvido, ensure_ascii=False), encoding='utf-8')
    if recolher:
        produzir.ativos(resolvido, saida)
    return {'pronto': True, 'etapa': 'pronto_para_quadros',
            'duracao_provisoria': meta['duracao'], 'bloqueios': []}


def executar(arq: Path, saida: Path):
    plano = json.loads(Path(arq).read_text(encoding='utf-8'))
    r = preparar(plano, saida)
    (saida / 'animatic.json').write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
    if not r['pronto']:
        return r
    cmd = [sys.executable, '-m', 'src.v4.formatos', 'quadros', str(arq), str(saida)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode:
        r = {'pronto': False, 'etapa': 'quadros',
             'bloqueios': [(proc.stdout + proc.stderr)[-1500:]]}
    else:
        r['etapa'] = 'quadros_reais_sem_tts'
    (saida / 'animatic.json').write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
    return r


def main(argv=None):
    args = argv or sys.argv[1:]
    if len(args) != 2:
        print('uso: python -m src.v4.formatos.animatic PLANO destino', file=sys.stderr)
        return 2
    r = executar(Path(args[0]), Path(args[1]))
    print(json.dumps(r, ensure_ascii=False)[:6000])
    return 0 if r['pronto'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
