"""Resumo inequívoco das provas obrigatórias de um job: APROVADA, REPROVADA, NAO_EXECUTADA, BLOQUEADA.

O job só passa se TODAS as provas esperadas estiverem APROVADAS. Prova bloqueada por acesso ou infraestrutura não
conta como aprovação (homologação parcial explícita), e prova sem registro é NAO_EXECUTADA.
Uso: python scripts/resumo_provas.py <dir> prova1 prova2 ...
"""
import os
import sys
from pathlib import Path


def resumir(pasta, esperadas):
    linhas = {}
    for nome in esperadas:
        f = Path(pasta) / f'{nome}.tsv'
        if f.is_file():
            partes = f.read_text(encoding='utf8').strip().split('\t')
            linhas[nome] = partes[1] if len(partes) > 1 else 'REPROVADA'
        else:
            linhas[nome] = 'NAO_EXECUTADA'
    return linhas


def main(argv):
    pasta, esperadas = argv[0], argv[1:]
    if not esperadas:
        print('nenhuma prova esperada declarada'); return 2
    est = resumir(pasta, esperadas)
    tabela = ['| prova | estado |', '|---|---|'] + [f'| {k} | {v} |' for k, v in est.items()]
    homologado = all(v == 'APROVADA' for v in est.values())
    tabela.append(f'\n**Homologação: {"COMPLETA" if homologado else "INCOMPLETA"}**')
    texto = '\n'.join(tabela)
    print(texto)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf8') as fh:
            fh.write(texto + '\n')
    return 0 if homologado else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
