"""Sound design automático: escolhe o FOLEY de cada cena olhando a imagem (CLIP) e monta o plano de som.

- Cada cena recebe o som do que aparece nela (fogo, avião, vento, galinhas...) — biblioteca em assets/foley/.
- `"foley": "<nome>"` no cenas.json força um som; `"foley": null` deixa a cena sem foley.
- Volume do foley por intensidade da cena (movimento) e fades nas bordas; cenas vizinhas com o mesmo
  som viram UMA faixa contínua (ambiência não "pula" no corte).
Uso interno: chamado por viitu.editar no modo --remotion.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
FOLEY = RAIZ / "assets" / "foley"

ROTULOS = {
    "fogo_crepitando": "close-up of flames burning grass or wood",
    "fogo_rugido": "a huge wildfire with big flames and smoke",
    "vento": "trees and grass blowing in strong wind",
    "aviao": "an airplane flying in the sky",
    "helicoptero": "a helicopter flying",
    "agua_jato": "water being sprayed",
    "passos_mato": "people walking on dry grass",
    "noite_grilos": "a dark forest at night",
    "galinhas": "chickens on a farm",
    "ovo_quebrando": "an egg in a frying pan",
    "floresta_dia": "a calm forest in daylight",
    "multidao": "a group of people standing together",
    "fumaca_brasa": "a burned forest with smoke and ashes",
}


def _quadro(clipe: Path, t: float):
    cap = cv2.VideoCapture(str(clipe))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ok, img = cap.read()
    cap.release()
    return img if ok else None


def escolher(segs: list[dict], pasta: Path, fps: int) -> list[dict]:
    """[{f0, f1, som, vol}] — uma entrada por trecho contínuo com o mesmo som."""
    import torch
    from PIL import Image
    from viitu.inteligencia import _clip
    modelo, prep, tok = _clip()
    with torch.no_grad():
        txt = modelo.encode_text(tok(list(ROTULOS.values())))
        txt /= txt.norm(dim=-1, keepdim=True)
    nomes = list(ROTULOS)
    por_cena = []
    for s in segs:
        if "foley" in s:
            por_cena.append(s["foley"])
            continue
        clipe = pasta / "clipes" / s["clipe"]
        img = _quadro(clipe, s.get("inicio", 0) + (s["f1"] - s["f0"]) / fps / 2 * float(s.get("velocidade", 1)))
        if img is None:
            por_cena.append(None)
            continue
        with torch.no_grad():
            e = modelo.encode_image(prep(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))).unsqueeze(0))
            e /= e.norm(dim=-1, keepdim=True)
            p = (100 * e @ txt.T).softmax(-1)[0].numpy()
        i = int(p.argmax())
        por_cena.append(nomes[i] if p[i] > 0.35 else None)
    faixas = []
    for s, som in zip(segs, por_cena):
        if not som or not (FOLEY / f"{som}.mp3").exists():
            continue
        if faixas and faixas[-1]["_som"] == som and abs(faixas[-1]["f1"] - s["f0"]) <= 1:
            faixas[-1]["f1"] = s["f1"]           # continua a mesma ambiência através do corte
        else:
            faixas.append({"f0": s["f0"], "f1": s["f1"], "som": f"foley_{som}.mp3", "_som": som})
    for f in faixas:
        f["vol"] = 0.32 if f["_som"] in ("noite_grilos", "floresta_dia", "multidao", "fumaca_brasa") else 0.5
    return faixas
