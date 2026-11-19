"""DECUPAGEM (o "cérebro de editor" — dono, 19/11): antes de qualquer render, uma folha com CADA cena como ela vai
aparecer — o quadro exato do clipe (início, meio e fim do trecho, já no recorte 9:16), a frase da voz, a parte do
roteiro, a função da cena e os SONS escolhidos (nome do arquivo). Nada é decidido no escuro: o Claude confere a folha
(e o dono pode olhar em 10 s) ANTES dos 30 min de render. Erros que ela pega: cena trocada, tomada errada, som de
outro contexto, repetição, imagem fraca.

Uso: python3 -m viitu.decupagem <projeto>  → projetos/<p>/saida/decupagem.jpg (+ .txt com a lista)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
W, H = 216, 384                                   # quadro 9:16 pequeno


def _quadro(arq: Path, t: float, zoom: float = 1.0, alvo=(0.5, 0.5), inteiro: bool = False) -> np.ndarray:
    cap = cv2.VideoCapture(str(arq))
    cap.set(cv2.CAP_PROP_POS_MSEC, max(t, 0) * 1000)
    ok, img = cap.read()
    cap.release()
    if not ok:
        return np.full((H, W, 3), 40, np.uint8)
    h, w = img.shape[:2]
    if inteiro:                                   # clipe inteiro sobre fundo desfocado
        fundo = cv2.GaussianBlur(cv2.resize(img, (W, H)), (31, 31), 0)
        esc = W / w
        m = cv2.resize(img, (W, int(h * esc)))
        y = (H - m.shape[0]) // 2
        fundo[max(y, 0):max(y, 0) + m.shape[0]] = m[: H - max(y, 0)]
        return fundo
    ch, cw = (h, int(h * 9 / 16)) if w / h > 9 / 16 else (int(w * 16 / 9), w)
    ch, cw = int(ch / zoom), int(cw / zoom)
    cx, cy = int(alvo[0] * w), int(alvo[1] * h)
    x0, y0 = min(max(cx - cw // 2, 0), w - cw), min(max(cy - ch // 2, 0), h - ch)
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (W, H))


def decupar(projeto: str) -> Path:
    pasta = RAIZ / "projetos" / projeto
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    from viitu.montagem import _tempos
    tempos = _tempos(pasta, cfg["cenas"])
    linhas, txt = [], [f"# Decupagem {projeto} — formato {cfg.get('formato')} — música {cfg.get('musica')}"]
    for k, (c, (t0, t1)) in enumerate(zip(cfg["cenas"], tempos)):
        dur = t1 - t0
        if c.get("animacao"):
            tiles = [np.full((H, W, 3), (60, 30, 20), np.uint8)] * 3
            cv2.putText(tiles[1], "3D", (80, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 220, 120), 3)
            sons = [e.get("arquivo") or e.get("busca") for e in c["animacao"].get("sfx", [])]
            ident = f"3D {c['animacao']['nome']}"
        else:
            arq = pasta / "clipes" / c["clipe"]
            usado = dur * float(c.get("velocidade", 1.0))
            z = c.get("zoom", [1.0, 1.0])
            tiles = [_quadro(arq, c.get("inicio", 0) + f * usado, z[0], c.get("alvo", (0.5, 0.5)), c.get("layout") == "inteiro")
                     for f in (0.05, 0.5, 0.95)]
            sons = [f'{Path(str(e.get("arquivo") or e.get("busca"))).name} @{e.get("no_clipe", "SEM INSTANTE")}s' for e in c.get("sfx_cena", [])]
            ident = f"{c['clipe'][:28]} @{c.get('inicio', 0)}s"
        info = np.full((H, 330, 3), 18, np.uint8)
        y = 24
        for t, cor, esc in ((f"{k + 1}. {t0:.1f}-{t1:.1f}s ({dur:.1f}s)  {c.get('_parte', '')}", (0, 215, 255), 0.5),
                            (f"\"{c['em']}...\"", (255, 255, 255), 0.5), (ident, (180, 180, 180), 0.4),
                            (str(c.get("_funcao", ""))[:46], (150, 220, 150), 0.4),
                            (str(c.get("_funcao", ""))[46:92], (150, 220, 150), 0.4)):
            cv2.putText(info, t, (8, y), cv2.FONT_HERSHEY_SIMPLEX, esc, cor, 1)
            y += 26
        cv2.putText(info, "SONS:", (8, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 200, 255), 1)
        for s in sons[:5] or ["(nenhum)"]:
            y += 24
            cv2.putText(info, Path(str(s)).name[-44:], (8, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 255), 1)
        linhas.append(np.hstack(tiles + [info]))
        txt.append(f"{k + 1}. {t0:.1f}-{t1:.1f}s [{c.get('_parte', '')}] \"{c['em']}\" — {ident} — {c.get('_funcao', '')} — sons: {sons}")
    folha = np.vstack(linhas)
    saida = pasta / "saida" / "decupagem.jpg"
    saida.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(saida), folha, [cv2.IMWRITE_JPEG_QUALITY, 82])
    (pasta / "saida" / "decupagem.txt").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))
    print(f"\nDecupagem: {saida.relative_to(RAIZ)} — CONFERIR cada linha antes do render.")
    return saida


if __name__ == "__main__":
    decupar(sys.argv[1])
