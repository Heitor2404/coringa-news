"""Entrega privada no Telegram de uma prova E284 já verificada (qa.json), com identificação completa.
Mesmo bot e chat autorizado de sempre; nenhum segredo ou resposta do bot no log; nunca publica."""
import json
import sys
from pathlib import Path

from src.v3 import previa_telegram as T


def main(root, commit, run, prova):
    root = Path(root)
    qa = json.loads((root / 'qa.json').read_text())
    if qa.get('publish') is not False or qa.get('visual_approval') != 'PENDING':
        raise SystemExit('E284-ESCOPO')
    prova_j = json.loads((root / 'prova.json').read_text()) if (root / 'prova.json').is_file() else {}
    r = json.loads((root / 'revisao.json').read_text())
    tema = {'acao': 'Seleção de filmagem de ação: foguete se elevando (prova curta)',
            'geleiras': 'Como as geleiras esculpem paisagens (documentário integral)'}[prova]
    legenda = (f"CORINGA EXPLICA · PROVA PRIVADA E284\n{tema}\n{qa['duration']:.1f}s · commit {commit[:8]} · run {run}\n"
               f"Tipo: {prova_j.get('tipo') or 'DOCUMENTARIO_INTEGRAL_PRIVADO'}\nModalidades: {', '.join(qa['types'])}\n"
               f"Narração: {'sim' if qa['narrado'] else 'não'} · Legendas medidas: {'sim' if qa['legendas_medidas'] else 'não'}\n"
               f"Seleção: autônoma (motor), visão nova {r['visao_chamadas_logicas']}, reusos {r['reusos_analises']}\n"
               "NÃO PUBLICADO · AGUARDANDO REVISÃO HUMANA")
    try:
        chat, _ = T.chat_autorizado()
        video = T._caber(root / 'filme.mp4')
        res = T._api('sendVideo', {'chat_id': chat, 'caption': legenda[:1000], 'supports_streaming': 'true'}, ('video', video))
        if not isinstance(res, dict) or not res.get('message_id'):
            raise RuntimeError('sem recibo')
    except Exception:
        raise SystemExit('E284-TELEGRAM: entrega não confirmada') from None
    print('TELEGRAM_ENTREGUE', prova, qa['duration'])


if __name__ == '__main__':
    main(*sys.argv[1:5])
