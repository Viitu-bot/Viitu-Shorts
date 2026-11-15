"""Planejador de CONTRASTE entre cenas vizinhas (usar na ESCOLHA das cenas, antes de editar).

Princípio (definido com o dono): o cérebro se acostuma com o que se repete. Cada cena deve ser
diferente da anterior em pelo menos 1 eixo:
  - ESCALA: close ↔ médio ↔ aberto
  - QUANTIDADE: um sujeito ↔ muitos (uma galinha → um monte de galinhas)
  - DIREÇÃO: sujeito/movimento para a esquerda ↔ para a direita (dá para inverter com "espelhar")
  - ENERGIA: parado ↔ em movimento

Uso:
  python -m viitu.contraste <projeto>            relatório
  python -m viitu.contraste <projeto> --aplicar  liga "espelhar" onde a direção repete
Cenas com texto/logo/marca d'água na imagem nunca são espelhadas ("texto_na_imagem": true ou layout inteiro).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from viitu.visao import detectar

RAIZ = Path(__file__).resolve().parent.parent


def perfil(clipe: Path, t: float) -> dict:
    cap = cv2.VideoCapture(str(clipe))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(t * fps), max(total - 8, 0)))
    ok, a = cap.read()
    for _ in range(5):
        ok2, b = cap.read()
    cap.release()
    if not ok:
        return {}
    dets = detectar(a)
    ga = cv2.cvtColor(cv2.resize(a, (256, 144)), cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(cv2.resize(b, (256, 144)), cv2.COLOR_BGR2GRAY) if ok2 else ga
    fluxo = cv2.calcOpticalFlowFarneback(ga, gb, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mov = float(np.linalg.norm(fluxo, axis=2).mean())
    dx = float(fluxo[..., 0].mean())
    area = max((d["caixa"][2] * d["caixa"][3] for d in dets), default=0)
    escala = "close" if area > 0.35 else ("médio" if area > 0.08 else ("aberto" if dets else "?"))
    lado = 0.0
    if dets:
        x, _, w, _ = dets[0]["caixa"]
        lado = (x + w / 2) - 0.5            # sujeito à esquerda (<0) ou direita (>0) do quadro
    direcao = dx if abs(dx) > 0.15 else lado  # movimento manda; se parado, o lado em que está
    return {"n": len(dets), "escala": escala, "mov": round(mov, 2),
            "energia": "ação" if mov > 0.8 else "parado", "direcao": "→" if direcao > 0.03 else ("←" if direcao < -0.03 else "·")}


def analisar(projeto: str, aplicar: bool) -> None:
    pasta = RAIZ / "projetos" / projeto
    arq = pasta / "cenas.json"
    cfg = json.loads(arq.read_text(encoding="utf-8"))
    ant = None
    for i, c in enumerate(cfg["cenas"]):
        clipe = pasta / "clipes" / c["clipe"]
        if clipe.suffix.lower() in (".jpg", ".png"):
            continue
        p = perfil(clipe, c.get("inicio", 0) + 0.8)
        if not p:
            continue
        if c.get("espelhar") and p["direcao"] != "·":
            p["direcao"] = "←" if p["direcao"] == "→" else "→"
        quant = "muitos" if p["n"] >= 3 else ("um" if p["n"] else "—")
        avisos = []
        if ant:
            iguais = [nome for nome, a, b in (("escala", ant["escala"], p["escala"]), ("quantidade", ant["q"], quant),
                                              ("energia", ant["energia"], p["energia"])) if a == b]
            if len(iguais) == 3:
                avisos.append("MONÓTONA: igual à anterior em escala, quantidade e energia → troque a cena")
            if p["direcao"] != "·" and p["direcao"] == ant["direcao"]:
                pode = not (c.get("texto_na_imagem") or c.get("layout") == "inteiro")
                if aplicar and pode:
                    c["espelhar"] = not c.get("espelhar", False)
                    p["direcao"] = "←" if p["direcao"] == "→" else "→"
                    avisos.append("direção repetia → espelhada")
                else:
                    avisos.append("mesma direção da anterior" + (" (sugestão: espelhar)" if pode else ""))
        print(f"{i + 1:>2}. {c['em'][:24]:<24} | {p['escala']:<6} | {quant:<6} | {p['energia']:<6} | {p['direcao']} "
              f"| {'; '.join(avisos)}")
        ant = {**p, "q": quant}
    if aplicar:
        arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    analisar(a.projeto, a.aplicar)
