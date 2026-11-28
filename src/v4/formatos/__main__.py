"""python -m src.v4.formatos {validar|narrar|ativos|preflight|quadros|render|folhas|telegram|gate} <plano.json> [saida]

Ordem no Actions: narrar → ativos → preflight → quadros (styleframes + colisões nos quadros renderizados) → render →
folhas (contato + antes/depois) → telegram. Para no primeiro vermelho. Nenhum passo repete chamada de IA.
"""
import json
import sys
from pathlib import Path


def main(a):
    from src.v4.formatos import plano as P, produzir
    cmd, arq = a[0], Path(a[1])
    pl = json.loads(arq.read_text(encoding='utf-8'))
    saida = Path(a[2]) if len(a) > 2 else Path('saida_formatos') / pl['video_id']
    if cmd == 'validar':                     # só estrutura (tempos numéricos ou âncoras ignoradas)
        try:
            r = P.validar(P.resolver_tempos(pl, []))
        except ValueError as e:
            r = [{'gravidade': 'aviso', 'regra': 'ANCORAS', 'onde': '-', 'texto': f'tempos ancorados na fala: validar após narrar ({e})'}]
        for v in r:
            print(f"[{v['gravidade']}] {v['regra']} {v['onde']}: {v['texto']}")
        sys.exit(1 if any(v['gravidade'] == 'erro' for v in r) else 0)
    if cmd == 'narrar':
        print(json.dumps({k: v for k, v in produzir.narrar(pl, saida).items() if k != 'palavras'}, ensure_ascii=False))
    elif cmd == 'ativos':
        print(json.dumps({k[:40]: v['src'] for k, v in produzir.ativos(pl, saida).items()}, ensure_ascii=False))
    elif cmd == 'preflight':
        r = produzir.preflight(pl, saida)
        for i in r['itens']:
            print(f"  [{'OK ' if i['ok'] else 'NÃO'}] {i['item']}" + (f" — {i['detalhe']}" if i['detalhe'] else ''))
        print(json.dumps({'pronto': r['pronto'], 'itens': len(r['itens']), 'falhas': sum(not i['ok'] for i in r['itens'])}))
        sys.exit(0 if r['pronto'] else 1)
    elif cmd == 'quadros':
        import importlib.util
        spec = importlib.util.spec_from_file_location('fv', Path(__file__).resolve().parents[3] / 'scripts' / 'formatos_validar.py')
        fv = importlib.util.module_from_spec(spec); spec.loader.exec_module(fv)
        r = fv.main(saida, saida / 'quadros', 'auto', int(pl.get('styleframes', 6)))
        sys.exit(0 if r['ok'] else 1)
    elif cmd == 'folhas':
        print(json.dumps(produzir.folhas(saida, pl.get('antes')), ensure_ascii=False))
        produzir.evolucao(saida, pl)
    elif cmd == 'telegram':
        print(json.dumps(produzir.telegram(saida, pl['titulo']), ensure_ascii=False, default=str))
    elif cmd == 'render':
        r = produzir.render(saida)
        print(json.dumps({k: r[k] for k in ('video_id', 'estado', 'duracao', 'audio')}, ensure_ascii=False))
    elif cmd == 'gate':
        from src.v3 import estado_final
        from src.v4.formatos import estado
        r = estado.conferir(saida)
        print('ATLAS_GATE ' + json.dumps(r, ensure_ascii=False))
        # É sucesso apenas de integridade, nunca APROVADO ou PUBLICÁVEL.
        sys.exit(0 if r['estado'] == estado_final.AGUARDANDO else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
