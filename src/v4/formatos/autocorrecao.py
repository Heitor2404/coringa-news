"""ATLAS: UMA autocorreção de storyboard guiada pelo crítico visual real.

Não se autoaprova, não muda regras globais nem altera repo em GitHub.
Usa a MESMA fala e apenas materiais com proveniência comprovada.
As evidências são re-renderizadas e REJULGADAS; sem nova aprovação bloqueia.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from src.v4.formatos import triagem_editorial


def preparar_candidato(original: dict, critico: dict, chamar, catalogo: dict) -> tuple[dict | None, dict]:
    """Devolve plano e diagnóstico de uma tentativa; sem autorização para inventar mídia."""
    bloqueios = critico.get('bloqueios') or []
    registro = {'origem': 'revisao_visual', 'limite_tentativas': 1, 'defeitos': bloqueios}
    if critico.get('pronto'):
        return copy.deepcopy(original), {**registro, 'decisao': 'sem_correcao_necessaria'}
    if not bloqueios:
        return None, {**registro, 'decisao': 'bloqueado', 'motivo': 'crítico sem resultado verificável'}
    if any(any(str(p).startswith(('SEM-REVISAO', 'SEM-FRAME')) for p in b.get('problemas') or [])
           for b in bloqueios):
        return None, {**registro, 'decisao': 'bloqueado',
                      'motivo': 'modelo de visão indisponível ou evento não inspecionável; não consertar às cegas'}
    # Rastreia candidatos apenas do catálogo comprovado. "Reenquadrar" só é viável
    # se os pixels originais permitem; caso contrário deve escolher OUTRA mídia.
    midias = [
        {k: it.get(k) for k in ('id', 'mostra', 'licenca', 'autor', 'natureza', 'wh')}
        for it in catalogo.get('itens') or []
        if it.get('sha256_origem') and (it.get('prova') or {}).get('midia_corresponde') is True
    ]
    msg = (
        'Você é o DIRETOR DE CORREÇÃO do ATLAS, NÃO o crítico da própria edição. '
        'Há uma prévia REAL cuja leitura visual falhou. Corrija SOMENTE cenas de evidência ruim. '
        'Use composição adequada, realce o objeto, retire mapa decorativo e mostre relação física, '
        'sem inventar material, máquina, vídeo, foto, licença, números ou fontes. '
        'Preserve EXATAMENTE narracao.texto, narracao.fatos, video_id, formato, canal, duração e conteúdo factual. '
        'Não altere cor, fonte, zoom máximo e presets globais. '
        'Cada beat deve conter direcao_visual {verbo, pergunta, referente, aprendizado, provas:[IDs reais]}. '
        'Falas de ação exigem demonstração; título/card/etiqueta de país NÃO são evidência. '
        'Mapa continental grande sem evento geográfico não é permitido. '
        'Não há cota de 2 fotos nem de 6 beats. '
        'Se a biblioteca não contém prova suficiente para a fala, devolva {"bloqueado":"MÍDIA INSUFICIENTE", '
        '"faltam":["objetos/mecanismos necessários"]} em vez de produzir vídeo falso. '
        'Devolva só UM objeto JSON: plano inteiro corrigido OU bloqueio explícito.\n'
        'MÍDIAS COMPROVADAS:\n' + json.dumps(midias, ensure_ascii=False)[:18000] +
        '\nREPROVAÇÃO DO CRÍTICO EM CENAS REAIS:\n' + json.dumps(bloqueios, ensure_ascii=False)[:12000] +
        '\nPLANO ORIGINAL:\n' + json.dumps(original, ensure_ascii=False)[:33000]
    )
    try:
        candidato = chamar(msg)
    except Exception as exc:
        return None, {**registro, 'decisao': 'bloqueado',
                      'motivo': f'diretor indisponível: {type(exc).__name__}: {str(exc)[:180]}'}
    if not isinstance(candidato, dict):
        return None, {**registro, 'decisao': 'bloqueado', 'motivo': 'diretor não retornou objeto JSON'}
    if candidato.get('bloqueado'):
        return None, {**registro, 'decisao': 'bloqueado', 'motivo': candidato.get('bloqueado'),
                      'faltam': candidato.get('faltam')}
    protegidos = ('video_id', 'canal', 'formato', 'duracao')
    mudados = [k for k in protegidos if candidato.get(k) != original.get(k)]
    if candidato.get('narracao') != original.get('narracao'):
        mudados.append('narracao')
    if mudados:
        return None, {**registro, 'decisao': 'bloqueado',
                      'motivo': 'correção alteraria voz/fatos/identidade sem autorização: ' + ', '.join(mudados)}
    prova = triagem_editorial.avaliar(candidato, catalogo)
    if not prova['pronto']:
        return None, {**registro, 'decisao': 'bloqueado', 'motivo': 'candidato também sem evidência',
                      'falhas_contrato': prova['bloqueios'][:20]}
    return candidato, {**registro, 'decisao': 'candidato_validado_por_contrato'}


def executar(plano_arq: Path, saida: Path, chamar=None, reavaliar=None) -> dict:
    """Replaneja (1x), refaz imagens/QA e exige novo crítico visual.

    reavaliar é injetável em testes; na execução usa mídia licenciada real,
    preflight, Playwright/Remotion e Gemini Vision.
    """
    from src.v4.formatos import ponte_biblioteca
    plano_arq, saida = Path(plano_arq), Path(saida)
    original_texto = plano_arq.read_text(encoding='utf-8')
    original = json.loads(original_texto)
    critico = json.loads((saida / 'revisao_visual.json').read_text(encoding='utf-8'))
    if critico.get('pronto') is True:
        registro = {'decisao': 'aprovado_pelo_critico_visual', 'tentativas': 0,
                    'nota': 'revisão automática não é aprovação humana'}
        (saida / 'autocorrecao.json').write_text(json.dumps(registro, ensure_ascii=False, indent=2))
        return registro
    catalogo = ponte_biblioteca.catalogo()
    if chamar is None:
        from src import gemini
        chamar = lambda prompt: gemini.json_(prompt, leve=False)
    candidato, registro = preparar_candidato(original, critico, chamar, catalogo)
    registro['tentativas'] = 0 if candidato is None else 1
    rel = saida / 'autocorrecao.json'
    if candidato is None:
        rel.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding='utf-8')
        return registro
    if reavaliar is None:
        def reavaliar(pl):
            from src.v4.formatos import produzir, revisao_visual
            produzir.ativos(pl, saida)
            pre = produzir.preflight(pl, saida)
            if not pre['pronto']:
                raise ValueError('novo preflight reprovado: ' +
                                 '; '.join(i['item'] for i in pre['itens'] if not i['ok'])[:700])
            proc = subprocess.run([sys.executable, '-m', 'src.v4.formatos', 'quadros',
                                   str(plano_arq), str(saida)], check=False, capture_output=True, text=True)
            if proc.returncode:
                raise ValueError('novos quadros reprovados: ' + (proc.stdout + proc.stderr)[-900:])
            return revisao_visual.revisar(saida)
    try:
        plano_arq.write_text(json.dumps(candidato, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        visto = reavaliar(candidato)
        registro['novo_critico'] = {'pronto': visto.get('pronto'), 'bloqueios': visto.get('bloqueios'),
                                    'chamadas': visto.get('chamadas')}
        if visto.get('pronto'):
            registro['decisao'] = 'candidato_revalidado_visual'
        else:
            registro['decisao'] = 'bloqueado'
            registro['motivo'] = 'uma tentativa de correção não eliminou defeitos visuais'
    except Exception as exc:
        registro['decisao'] = 'bloqueado'
        registro['motivo'] = f'falha na nova validação: {type(exc).__name__}: {str(exc)[:600]}'
    finally:
        if registro['decisao'] != 'candidato_revalidado_visual':
            plano_arq.write_text(original_texto, encoding='utf-8')
        rel.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding='utf-8')
    return registro


def main(argv=None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 2:
        print('uso: python -m src.v4.formatos.autocorrecao PLANO saida', file=sys.stderr)
        return 2
    r = executar(Path(args[0]), Path(args[1]))
    print(json.dumps(r, ensure_ascii=False, indent=2)[:12000])
    return 0 if r['decisao'] in ('aprovado_pelo_critico_visual', 'candidato_revalidado_visual') else 1


if __name__ == '__main__':
    raise SystemExit(main())
