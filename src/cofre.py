"""Textos privados (prompts) ficam no repositório privado coringa-cofre.

O workflow baixa o cofre para a pasta cofre/ (ou COFRE_DIR). Sem o cofre, o sistema
continua importando, mas os prompts viram um aviso e a IA não terá as regras do canal.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = Path(os.environ.get('COFRE_DIR') or RAIZ / 'cofre')


def disponivel() -> bool:
    return (PASTA / 'prompts').is_dir()


def prompt(nome: str) -> str:
    arq = PASTA / 'prompts' / f'{nome}.txt'
    if arq.exists():
        return arq.read_text(encoding='utf-8')
    return f'[{nome}: texto guardado no cofre privado]'
