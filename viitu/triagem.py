"""TRIAGEM OBRIGATÓRIA de todo clipe que entra no projeto (antes de qualquer escolha de cena).

Para cada clipe de projetos/<p>/clipes/ mede, a cada 0,25 s:
  - tela de encerramento/abertura de TikTok/Reels (fundo escuro sem conteúdo)
  - quadro preto/vazio, desfoque forte, transição/corte interno
Resultado: os TRECHOS UTILIZÁVEIS (contínuos, ≥ 1 s, nítidos, sem tela de app) e uma nota.
Grava projetos/<p>/clipes/triagem.json. O editor só aceita cenas dentro desses trechos e o
/clipes só escolhe a partir deles. Clipe sem trecho utilizável = REPROVADO (não entra no vídeo).

Uso: python -m viitu.triagem <projeto>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
PASSO = 0.25


def _ruim(img) -> str | None:
    from viitu.editar import eh_tela_final
    if eh_tela_final(img):
        return "tela do app"
    g = cv2.cvtColor(cv2.resize(img, (144, 256)), cv2.COLOR_BGR2GRAY)
    if g.mean() < 12:
        return "preto"
    if cv2.Laplacian(g, cv2.CV_64F).var() < 8 and g.std() < 25:
        return "vazio/desfocado"
    return None


def triar_clipe(arq: Path) -> dict:
    cap = cv2.VideoCapture(str(arq))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = n / fps
    marcas, ant = [], None
    t = 0.0
    while t < dur - 0.05:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ok, img = cap.read()
        if not ok:
            break
        motivo = _ruim(img)
        g = cv2.cvtColor(cv2.resize(img, (64, 112)), cv2.COLOR_BGR2GRAY).astype(int)
        corte = ant is not None and np.abs(g - ant).mean() > 45      # troca brusca de plano
        marcas.append((round(t, 2), motivo, corte))
        ant = g
        t += PASSO
    cap.release()
    trechos, ini = [], None
    for i, (t, motivo, corte) in enumerate(marcas):
        if motivo is None and ini is None:
            ini = t
        if ini is not None and (motivo is not None or (corte and t > ini)):
            fim = t - 0.3                                          # folga antes do problema/corte
            if fim - ini >= 1.0:
                trechos.append([round(ini, 2), round(fim, 2)])
            ini = t if motivo is None else None
    if ini is not None and (marcas[-1][0] - ini) >= 1.0:
        trechos.append([round(ini, 2), round(marcas[-1][0], 2)])
    util = sum(b - a for a, b in trechos)
    ruins = sorted({m for _, m, _ in marcas if m})
    nota = "REPROVADO" if not trechos else ("BAIXA RESOLUÇÃO" if min(w, h) < 720 else "OK")
    return {"arquivo": arq.name, "duracao": round(dur, 2), "resolucao": f"{w}x{h}",
            "trechos_utilizaveis": trechos, "segundos_uteis": round(util, 1), "problemas": ruins, "nota": nota}


def triar(projeto: str) -> dict:
    pasta = RAIZ / "projetos" / projeto / "clipes"
    arq_json = pasta / "triagem.json"
    feito = json.loads(arq_json.read_text(encoding="utf-8")) if arq_json.exists() else {}
    for arq in sorted(pasta.iterdir()):
        if arq.suffix.lower() not in (".mp4", ".mov", ".webm", ".mkv") or arq.name in feito:
            continue
        feito[arq.name] = triar_clipe(arq)
        r = feito[arq.name]
        print(f"{r['nota']:<15} {arq.name:<28} {r['resolucao']:<10} úteis {r['segundos_uteis']:>5}s "
              f"trechos {r['trechos_utilizaveis']} {('| ' + ', '.join(r['problemas'])) if r['problemas'] else ''}")
    arq_json.write_text(json.dumps(feito, ensure_ascii=False, indent=1), encoding="utf-8")
    return feito


def dentro(projeto: str, clipe: str, inicio: float, dur: float) -> bool:
    arq = RAIZ / "projetos" / projeto / "clipes" / "triagem.json"
    if not arq.exists() or clipe.lower().endswith((".jpg", ".png")):
        return True
    t = json.loads(arq.read_text(encoding="utf-8")).get(clipe)
    if not t:
        return True
    return any(a - 0.01 <= inicio and inicio + dur <= b + 0.01 for a, b in t["trechos_utilizaveis"])


if __name__ == "__main__":
    triar(sys.argv[1])
