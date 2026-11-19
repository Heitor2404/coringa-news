"""Revisor do FILME EDITORIAL utilizando a MESMA rubrica do ATLAS.

Duas imagens reais por etapa de mudança visual; não infere movimento de um
frame isolado nem aceita título na tela como demonstração. Falha fechada sem
modelo de visão. Chamada explícita; não é uma etapa que gaste IA escondida.
Não aprova publicação, só registra inconsistências e diagnóstico.
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
from pathlib import Path

from PIL import Image
from src.v4.formatos import contrato_visual_comum as comum
from src.v4.formatos.revisao_visual import _tirinha


def janelas(plano: dict) -> list[dict]:
    """Planilha de instantes com cobertura de TODAS as ações prometidas."""
    resultado = []
    for shot in plano.get('shots') or []:
        start, end = float(shot['start']), float(shot['end'])
        dur = end - start
        cues = shot.get('cues') or []
        expected = shot.get('estados_esperados') or []
        if expected:
            for i, action in enumerate(expected):
                cue = cues[i]
                t0 = start + float(cue['at'])
                t1 = start + float(cues[i+1]['at']) if i+1 < len(cues) else end
                # Um quadro no início e outro após o processo ter tempo de ocorrer.
                left = min(end-.1, t0 + .12)
                right = min(end-.09, t0 + max(.35, (t1-t0)*.78))
                resultado.append({'id': shot['id'], 'etapa': action,
                                  't0': round(left,3), 't1': round(right,3),
                                  'descricao': cue['label']})
        else:
            resultado.append({'id': shot['id'], 'etapa': None,
                              't0': round(start+min(.25,dur*.18),3),
                              't1': round(end-min(.15,dur*.14),3),
                              'descricao': shot.get('headline') or ''})
    return resultado


def _quadro(mp4: Path, instante: float, destino: Path) -> Path:
    destino.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{instante:.3f}',
        '-i',str(mp4),'-frames:v','1',str(destino),
    ],check=True,timeout=40)
    with Image.open(destino) as im:
        if min(im.size) < 320:
            raise ValueError('frame extraído pequeno demais')
        im.verify()
    return destino


def _prompt(contrato: dict, etapa: dict) -> str:
    verbo=contrato['verbo']
    return (
        'Você é CRÍTICO INDEPENDENTE, não o diretor nem o autor do vídeo. '
        'Veja a dupla de frames em ordem temporal. NÃO presuma movimento sem evidência visual. '
        'Não aceite texto escrito na tela como prova da ação. '
        f'Intenção: {verbo}; referente: {contrato["referente"]}; '
        f'pergunta: {contrato["pergunta"]}; aprendizado prometido: {contrato["aprendizado"]}. '
        f'Etapa que precisa SER VISÍVEL: {etapa["etapa"] or "(cena)"} — {etapa["descricao"]}. '
        'Avalie se é o mesmo objeto real/documental esperado e se a relação ou '
        'transformação é observável nos pixels, não só na legenda. '
        'Dois frames não provam a cronologia contínua de uma animação; '
        'se for inconclusivo, responda false, não preencha pela imaginação. '
        'Responda apenas JSON de booleanos referente_visivel, aprendizado_demonstrado, '
        'enquadramento_adequado, imagem_celular_legivel, mapa_informativo, '
        'acao_ou_relacao_visivel e problemas: array de strings.'
    )


def revisar(plano: dict, mp4: Path, saida: Path, chamar_visao=None) -> dict:
    """Requer MP4 efetivamente existente; API de visão injetada ou explicitamente selecionada."""
    if plano.get('formato') != 'filme_editorial':
        raise ValueError('este revisor recebe somente o compositor FilmeEditorial')
    from src.v4.formatos.filme_editorial import avaliar as preflight
    validacao=preflight(plano)
    if not validacao['pronto']:
        raise ValueError('plano bloqueado no preflight: '+json.dumps(validacao['bloqueios'],ensure_ascii=False)[:1000])
    mp4,saida=Path(mp4),Path(saida)
    if not mp4.is_file() or mp4.stat().st_size < 10000:
        raise ValueError('MP4 real ausente: não criar resultado de revisão sem vídeo')
    if chamar_visao is None:
        from src import gemini
        chamar_visao=lambda prompt,imagens: gemini.json_visao(prompt,imagens,leve=False)
    saida.mkdir(parents=True,exist_ok=True)
    contratos={x['id']:x for x in comum.extrair(plano)}
    resultados, julgamentos={}, {}
    for i,janela in enumerate(janelas(plano)):
        chave=janela['id']
        contrato=contratos[chave]
        reg={'id':chave,'etapa':janela['etapa'],'tempos':[janela['t0'],janela['t1']]}
        try:
            arqs=[_quadro(mp4,janela[t],saida/'frames_revisao'/f'{i:03d}_{n}.png')
                  for n,t in enumerate(('t0','t1'))]
            imagens=[_tirinha(arqs)]
            resposta=chamar_visao(_prompt(contrato,janela),imagens)
            reg['problemas']=comum.julgar_inspecao(contrato['verbo'],contrato['mapa'],resposta)
            reg['veredito']=resposta if isinstance(resposta,dict) else None
        except Exception as exc:
            reg['problemas']=['SEM-REVISAO: '+type(exc).__name__+': '+str(exc)[:200]]
        resultados.setdefault(chave,[]).append(reg)
    # Uma etapa negativa torna o compromisso inteiro reprovado.
    for chave,lista in resultados.items():
        demands=comum.criterios(contratos[chave]['verbo'],contratos[chave]['mapa'])
        julgamentos[chave]={k:bool(lista) and all(
            (x.get('veredito') or {}).get(k) is True and not x['problemas'] for x in lista)
            for k in demands}
    rel=comum.auditar(plano,julgamentos)
    falhas_de_etapas=[x for lista in resultados.values() for x in lista if x['problemas']]
    rel['etapas']=resultados
    rel['revisao_semantica_sem_bloqueio']=not falhas_de_etapas and rel['estrutura_declarada_ok']
    rel['pronto_para_aprovacao_humana']=rel['revisao_semantica_sem_bloqueio'] and (
        rel['inspecoes_com_veredito']==rel['total_compromissos'])
    rel['publicavel']=False
    (saida/'revisao_filme_editorial.json').write_text(
        json.dumps(rel,ensure_ascii=False,indent=2),encoding='utf-8')
    return rel


def main(argv=None) -> int:
    p=argparse.ArgumentParser()
    p.add_argument('plano',type=Path)
    p.add_argument('mp4',type=Path)
    p.add_argument('saida',type=Path)
    a=p.parse_args(argv)
    rel=revisar(json.loads(a.plano.read_text(encoding='utf-8')),a.mp4,a.saida)
    print(json.dumps({'pronto_para_aprovacao_humana':rel['pronto_para_aprovacao_humana'],
                      'aprovacao_humana':rel['aprovacao_humana'],'falhas':rel['falhas'][:8]},
                     ensure_ascii=False))
    return 0 if rel['pronto_para_aprovacao_humana'] else 1


if __name__=='__main__':
    raise SystemExit(main())
