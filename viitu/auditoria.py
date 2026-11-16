"""Auditoria técnica do vídeo final: medições objetivas + crítica do Gemini comparando com o Hall da Fama.

Uso: python -m viitu.auditoria <projeto> <video.mp4>
Gera projetos/<p>/saida/auditoria.md
Medições: loudness, picos, voz x trilha, brilho por segundo (cenas escuras), movimento nos 2 primeiros
segundos, duração de cenas (curtas/longas demais), palavras muito rápidas na legenda, silêncio no fim (loop),
resolução das fontes.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent


def _lufs(arq: str, extra: list[str] | None = None) -> float | None:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", arq, *(extra or []), "-af", "ebur128=framelog=quiet",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    return float(m[-1]) if m else None


def medir(projeto: str, video: str) -> list[str]:
    pasta = RAIZ / "projetos" / projeto
    plano = json.loads((RAIZ / "remotion" / "public" / "plano.json").read_text(encoding="utf-8"))
    tri = json.loads((pasta / "clipes" / "triagem.json").read_text(encoding="utf-8")) if (pasta / "clipes" / "triagem.json").exists() else {}
    fps = plano["fps"]
    A = []
    lu = _lufs(video)
    A.append(f"{'✅' if lu and -15.5 <= lu <= -13 else '⚠️'} Loudness {lu} LUFS (alvo −14)")
    voz = _lufs(str(RAIZ / "remotion" / "public" / "audio.m4a"))
    mus = _lufs(str(RAIZ / "remotion" / "public" / "musica.mp3"))
    if voz and mus:
        dif = voz - (mus + 20 * np.log10(0.11))
        A.append(f"{'✅' if dif >= 15 else '⚠️'} Voz {dif:.0f} dB acima da trilha sob a fala (alvo ≥ 15 dB)")
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    brilhos, movs, ant = [], [], None
    for f in range(0, n, fps // 2):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, img = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(img, (90, 160)), cv2.COLOR_BGR2GRAY)
        brilhos.append((f / fps, float(g.mean())))
        if ant is not None:
            movs.append((f / fps, float(np.abs(g.astype(int) - ant).mean())))
        ant = g.astype(int)
    cap.release()
    escuros = [t for t, b in brilhos if b < 35]
    A.append(f"{'✅' if len(escuros) <= 2 else '⚠️'} Quadros muito escuros: {len(escuros)} (em {', '.join(f'{t:.1f}s' for t in escuros[:8])})")
    mov0 = np.mean([m for t, m in movs if t <= 2]) if movs else 0
    A.append(f"{'✅' if mov0 > 4 else '⚠️'} Movimento nos 2 primeiros segundos: {mov0:.1f} (gancho precisa de ação)")
    cortes = [0] + plano["cortes"] + [plano["duracao_frames"]]
    durs = [(b - a) / fps for a, b in zip(cortes, cortes[1:])]
    curtas = [round(d, 2) for d in durs if d < 0.9]
    longas = [round(d, 2) for d in durs if d > 3.5]
    A.append(f"{'✅' if not curtas else '⚠️'} Cenas curtas demais (<0,9 s, piscam): {curtas or 'nenhuma'}")
    A.append(f"{'✅' if not longas else '⚠️'} Cenas longas (>3,5 s, risco de tédio): {longas or 'nenhuma'}")
    rap = [p["texto"] for p in plano["palavras"] if p["texto"] and (p["f1"] - p["f0"]) < 5]
    A.append(f"{'✅' if len(rap) <= 5 else '⚠️'} Palavras que ficam < 0,17 s na tela (ilegíveis): {len(rap)} {rap[:8]}")
    fim = plano["duracao_frames"] - plano["palavras"][-1]["f1"]
    A.append(f"{'✅' if fim <= 6 else '⚠️'} Folga depois da última palavra: {fim / fps:.2f}s (loop pede ≤ 0,2 s)")
    baixa = [k for k, v in tri.items() if v.get("nota") == "BAIXA RESOLUÇÃO"]
    A.append(f"{'✅' if not baixa else '⚠️'} Fontes em baixa resolução (<720p): {baixa or 'nenhuma'}")
    return A


PROMPT_CRITICA = """Você é um editor sênior de YouTube Shorts de curiosidade (canais como 'A vida é uma maravilha',
Zack D. Films). Assista este vídeo do canal Viitu Shorts e faça uma AUDITORIA TÉCNICA honesta, em português.
Padrões dos virais de referência: seta vermelha no frame 0, ~2,5 s por cena, legenda de 1 palavra no
centro-inferior, cena satisfatória no final, CTA simples, som do que está na tela, gancho com ação no 1º segundo.
Responda em JSON: {"nota_0a10": n, "pontos_fortes": [...], "problemas": [{"tempo": "MM:SS", "problema": "...",
"correcao": "..."}], "som": "...", "legenda": "...", "gancho": "...", "ritmo": "...", "prioridades": ["as 3 mudanças
que mais aumentariam a retenção"]}. Seja específico com tempos. Não elogie à toa."""


def auditar(projeto: str, video: str) -> None:
    A = medir(projeto, video)
    try:
        from viitu.assistir import perguntar
        crit = json.loads(perguntar(video, PROMPT_CRITICA))
    except BaseException as e:  # Gemini fora do ar/cota (SystemExit incluído)
        crit = {"erro": str(e)[:200]}
    md = [f"# Auditoria — {projeto}", "", "## Medições", *[f"- {a}" for a in A], "", "## Crítica (Gemini)"]
    if "erro" in crit:
        md.append(f"- indisponível: {crit['erro']}")
    else:
        md.append(f"- Nota: **{crit.get('nota_0a10')}/10**")
        md += [f"- ✅ {p}" for p in crit.get("pontos_fortes", [])]
        md += [f"- ⚠️ {p['tempo']}: {p['problema']} → {p['correcao']}" for p in crit.get("problemas", [])]
        for k in ("som", "legenda", "gancho", "ritmo"):
            md.append(f"- **{k}:** {crit.get(k)}")
        md += ["", "## Prioridades"] + [f"{i + 1}. {p}" for i, p in enumerate(crit.get("prioridades", []))]
    (RAIZ / "projetos" / projeto / "saida" / "auditoria.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    auditar(sys.argv[1], sys.argv[2])
