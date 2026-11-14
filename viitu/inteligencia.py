"""Inteligência visual para escolher e enquadrar cenas como um editor.

  localizar(clipe, "goat eye", t0, t1)   OWLv2: onde está o objeto descrito, quadro a quadro
  pico_acao(clipe, t0, t1)               fluxo óptico: segundo de maior movimento (o "bote")
  semantica(clipes, frases)              CLIP: qual trecho de qual clipe combina com cada frase

Modelos baixados do Hugging Face na primeira vez (cache em ~/.cache/huggingface).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np


def _quadros(clipe: Path, tempos: list[float]) -> list[tuple[float, np.ndarray]]:
    cap = cv2.VideoCapture(str(clipe))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    saida = []
    for t in tempos:
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(t * fps), max(total - 1, 0)))
        ok, img = cap.read()
        if ok:
            saida.append((t, img))
    cap.release()
    return saida


def duracao(clipe: Path) -> float:
    cap = cv2.VideoCapture(str(clipe))
    d = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    cap.release()
    return d


# ---------- OWLv2: localizar objeto descrito em texto ----------

@lru_cache(maxsize=1)
def _owl():
    from transformers import Owlv2ForObjectDetection, Owlv2Processor
    nome = "google/owlv2-base-patch16-ensemble"
    return Owlv2Processor.from_pretrained(nome), Owlv2ForObjectDetection.from_pretrained(nome).eval()


def localizar(clipe: Path, texto: str, t0: float, t1: float, passos: int = 6,
              limiar: float = 0.12, area_max: float = 0.25) -> list[dict]:
    """[{t, x, y, w, h, conf}] normalizado (0–1) do melhor achado de `texto` em cada quadro."""
    import torch
    from PIL import Image
    proc, modelo = _owl()
    tempos = [t0 + (t1 - t0) * k / max(passos - 1, 1) for k in range(passos)]
    res = []
    for t, img in _quadros(clipe, tempos):
        h, w = img.shape[:2]
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ent = proc(text=[[texto]], images=pil, return_tensors="pt")
        with torch.no_grad():
            out = modelo(**ent)
        lado = max(h, w)  # o OWLv2 trabalha em imagem quadrada com padding
        r = proc.post_process_grounded_object_detection(out, threshold=limiar,
                                               target_sizes=torch.tensor([[lado, lado]]))[0]
        # descarta caixas enormes (o modelo às vezes marca o animal inteiro) e pega a melhor
        boas = [k for k in range(len(r["scores"]))
                if ((r["boxes"][k][2] - r["boxes"][k][0]) / w) * ((r["boxes"][k][3] - r["boxes"][k][1]) / h) <= area_max]
        if boas:
            i = max(boas, key=lambda k: float(r["scores"][k]))
            x0, y0, x1, y1 = r["boxes"][i].tolist()
            res.append({"t": round(t, 2), "x": round(x0 / w, 3), "y": round(y0 / h, 3),
                        "w": round((x1 - x0) / w, 3), "h": round((y1 - y0) / h, 3),
                        "conf": round(float(r["scores"][i]), 2)})
    return res


# ---------- fluxo óptico: pico de ação ----------

def pico_acao(clipe: Path, t0: float = 0, t1: float | None = None) -> dict:
    """Segundo com mais movimento no trecho (ex.: o bote, o salto, a fuga)."""
    cap = cv2.VideoCapture(str(clipe))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    t1 = t1 if t1 is not None else duracao(clipe)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t0 * fps))
    ant, curva = None, []
    t = t0
    passo = max(int(fps / 10), 1)          # ~10 medições por segundo
    while t < t1:
        ok, img = cap.read()
        if not ok:
            break
        if int(t * fps) % passo == 0:
            g = cv2.cvtColor(cv2.resize(img, (256, 144)), cv2.COLOR_BGR2GRAY)
            if ant is not None:
                fluxo = cv2.calcOpticalFlowFarneback(ant, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                curva.append((t, float(np.linalg.norm(fluxo, axis=2).mean())))
            ant = g
        t += 1 / fps
    cap.release()
    if not curva:
        return {"t": t0, "intensidade": 0, "curva": []}
    v = np.convolve([c[1] for c in curva], np.ones(3) / 3, mode="same")
    i = int(v.argmax())
    return {"t": round(curva[i][0], 2), "intensidade": round(float(v[i]), 2),
            "curva": [(round(a, 2), round(float(b), 2)) for (a, _), b in zip(curva, v)]}


# ---------- CLIP: frase ↔ trecho de vídeo ----------

@lru_cache(maxsize=1)
def _clip():
    import open_clip
    modelo, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    return modelo.eval(), prep, open_clip.get_tokenizer("ViT-B-32")


def semantica(clipes: list[Path], frases: dict[str, str], passo: float = 0.5, top: int = 5) -> dict:
    """Para cada frase (descrição em inglês), os melhores trechos: [{clipe, t, nota}]."""
    import torch
    from PIL import Image
    modelo, prep, tok = _clip()
    with torch.no_grad():
        txt = modelo.encode_text(tok(list(frases.values())))
        txt /= txt.norm(dim=-1, keepdim=True)
    registros, embs = [], []
    for c in clipes:
        d = duracao(c)
        tempos = list(np.arange(0.2, max(d - 0.2, 0.3), passo))
        imgs = _quadros(c, tempos)
        if not imgs:
            continue
        lote = torch.stack([prep(Image.fromarray(cv2.cvtColor(i, cv2.COLOR_BGR2RGB))) for _, i in imgs])
        with torch.no_grad():
            e = modelo.encode_image(lote)
            e /= e.norm(dim=-1, keepdim=True)
        embs.append(e)
        registros += [(c.name, round(float(t), 2)) for t, _ in imgs]
    todas = torch.cat(embs)
    notas = (todas @ txt.T).numpy()                      # (quadros, frases)
    saida = {}
    for j, chave in enumerate(frases):
        ordem = np.argsort(-notas[:, j])
        vistos, lista = set(), []
        for i in ordem:
            nome, t = registros[i]
            k = (nome, round(t))                          # evita 5 quadros do mesmo segundo
            if k in vistos:
                continue
            vistos.add(k)
            lista.append({"clipe": nome, "t": t, "nota": round(float(notas[i, j]), 3)})
            if len(lista) == top:
                break
        saida[chave] = lista
    return saida


if __name__ == "__main__":
    import sys
    print(json.dumps(localizar(Path(sys.argv[1]), sys.argv[2], 0, duracao(Path(sys.argv[1])) - 0.1),
                     indent=1))
