"""Amostra de TTS local livre para ATLAS, NÃO altera narrador oficial.

Piper pt_BR-cadu-medium (nova versão treinada a partir de rdh CC0).
Use somente para comparar naturalidade antes de decidir sobre áudio monetizável.
Nenhuma chamada Gemini, Edge, Azure ou API paga.
"""
from __future__ import annotations

import hashlib
import json
import sys
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PLANO = RAIZ / "src/v4/formatos/planos/reuso/atlas_chips_factual_2026.json"


def amostra(model_dir: Path, saida: Path) -> dict:
    from piper import PiperVoice

    card = (model_dir / "MODEL_CARD").read_text(encoding="utf-8")
    assert "License: CC0" in card, "Modelo sem declaração de dataset CC0"
    assert "Finetuned from the rdh base model" in card, "Modelo antigo não é a versão retrain CC0."
    model = model_dir / "pt_BR-cadu-medium.onnx"
    cfg = model_dir / "pt_BR-cadu-medium.onnx.json"
    assert model.stat().st_size > 20_000_000 and cfg.is_file()
    plano = json.loads(PLANO.read_text(encoding="utf-8"))
    texto = plano["narracao"]["texto"].split("Em 2025,")[0].strip()
    assert "Taiwan" in texto and len(texto) > 70, "Amostra não contém o gancho correto"
    saida.mkdir(parents=True, exist_ok=True)
    wav = saida / "voz_ptbr_cadu_amostra.wav"
    voz = PiperVoice.load(str(model), config_path=str(cfg))
    with wave.open(str(wav), "wb") as arq:
        if hasattr(voz, "synthesize_wav"):
            voz.synthesize_wav(texto, arq)
        else:
            voz.synthesize(texto, arq)
    with wave.open(str(wav), "rb") as arq:
        segundos = arq.getnframes() / arq.getframerate()
        sample_rate = arq.getframerate()
        canais = arq.getnchannels()
    assert 3 <= segundos <= 55 and canais == 1, f"Amostra inválida: {segundos:.2f}s"
    resultado = {
        "status": "DEMONSTRACAO_PRIVADA_SEM_APROVACAO",
        "motor": "Piper-TTS", "voz": "pt_BR-cadu-medium",
        "licenca_dataset": "CC0", "base_modelo": "rdh / CC0",
        "fonte_modelo": "https://huggingface.co/rhasspy/piper-voices",
        "fonte_licenca": "https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/COMMERCIAL_USE.md",
        "licenca_do_codigo": "GPL-3.0-or-later (Piper engine)",
        "texto": texto, "duracao_s": round(segundos, 2),
        "sample_rate_hz": sample_rate, "canais": canais,
        "sha256_audio": hashlib.sha256(wav.read_bytes()).hexdigest(),
        "comparacao_necessaria": "O áudio deve ser ouvido; qualidade não é provada pelo status do workflow.",
        "uso": "Somente prévia; não muda voz oficial nem publica vídeo."
    }
    (saida / "amostra_voz.json").write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding="utf-8")
    (saida / "MODEL_CARD").write_text(card,encoding="utf-8")
    print(json.dumps({"voz":resultado["voz"],"duracao_s":resultado["duracao_s"],
                      "sample_rate":sample_rate,"sha256_audio":resultado["sha256_audio"]},
                     ensure_ascii=False),flush=True)
    return resultado


if __name__ == "__main__":
    amostra(Path(sys.argv[1]), Path(sys.argv[2]))
