"""Relógio da execução: o GitHub corta o trabalho em 120 min. Com isso o sistema sabe quanto tempo sobra e
pula as etapas opcionais (2ª versão do roteiro, revisões extras, fiscais) quando o tempo aperta — melhor entregar
um vídeo muito bom do que perder tudo no limite."""
import os, time

INICIO = time.time()
LIMITE = float(os.getenv('TEMPO_MAX_MIN') or 105)      # minutos úteis (o job tem 120; ~10 vão na instalação)


def passou() -> float:
    return (time.time() - INICIO) / 60


def sobra() -> float:
    return LIMITE - passou()


def marca(etapa: str):
    print(f'  [tempo] {etapa}: {passou():.0f} min (sobram {sobra():.0f})')


def vigia():
    """Trava de segurança: se a execução passar do limite + 8 min (algo travou), encerra na hora para não queimar
    minutos do GitHub (o GitHub só cortaria muito depois)."""
    import os, sys, threading

    def matar():
        print(f'\n  [tempo] passou de {LIMITE + 8:.0f} min: algo travou. Encerrando para não gastar minutos à toa.', flush=True)
        sys.stdout.flush()
        os._exit(3)
    t = threading.Timer((LIMITE + 8) * 60, matar)
    t.daemon = True
    t.start()
