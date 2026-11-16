"""Coringa V3.1 — biblioteca global de mídia, receitas de direção, memória (erros e feedback) e o diretor automático
ligado ao fluxo real (MOTOR_VISUAL=v3). Ver docs/v3/ARQUITETURA_V3_1.md."""
import os


def ativo() -> bool:
    return os.getenv('MOTOR_VISUAL') == 'v3'


def motor_documental() -> bool:
    """V2 e V3 compartilham pesquisa, contratos e checkpoint; a direção/montagem é que muda."""
    return os.getenv('MOTOR_VISUAL') in ('v2', 'v3')
