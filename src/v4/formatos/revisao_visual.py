"""Crítico independente ATLAS: avalia styleframes reais ANTES de renderizar MP4 caro.

Complementa (não substitui) fiscal geométrico e aprovação humana. Uma avaliação
por beat, sempre com plano de evidência; falha fechada sem VLM/cota. Não escreve
automaticamente no repositório nem rebaixa os portões para obter vídeo verde.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from PIL import Image


def _tirinha(caminhos: list[Path]) -> bytes:
    quadros = []
    for c in caminhos[:2]:
        with Image.open(c) as im:
            quadros.append(im.convert('RGB').resize((405, 720), Image.Resampling.LANCZOS))
    img = Image.new('RGB', (405 * len(quadros), 720), '#10131A')
    for i, quadro in enumerate(quadros):
        img.paste(quadro, (405 * i, 0))
    destino = io.BytesIO()
    img.save(destino, format='JPEG', quality=85, optimize=True)
    return destino.getvalue()


def _prompt(b: dict, narration: str) -> str:
    d = b.get('direcao_visual') or {}
    return (f'Você é um CRÍTICO AUDIOVISUAL INDEPENDENTE de documentários verticais, não o diretor. '
            f'As imagens são instantes da mesma cena, em ordem temporal. NÃO deduza movimento que não aparece. '
            f'Cena: {b.get("id")}; composição: {b.get("composicao")}; '
            f'verbo visual: {d.get("verbo")}; pergunta: {d.get("pergunta")}; '
            f'objeto concreto: {d.get("referente")}; aprendizado prometido: {d.get("aprendizado")}; '
            f'provas planejadas: {d.get("provas")}. Narração global para contexto: {narration[:1900]}\n'
            'Avalie somente o que VÊ: objeto principal está identificável e dominante? '
            'A imagem é útil e nítida num celular? Mapa está enquadrado para mostrar a relação '
            'ou virou apenas decoração e continente distante? O que a fala promete aparece? '
            'Uma etiqueta de país não prova uma máquina nem dependência. '
            'Não premie fotografia com hash se está escura, pequena ou com barras pretas. '
            'Se a evidência não puder ser verificada pelas imagens, responda false, não suponha. '
            'Responda apenas JSON com booleanos: '
            '{"referente_visivel":true|false,"aprendizado_demonstrado":true|false,'
            '"enquadramento_adequado":true|false,"imagem_celular_legivel":true|false,'
            '"mapa_informativo":true|false,"acao_ou_relacao_visivel":true|false,'
            '"problemas":["descrição específica do que foi VISTO"],'
            '"correcao":"ação visual concreta, sem baixar requisitos"}. '
            'mapa_informativo só é exigido quando a composição é cartográfica, '
            'acao_ou_relacao_visivel é exigido para DEMONSTRAR/CONECTAR/COMPARAR/REVELAR.')


def revisar(saida: Path, chamar_visao=None) -> dict:
    saida = Path(saida)
    pl = json.loads((saida / 'plano_resolvido.json').read_text(encoding='utf-8'))
    rel = json.loads((saida / 'quadros' / 'relatorio.json').read_text(encoding='utf-8'))
    if not rel.get('ok'):
        raise ValueError('quadros técnicos reprovados: não executar revisão semântica')
    if chamar_visao is None:
        from src import gemini
        chamar_visao = lambda prompt, ims: gemini.json_visao(prompt, ims, leve=False)
    total, blocos = 0, []
    for beat in pl.get('beats') or []:
        arquivos = [(saida / 'quadros' / q['arquivo'])
                    for q in rel.get('quadros') or [] if q.get('beat') == beat.get('id')]
        arquivos = [p for p in arquivos if p.is_file()]
        rec = {'beat': beat.get('id'), 'amostras': len(arquivos), 'problemas': []}
        verbo = (beat.get('direcao_visual') or {}).get('verbo')
        if not arquivos:
            rec['problemas'].append('SEM-FRAME: cena não inspecionável em styleframes; requer revisão do clipe real')
        elif not beat.get('direcao_visual'):
            rec['problemas'].append('SEM-CONTRATO: não há prova narrativa para comparar com as imagens')
        else:
            try:
                resultado = chamar_visao(_prompt(beat, (pl.get('narracao') or {}).get('texto', '')),
                                        [_tirinha([arquivos[0], arquivos[-1]])])
                total += 1
                if not isinstance(resultado, dict):
                    raise ValueError('modelo não retornou objeto JSON')
                rec['veredito'] = resultado
                exigidas = ['referente_visivel', 'aprendizado_demonstrado',
                            'enquadramento_adequado', 'imagem_celular_legivel']
                if beat.get('composicao') != 'atlas.prova':
                    exigidas.append('mapa_informativo')
                if verbo in ('DEMONSTRAR', 'CONECTAR', 'COMPARAR', 'REVELAR'):
                    exigidas.append('acao_ou_relacao_visivel')
                rec['problemas'] += [f'V-{chave}: modelo não confirmou' for chave in exigidas
                                    if resultado.get(chave) is not True]
                if rec['problemas']:
                    rec['problemas'] += [str(x) for x in (resultado.get('problemas') or [])[:3]]
            except Exception as ex:
                rec['problemas'].append(f'SEM-REVISAO: {type(ex).__name__}: {str(ex)[:200]}')
        blocos.append(rec)
    bloqueios = [b for b in blocos if b['problemas']]
    result = {'pronto': not bloqueios and bool(blocos), 'chamadas': total,
              'beats': blocos, 'bloqueios': bloqueios,
              'nota': 'crítico de visão independente: diagnóstico, NÃO aprovação estética humana'}
    (saida / 'revisao_visual.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main(argv=None) -> int:
    a = argv or sys.argv[1:]
    if len(a) != 1:
        print('uso: python -m src.v4.formatos.revisao_visual <saida_preflight>', file=sys.stderr)
        return 2
    r = revisar(Path(a[0]))
    print(json.dumps({'pronto': r['pronto'], 'chamadas': r['chamadas'],
                      'bloqueios': r['bloqueios']}, ensure_ascii=False))
    return 0 if r['pronto'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
