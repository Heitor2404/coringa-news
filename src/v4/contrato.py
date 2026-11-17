"""Contrato canônico V4 (versão 4.0): episódio → cenas. Validação = regras de direção VERIFICÁVEIS (não prompt).

`validar(ep, acervo)` → lista de violações {cena, regra, gravidade: erro|aviso, texto}.
`impor(ep)` → corrige o que tem correção segura e registra (câmera sem motivo → fixa; transição sem motivo → corte;
efeito proibido → corte). O que não tem correção segura (mecanismo em foto parada, rota sem fonte, asset sem licença)
continua como erro e bloqueia o render daquela cena.
"""
from __future__ import annotations

import re

from src.v4.componentes import COMPONENTES, DEMONSTRAM_ACAO, MODALIDADES

VERSAO = '4.0'
CAMERAS = {'fixa', 'revelar', 'aproximar'}
TRANSICOES_OK = {'corte', 'dissolve'}
PROIBIDAS = {'whip', 'iris', 'flash', 'zoom', 'chicote', 'circulo', 'glitch', 'spin'}
ACAO = re.compile(r'\b(sobe|subir|subindo|desce|descer|enche|encher|esvazia|flui|fluir|escoa|abre|abrir|fecha|fechar|move|empurra|levanta|eleva|'
                  r'atravess|percorre|espalha|gira|cai|cair)\w*', re.I)
CAMPOS = ('id', 'ini', 'fim', 'fala', 'objetivo', 'o_que_precisa_aparecer', 'modalidade', 'componente', 'params', 'camera', 'transicao')


def _v(lst, cena, regra, grav, texto):
    lst.append({'cena': cena, 'regra': regra, 'gravidade': grav, 'texto': texto})


def validar(ep: dict, acervo: dict | None = None, geo: dict | None = None) -> list[dict]:
    acervo = acervo or {}
    out = []
    cenas = ep.get('cenas') or []
    if ep.get('versao_contrato') != VERSAO:
        _v(out, None, 'C-VERSAO', 'erro', f"versao_contrato deve ser {VERSAO}")
    if not cenas:
        _v(out, None, 'C-VAZIO', 'erro', 'episódio sem cenas')
        return out
    usos = {}
    for i, c in enumerate(cenas):
        cid = c.get('id', i)
        for k in CAMPOS:
            if k not in c:
                _v(out, cid, 'C-CAMPO', 'erro', f'campo obrigatório ausente: {k}')
        mod, comp = c.get('modalidade'), c.get('componente')
        if mod not in MODALIDADES:
            _v(out, cid, 'C-MODALIDADE', 'erro', f'modalidade inválida {mod!r}')
        elif comp not in COMPONENTES:
            _v(out, cid, 'C-COMPONENTE', 'erro', f'componente inexistente {comp!r}')
        elif mod not in COMPONENTES[comp]['modalidades']:
            _v(out, cid, 'C-COMPONENTE-MODALIDADE', 'erro', f'{comp} não serve à modalidade {mod}')
        # tempos contíguos e duração de plano
        d = (c.get('fim') or 0) - (c.get('ini') or 0)
        if d <= 0:
            _v(out, cid, 'C-TEMPO', 'erro', 'cena sem duração')
        elif d < 1.2:
            _v(out, cid, 'R-PLANO-CURTO', 'aviso', f'plano de {d:.1f}s (<1,2 s) pisca no celular')
        elif d > 9.5 and mod in ('registro_foto', 'documento', 'tipografia'):
            _v(out, cid, 'R-PLANO-LONGO-ESTATICO', 'aviso', f'{mod} parado por {d:.1f}s')
        if i and abs((cenas[i - 1].get('fim') or 0) - (c.get('ini') or 0)) > .05:
            _v(out, cid, 'C-CONTINUIDADE', 'erro', 'cena não começa onde a anterior termina')
        # CÂMERA: fixa por padrão; movimento só com motivo verificável
        cam = c.get('camera') or {}
        tipo = cam.get('tipo', 'fixa')
        if tipo not in CAMERAS:
            _v(out, cid, 'R-CAMERA-PROIBIDA', 'erro', f'câmera {tipo!r} não existe no canal (fixa|revelar|aproximar)')
        if tipo == 'revelar' and not cam.get('revela'):
            _v(out, cid, 'R-RECUO-SEM-REVELACAO', 'erro', 'revelar exige "revela": o que entra no quadro e não estava')
        if tipo in ('revelar', 'aproximar') and not (cam.get('justificativa') or '').strip():
            _v(out, cid, 'R-MOVIMENTO-SEM-MOTIVO', 'erro', 'movimento de câmera sem justificativa')
        if i == 0 and tipo == 'revelar':
            _v(out, cid, 'R-GANCHO-RECUO', 'erro', 'o gancho não pode recuar (começa cheio e encolhe)')
        # TRANSIÇÃO: corte por padrão
        tr = (c.get('transicao') or {})
        ttipo = tr.get('tipo', 'corte') if isinstance(tr, dict) else str(tr)
        if ttipo in PROIBIDAS or ttipo not in TRANSICOES_OK:
            _v(out, cid, 'R-TRANSICAO-PROIBIDA', 'erro', f'transição {ttipo!r} proibida (corte limpo; dissolve só com motivo)')
        elif ttipo == 'dissolve' and not (isinstance(tr, dict) and (tr.get('justificativa') or '').strip()):
            _v(out, cid, 'R-TRANSICAO-SEM-MOTIVO', 'erro', 'dissolve sem justificativa temporal/espacial/narrativa')
        # DEMONSTRAÇÃO: ação física narrada não pode ficar em foto parada / tipografia
        alvo = f"{c.get('fala', '')} {c.get('o_que_precisa_aparecer', '')}"
        if (c.get('acao_fisica') or ACAO.search(c.get('o_que_precisa_aparecer') or '')) and mod not in DEMONSTRAM_ACAO:
            _v(out, cid, 'R-ACAO-SEM-DEMONSTRACAO', 'erro', f'a cena precisa mostrar ação ({alvo[:70]!r}) e {mod} não demonstra movimento')
        # PROVA NARRATIVA (auditoria 16/11): ação física declara sujeito → estado inicial → ação → resultado
        if c.get('acao_fisica'):
            pv = c.get('prova') or {}
            falta = [k for k in ('sujeito', 'estado_inicial', 'acao', 'resultado') if not str(pv.get(k) or '').strip()]
            if falta:
                _v(out, cid, 'R-ACAO-SEM-PROVA', 'erro', f"cena de ação sem a cadeia visível: falta {', '.join(falta)}")
        # ACERVO: registro precisa de asset com licença e crédito do PRÓPRIO asset
        p = c.get('params') or {}
        if comp in COMPONENTES and COMPONENTES[comp]['acervo'] in ('foto', 'video'):
            a = acervo.get(p.get('asset'))
            if not a:
                _v(out, cid, 'R-ASSET-AUSENTE', 'erro', f"asset {p.get('asset')!r} não está no acervo")
            else:
                if not (a.get('credito') and a.get('licenca')):
                    _v(out, cid, 'R-ASSET-SEM-LICENCA', 'erro', f"asset {a.get('id')} sem licença/crédito")
                if COMPONENTES[comp]['acervo'] == 'video' and not a.get('video'):
                    _v(out, cid, 'R-ASSET-NAO-E-VIDEO', 'erro', f"{a.get('id')} não é vídeo")
                usos.setdefault(a.get('id'), []).append(i)
        # MAPA: rota só com geometria de fonte
        if comp == 'mapa.rota' and p.get('rota') and not p.get('rota_osm') and not (geo or {}).get('rota_km'):
            _v(out, cid, 'R-ROTA-SEM-FONTE', 'erro', 'rota pedida sem geometria de fonte (não se desenha linha inventada)')
        # SOM: efeito com intenção
        for s in c.get('sfx') or []:
            if not (s.get('justificativa') or '').strip():
                _v(out, cid, 'R-SFX-SEM-MOTIVO', 'aviso', f"sfx {s.get('id')} sem acontecimento/justificativa")
    for a, idx in usos.items():
        if len(idx) > 2:
            _v(out, None, 'R-REPETICAO', 'erro', f'asset {a} usado em {len(idx)} cenas (slideshow por reenquadramento)')
        if any(b - a2 == 1 for a2, b in zip(idx, idx[1:])):
            _v(out, cenas[idx[1]].get('id'), 'R-REPETICAO-SEGUIDA', 'aviso', f'mesmo asset {a} em cenas seguidas')
    if cenas and cenas[0].get('modalidade') == 'tipografia':
        _v(out, cenas[0].get('id'), 'R-GANCHO-SEM-IMAGEM', 'aviso', 'gancho só com texto: prefira registro real forte')
    dur = (cenas[-1].get('fim') or 0) - (cenas[0].get('ini') or 0)
    if ep.get('alvo_duracao') and not (ep['alvo_duracao'][0] - 10 <= dur <= ep['alvo_duracao'][1] + 5):
        _v(out, None, 'R-DURACAO', 'aviso', f'episódio com {dur:.0f}s (alvo {ep["alvo_duracao"]})')
    return out


def impor(ep: dict) -> list[dict]:
    """correções SEGURAS aplicadas em código (registradas); o resto continua erro"""
    reg = []
    for i, c in enumerate(ep.get('cenas') or []):
        cam = c.setdefault('camera', {'tipo': 'fixa'})
        if cam.get('tipo') not in CAMERAS or (cam.get('tipo') != 'fixa' and not (cam.get('justificativa') or '').strip()) \
                or (cam.get('tipo') == 'revelar' and (not cam.get('revela') or i == 0)):
            reg.append({'cena': c.get('id'), 'correcao': 'camera→fixa', 'antes': dict(cam)})
            c['camera'] = {'tipo': 'fixa', 'enquadramento': cam.get('enquadramento')}
        tr = c.get('transicao') or {'tipo': 'corte'}
        if not isinstance(tr, dict):
            tr = {'tipo': str(tr)}
        if tr.get('tipo') not in TRANSICOES_OK or (tr.get('tipo') == 'dissolve' and not (tr.get('justificativa') or '').strip()):
            reg.append({'cena': c.get('id'), 'correcao': 'transicao→corte', 'antes': tr})
            tr = {'tipo': 'corte'}
        c['transicao'] = tr
    return reg


def familias(ep: dict) -> dict:
    """cobertura de famílias (teste integrado): o que de fato está no contrato, por modalidade e backend"""
    mods = [c.get('modalidade') for c in ep.get('cenas') or []]
    comps = [c.get('componente') for c in ep.get('cenas') or []]
    # só o que foi usado: NÃO existe cota de famílias no episódio editorial (auditoria 16/11, 3.7); a prova de cada
    # ferramenta é a suíte técnica (capacidades), não o filme
    return {'modalidades': {m: mods.count(m) for m in MODALIDADES if m in mods}, 'componentes': {k: comps.count(k) for k in set(comps)}}
