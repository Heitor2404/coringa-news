"""Pacote de reprodução de um vídeo do NTC (Fase 4, CP1). Só registra, nunca muda o vídeo.

O pacote guarda tudo o que é preciso para remontar o vídeo sem chamar IA:
roteiro validado, dados de montagem (o que o fabula.html recebe), tempos da
narração, legendas, versão do motor (commit + hash dos arquivos do desenho),
relatório de acontecimentos e dados básicos (tema, data, personagem).

Fica em saida/pacotes_ntc/ e o workflow copia para o cofre privado
(arquivo_ntc/). A voz (wav) não entra: é pesada e a remontagem de conferência
usa só a imagem; o tempo de cada fala está nos dados.
"""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
VETOR = RAIZ / 'canais' / 'ntc' / 'vetor'
PASTA = RAIZ / 'saida' / 'pacotes_ntc'
FORMATO = 1
BRT = timezone(timedelta(hours=-3))


def _commit() -> str:
    sha = os.getenv('GITHUB_SHA')
    if sha:
        return sha
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=RAIZ, capture_output=True, text=True, timeout=10).stdout.strip() or '?'
    except Exception:
        return '?'


def versao_motor() -> dict:
    """Commit + hash de cada arquivo que decide o desenho (kits, página, regiões, catálogo, montagem)."""
    arqs = sorted(VETOR.glob('kit_*.js')) + [VETOR / n for n in ('fabula.html', 'regioes.json', 'capacidades.json')] \
        + [RAIZ / 'src' / 'fabula.py', RAIZ / 'src' / 'ntc_eventos.py']
    hashes = {str(a.relative_to(RAIZ)): hashlib.sha256(a.read_bytes()).hexdigest()[:16] for a in arqs if a.exists()}
    total = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    return {'commit': _commit(), 'hash_motor': total, 'arquivos': hashes}


def _slug(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', s.lower())[:50].strip('-') or 'sem-tema'


def montar(r: dict, dados: dict, tempos: list, legendas: list, eventos: dict | None, video: Path | None = None) -> dict:
    agora = datetime.now(BRT)
    return {'formato_pacote': FORMATO, 'canal': 'ntc', 'criado_em': agora.isoformat(timespec='seconds'),
            'tema': r.get('tema'), 'titulo_tela': r.get('titulo_tela'), 'personagem': r.get('personagem', 'val'),
            'motor': versao_motor(), 'roteiro': r, 'dados_montagem': dados, 'tempos': tempos, 'legendas': legendas,
            'eventos': eventos, 'video': video.name if video else None,
            'execucao': {k: os.getenv(k) for k in ('GITHUB_RUN_ID', 'GITHUB_WORKFLOW', 'GITHUB_REF_NAME') if os.getenv(k)}}


def salvar(pac: dict, pasta: Path | None = None) -> Path:
    pasta = pasta or PASTA
    pasta.mkdir(parents=True, exist_ok=True)
    dia = (pac.get('criado_em') or '')[:10] or datetime.now(BRT).strftime('%Y-%m-%d')
    arq = pasta / f"{dia}-{_slug(pac.get('tema') or '')}-{pac['motor']['hash_motor'][:8]}.json"
    arq.write_text(json.dumps(pac, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return arq


def ler(arq: Path) -> dict:
    pac = json.loads(Path(arq).read_text(encoding='utf-8'))
    if pac.get('formato_pacote') != FORMATO:
        raise ValueError(f"pacote formato {pac.get('formato_pacote')} (esperado {FORMATO})")
    return pac


def conferir_motor(pac: dict) -> list:
    """Lista os arquivos do desenho que mudaram desde que o pacote foi feito (vazio = mesmo motor)."""
    atual = versao_motor()['arquivos']
    return sorted(k for k in set(atual) | set(pac['motor']['arquivos']) if atual.get(k) != pac['motor']['arquivos'].get(k))


def resumo_telegram(pac: dict, arq: Path) -> str:
    m = pac['motor']
    return f"📦 Pacote: {arq.name} · motor {m['hash_motor'][:8]} · commit {m['commit'][:7]}"
