"""MIXAGEM POR REGRA (não por medição depois): cada camada tem um nível fixo RELATIVO À VOZ.

1. Todo áudio é normalizado para a mesma referência da voz (−14 LUFS):
   - leitos (voz, trilha, ambiência, foley): pela loudness INTEGRADA;
   - efeitos curtos (whoosh, pop, boom, riser, ding...): pela loudness MOMENTÂNEA MÁXIMA (o "pico percebido").
   Ou seja: depois de normalizado, todo som no seu ponto mais alto soa tão alto quanto a voz.
2. A tabela `edicao/especificacao.json` → "mix_db" diz quantos dB cada camada fica abaixo (−) da voz.
   ganho linear = 10^(dB/20). Ex.: música −12 dB → 0,25.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REF = -14.0
ESPEC = RAIZ / "edicao" / "especificacao.json"


def espec() -> dict:
    return json.loads(ESPEC.read_text(encoding="utf-8"))


def ganho(camada: str) -> float:
    return round(10 ** (espec()["mix_db"][camada] / 20), 4)


def _medir(arq: Path) -> tuple[float | None, float | None]:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(arq), "-af", "ebur128=framelog=verbose", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    integ = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    mom = [float(x) for x in re.findall(r"\sM:\s*(-?[\d.]+)", out) if float(x) > -70]
    return (float(integ[-1]) if integ else None), (max(mom) if mom else None)


def normalizar(origem: Path, destino: Path, tipo: str = "pontual") -> Path:
    """tipo 'leito' (integrada) ou 'pontual' (momentânea máxima) → mesma referência da voz."""
    integ, mmax = _medir(origem)
    base = integ if tipo == "leito" else mmax
    g = REF - base if base is not None and base > -70 else 0.0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(origem), "-af", f"volume={g:.2f}dB,alimiter=limit=0.95",
                    "-ar", "48000", str(destino)], check=True)
    return destino
