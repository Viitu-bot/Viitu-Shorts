"""PLANTA DA MONTAGEM: trava automática ANTES do render, feita das reclamações recorrentes do dono.

Cada regra aqui nasceu de uma reclamação real (catálogo completo: edicao/reclamacoes.md). Roda sobre o cenas.json +
palavras.json (tempos reais da voz) e os arquivos dos clipes. Com qualquer ❌ o editor NÃO monta o vídeo.

  R1 REPETIÇÃO   cada arquivo de clipe entra em no máximo 2 cenas (curto ou longo, tanto faz: o dono vê o mesmo
                 avião/cenário e sente repetição). Exceção: a última cena (loop) copia a primeira. Variedade mínima:
                 fontes diferentes ≥ 60% das cenas reais.
  R2 3D EM BLOCO o 3D é a EXPLICAÇÃO: um bloco contínuo só (nenhum clipe real no meio), de 4 s a 45% do vídeo.
                 Clipe real vem ANTES (gancho/contexto) e DEPOIS (prova/virada), nunca cortando o 3D.
  R3 GANCHO      1ª cena = vídeo real (nunca foto, nunca 3D), sujeito grande, clipe ≥ 720p.
  R4 QUALIDADE   todo clipe real ≥ 720 px no lado menor, nítido e com movimento no trecho usado; < 720p só com
                 "baixa_res_ok": "<motivo>" e nunca no gancho.
  R5 FOTO        no máximo 2 fotos, nunca no gancho, nunca seguidas.
  R6 LOOP        a última cena é o mesmo clipe e o mesmo segundo da primeira.
  R7 CENA LONGA  cena real ≥ 4 s sem "manter" vira o mesmo plano parado na tela (o editor divide, mas repete o clipe).

Exceção registrada: "bloco_3d_longo": "<pedido do dono>" no cenas.json (vd008: o dono pediu o tanque aberto em 3D).

Uso: python3 -m viitu.montagem <projeto>       (o editar chama sozinho; --forcar pula a trava, só com aval do dono)
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
FOTO = (".jpg", ".jpeg", ".png", ".webp")
MAX_USOS = 2
MIN_VARIEDADE = 0.6
MIN_RES = 720


def _dimensoes(arq: Path) -> tuple[int, int]:
    s = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True).stdout.strip().split(",")
    try:
        return int(s[0]), int(s[1])
    except (ValueError, IndexError):
        return 0, 0


def _nitidez_movimento(arq: Path, t0: float, dur: float) -> tuple[float, float]:
    """Nitidez (variância do Laplaciano, em 540 px) e movimento médio (diferença entre quadros) no trecho usado."""
    cap = cv2.VideoCapture(str(arq))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    nit, mov, ant = [], [], None
    for k in range(6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((t0 + dur * k / 5) * fps))
        ok, img = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(cv2.resize(img, (540, int(540 * img.shape[0] / img.shape[1]))), cv2.COLOR_BGR2GRAY)
        nit.append(cv2.Laplacian(g, cv2.CV_64F).var())
        if ant is not None and ant.shape == g.shape:
            mov.append(float(np.mean(cv2.absdiff(g, ant))))
        ant = g
    cap.release()
    return (float(np.median(nit)) if nit else 0.0, float(np.mean(mov)) if mov else 0.0)


def _tempos(pasta: Path, cenas: list[dict]) -> list[tuple[float, float]]:
    from viitu.editar import achar_palavra
    palavras = json.loads((pasta / "palavras.json").read_text(encoding="utf-8"))
    ini, ult = [], 0
    for c in cenas:
        i = achar_palavra(palavras, c["em"], ult)
        ult = i
        ini.append(0.0 if not ini else palavras[i]["inicio"])
    fim = palavras[-1]["fim"]
    return [(a, (ini[k + 1] if k + 1 < len(ini) else fim)) for k, a in enumerate(ini)]


def checar(projeto: str) -> tuple[list[str], list[str]]:
    pasta = RAIZ / "projetos" / projeto
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    cenas = cfg["cenas"]
    tempos = _tempos(pasta, cenas)
    total = tempos[-1][1]
    erros, avisos = [], []
    eh_3d = [bool(c.get("animacao")) for c in cenas]
    eh_foto = [c["clipe"].lower().endswith(FOTO) and not eh_3d[k] for k, c in enumerate(cenas)]
    ultima = len(cenas) - 1
    loop_ok = cenas[ultima]["clipe"] == cenas[0]["clipe"]

    # R1 repetição
    usos = defaultdict(list)
    for k, c in enumerate(cenas):
        if eh_3d[k] or (k == ultima and loop_ok):
            continue
        usos[c["clipe"]].append(k + 1)
    for cl, ks in usos.items():
        if len(ks) > MAX_USOS:
            erros.append(f"R1 REPETIÇÃO: {cl} aparece em {len(ks)} cenas ({ks}); máximo {MAX_USOS}. Buscar outra fonte.")
    reais = sum(len(v) for v in usos.values())
    if reais and len(usos) < math.ceil(reais * MIN_VARIEDADE):
        erros.append(f"R1 VARIEDADE: {len(usos)} fontes para {reais} cenas reais (mínimo {math.ceil(reais * MIN_VARIEDADE)}).")

    # R2 3D em bloco único
    idx3d = [k for k, v in enumerate(eh_3d) if v]
    if idx3d:
        blocos = [[idx3d[0]]]
        for k in idx3d[1:]:
            (blocos[-1].append(k) if k == blocos[-1][-1] + 1 else blocos.append([k]))
        if len(blocos) > 1:
            erros.append(f"R2 3D PICOTADO: {len(blocos)} blocos de 3D separados por clipe real "
                         f"(cenas {[[b[0] + 1, b[-1] + 1] for b in blocos]}). A explicação 3D é UM bloco contínuo.")
        dur3d = sum(tempos[k][1] - tempos[k][0] for k in idx3d)
        if dur3d < 4:
            erros.append(f"R2 3D CURTO: {dur3d:.1f} s de 3D; a explicação precisa de ≥ 4 s para ser entendida.")
        if dur3d > 0.45 * total and not cfg.get("bloco_3d_longo"):     # só quando o dono pediu o 3D longo
            erros.append(f"R2 3D DEMAIS: {dur3d:.1f} s ({dur3d / total:.0%}); máximo 45% do vídeo.")
        if 0 in idx3d:
            erros.append("R3 GANCHO EM 3D: o gancho é sempre clipe real.")

    # R3 gancho / R5 fotos
    if eh_foto[0]:
        erros.append("R3 GANCHO COM FOTO: a 1ª cena precisa ser vídeo real em movimento.")
    fotos = [k for k, v in enumerate(eh_foto) if v and not (k == ultima and loop_ok)]
    if len(fotos) > 2:
        erros.append(f"R5 FOTOS DEMAIS: {len(fotos)} (máximo 2).")
    if any(b - a == 1 for a, b in zip(fotos, fotos[1:])):
        erros.append("R5 FOTOS SEGUIDAS: duas fotos em sequência parecem slide.")

    # R6 loop
    if not loop_ok or abs(cenas[ultima].get("inicio", 0) - cenas[0].get("inicio", 0)) > 0.3:
        erros.append("R6 LOOP: a última cena precisa ser o mesmo clipe e o mesmo segundo da primeira.")

    # R4 qualidade + R7 cena longa (por cena real)
    medidos = {}
    for k, c in enumerate(cenas):
        if eh_3d[k] or eh_foto[k] or (k == ultima and loop_ok):
            continue
        arq = pasta / "clipes" / c["clipe"]
        if not arq.exists():
            erros.append(f"R4 ARQUIVO FALTANDO: {c['clipe']} (cena {k + 1}).")
            continue
        w, h = medidos.setdefault(c["clipe"], _dimensoes(arq))
        dur = tempos[k][1] - tempos[k][0]
        lado = min(w, h)
        if lado < MIN_RES:
            msg = f"R4 BAIXA RESOLUÇÃO: {c['clipe']} tem {w}x{h} (cena {k + 1})"
            if k == 0:
                erros.append(msg + " — proibido no gancho.")
            elif not c.get("baixa_res_ok"):
                erros.append(msg + " — trocar ou justificar com \"baixa_res_ok\".")
        nit, mov = _nitidez_movimento(arq, float(c.get("inicio", 0)), max(dur, 0.5))
        if nit < 40:
            erros.append(f"R4 DESFOCADO: cena {k + 1} ({c['clipe']}@{c.get('inicio', 0)}s) nitidez {nit:.0f}.")
        if mov < 1.0 and not c.get("parado_ok"):
            avisos.append(f"R4 PARADO: cena {k + 1} ({c['clipe']}) quase sem movimento ({mov:.1f}); parece foto.")
        if dur >= 4 and not c.get("manter"):
            avisos.append(f"R7 CENA LONGA: cena {k + 1} dura {dur:.1f} s com um clipe só; precisa de ação nova ou outro clipe.")
    return erros, avisos


def main() -> None:
    projeto = [a for a in sys.argv[1:] if not a.startswith("--")][0]
    erros, avisos = checar(projeto)
    print("PLANTA DA MONTAGEM:", "APROVADA ✅" if not erros else f"{len(erros)} erro(s) ❌")
    for e in erros:
        print("  ❌", e)
    for a in avisos:
        print("  ⚠️", a)
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
