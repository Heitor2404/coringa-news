"""Falha (exit 1) se a descoberta de checkpoints trouxer menos pacotes que o mínimo: prova sem coleção não é aprovada."""
import json
import sys

n = len(json.load(open(sys.argv[1]))['pacotes'])
print('PACOTES', n)
raise SystemExit(0 if n >= int(sys.argv[2]) else 1)
