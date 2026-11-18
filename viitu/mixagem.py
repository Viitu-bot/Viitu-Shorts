"""SOUND DESIGN À PROVA DE VOZ: a voz nunca fica coberta.

O Remotion toca ~10 camadas além da voz (música, foley, ambiente, whoosh nos cortes, sons de função, sfx do 3D,
foley de ação, riser/boom da virada, pop das marcas, ding). Aqui a mixagem inteira é SIMULADA a partir do plano,
quadro a quadro, e:
  1. MEDE a margem voz − fundo em cada quadro com fala (RMS de 1/30 s, suavizado);
  2. calcula um DUCKING universal (sidechain): ganho por quadro para todo o fundo ficar ≥ MARGEM dB abaixo da voz
     (ataque rápido, soltura suave), gravado em plano["duck"] — o Short.tsx multiplica TODA camada não-voz por ele;
  3. aplica um RECORTE DE FREQUÊNCIA (−4 dB em 2–4 kHz, onde mora a inteligibilidade da voz) na música, no foley e
     no ambiente, para a voz atravessar o fundo sem precisar abaixar tanto.

Uso (o editor já chama no fim de --remotion):  python3 -m viitu.mixagem [--medir]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
PUB = RAIZ / "remotion" / "public"
SR = 16000                 # suficiente para medir energia
FPS = 30
MARGEM = 10.0              # dB: fundo sempre pelo menos isso abaixo da voz durante a fala
RESERVA = {"voz": 1, "musica_fala": 0.11, "musica_pausa": 0.2, "som_original": 0.35, "whoosh": 0.32,
           "pop": 0.55, "boom": 0.8, "riser": 0.32, "ding": 0.85, "clique": 0.6}
WOOSHES = ["woosh.mp3", "whip.mp3", "woosh2.mp3", "woosh3.mp3"]


def _ler(arq: Path) -> np.ndarray:
    if not arq.exists():
        return np.zeros(0, dtype=np.float32)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def _por(som: np.ndarray, faixa: np.ndarray, ini: int, dur: int | None = None, ganho=1.0, loop=False) -> None:
    if len(som) == 0 or ini >= len(faixa):
        return
    ini = max(ini, 0)
    n = len(faixa) - ini if dur is None else min(dur, len(faixa) - ini)
    if loop:
        som = np.tile(som, int(np.ceil(n / len(som))) + 1)
    n = min(n, len(som))
    g = ganho if np.isscalar(ganho) else ganho[ini:ini + n]
    faixa[ini:ini + n] += som[:n] * g


def _camadas(plano: dict) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    M = lambda c: (plano.get("mix") or {}).get(c, RESERVA.get(c, 0.5))
    n = int(plano["duracao_frames"] / FPS * SR) + SR
    spf = SR / FPS
    fr = lambda f: int(f * spf)
    falando = np.zeros(n, dtype=bool)
    for p in plano["palavras"]:
        falando[fr(p["f0"] - 2):fr(p["f1"] + 2)] = True
    voz = np.zeros(n, np.float32)
    _por(_ler(PUB / "audio.m4a"), voz, 0, ganho=M("voz"))
    L = {k: np.zeros(n, np.float32) for k in ("musica", "foley", "ambiente", "whoosh", "sfx", "virada", "marcas")}
    g_mus = np.where(falando, M("musica_fala"), M("musica_pausa")).astype(np.float32)
    ult = plano["palavras"][-1]["f1"] if plano["palavras"] else plano["duracao_frames"]
    fim = fr(max(plano["duracao_frames"] - 45, ult))           # igual ao Short.tsx
    if fim < n:
        rampa = np.clip(np.arange(n - fim) / (40 * spf), 0, 1)
        g_mus[fim:] = g_mus[fim:] + (M("musica_pausa") * 1.3 - g_mus[fim:]) * rampa
    _por(_ler(PUB / "musica.mp3"), L["musica"], 0, ganho=g_mus, loop=True)
    if plano.get("foley_mix"):
        _por(_ler(PUB / "foley.m4a"), L["foley"], 0, ganho=np.where(falando, 0.85, 1.0).astype(np.float32))
    _por(_ler(PUB / "ambiente.m4a"), L["ambiente"], 0, ganho=M("som_original"))
    kit = plano.get("kit") or {}
    cache: dict[str, np.ndarray] = {}
    le = lambda s: cache.setdefault(s, _ler(PUB / s))
    cortes = [c for i, c in enumerate(plano.get("cortes", [])) if c not in plano.get("impactos", []) and i < len(plano.get("cortes", [])) - 1]
    for k, c in enumerate(cortes):
        lst = kit.get("whoosh_corte") or WOOSHES
        _por(le(lst[k % len(lst)]), L["whoosh"], fr(c - 4), fr(24), M("whoosh"))
    for e in plano.get("sfx", []):
        _por(le(e["som"]), L["sfx"], fr(e["f"]), fr(e.get("dur", 60)), e.get("vol", M("ding")))
    for k, f in enumerate(plano.get("impactos", [])):
        ri = (kit.get("riser_tensao") or ["tensao.mp3"]); bo = (kit.get("impacto_revelacao") or ["boom.mp3"])
        _por(le(ri[k % len(ri)]), L["virada"], fr(f - 50), fr(52), M("riser"))
        prox = next((p["f0"] for p in plano["palavras"] if p["f0"] > f + 4), f + 60)
        dur_b = max(prox - f - 1, 3)
        _por(le(bo[k % len(bo)]), L["virada"], fr(f), fr(min(60, dur_b)), M("boom"))   # igual ao Short.tsx
    for k, m in enumerate(plano.get("marcas", [])):
        po = kit.get("pop_marca") or ["pop.mp3"]
        _por(le(po[k % len(po)]), L["marcas"], fr(m["f0"]), fr(30), M("pop"))
    _por(le("ding.mp3"), L["marcas"], 0, fr(30), M("ding"))
    return voz, L | {"_falando": falando.astype(np.float32)}


def _db_por_quadro(x: np.ndarray, nq: int) -> np.ndarray:
    spf = SR / FPS
    out = np.full(nq, -120.0)
    for q in range(nq):
        a, b = int(q * spf), int((q + 1) * spf)
        seg = x[a:b]
        if len(seg):
            out[q] = 10 * np.log10(np.mean(seg.astype(np.float64) ** 2) + 1e-12)
    return out


def analisar(plano: dict) -> dict:
    voz, L = _camadas(plano)
    falando = L.pop("_falando")
    nq = plano["duracao_frames"]
    v = _db_por_quadro(voz, nq)
    # voz suavizada (sílabas têm buracos): máximo em ±3 quadros
    vs = np.array([v[max(q - 3, 0):q + 4].max() for q in range(nq)])
    fala_q = np.array([falando[int(q * SR / FPS):int((q + 1) * SR / FPS)].mean() > 0.5 for q in range(nq)])
    fala_q &= vs > -50                       # só onde a voz existe de fato
    fundo = sum(L.values())
    b = _db_por_quadro(fundo, nq)
    camadas_db = {k: _db_por_quadro(x, nq) for k, x in L.items()}
    margem = np.where(fala_q, vs - b, 99)
    return {"v": vs, "b": b, "fala": fala_q, "margem": margem, "camadas": camadas_db}


def calcular_duck(a: dict) -> list[float]:
    nq = len(a["margem"])
    precisa = np.where(a["fala"], np.minimum(0, a["margem"] - MARGEM), 0)       # dB a abaixar (≤ 0)
    alvo = 10 ** (precisa / 20)
    # ataque: o ganho já cai 2 quadros antes; soltura: volta em ~8 quadros
    g = np.ones(nq)
    for q in range(nq):
        g[q] = min(alvo[max(q - 2, 0):q + 3])
    out = np.ones(nq)
    for q in range(nq):
        prev = out[q - 1] if q else 1.0
        out[q] = g[q] if g[q] < prev else min(g[q], prev + 0.12)
    return [round(float(max(x, 0.03)), 3) for x in out]


def relatorio(a: dict, titulo: str) -> str:
    m = a["margem"][a["fala"]]
    if not len(m):
        return f"{titulo}: sem fala"
    ruins = int((m < MARGEM).sum())
    pior = int(np.argmin(np.where(a["fala"], a["margem"], 99)))
    culp = max(a["camadas"], key=lambda k: a["camadas"][k][pior])
    return (f"{titulo}: margem voz−fundo mediana {np.median(m):.1f} dB · pior {m.min():.1f} dB "
            f"(em {pior / FPS:.1f}s, culpa: {culp}) · quadros com fala abaixo de {MARGEM:.0f} dB: {ruins}/{len(m)}")


def recortar_frequencia() -> None:
    """−4 dB em 2–4 kHz na música, foley e ambiente (uma vez por geração do editor)."""
    for nome in ("musica.mp3", "foley.m4a", "ambiente.m4a"):
        arq = PUB / nome
        if not arq.exists():
            continue
        tmp = arq.with_name("_eq_" + nome)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(arq), "-af",
                        "equalizer=f=3000:t=q:w=1.0:g=-4,equalizer=f=1200:t=q:w=1.2:g=-1.5", str(tmp)], check=True)
        tmp.replace(arq)


def assar_duck(plano: dict) -> None:
    """Grava o duck DENTRO das faixas contínuas (música, foley, ambiente) em cópias *_d.m4a.
    Motivo: com o ganho por quadro no Short.tsx, o Remotion monta uma fórmula de volume gigante para o ffmpeg e o
    render falha ("Missing ')' or too many args", vd009 18/11). Os sons curtos seguem com D() no Remotion."""
    sr, n_q = 48000, plano["duracao_frames"]
    duck = np.array(plano["duck"], dtype=np.float32)
    for nome, loop in (("musica.mp3", True), ("foley.m4a", False), ("ambiente.m4a", False)):
        arq = PUB / nome
        if not arq.exists():
            continue
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"],
                             capture_output=True).stdout
        x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()
        n = int(n_q / FPS * sr) + sr
        if len(x) == 0:
            continue
        if loop and len(x) < n:
            x = np.tile(x, (int(np.ceil(n / len(x))), 1))
        t = np.arange(len(x)) / sr * FPS                      # posição em quadros
        g = np.interp(t, np.arange(len(duck)) + 0.5, duck, left=duck[0], right=1.0).astype(np.float32)
        y = (x * g[:, None]).astype(np.float32)
        destino = PUB / (arq.stem + "_d.m4a")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", "-",
                        "-c:a", "aac", "-b:a", "192k", str(destino)], input=y.tobytes(), check=True)
    plano["duck_assado"] = True


def aplicar(medir_so: bool = False) -> str:
    arq = PUB / "plano.json"
    plano = json.loads(arq.read_text(encoding="utf-8"))
    plano.pop("duck", None)
    if not medir_so and not plano.get("eq_aplicado"):
        recortar_frequencia()
        plano["eq_aplicado"] = True
    antes = analisar(plano)
    txt = [relatorio(antes, "ANTES do ducking")]
    if not medir_so:
        plano["duck"] = calcular_duck(antes)
        assar_duck(plano)
        arq.write_text(json.dumps(plano, ensure_ascii=False), encoding="utf-8")
        # medição do resultado: o fundo inteiro multiplicado pelo duck
        g = np.repeat(np.array(plano["duck"]), int(np.ceil(SR / FPS)))[: int(plano["duracao_frames"] / FPS * SR) + SR]
        voz, L = _camadas(plano)
        L.pop("_falando")
        g = np.pad(g, (0, max(0, len(voz) - len(g))), constant_values=1.0)[: len(voz)]
        depois = {**antes, "b": _db_por_quadro(sum(L.values()) * g, plano["duracao_frames"])}
        depois["margem"] = np.where(antes["fala"], antes["v"] - depois["b"], 99)
        depois["camadas"] = {k: _db_por_quadro(x * g, plano["duracao_frames"]) for k, x in L.items()}
        txt.append(relatorio(depois, "DEPOIS do ducking"))
    print("\n".join(txt))
    return "\n".join(txt)


if __name__ == "__main__":
    aplicar("--medir" in sys.argv)
