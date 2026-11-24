"""Visão: assiste os clipes candidatos e mede o que importa para a retenção.

Para cada clipe, amostra quadros ao longo do vídeo inteiro e calcula:
  - nitidez (descarta trechos desfocados)
  - movimento (descarta cena parada; ação prende o olho)
  - onde está o sujeito (animal/pessoa) em cada momento, com o detector YOLO
Gera uma prancha com os quadros + caixas do sujeito, para revisão visual.

Uso:
  python -m viitu.visao candidatos "goat eating" "goat face" -n 10 --saida <pasta>
      busca no Pixabay, baixa a versão leve de cada vídeo, analisa e ranqueia
  python -m viitu.visao clipe projetos/vd002/clipes/pixabay_123.mp4
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import requests

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "assets" / "modelos" / "yolo11n.onnx"
CLASSES = ("person,bicycle,car,motorcycle,airplane,bus,train,truck,boat,traffic light,fire hydrant,"
           "stop sign,parking meter,bench,bird,cat,dog,horse,sheep,cow,elephant,bear,zebra,giraffe,"
           "backpack,umbrella,handbag,tie,suitcase,frisbee,skis,snowboard,sports ball,kite,baseball bat,"
           "baseball glove,skateboard,surfboard,tennis racket,bottle,wine glass,cup,fork,knife,spoon,bowl,"
           "banana,apple,sandwich,orange,broccoli,carrot,hot dog,pizza,donut,cake,chair,couch,potted plant,"
           "bed,dining table,toilet,tv,laptop,mouse,remote,keyboard,cell phone,microwave,oven,toaster,sink,"
           "refrigerator,book,clock,vase,scissors,teddy bear,hair drier,toothbrush").split(",")
SUJEITOS = {"person", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}

_rede = None


def _net():
    global _rede
    if _rede is None:
        _rede = cv2.dnn.readNetFromONNX(str(MODELO))
    return _rede


def detectar(img: np.ndarray, conf_min: float = 0.3) -> list[dict]:
    """Retorna [{classe, conf, caixa:(x,y,w,h) normalizada 0–1}] dos sujeitos no quadro."""
    h, w = img.shape[:2]
    lado = max(h, w)
    quad = np.zeros((lado, lado, 3), np.uint8)
    quad[:h, :w] = img
    blob = cv2.dnn.blobFromImage(quad, 1 / 255, (640, 640), swapRB=True)
    net = _net()
    net.setInput(blob)
    out = net.forward()[0].T                      # (8400, 84)
    scores = out[:, 4:]
    cls = scores.argmax(1)
    conf = scores.max(1)
    ok = conf > conf_min
    caixas, confs, ids = [], [], []
    esc = lado / 640
    for (cx, cy, bw, bh), c, k in zip(out[ok, :4], conf[ok], cls[ok]):
        if CLASSES[k] not in SUJEITOS:
            continue
        caixas.append([int((cx - bw / 2) * esc), int((cy - bh / 2) * esc), int(bw * esc), int(bh * esc)])
        confs.append(float(c))
        ids.append(int(k))
    res = []
    for i in cv2.dnn.NMSBoxes(caixas, confs, conf_min, 0.45):
        i = int(np.array(i).flatten()[0])
        x, y, bw, bh = caixas[i]
        res.append({"classe": CLASSES[ids[i]], "conf": round(confs[i], 2),
                    "caixa": [round(x / w, 3), round(y / h, 3), round(bw / w, 3), round(bh / h, 3)]})
    return sorted(res, key=lambda r: -r["caixa"][2] * r["caixa"][3])


def analisar(caminho: Path, amostras: int = 8) -> dict:
    cap = cv2.VideoCapture(str(caminho))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = total / fps if total else 0
    quadros = []
    for k in range(amostras):
        t = dur * (k + 0.5) / amostras
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ok, a = cap.read()
        if not ok:
            continue
        # quadro ~0,2 s depois, para medir movimento
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((t + 0.2) * fps))
        ok2, b = cap.read()
        pa = cv2.cvtColor(cv2.resize(a, (320, 180)), cv2.COLOR_BGR2GRAY)
        nit = float(cv2.Laplacian(pa, cv2.CV_64F).var())
        mov = float(np.abs(pa.astype(int) - cv2.cvtColor(cv2.resize(b, (320, 180)), cv2.COLOR_BGR2GRAY)
                           .astype(int)).mean()) if ok2 else 0.0
        det = detectar(a)
        quadros.append({"t": round(t, 2), "nitidez": round(nit), "movimento": round(mov, 1),
                        "sujeito": det[0] if det else None, "img": a})
    cap.release()
    com_sujeito = [q for q in quadros if q["sujeito"]]
    nit_med = float(np.median([q["nitidez"] for q in quadros])) if quadros else 0
    mov_med = float(np.median([q["movimento"] for q in quadros])) if quadros else 0
    tam = float(np.median([q["sujeito"]["caixa"][2] * q["sujeito"]["caixa"][3] for q in com_sujeito])) \
        if com_sujeito else 0
    # nota 0–10: nitidez + movimento (sem exagero) + sujeito presente e grande
    nota = (min(nit_med / 150, 1) * 3 + min(mov_med / 6, 1) * 3
            + (len(com_sujeito) / max(len(quadros), 1)) * 2 + min(tam / 0.25, 1) * 2)
    return {"arquivo": str(caminho), "duracao": round(dur, 1), "nota": round(nota, 1),
            "nitidez": round(nit_med), "movimento": round(mov_med, 1),
            "sujeito_pct": round(100 * len(com_sujeito) / max(len(quadros), 1)),
            "quadros": quadros}


def prancha(an: dict, rotulo: str, destino: Path) -> None:
    """Uma linha de quadros com a caixa do sujeito desenhada."""
    tiles = []
    for q in an["quadros"]:
        img = cv2.resize(q["img"], (240, 135))
        if q["sujeito"]:
            x, y, w, h = q["sujeito"]["caixa"]
            cv2.rectangle(img, (int(x * 240), int(y * 135)), (int((x + w) * 240), int((y + h) * 135)),
                          (0, 255, 0), 2)
        cv2.putText(img, f"{q['t']}s", (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        tiles.append(img)
    while len(tiles) < 8:
        tiles.append(np.zeros((135, 240, 3), np.uint8))
    linha = np.hstack(tiles[:8])
    faixa = np.zeros((22, linha.shape[1], 3), np.uint8)
    cv2.putText(faixa, f"{rotulo} | nota {an['nota']} | nit {an['nitidez']} | mov {an['movimento']} | "
                f"sujeito {an['sujeito_pct']}% | {an['duracao']}s", (4, 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imwrite(str(destino), np.vstack([faixa, linha]))


def _pixabay_chave() -> str:
    import os
    if os.environ.get("PIXABAY_API_KEY"):  # variável do ambiente da nuvem (configurações)
        return os.environ["PIXABAY_API_KEY"]
    env = RAIZ / ".env"
    if env.exists():
        for l in env.read_text(encoding="utf-8").splitlines():
            if l.startswith("PIXABAY_API_KEY="):
                return l.split("=", 1)[1].strip()
    raise SystemExit("Falta PIXABAY_API_KEY (variável do ambiente ou .env)")


def candidatos(termos: list[str], n: int, saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    chave = _pixabay_chave()
    resultados = []
    for termo in termos:
        hits = requests.get("https://pixabay.com/api/videos/", timeout=30,
                            params={"key": chave, "q": termo, "per_page": max(n, 3)}).json().get("hits", [])
        for h in hits[:n]:
            arq = saida / f"leve_{h['id']}.mp4"
            if not arq.exists():
                v = h["videos"].get("tiny") or h["videos"]["small"]
                arq.write_bytes(requests.get(v["url"], timeout=120).content)
            an = analisar(arq)
            an.update(id=h["id"], termo=termo, tags=h.get("tags", ""))
            prancha(an, f"{termo} #{h['id']}", saida / f"prancha_{h['id']}.jpg")
            resultados.append(an)
            print(f"  {an['nota']:>4} | {termo:<20} | #{h['id']:<8} | nit {an['nitidez']:>4} | "
                  f"mov {an['movimento']:>4} | sujeito {an['sujeito_pct']:>3}% | {an['duracao']}s")
    for r in resultados:
        for q in r["quadros"]:
            q.pop("img", None)
    (saida / "analise.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    c = sub.add_parser("candidatos")
    c.add_argument("termos", nargs="+")
    c.add_argument("-n", type=int, default=8)
    c.add_argument("--saida", required=True)
    k = sub.add_parser("clipe")
    k.add_argument("arquivo")
    a = p.parse_args()
    if a.modo == "candidatos":
        candidatos(a.termos, a.n, Path(a.saida))
    else:
        an = analisar(Path(a.arquivo))
        for q in an["quadros"]:
            q.pop("img")
        print(json.dumps(an, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
