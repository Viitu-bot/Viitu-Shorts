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
        if not som or not ((FOLEY / f"{som}.mp3").exists() or som in CAMADAS):
            continue
        if faixas and faixas[-1]["_som"] == som and abs(faixas[-1]["f1"] - s["f0"]) <= 1:
            faixas[-1]["f1"] = s["f1"]           # continua a mesma ambiência através do corte
        else:
            faixas.append({"f0": s["f0"], "f1": s["f1"], "som": f"foley_{som}.mp3", "_som": som})
    for f in faixas:
        from viitu.mix import ganho      # foley próprio (reserva) = camada de ambiência
        f["vol"] = ganho("ambiencia")
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


# Camadas profissionais (Sonniss) por tipo de cena: (ambiência de fundo, detalhe de perto / ASMR)
CAMADAS = {
    "fogo_rugido": ("large wildfire roaring flames burning forest", "close up fire crackling and popping"),
    "fogo_crepitando": ("burning grass fire crackling outdoors", "close up campfire crackling and popping"),
    "fumaca_brasa": ("quiet smoldering embers after fire, soft crackle", "close up campfire crackling and popping"),
    "vento": ("strong wind blowing through trees", "wind gust whoosh"),
    "aviao": ("propeller airplane flying overhead", "airplane flyby pass"),
    "helicoptero": ("helicopter flying overhead", "helicopter rotor close"),
    "agua_jato": ("water hose spraying", "water splashing close"),
    "passos_mato": ("footsteps on dry grass and leaves", "boots walking on dry leaves close"),
    "noite_grilos": ("night forest ambience crickets", "crickets close"),
    "floresta_dia": ("forest daytime birds ambience", "birds chirping close"),
    "multidao": ("crowd murmur outdoors", "people talking nearby"),
    "galinhas": ("chickens clucking on a farm", "chicken clucking close"),
    "ovo_quebrando": ("egg sizzling in frying pan", "oil sizzling close"),
    "turbina": ("jet engine idling at the airport, distant", "airliner jet engine whine"),
    "hangar": ("large industrial hangar room tone", "industrial machine hum"),
    "voo": ("airliner flying overhead", "wind at high altitude"),
    "cabine": ("airplane cabin interior ambience during flight", "airplane cabin hum"),
    "oficina": ("industrial machine hum", "mechanical gears whirring"),
    "carro": ("car driving by on asphalt", "car tires rolling on asphalt"),
    "lama": ("car wheel spinning in mud", "mud splash squelch"),
    "passaros": ("flock of seagulls flying overhead", "flock of seagulls flying overhead"),
}
FOGO = r"fire|flame|burn|campfire|ember|blaze|bonfire|fireplace|wood ?stove"
EXIGIR = {"fogo_rugido": FOGO, "fogo_crepitando": FOGO, "fumaca_brasa": r"ember|smolder|campfire|fireplace|stove|small fire|fire gentle|fire calm", "vento": r"wind|gust",
          "aviao": r"plane|aircraft|airliner|propeller", "helicoptero": r"helicopter|heli|rotor",
          "agua_jato": r"water|hose|spray|splash", "passos_mato": r"footstep|step|walk",
          "noite_grilos": r"cricket|night", "floresta_dia": r"forest|bird|wood", "multidao": r"crowd|people|walla",
          "galinhas": r"chicken|hen|rooster", "ovo_quebrando": r"sizzl|fry|pan",
          "turbina": r"jet|airliner|aircraft|airport", "hangar": r"hangar|hall|warehouse|industrial|factory|machine",
          "voo": r"plane|aircraft|airliner|jet|wind", "cabine": r"cabin|interior|airplane|plane",
          "oficina": r"workshop|garage|tool|gear|mechan|machine", "carro": r"car|tire|tyre|vehicle|drive",
          "lama": r"mud|squelch|splash|wheel|tire|tyre",
          "passaros": r"flock|seagull|gull|starling|flap|flutter|wings"}
ESCOLHAS = RAIZ / "assets" / "sonniss" / "escolhas.json"     # mesma descrição → mesmo som (rápido e consistente)


def _som_sonniss(desc: str, dur_min: float, exigir: str | None = None) -> str | None:
    import json
    esc = json.loads(ESCOLHAS.read_text(encoding="utf-8")) if ESCOLHAS.exists() else {}
    if desc not in esc:
        try:
            from viitu.sons import buscar
            r = buscar(desc, dur_min=dur_min, n=1, exigir=exigir)[0]
            esc[desc] = {"id": r["id"], "nome": r["nome"], "nota": r["nota"]}
            ESCOLHAS.write_text(json.dumps(esc, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as e:          # sem rede/CLAP: fica o foley próprio
            print(f"    sonniss indisponível para '{desc}': {str(e)[:80]}")
            return None
    from viitu.sons import baixar, _catalogo
    return str(baixar(_catalogo()[esc[desc]["id"]]))


def camadas(faixas: list[dict]) -> list[dict]:
    """Troca cada faixa por 2 camadas Sonniss (fundo + detalhe ASMR) — ou mantém o foley próprio se faltar."""
    out = []
    for f in faixas:
        par = CAMADAS.get(f["_som"])
        rx = EXIGIR.get(f["_som"])
        arqs = [_som_sonniss(par[0], 20, rx), _som_sonniss(par[1], 4, rx)] if par else [None, None]
        if not arqs[0]:
            out.append(f)
            continue
        from viitu.mix import ganho
        out.append({**f, "arquivo": arqs[0], "vol": ganho("ambiencia"), "camada": "fundo"})
        if arqs[1]:
            out.append({**f, "arquivo": arqs[1], "vol": ganho("foley_detalhe"), "camada": "detalhe"})
    return out


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
        arq = f.get("arquivo") or str(FOLEY / f"{f['_som']}.mp3")
        ofs = (f["f0"] * 7.3) % 20 if f.get("arquivo") else 0        # cada cena pega outro trecho do som
        entradas += ["-stream_loop", "-1", "-ss", f"{ofs:.2f}", "-i", arq]
        norm = "loudnorm=I=-14:TP=-2,aresample=48000,"     # toda camada na referência da voz; o nível vem de "vol"
        filtros.append(
            f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,{norm}atrim=0:{d:.3f},asetpts=PTS-STARTPTS,"
            f"pan=stereo|c0={ge:.3f}*c0|c1={gd:.3f}*c1,volume={f['vol']:.2f},"
            f"afade=t=in:d={max(fade_in, 0.12):.3f},afade=t=out:st={max(d - 0.25, 0):.3f}:d=0.25,"
            f"adelay={int(ini * 1000)}|{int(ini * 1000)}[f{i}]")
        rot.append(f"[f{i}]")
    filtros.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0,apad,atrim=0:{dur:.3f}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros),
                    "-map", "[a]", "-ar", "48000", "-ac", "2", str(saida)], check=True)
    return saida
