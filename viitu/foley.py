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
        # posição horizontal do sujeito (para o PAN estéreo): média das cenas cobertas pela faixa
        xs = [_x_sujeito(s) for s in segs if s["f0"] < f["f1"] and s["f1"] > f["f0"]]
        f["x"] = float(np.mean(xs)) if xs else 0.5
    return faixas


def _x_sujeito(s: dict) -> float:
    """0 = esquerda, 1 = direita. Clipe espelhado inverte o lado."""
    if s.get("layout") == "inteiro":
        x = 0.5
    else:
        x = float(s.get("alvo", s.get("foco", [0.5, 0.5]))[0])
    return 1 - x if s.get("espelhar") else x


def x_movimento(video: Path, f0: int, f1: int) -> float:
    """Lado da tela de onde vem a AÇÃO (centro de massa horizontal do movimento no vídeo final), 0..1.
    É daí que o som deve sair no pan estéreo."""
    cap = cv2.VideoCapture(str(video))
    passos = np.linspace(f0, max(f1 - 2, f0), 8).astype(int)
    soma, peso, ant = 0.0, 0.0, None
    for f in passos:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(f))
        ok, img = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(img, (90, 160)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if ant is not None:
            d = np.abs(g - ant)
            d[d < 8] = 0
            col = d.sum(axis=0)
            soma += float((col * np.arange(90)).sum())
            peso += float(col.sum())
        ant = g
    cap.release()
    return soma / peso / 89 if peso > 500 else 0.5


PRE_LAP = 8     # quadros: o som da próxima cena entra ANTES do corte (corte em J)
CAUDA = 6        # quadros: o som da cena anterior se arrasta depois do corte (corte em L)


def mixar(faixas: list[dict], fps: int, dur: float, saida: Path) -> Path:
    """Mixa o foley numa faixa estéreo profissional:
    - corte em J/L (entra antes, sai depois do corte, com crossfade) → o som "puxa" o olho para a próxima cena;
    - PAN estéreo pela posição do sujeito (lei de potência constante; até 70% para o lado);
    - fades suaves; som em loop se a faixa for maior que o arquivo."""
    import math
    import subprocess
    if not faixas:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-t", f"{dur:.3f}", str(saida)], check=True)
        return saida
    entradas, filtros, rot = [], [], []
    for i, f in enumerate(faixas):
        ini = max(f["f0"] - PRE_LAP, 0) / fps
        fim = min(f["f1"] + CAUDA, round(dur * fps)) / fps
        d = fim - ini
        fade_in = (f["f0"] - max(f["f0"] - PRE_LAP, 0)) / fps or 0.15
        p = (f.get("x", 0.5) - 0.5) * 2 * 0.7                       # -0,7 … +0,7
        ang = (p + 1) * math.pi / 4
        ge, gd = math.cos(ang) * math.sqrt(2), math.sin(ang) * math.sqrt(2)
        entradas += ["-stream_loop", "-1", "-i", str(FOLEY / f"{f['_som']}.mp3")]
        filtros.append(
            f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{d:.3f},asetpts=PTS-STARTPTS,"
            f"pan=stereo|c0={ge:.3f}*c0|c1={gd:.3f}*c1,volume={f['vol']:.2f},"
            f"afade=t=in:d={max(fade_in, 0.12):.3f},afade=t=out:st={max(d - 0.25, 0):.3f}:d=0.25,"
            f"adelay={int(ini * 1000)}|{int(ini * 1000)}[f{i}]")
        rot.append(f"[f{i}]")
    filtros.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0,apad,atrim=0:{dur:.3f}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros),
                    "-map", "[a]", "-ar", "48000", "-ac", "2", str(saida)], check=True)
    return saida
