"""Compara o replay sem IA do código do Work (257ce75d) com o desta branch: mesmas revisões reaproveitadas."""
import sys
from scripts import contrato_reuso_replay as C

a, b = C.extrair(sys.argv[1]), C.extrair(sys.argv[2])
print('WORK', a['reusos_analises'], a['estados'], len(a['reusos_ids_unicos']))
print('CLAUDE', b['reusos_analises'], b['estados'], len(b['reusos_ids_unicos']))
campos = ('reusos_ids_unicos', 'reusos_analises', 'estados', 'selecionados')
dif = [k for k in campos if a[k] != b[k]]
print('DIFERENCAS', dif)
raise SystemExit(1 if dif else 0)
