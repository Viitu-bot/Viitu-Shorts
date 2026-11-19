"""Revisão técnica OBRIGATÓRIA antes de entregar um vídeo ao dono.

Para cada cena do vídeo montado (saida/video_mudo.mp4), olha INÍCIO, MEIO e FIM e verifica:
  - o assunto esperado está na tela? (campo "esperado" ou "sujeito" do cenas.json → OWLv2;
    sem isso, o detector YOLO de animais/pessoas)
  - está enquadrado? (centro do assunto dentro da faixa central e tamanho mínimo)
  - outro elemento domina a imagem? (ex.: a galinha do fundo maior que o galo)
Também conta a repetição de clipes (cada arquivo ≤ 2 cenas, curto ou longo; ver viitu/montagem.py).
Gera saida/revisao.jpg (3 quadros por cena, com os problemas escritos) e saida/revisao.json.

Uso: python -m viitu.revisar <projeto>
Saída com código 1 se houver problema (não entregar).
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
FPS = 30
MAX_ANCORA, MAX_OUTROS = 4, 1
RIGOROSO = "--rigoroso" in sys.argv     # padrão: 1 quadro por cena (rede de segurança, não o critério)


def _quadro(cap, f):
    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, img = cap.read()
    return img if ok else None


def _owl(img, texto):
    import torch
    from PIL import Image
    from viitu.inteligencia import _owl as carregar
    proc, modelo = carregar()
    h, w = img.shape[:2]
    ent = proc(text=[[texto]], images=Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)), return_tensors="pt")
    with torch.no_grad():
        out = modelo(**ent)
    lado = max(h, w)
    r = proc.post_process_grounded_object_detection(out, threshold=0.06, target_sizes=torch.tensor([[lado, lado]]))[0]
    caixas = [(float(s), [float(v) for v in b]) for s, b in zip(r["scores"], r["boxes"])]
    if not caixas:
        return None
    s, (x0, y0, x1, y1) = max(caixas)
    return {"conf": s, "x": x0 / w, "y": y0 / h, "w": (x1 - x0) / w, "h": (y1 - y0) / h}


def revisar(projeto: str) -> bool:
    pasta = RAIZ / "projetos" / projeto
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    plano = json.loads((RAIZ / "remotion" / "public" / "plano.json").read_text(encoding="utf-8"))
    video = pasta / "saida" / "video_mudo.mp4"
    cap = cv2.VideoCapture(str(video))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cortes = [0] + plano["cortes"] + [total]
    cenas = cfg["cenas"]

    from viitu.visao import detectar
    problemas, linhas = [], []
    # mapeia cada corte para a cena do cenas.json (cenas divididas repetem o mesmo item)
    from viitu.editar import achar_palavra
    palavras = json.loads((pasta / "palavras.json").read_text(encoding="utf-8"))
    inicios, ult = [], 0
    for c in cenas:
        i = achar_palavra(palavras, c["em"], ult)
        ult = i
        inicios.append(0 if not inicios else round(palavras[i]["inicio"] * FPS))

    # repetição = o MESMO trecho do mesmo clipe (inícios a menos de 3 s); trechos diferentes de um
    # clipe rico não são repetição. Exceção: a última cena pode repetir a primeira (loop).
    vistos = []
    for j, c in enumerate(cenas):
        t = c.get("inicio", 0)
        if c.get("animacao"):          # clipe escondido atrás da animação: não conta como repetição
            continue
        if c["clipe"].lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            # foto: o "trecho" é o enquadramento; outro foco/zoom = outra imagem (máx. 2 usos por foto)
            t = (tuple(c.get("foco", [])), tuple(c.get("zoom", [])))
            usos = sum(1 for o in cenas[:j] if o["clipe"] == c["clipe"])
            if usos >= 2 and j != len(cenas) - 1:     # a última cena (loop) copia a primeira de propósito
                problemas.append(f"REPETIÇÃO: foto {c['clipe']} usada mais de 2 vezes")
            if any(cl == c["clipe"] and tt == t for cl, tt in vistos):
                problemas.append(f"REPETIÇÃO: cena '{c['em']}' repete o mesmo enquadramento de {c['clipe']}")
            vistos.append((c["clipe"], t))
            continue
        rep = [k for k, (cl, tt) in enumerate(vistos) if cl == c["clipe"] and abs(tt - t) < 3]
        if rep and not (j == len(cenas) - 1 and rep == [0]):
            problemas.append(f"REPETIÇÃO: cena '{c['em']}' repete o trecho {c['clipe']}@{t}s")
        vistos.append((c["clipe"], t))
    # REGRA DO DONO: clipe curto (< 60 s) entra no máximo 2 vezes no vídeo (trechos diferentes ainda cansam);
    # bruto longo conta cenas a mais de 10 s de distância como clipes diferentes. A última cena (loop) não conta.
    import collections
    usos = collections.defaultdict(list)
    for j, c in enumerate(cenas):
        if c.get("animacao") or (j == len(cenas) - 1 and c["clipe"] == cenas[0]["clipe"]):
            continue
        usos[c["clipe"]].append(c.get("inicio", 0))
    usos.pop(cfg.get("bruto_cronologico"), None)      # bruto cronológico: cada cena é uma etapa nova (montagem R1 confere a ordem)
    for cl, ts in usos.items():
        arq = pasta / "clipes" / cl
        dur_cl = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                       str(arq)], capture_output=True, text=True).stdout.strip() or 0) if arq.exists() else 0
        grupos = len(ts)       # dono (18/11): bruto longo também cansa — 7 cenas do mesmo avião = repetição
        if grupos > 2:
            problemas.append(f"CLIPE REPETIDO: {cl} aparece em {grupos} cenas (máx. 2) — troque por outro clipe ou 3D")

    for k in range(len(cortes) - 1):
        f0, f1 = cortes[k], cortes[k + 1]
        idx = max(i for i, s in enumerate(inicios) if s <= f0 + 1)
        cena = cenas[idx]
        esperado = cena.get("esperado") or cena.get("sujeito")
        if cena.get("revisao") == "manual":     # conferida a olho (detector não serve p/ esse plano)
            esperado = None
        tiles, notas = [], []
        quadros = (f0 + 2, (f0 + f1) // 2, f1 - 3) if RIGOROSO else ((f0 + f1) // 2,)
        for f in quadros:
            img = _quadro(cap, max(min(f, total - 1), 0))
            if img is None:
                continue
            h, w = img.shape[:2]
            if esperado and not cena.get("layout") == "inteiro":
                d = _owl(img, esperado)
                ok_txt = esperado
            else:
                dd = detectar(img)
                d = None if not dd else {"conf": dd[0]["conf"], "x": dd[0]["caixa"][0], "y": dd[0]["caixa"][1],
                                         "w": dd[0]["caixa"][2], "h": dd[0]["caixa"][3]}
                if dd and len(dd) > 1:
                    a0 = dd[0]["caixa"][2] * dd[0]["caixa"][3]
                    a1 = dd[1]["caixa"][2] * dd[1]["caixa"][3]
                ok_txt = "sujeito"
            nota = ""
            if d is None:
                nota = f"sem '{ok_txt}'"
            else:
                cx, cy = d["x"] + d["w"] / 2, d["y"] + d["h"] / 2
                area = d["w"] * d["h"]
                if not (0.15 < cx < 0.85):
                    nota = "fora do centro"
                elif d["x"] < -0.02 or d["x"] + d["w"] > 1.02:
                    nota = "cortado na borda"
                elif area < 0.02 and esperado and "eye" not in esperado and "egg" not in esperado:
                    nota = "pequeno demais"
                cv2.rectangle(img, (int(d["x"] * w), int(d["y"] * h)), (int((d["x"] + d["w"]) * w), int((d["y"] + d["h"]) * h)),
                              (0, 255, 0) if not nota else (0, 0, 255), 6)
            if nota:
                notas.append(nota)
            t = cv2.resize(img, (180, 320))
            cv2.putText(t, f"{f / FPS:.1f}s", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            if nota:
                cv2.putText(t, nota[:22], (4, 312), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1)
            tiles.append(t)
        # problema real só se aparecer em 2 dos 3 quadros (evita falso alarme de 1 quadro)
        if len(notas) >= (2 if RIGOROSO else 1) and cena.get("revisao") != "manual":
            problemas.append(f"CENA {k + 1} ({f0 / FPS:.1f}–{f1 / FPS:.1f}s, '{cena['em']}', {cena['clipe']}): {', '.join(sorted(set(notas)))}")
        faixa = np.zeros((320, 150, 3), np.uint8)
        cv2.putText(faixa, f"cena {k + 1}", (4, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        for j, palavra in enumerate(cena["em"].split()[:6]):
            cv2.putText(faixa, palavra[:14], (4, 50 + 22 * j), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        cv2.putText(faixa, (esperado or "")[:16], (4, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        linhas.append(np.hstack([faixa] + tiles + [np.zeros((320, 180, 3), np.uint8)] * (3 - len(tiles))))
    # varredura QUADRO A QUADRO do vídeo final: nenhuma tela final de TikTok/Reels pode aparecer
    from viitu.editar import eh_tela_final
    for f in range(0, total, 2):
        img = _quadro(cap, f)
        if img is not None and eh_tela_final(img):
            problemas.append(f"TELA FINAL de TikTok/Reels aparece em {f / FPS:.2f}s")
            break
    cap.release()
    # junta em colunas de até 8 linhas para caber numa imagem
    blocos = [np.vstack(linhas[i:i + 8]) for i in range(0, len(linhas), 8)]
    altura = max(b.shape[0] for b in blocos)
    blocos = [np.vstack([b, np.zeros((altura - b.shape[0], b.shape[1], 3), np.uint8)]) for b in blocos]
    cv2.imwrite(str(pasta / "saida" / "revisao.jpg"), np.hstack(blocos))
    (pasta / "saida" / "revisao.json").write_text(json.dumps({"problemas": problemas}, ensure_ascii=False, indent=1),
                                                  encoding="utf-8")
    print("REVISÃO:", "APROVADO ✅" if not problemas else f"{len(problemas)} problema(s) ❌")
    for p in problemas:
        print("  -", p)
    return not problemas


if __name__ == "__main__":
    sys.exit(0 if revisar([a for a in sys.argv[1:] if not a.startswith("--")][0]) else 1)
