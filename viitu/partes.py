"""MONTAGEM PARTE POR PARTE (dono, 20/11: "o vídeo ser feito em partes... várias conferências durante o processo").
Depois do `editar`, cada parte do roteiro (GANCHO, INÍCIO, MEIO, FINAL, CTA, LOOP) é renderizada SOZINHA, em baixa
resolução (rápido), com voz e efeitos. Para cada parte sai:
  saida/partes/<n>_<PARTE>.mp4  — o trecho para o dono assistir no celular, se quiser
  saida/partes/<n>_<PARTE>.jpg  — prancha de 0,2 em 0,2 s com a palavra falada e os sons naquele instante
O Claude confere UMA parte, corrige o cenas.json, re-renderiza SÓ aquela parte e só então passa para a próxima.
O render completo só acontece com todas as partes conferidas (a entrega cobra).

Uso: python3 -m viitu.partes <projeto>            → todas as partes
     python3 -m viitu.partes <projeto> MEIO       → só a parte MEIO (depois de um ajuste)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
FPS = 30


def _partes(pasta: Path, cenas: list[dict]) -> list[tuple[str, float, float, list[int]]]:
    from viitu.montagem import _tempos
    tempos = _tempos(pasta, cenas)
    grupos: list[tuple[str, float, float, list[int]]] = []
    for k, (c, (t0, t1)) in enumerate(zip(cenas, tempos)):
        nome = (c.get("_parte") or "SEM_PARTE").upper()
        if grupos and grupos[-1][0] == nome:
            n, a, _, ks = grupos[-1]
            grupos[-1] = (n, a, t1, ks + [k])
        else:
            grupos.append((nome, t0, t1, [k]))
    return grupos


def _prancha(mp4: Path, t0: float, plano: dict, saida: Path) -> None:
    cap = cv2.VideoCapture(str(mp4))
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) / FPS
    sons = [(s["f"] / FPS, s["som"]) for s in plano.get("sfx", [])]
    cortes = [f / FPS for f in plano.get("cortes", [])]
    ims, t = [], 0.0
    while t < total - 0.02:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, im = cap.read()
        if not ok:
            break
        im = cv2.resize(im, (180, 320))
        ta = t0 + t
        cv2.putText(im, f"{ta:.1f}s", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        pal = next((p["texto"] for p in plano.get("palavras", []) if p["f0"] <= ta * FPS < p["f1"]), "")
        cv2.putText(im, pal[:14], (4, 312), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if any(abs(ta - c) < 0.1 for c in cortes):
            cv2.rectangle(im, (0, 0), (179, 319), (0, 0, 255), 3)          # vermelho = corte aqui
        for m in plano.get("marcas", []):                                # mira verde = onde a seta/círculo aponta
            q = round(ta * FPS)
            if m["f0"] <= q < m["f1"] and m.get("pos"):
                x, yy, r = m["pos"][min(max(q - m["cena_f0"], 0), len(m["pos"]) - 1)]
                c, rr = (int(x / 6), int(yy / 6)), max(int(r / 6), 3)
                cv2.circle(im, c, rr, (0, 255, 0), 1); cv2.line(im, (c[0] - 6, c[1]), (c[0] + 6, c[1]), (0, 255, 0), 1)
                cv2.line(im, (c[0], c[1] - 6), (c[0], c[1] + 6), (0, 255, 0), 1)
        y = 40
        for ts, nome in sons:
            if ta - 0.1 <= ts < ta + 0.1:
                cv2.putText(im, "SOM", (4, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 255, 120), 1)
                cv2.putText(im, Path(nome).stem[:20], (40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 255, 120), 1)
                y += 16
        ims.append(im)
        t += 0.2
    cap.release()
    if not ims:
        return
    while len(ims) % 8:
        ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(str(saida), np.vstack([np.hstack(ims[i:i + 8]) for i in range(0, len(ims), 8)]), [cv2.IMWRITE_JPEG_QUALITY, 80])


def renderizar_partes(projeto: str, so: str | None = None) -> list[Path]:
    pasta = RAIZ / "projetos" / projeto
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    plano = json.loads((RAIZ / "remotion" / "public" / "plano.json").read_text(encoding="utf-8"))
    from viitu.montagem import hash_cenas
    if plano.get("_cenas_hash") and plano["_cenas_hash"] != hash_cenas(cfg):
        sys.exit("❌ o plano é de um cenas.json antigo: rode `python3 -m viitu.editar <p> --remotion` antes")
    dest = pasta / "saida" / "partes"
    dest.mkdir(parents=True, exist_ok=True)
    feitas = []
    for n, (nome, t0, t1, ks) in enumerate(_partes(pasta, cfg["cenas"]), 1):
        if so and nome != so.upper():
            continue
        a, b = round(t0 * FPS), min(round(t1 * FPS) - 1, plano["duracao_frames"] - 1)
        mp4 = dest / f"{n}_{nome}.mp4"
        print(f"→ parte {n} {nome}: {t0:.1f}–{t1:.1f}s (cenas {[k + 1 for k in ks]})", flush=True)
        r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "Short", str(mp4), f"--frames={a}-{b}",
                            "--scale=0.4", "--concurrency=4", "--log=error"], cwd=RAIZ / "remotion", capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"❌ render da parte {nome} falhou:\n{r.stderr[-1500:]}")
        _prancha(mp4, t0, plano, mp4.with_suffix(".jpg"))
        feitas.append(mp4.with_suffix(".jpg"))
        print(f"   prancha: {mp4.with_suffix('.jpg').relative_to(RAIZ)} — CONFERIR antes da próxima parte", flush=True)
    return feitas


if __name__ == "__main__":
    renderizar_partes(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
