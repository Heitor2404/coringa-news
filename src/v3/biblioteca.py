"""Biblioteca Coringa — acervo GLOBAL de mídia, independente do vídeo.

- Metadados em SQLite (`BIBLIOTECA_DB`, padrão data/biblioteca/coringa.sqlite3, fora do Git), com migrações numeradas.
- Binários num armazém endereçado pelo conteúdo (`BIBLIOTECA_ARMAZEM`, padrão data/biblioteca/arquivos/<sha[:2]>/<sha>.<ext>),
  também fora do Git. A cópia durável de cada arquivo é a URL de ORIGEM + sha256: `recuperar()` baixa de novo e confere o
  hash quando o armazém local não tem o arquivo (Commons, NASA, LoC… são duráveis e gratuitos).
- Manifesto portátil e versionável (`exportar_manifesto`): JSON Lines só com metadados, licenças, regiões e usos — sem
  caminhos locais e sem binários. `importar_manifesto` reconstrói o banco em outra máquina/execução.
- IDs estáveis: `cm-<12 primeiros do sha256>`. Os ids de produção (`a3`) viram ALIAS por vídeo (tabela usos).
- Reuso: o mesmo arquivo (sha) ou quase o mesmo (hash perceptual ≤ LIMIAR_QUASE) não é baixado nem analisado de novo;
  regiões de interesse e análises ficam presas ao sha e valem para qualquer vídeo.

Nada aqui chama IA. Remoto desativado: não existe destino de armazenamento aprovado (ver docs/v3/BIBLIOTECA.md).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DB_PADRAO = RAIZ / 'data' / 'biblioteca' / 'coringa.sqlite3'
ARMAZEM_PADRAO = RAIZ / 'data' / 'biblioteca' / 'arquivos'
LIMIAR_QUASE = 6            # distância de Hamming do pHash (64 bits) para "quase igual" (recorte, recompressão)
LIMITE_ARMAZEM_MB = int(os.getenv('BIBLIOTECA_LIMITE_MB') or 4000)

MIGRACOES = [
    # 1 — esquema inicial
    """
    CREATE TABLE midia (
      id TEXT PRIMARY KEY, sha256 TEXT UNIQUE NOT NULL, phash TEXT, tipo TEXT NOT NULL,
      titulo TEXT, descricao TEXT, mostra TEXT, entidades TEXT DEFAULT '[]', acontecimentos TEXT DEFAULT '[]',
      local TEXT, epoca TEXT, ano INTEGER, fonte TEXT, url_original TEXT, url_pagina TEXT, autor TEXT,
      licenca TEXT, licenca_prova TEXT, uso_comercial TEXT CHECK (uso_comercial IN ('sim','nao','indefinido')),
      atribuicao TEXT, restricoes_modificacao TEXT, largura INTEGER, altura INTEGER, duracao REAL,
      qualidade TEXT DEFAULT '{}', verificacao TEXT DEFAULT 'nao_verificada', ia INTEGER DEFAULT 0,
      tipo_img TEXT, ext TEXT, tamanho INTEGER, variante_de TEXT, criado REAL, atualizado REAL);
    CREATE TABLE regioes (
      sha256 TEXT NOT NULL, objeto TEXT NOT NULL, caixa TEXT, visivel INTEGER, ancoravel INTEGER, confianca TEXT,
      descricao TEXT, origem TEXT, criado REAL, PRIMARY KEY (sha256, objeto));
    CREATE TABLE analises (sha256 TEXT NOT NULL, tipo TEXT NOT NULL, conteudo TEXT, origem TEXT, custo_usd REAL DEFAULT 0,
      criado REAL, PRIMARY KEY (sha256, tipo));
    CREATE TABLE usos (midia_id TEXT NOT NULL, video TEXT NOT NULL, alias TEXT, plano INTEGER, funcao_documental TEXT,
      evento_id TEXT, criado REAL);
    CREATE TABLE temas (midia_id TEXT NOT NULL, tema TEXT NOT NULL, PRIMARY KEY (midia_id, tema));
    CREATE INDEX usos_midia ON usos(midia_id);
    """,
]

_COLS = ('id', 'sha256', 'phash', 'tipo', 'titulo', 'descricao', 'mostra', 'entidades', 'acontecimentos', 'local', 'epoca',
         'ano', 'fonte', 'url_original', 'url_pagina', 'autor', 'licenca', 'licenca_prova', 'uso_comercial', 'atribuicao',
         'restricoes_modificacao', 'largura', 'altura', 'duracao', 'qualidade', 'verificacao', 'ia', 'tipo_img', 'ext',
         'tamanho', 'variante_de', 'criado', 'atualizado')
_JSON = {'entidades', 'acontecimentos', 'qualidade'}


def _sha_arq(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _norm(s) -> str:
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]+', ' ', s)


_VAZIAS = set('a o as os de da do das dos e em no na nos nas um uma que se por para com ao the of and in on at to with from by foto photo image'.split())


def _tokens(s) -> set[str]:
    return {t for t in _norm(s).split() if len(t) > 2 and t not in _VAZIAS}


def classificar_licenca(item: dict) -> dict:
    """Licença declarada no crédito/licença → uso comercial sim/nao/indefinido. Usa a regra já existente do acervo V2
    (NC e ND ficam de fora: o vídeo recorta e anima). 'indefinido' NUNCA é tratado como liberado."""
    from src.v2.acervo_v2 import licenca
    r = licenca(item)
    txt = _norm(f"{item.get('licenca', '')} {item.get('credito', '')}")
    nome = next((n for n, rx in (('CC0', r'\bcc0\b'), ('domínio público', r'public domain|dominio publico|\bpd\b'),
                                 ('CC BY-SA', r'cc by sa'), ('CC BY', r'cc by'), ('NASA (domínio público EUA)', r'\bnasa\b'),
                                 ('governo dos EUA', r'us ?gov')) if re.search(rx, txt)), None)
    if r['ok']:
        return {'uso_comercial': 'sim', 'licenca': nome or 'declarada', 'atribuicao': r.get('atribuicao') or '',
                'restricoes_modificacao': 'compartilhar pela mesma licença' if nome == 'CC BY-SA' else ''}
    return {'uso_comercial': 'nao' if 'nao comercial' in r['motivo'] or 'derivacao' in _norm(r['motivo']) else 'indefinido',
            'licenca': nome or '', 'atribuicao': str(item.get('credito') or ''), 'restricoes_modificacao': r['motivo']}


class Biblioteca:
    def __init__(self, db: Path | str | None = None, armazem: Path | str | None = None):
        self.db_path = Path(db or os.getenv('BIBLIOTECA_DB') or DB_PADRAO)
        self.armazem = Path(armazem or os.getenv('BIBLIOTECA_ARMAZEM') or ARMAZEM_PADRAO)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(self.db_path))
        self.con.row_factory = sqlite3.Row
        self.migrar()
        self.estat = {'reuso_sha': 0, 'reuso_quase': 0, 'novos': 0, 'regioes_reusadas': 0, 'regioes_novas': 0}

    # ------------------------------------------------------------ esquema
    def migrar(self):
        v = self.con.execute('PRAGMA user_version').fetchone()[0]
        for i, sql in enumerate(MIGRACOES[v:], start=v + 1):
            self.con.executescript(sql)
            self.con.execute(f'PRAGMA user_version = {i}')
        self.con.commit()

    def versao(self) -> int:
        return self.con.execute('PRAGMA user_version').fetchone()[0]

    def fechar(self):
        self.con.commit()
        self.con.close()

    # ------------------------------------------------------------ armazém
    def caminho(self, sha: str, ext: str) -> Path:
        return self.armazem / sha[:2] / f'{sha}{ext}'

    def _row(self, r) -> dict | None:
        if not r:
            return None
        d = dict(r)
        for k in _JSON:
            try:
                d[k] = json.loads(d.get(k) or ('{}' if k == 'qualidade' else '[]'))
            except Exception:
                pass
        return d

    def obter(self, mid: str) -> dict | None:
        return self._row(self.con.execute('SELECT * FROM midia WHERE id=? OR sha256=?', (mid, mid)).fetchone())

    def por_sha(self, sha: str) -> dict | None:
        return self._row(self.con.execute('SELECT * FROM midia WHERE sha256=?', (sha,)).fetchone())

    def quase_igual(self, ph: str | None, exceto: str = '') -> dict | None:
        if not ph:
            return None
        from src.v2.acervo_v2 import distancia
        alvo = int(ph, 16)
        melhor = None
        for r in self.con.execute("SELECT id, sha256, phash FROM midia WHERE phash IS NOT NULL AND sha256 != ?", (exceto,)):
            d = distancia(alvo, int(r['phash'], 16))
            if d <= LIMIAR_QUASE and (melhor is None or d < melhor[0]):
                melhor = (d, r['id'])
        return self.obter(melhor[1]) if melhor else None

    # ------------------------------------------------------------ catalogar
    def ingerir(self, arq: Path | str, meta: dict, video: str = '', alias: str = '', tema: str = '') -> dict:
        """Cataloga um arquivo. Igual (sha) → reusa o registro (completa campos vazios). Quase igual (pHash) → registro
        novo marcado `variante_de` (o arquivo é outro; as análises da original NÃO são copiadas, só sugeridas).
        → {'id', 'sha256', 'reuso': 'sha'|'quase'|None, 'arquivo': caminho no armazém}"""
        arq = Path(arq)
        sha = _sha_arq(arq)
        ext = arq.suffix.lower() or '.bin'
        dest = self.caminho(sha, ext)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(arq, dest)
        ex = self.por_sha(sha)
        agora = time.time()
        if ex:
            self.estat['reuso_sha'] += 1
            novos = {k: v for k, v in self._campos(meta, arq).items() if v not in (None, '', [], {}) and ex.get(k) in (None, '', [], {})}
            if novos:
                self.con.execute(f"UPDATE midia SET {', '.join(f'{k}=?' for k in novos)}, atualizado=? WHERE id=?",
                                 [json.dumps(v, ensure_ascii=False) if k in _JSON else v for k, v in novos.items()] + [agora, ex['id']])
            mid, reuso = ex['id'], 'sha'
        else:
            c = self._campos(meta, arq)
            ph = None
            if c['tipo'] in ('foto', 'documento', 'mapa'):
                try:
                    from src.v2.acervo_v2 import phash
                    ph = format(phash(arq), '016x')
                except Exception:
                    ph = None
            irma = self.quase_igual(ph, exceto=sha)
            mid = f'cm-{sha[:12]}'
            c.update(id=mid, sha256=sha, phash=ph, ext=ext, tamanho=arq.stat().st_size, variante_de=irma['id'] if irma else None,
                     criado=agora, atualizado=agora)
            self.con.execute(f"INSERT INTO midia ({', '.join(_COLS)}) VALUES ({', '.join('?' * len(_COLS))})",
                             [json.dumps(c.get(k), ensure_ascii=False) if k in _JSON else c.get(k) for k in _COLS])
            reuso = 'quase' if irma else None
            self.estat['reuso_quase' if irma else 'novos'] += 1
        if tema:
            self.con.execute('INSERT OR IGNORE INTO temas VALUES (?, ?)', (mid, _norm(tema).strip()[:80]))
        if video and alias:
            self.con.execute('INSERT INTO usos (midia_id, video, alias, criado) VALUES (?, ?, ?, ?)', (mid, video, alias, agora))
        self.con.commit()
        return {'id': mid, 'sha256': sha, 'reuso': reuso, 'arquivo': str(dest)}

    @staticmethod
    def _campos(meta: dict, arq: Path) -> dict:
        lic = classificar_licenca(meta)
        txt = f"{meta.get('desc', '')} {meta.get('titulo', '')} {meta.get('mostra', '')}"
        ia = bool(meta.get('ia')) or bool(re.search(r'\bai[ -]generated\b|gerad[ao] por ia|midjourney|stable diffusion', txt, re.I))
        wh = meta.get('wh') or [meta.get('w') or 0, meta.get('h') or 0]
        if not all(wh):
            try:
                from PIL import Image
                with Image.open(arq) as im:
                    wh = list(im.size)
            except Exception:
                wh = [None, None]
        tipo = 'video' if meta.get('video') or arq.suffix.lower() in ('.mp4', '.webm', '.mov') else \
            'audio' if arq.suffix.lower() in ('.mp3', '.wav', '.ogg', '.m4a') else \
            'mapa' if meta.get('tipo_img') == 'mapa' else 'documento' if meta.get('tipo_img') in ('diagrama', 'documento') else 'foto'
        try:
            ano = int(str(meta.get('ano'))[:4]) if meta.get('ano') else None
        except ValueError:
            ano = None
        autor = ''
        m = re.search(r'—\s*([^(]+?)\s*\(', str(meta.get('credito') or ''))
        if m:
            autor = m.group(1).strip()[:120]
        return {'tipo': tipo, 'titulo': str(meta.get('titulo') or '')[:200], 'descricao': str(meta.get('desc') or '')[:400],
                'mostra': str(meta.get('mostra') or '')[:400], 'entidades': [x for x in (meta.get('pessoas') or []) if x][:12],
                'acontecimentos': list(meta.get('acontecimentos') or []), 'local': str(meta.get('lugar') or '')[:120],
                'epoca': str(meta.get('epoca') or '')[:60], 'ano': ano, 'fonte': str(meta.get('fonte') or '')[:60],
                'url_original': meta.get('url') or (meta.get('video') or {}).get('url'), 'url_pagina': meta.get('pagina') or meta.get('url_pagina'),
                'autor': autor, 'licenca': lic['licenca'], 'licenca_prova': meta.get('licenca_prova') or ('crédito declarado pela fonte: ' + str(meta.get('credito') or '')[:200] if meta.get('credito') else ''),
                'uso_comercial': lic['uso_comercial'], 'atribuicao': lic['atribuicao'][:300], 'restricoes_modificacao': lic['restricoes_modificacao'],
                'largura': wh[0], 'altura': wh[1], 'duracao': (meta.get('video') or {}).get('dur'),
                'qualidade': {k: meta[k] for k in ('util', 'rotulado', 'generica') if k in meta},
                'verificacao': 'nao_verificada', 'ia': int(ia), 'tipo_img': meta.get('tipo_img') or ''}

    # ------------------------------------------------------------ consultar
    def buscar(self, consulta: str, tipo: str | None = None, so_comercial: bool = True, limite: int = 12,
               excluir_ia: bool = True) -> list[dict]:
        """Busca por texto (título, descrição, o que a foto mostra, entidades, local, temas). Sem IA, sem rede.
        Licença 'indefinido'/'nao' e foto de IA ficam de fora por padrão."""
        q = _tokens(consulta)
        if not q:
            return []
        out = []
        for r in self.con.execute('SELECT * FROM midia'):
            d = self._row(r)
            if tipo and d['tipo'] != tipo:
                continue
            if so_comercial and d['uso_comercial'] != 'sim':
                continue
            if excluir_ia and d['ia']:
                continue
            temas = [t[0] for t in self.con.execute('SELECT tema FROM temas WHERE midia_id=?', (d['id'],))]
            campo = _tokens(' '.join([d['titulo'] or '', d['descricao'] or '', d['mostra'] or '', d['local'] or '',
                                      ' '.join(d['entidades'] or []), ' '.join(temas)]))
            hit = q & campo
            if hit:
                out.append({**d, 'temas': temas, 'pontos': round(len(hit) / len(q), 3), 'termos': sorted(hit)})
        out.sort(key=lambda x: (-x['pontos'], -(x['largura'] or 0)))
        return out[:limite]

    def usos(self, mid: str) -> list[dict]:
        return [dict(r) for r in self.con.execute('SELECT * FROM usos WHERE midia_id=? ORDER BY criado', (mid,))]

    def registrar_uso(self, mid: str, video: str, alias: str = '', plano: int | None = None, funcao: str = '', evento: str = ''):
        self.con.execute('INSERT INTO usos VALUES (?, ?, ?, ?, ?, ?, ?)', (mid, video, alias, plano, funcao, evento, time.time()))
        self.con.commit()

    # ------------------------------------------------------------ regiões e análises (reuso por sha)
    def regioes(self, sha: str) -> dict:
        """Mesmo formato de src.v2.regioes (cache por sha): {'foco': {...}, 'objetos': {nome: {...}}}."""
        out = {'objetos': {}}
        for r in self.con.execute('SELECT * FROM regioes WHERE sha256=?', (sha,)):
            d = {'caixa': json.loads(r['caixa']) if r['caixa'] else None, 'visivel': bool(r['visivel']), 'ancoravel': bool(r['ancoravel']),
                 'confianca': r['confianca'], 'descricao': r['descricao'], 'origem': r['origem']}
            if r['objeto'] == '__foco__':
                out['foco'] = d
            else:
                out['objetos'][r['objeto']] = d
        return out

    def gravar_regioes(self, sha: str, feito: dict):
        agora = time.time()
        itens = list((feito.get('objetos') or {}).items()) + ([('__foco__', feito['foco'])] if feito.get('foco') else [])
        for nome, d in itens:
            if d.get('origem') == 'saliencia':        # saliência é recalculada localmente, de graça
                continue
            self.con.execute('INSERT OR REPLACE INTO regioes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (sha, nome, json.dumps(d.get('caixa')) if d.get('caixa') else None, int(bool(d.get('visivel', True))),
                              int(bool(d.get('ancoravel'))), d.get('confianca'), str(d.get('descricao') or '')[:160], d.get('origem'), agora))
        self.con.commit()

    def localizar(self, arq: Path, objetos: list[str], chamar=None) -> dict:
        """src.v2.regioes.localizar com o cache GLOBAL: só os objetos que ninguém pediu antes para este arquivo vão à visão."""
        from src.v2 import regioes as rg
        sha = _sha_arq(Path(arq))
        cache = {sha: self.regioes(sha)}
        if not cache[sha].get('objetos') and not cache[sha].get('foco'):
            cache = {}
        ja = set((cache.get(sha) or {}).get('objetos') or {})
        pedidos = [o for o in objetos if o]
        self.estat['regioes_reusadas'] += len([o for o in pedidos if o in ja])
        novos = [o for o in pedidos if o not in ja]
        feito = rg.localizar(Path(arq), pedidos, cache, chamar if (novos or not ja) else None)
        if novos and chamar and not feito.get('erro_visao'):
            self.estat['regioes_novas'] += len(novos)
        self.gravar_regioes(sha, feito)
        return feito

    def analise(self, sha: str, tipo: str) -> dict | None:
        r = self.con.execute('SELECT conteudo FROM analises WHERE sha256=? AND tipo=?', (sha, tipo)).fetchone()
        return json.loads(r[0]) if r else None

    def gravar_analise(self, sha: str, tipo: str, conteudo: dict, origem: str = '', custo: float = 0.0):
        self.con.execute('INSERT OR REPLACE INTO analises VALUES (?, ?, ?, ?, ?, ?)',
                         (sha, tipo, json.dumps(conteudo, ensure_ascii=False), origem, custo, time.time()))
        self.con.commit()

    # ------------------------------------------------------------ durabilidade
    def recuperar(self, mid: str, baixar=None) -> Path | None:
        """Caminho do binário verificado (sha confere). Sem arquivo local: baixa da URL de origem (se houver) e confere."""
        d = self.obter(mid)
        if not d:
            return None
        p = self.caminho(d['sha256'], d['ext'] or '')
        if p.exists() and _sha_arq(p) == d['sha256']:
            return p
        if p.exists():                                   # corrompido: não usa
            p.unlink()
        if not d.get('url_original'):
            return None
        if baixar is None:
            import requests
            def baixar(url, dest):
                r = requests.get(url, timeout=60, headers={'User-Agent': 'CoringaBiblioteca/1.0 (projeto documental)'})
                r.raise_for_status()
                dest.write_bytes(r.content)
        tmp = p.with_suffix(p.suffix + '.parcial')
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            baixar(d['url_original'], tmp)
        except Exception:
            tmp.unlink(missing_ok=True)
            return None
        if _sha_arq(tmp) != d['sha256']:                 # a origem mudou (outro tamanho/thumbnail): não é o mesmo arquivo
            tmp.unlink(missing_ok=True)
            return None
        tmp.rename(p)
        return p

    def verificar(self) -> dict:
        ok, falta, corrompido = 0, [], []
        for r in self.con.execute('SELECT id, sha256, ext FROM midia'):
            p = self.caminho(r['sha256'], r['ext'] or '')
            if not p.exists():
                falta.append(r['id'])
            elif _sha_arq(p) != r['sha256']:
                corrompido.append(r['id'])
            else:
                ok += 1
        mb = sum(f.stat().st_size for f in self.armazem.rglob('*') if f.is_file()) / 1e6 if self.armazem.exists() else 0
        return {'ok': ok, 'faltam': falta, 'corrompidos': corrompido, 'armazem_mb': round(mb, 1), 'limite_mb': LIMITE_ARMAZEM_MB,
                'acima_do_limite': mb > LIMITE_ARMAZEM_MB}

    def limpar(self, aplicar: bool = False) -> dict:
        """Limpeza segura: só remove do armazém (1) arquivos sem registro no banco e (2) .parcial. Nunca apaga registro
        nem binário catalogado; `aplicar=False` só lista."""
        conhecidos = {(r['sha256'] + (r['ext'] or '')) for r in self.con.execute('SELECT sha256, ext FROM midia')}
        orfaos = [f for f in self.armazem.rglob('*') if f.is_file() and (f.name not in conhecidos or f.suffix == '.parcial')] \
            if self.armazem.exists() else []
        if aplicar:
            for f in orfaos:
                f.unlink()
        return {'orfaos': [str(f.relative_to(self.armazem)) for f in orfaos], 'aplicado': aplicar}

    # ------------------------------------------------------------ portabilidade
    def exportar_manifesto(self, destino: Path) -> int:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        with open(destino, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'_manifesto': 'biblioteca-coringa', 'versao_esquema': self.versao()}) + '\n')
            for r in self.con.execute('SELECT * FROM midia ORDER BY id'):
                d = self._row(r)
                d['regioes'] = self.regioes(d['sha256'])
                d['temas'] = [t[0] for t in self.con.execute('SELECT tema FROM temas WHERE midia_id=?', (d['id'],))]
                d['usos'] = [{k: u[k] for k in ('video', 'alias', 'plano', 'funcao_documental', 'evento_id')} for u in self.usos(d['id'])]
                d['analises'] = {a['tipo']: json.loads(a['conteudo']) for a in self.con.execute('SELECT tipo, conteudo FROM analises WHERE sha256=?', (d['sha256'],))}
                f.write(json.dumps(d, ensure_ascii=False, sort_keys=True) + '\n')
                n += 1
        return n

    def importar_manifesto(self, origem: Path) -> int:
        n = 0
        for linha in Path(origem).read_text(encoding='utf-8').splitlines():
            d = json.loads(linha)
            if '_manifesto' in d:
                continue
            if not self.por_sha(d['sha256']):
                self.con.execute(f"INSERT INTO midia ({', '.join(_COLS)}) VALUES ({', '.join('?' * len(_COLS))})",
                                 [json.dumps(d.get(k), ensure_ascii=False) if k in _JSON else d.get(k) for k in _COLS])
                n += 1
            self.gravar_regioes(d['sha256'], d.get('regioes') or {})
            for t in d.get('temas') or []:
                self.con.execute('INSERT OR IGNORE INTO temas VALUES (?, ?)', (d['id'], t))
            ja = {(u['video'], u['alias']) for u in self.usos(d['id'])}
            for u in d.get('usos') or []:
                if (u['video'], u['alias']) not in ja:
                    self.registrar_uso(d['id'], u['video'], u.get('alias') or '', u.get('plano'), u.get('funcao_documental') or '', u.get('evento_id') or '')
            for tipo, c in (d.get('analises') or {}).items():
                if not self.analise(d['sha256'], tipo):
                    self.gravar_analise(d['sha256'], tipo, c, 'manifesto')
        self.con.commit()
        return n

    def backup(self, destino: Path) -> dict:
        """Cópia consistente do banco (API de backup do SQLite) + manifesto + lista de sha (para conferir o armazém)."""
        destino = Path(destino)
        destino.mkdir(parents=True, exist_ok=True)
        b = sqlite3.connect(str(destino / 'coringa.sqlite3'))
        self.con.backup(b)
        b.close()
        n = self.exportar_manifesto(destino / 'manifesto.jsonl')
        (destino / 'sha256.txt').write_text('\n'.join(r[0] for r in self.con.execute('SELECT sha256 FROM midia ORDER BY sha256')) + '\n')
        return {'midias': n, 'pasta': str(destino)}


def ingerir_acervo(bib: Biblioteca, acervo: list[dict], video: str, tema: str = '') -> dict:
    """Acervo de uma produção (itens com `arq`) → biblioteca. Devolve {alias: id_global} e o que foi reusado."""
    mapa, reusos = {}, []
    for x in acervo or []:
        if not x.get('arq') or not Path(x['arq']).exists():
            continue
        r = bib.ingerir(x['arq'], x, video=video, alias=x.get('id', ''), tema=tema)
        mapa[x.get('id')] = r['id']
        if r['reuso']:
            reusos.append({'alias': x.get('id'), 'id': r['id'], 'reuso': r['reuso']})
    return {'mapa': mapa, 'reusos': reusos}


def _cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='Biblioteca Coringa (metadados SQLite + armazém por sha256)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('buscar'); s.add_argument('consulta'); s.add_argument('--todas-licencas', action='store_true')
    sub.add_parser('verificar')
    s = sub.add_parser('limpar'); s.add_argument('--aplicar', action='store_true')
    s = sub.add_parser('exportar'); s.add_argument('destino')
    s = sub.add_parser('importar'); s.add_argument('origem')
    s = sub.add_parser('backup'); s.add_argument('destino')
    s = sub.add_parser('ingerir-checkpoint'); s.add_argument('pasta'); s.add_argument('--video', default='')
    a = ap.parse_args(argv)
    bib = Biblioteca()
    if a.cmd == 'buscar':
        for d in bib.buscar(a.consulta, so_comercial=not a.todas_licencas):
            print(f"{d['id']} · {d['pontos']:.2f} · {d['uso_comercial']} · {(d['mostra'] or d['titulo'])[:90]} · usos={len(bib.usos(d['id']))}")
    elif a.cmd == 'verificar':
        print(json.dumps(bib.verificar(), ensure_ascii=False, indent=1))
    elif a.cmd == 'limpar':
        print(json.dumps(bib.limpar(a.aplicar), ensure_ascii=False, indent=1))
    elif a.cmd == 'exportar':
        print(bib.exportar_manifesto(Path(a.destino)), 'mídias')
    elif a.cmd == 'importar':
        print(bib.importar_manifesto(Path(a.origem)), 'mídias novas')
    elif a.cmd == 'backup':
        print(bib.backup(Path(a.destino)))
    elif a.cmd == 'ingerir-checkpoint':
        ck = Path(a.pasta)
        ac = json.loads((ck / 'acervo.json').read_text(encoding='utf-8'))
        ac = ac.get('acervo', ac) if isinstance(ac, dict) else ac
        for x in ac:
            if x.get('arq'):
                x['arq'] = str(ck / x['arq'])
        print(json.dumps(ingerir_acervo(bib, ac, a.video or ck.name), ensure_ascii=False))
    bib.fechar()


if __name__ == '__main__':
    _cli()
