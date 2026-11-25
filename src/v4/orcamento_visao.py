"""Autorização persistente de visão (E284): saldo lógico e de operações externas que sobrevive a workflows,
retomadas e falhas.

Regras:
- O livro é criado UMA vez por autorização e nunca reiniciado (abrir() sobre um livro existente só lê).
- Cada chamada lógica é RESERVADA e gravada antes de chamar o provedor; reserva não liquidada (execução morta)
  conta como consumida, no pior caso de operações.
- Operações externas efetivas (tentativas no provedor, inclusive inválidas e retries) são liquidadas a partir da
  telemetria; antes de reservar exige-se saldo para o pior caso de tentativas de uma chamada.
- Armazéns: 'cofre' (arquivo JSON no repositório privado, gravação com compare-and-swap pelo sha do GitHub) ou
  'local' (arquivo com trava, para testes e execução local).
Teto financeiro do motor continua USD 0: este livro só controla cota gratuita autorizada.
"""
from __future__ import annotations

import base64
import copy
import fcntl
import json
import os
import time
import uuid
from pathlib import Path


class SaldoEsgotado(RuntimeError):
    pass


class ArmazemLocal:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def aplicar(self, fn):
        """fn(livro|None) -> (novo_livro|None, resultado). Grava só se mudou."""
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(str(self.caminho) + '.lock', 'w') as trava:
            fcntl.flock(trava, fcntl.LOCK_EX)
            atual = json.loads(self.caminho.read_text(encoding='utf8')) if self.caminho.is_file() else None
            novo, res = fn(copy.deepcopy(atual))
            if novo is not None and novo != atual:
                tmp = self.caminho.with_suffix('.tmp')
                tmp.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding='utf8')
                tmp.replace(self.caminho)
            return res


class ArmazemCofre:
    """Arquivo no ramo privado do cofre; PUT com o sha lido (CAS). Conflito → relê e refaz a decisão."""
    REPO_ID = 1454059520

    def __init__(self, caminho, token, repo='Heitor2404/coringa-cofre', ramo='revisao-privada'):
        import requests
        self.url = f'https://api.github.com/repos/{repo}/contents/{caminho}'
        self.ramo = ramo
        self.s = requests.Session()
        self.s.headers.update({'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
        r = self.s.get(f'https://api.github.com/repos/{repo}', timeout=30)
        if r.status_code != 200 or r.json().get('id') != self.REPO_ID or r.json().get('private') is not True:
            raise RuntimeError('ORCAMENTO-COFRE-NAO-CONFIRMADO')

    def aplicar(self, fn):
        for _ in range(6):
            r = self.s.get(self.url, params={'ref': self.ramo}, timeout=30)
            if r.status_code == 404:
                atual, sha = None, None
            elif r.status_code == 200:
                j = r.json()
                atual, sha = json.loads(base64.b64decode(j['content'])), j['sha']
            else:
                raise RuntimeError(f'ORCAMENTO-COFRE-HTTP-{r.status_code}')
            novo, res = fn(copy.deepcopy(atual))
            if novo is None or novo == atual:
                return res
            corpo = {'message': 'orcamento visao: ' + novo['autorizacao'], 'branch': self.ramo,
                     'content': base64.b64encode(json.dumps(novo, ensure_ascii=False, indent=1).encode()).decode()}
            if sha:
                corpo['sha'] = sha
            w = self.s.put(self.url, json=corpo, timeout=30)
            if w.status_code in (200, 201):
                return res
            if w.status_code not in (409, 422):
                raise RuntimeError(f'ORCAMENTO-COFRE-HTTP-{w.status_code}')
            time.sleep(2)
        raise RuntimeError('ORCAMENTO-COFRE-CONFLITO')


def armazem_padrao(autorizacao):
    token = os.getenv('CORINGA_ORCAMENTO_TOKEN')
    if token:
        return ArmazemCofre(f'orcamento/{autorizacao}.json', token)
    return ArmazemLocal(Path(os.getenv('CORINGA_ORCAMENTO_DIR') or '.orcamento') / f'{autorizacao}.json')


def _resumo(lv):
    reservadas = [e for e in lv['eventos'] if e['estado'] == 'RESERVADA']
    liquidadas = [e for e in lv['eventos'] if e['estado'] == 'LIQUIDADA']
    logicas = len(reservadas) + len(liquidadas)
    ops = sum(e.get('operacoes', 0) for e in liquidadas) + lv['max_operacoes_por_chamada'] * len(reservadas)
    return {'autorizacao': lv['autorizacao'], 'limite_logico': lv['limite_logico'], 'limite_operacoes': lv['limite_operacoes'],
            'logicas_consumidas': logicas, 'operacoes_consumidas': ops,
            'saldo_logico': lv['limite_logico'] - logicas, 'saldo_operacoes': lv['limite_operacoes'] - ops,
            'reservas_nao_liquidadas': len(reservadas),
            'tokens': sum((e.get('tokens') or 0) for e in liquidadas), 'custo_usd': 0.0,
            'por_finalidade': {f: sum(1 for e in lv['eventos'] if e.get('finalidade') == f)
                               for f in sorted({e.get('finalidade') for e in lv['eventos']})}}


def abrir(autorizacao, *, limite_logico, limite_operacoes, max_operacoes_por_chamada=2, armazem=None):
    """Cria o livro só se não existir. Limites divergentes de um livro existente são recusados (não reinicia)."""
    def fn(lv):
        if lv is None:
            lv = {'autorizacao': autorizacao, 'limite_logico': limite_logico, 'limite_operacoes': limite_operacoes,
                  'max_operacoes_por_chamada': max_operacoes_por_chamada, 'teto_usd': 0.0,
                  'criado_em': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'eventos': []}
        if (lv['limite_logico'], lv['limite_operacoes']) != (limite_logico, limite_operacoes):
            raise RuntimeError('ORCAMENTO-LIMITES-DIVERGENTES: autorização não pode ser ampliada nem reiniciada')
        return lv, _resumo(lv)
    return (armazem or armazem_padrao(autorizacao)).aplicar(fn)


def saldo(autorizacao, armazem=None):
    def fn(lv):
        if lv is None:
            raise RuntimeError('ORCAMENTO-INEXISTENTE')
        return None, _resumo(lv)
    return (armazem or armazem_padrao(autorizacao)).aplicar(fn)


def reservar(autorizacao, finalidade, *, execucao=None, limite_finalidade=None, armazem=None):
    def fn(lv):
        if lv is None:
            raise SaldoEsgotado('ORCAMENTO-INEXISTENTE')
        r = _resumo(lv)
        if r['saldo_logico'] < 1 or r['saldo_operacoes'] < lv['max_operacoes_por_chamada']:
            raise SaldoEsgotado(f'ORCAMENTO-ESGOTADO {r}')
        if limite_finalidade is not None and r['por_finalidade'].get(finalidade, 0) >= limite_finalidade:
            raise SaldoEsgotado(f'ORCAMENTO-FINALIDADE-ESGOTADA {finalidade}')
        ticket = {'id': uuid.uuid4().hex, 'estado': 'RESERVADA', 'finalidade': finalidade,
                  'execucao': execucao or os.getenv('GITHUB_RUN_ID') or 'local',
                  'reservado_em': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        lv['eventos'].append(ticket)
        return lv, dict(ticket)
    return (armazem or armazem_padrao(autorizacao)).aplicar(fn)


def liquidar(autorizacao, ticket_id, *, operacoes, tokens=None, ok=True, motivo=None, armazem=None):
    def fn(lv):
        e = next((x for x in (lv or {}).get('eventos', []) if x['id'] == ticket_id), None)
        if e is None or e['estado'] != 'RESERVADA':
            raise RuntimeError('ORCAMENTO-TICKET-INVALIDO')
        e.update(estado='LIQUIDADA', operacoes=int(max(1, operacoes)), tokens=tokens, ok=bool(ok), motivo=motivo,
                 liquidado_em=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        return lv, _resumo(lv)
    return (armazem or armazem_padrao(autorizacao)).aplicar(fn)
