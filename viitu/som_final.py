"""PÓS-PRODUÇÃO DE SOM: a mixagem é feita DEPOIS do render, num lugar só (decisão do dono, 18/11).

Antes: o Python planejava o som e o Remotion tocava as camadas; quando os dois discordavam nascia defeito (a trilha
afundava nas pausas) e o Remotion travava com volume por quadro. Agora o Remotion só faz a IMAGEM; aqui:
  1. reconstrói cada camada em 48 kHz a partir do plano (mesma conta de viitu/mixagem._camadas: voz, trilha da
     categoria com fala/pausa e crescimento na virada, foley, ambiente, whoosh nos cortes, sfx de ação e do 3D,
     riser/boom, pop, ding) + o VÁCUO antes do boom;
  2. junta em 3 grupos (stems): VOZ · LEITO (música/foley/ambiente) · EFEITOS (curtos);
  3. mixa como estúdio: sidechain REAL guiado pela voz (leito −10 dB, efeitos leve), voz com passa-alta e compressão
     suave, limitador e loudness −14 LUFS (padrão YouTube);
  4. troca o áudio do mp4 (imagem intacta, sem novo render) e grava os stems em saida/stems/ para conferência.
Remixar leva segundos: ajustar níveis e rodar de novo, sem renderizar a imagem.

Uso: python3 -m viitu.som_final <projeto>        (mp4 em remotion/out/<projeto>.mp4)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from viitu import mixagem as mx

RAIZ = Path(__file__).resolve().parent.parent
SR = 48000
LEITO, FX = mx.LEITO, mx.FX


def _wav(x: np.ndarray, arq: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_f32le", str(arq)], input=np.clip(x, -4, 4).astype(np.float32).tobytes(), check=True)


def _vacuo(plano: dict, n: int) -> np.ndarray:
    """Igual ao Short.tsx: o leito some 10 quadros antes do impacto e volta mais forte depois."""
    g = np.ones(n, np.float32)
    spf = SR / mx.FPS
    for i in plano.get("impactos", []):
        a, b, c = int((i - 10) * spf), int((i - 6) * spf), int(i * spf)
        if a < n:
            g[a:b] = np.minimum(g[a:b], np.linspace(1, 0.05, max(b - a, 1))[: len(g[a:b])])
            g[b:c] = np.minimum(g[b:c], 0.05)
        d, e = int((i + 4) * spf), int((i + 36) * spf)
        if c < n:
            g[c:d] = np.linspace(0.05, 1.35, max(d - c, 1))[: len(g[c:d])]
            g[d:e] = np.linspace(1.35, 1.0, max(e - d, 1))[: len(g[d:e])]
    return g


def _ler(arq: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                       capture_output=True).stdout
    return np.frombuffer(r, np.float32)


def medir(projeto: str, plano: dict) -> dict:
    """SOM MEDIDO (trava objetiva; o Gemini dá notas de 3 a 8,5 para o mesmo arquivo). Nos stems já mixados:
    música audível sob a voz, respira nas pausas, efeitos de ação presentes, impacto na virada, ambiência, nada por
    cima das palavras. Mesmo áudio = mesmo resultado."""
    st = RAIZ / "projetos" / projeto / "saida" / "stems"
    v, l, f = (_ler(st / f"{n}_m.wav") for n in ("voz", "leito", "efeitos"))
    n = min(len(v), len(l), len(f))
    v, l, f = v[:n], l[:n], f[:n]
    w = 1600                                                         # 0,1 s
    db = lambda x: 10 * np.log10(np.mean(x.astype(np.float64) ** 2) + 1e-12)
    jan = lambda x: np.array([db(x[i:i + w]) for i in range(0, n - w, w)])
    V, Lj, F = jan(v), jan(l), jan(f)
    vref = np.median(V[V > np.percentile(V, 40)])
    fala, pausa = V > vref - 10, V < vref - 25
    t = lambda q: min(int(q / mx.FPS * 10), len(V) - 1)              # quadro → janela
    sob = float(np.median(Lj[fala] - vref))
    respira = float(np.median(Lj[pausa]) - np.median(Lj[fala])) if pausa.sum() >= 3 else 0.0
    picos = [float(F[max(t(e["f"]) - 1, 0):t(e["f"]) + 6].max() - vref) for e in plano.get("sfx", [])]
    acao_ok = sum(p >= -12 for p in picos)
    imp = [float(F[t(i):t(i) + 6].max() - vref) for i in plano.get("impactos", [])]
    tapa = float(np.percentile((F - V)[fala], 98))                 # efeito acima da voz em plena fala
    r = {
        "musica_sob_voz_db": (round(sob, 1), -20 <= sob <= -8),
        "musica_respira_db": (round(respira, 1), respira >= 3 or pausa.sum() < 3),
        "efeitos_acao_audiveis": (f"{acao_ok}/{len(picos)}", not picos or acao_ok >= 0.7 * len(picos)),
        "impacto_virada_db": ([round(x, 1) for x in imp], all(x >= -6 for x in imp)),
        "efeito_sobre_voz_db": (round(tapa, 1), tapa <= 0),
    }
    print("SOM MEDIDO:")
    for k, (val, ok) in r.items():
        print(f"  {'✅' if ok else '❌'} {k}: {val}")
    return {k: {"valor": val, "ok": bool(ok)} for k, (val, ok) in r.items()}


def montar(projeto: str) -> dict:
    pasta = RAIZ / "projetos" / projeto
    mp4 = RAIZ / "remotion" / "out" / f"{projeto}.mp4"
    plano = json.loads((mx.PUB / "plano.json").read_text(encoding="utf-8"))
    sr_antigo, mx.SR = mx.SR, SR                         # mesma reconstrução, em qualidade de entrega
    try:
        voz, L = mx._camadas({k: v for k, v in plano.items() if k not in ("duck", "duck_fx")})
    finally:
        mx.SR = sr_antigo
    L.pop("_falando")
    n = int(plano["duracao_frames"] / mx.FPS * SR)
    voz = voz[:n]
    vac = _vacuo(plano, n)
    AMB = 2.0                                           # ambiência/foley +6 dB (ouvido: "ambiência tímida")
    leito = (L["musica"][:n] + AMB * (L["foley"][:n] + L["ambiente"][:n])) * vac
    BOOM = 2.2                                          # riser/boom da virada +7 dB: o "ponto de exclamação" precisa bater
    fx = L["whoosh"][:n] + L["sfx"][:n] + L["marcas"][:n] + BOOM * L["virada"][:n]
    st = pasta / "saida" / "stems"
    st.mkdir(parents=True, exist_ok=True)
    for nome, x in (("voz", voz), ("leito", leito), ("efeitos", fx)):
        _wav(x, st / f"{nome}.wav")

    mix = st / "mix.wav"
    grafo = (
        "[0:a]highpass=f=80,acompressor=threshold=0.125:ratio=2.5:attack=8:release=120:makeup=1.3,asplit=3[v][vk1][vk2];"
        # leito: sidechain real pela voz — abaixa ~10 dB quando a voz fala, sobe nas pausas (soltura 250 ms: sem bombear)
        "[1:a][vk1]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=250:knee=4[l];"
        # efeitos curtos: só encostam (ratio baixo), continuam claros
        "[2:a][vk2]sidechaincompress=threshold=0.08:ratio=2:attack=5:release=150[f];"
        "[l]asplit=2[l1][l2];[f]asplit=2[f1][f2];[v]asplit=2[v1][v2];"
        "[v1][l1][f1]amix=inputs=3:normalize=0,alimiter=limit=0.89:level=false,"
        "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[out]"
    )
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(st / "voz.wav"), "-i", str(st / "leito.wav"),
                    "-i", str(st / "efeitos.wav"), "-filter_complex", grafo, "-map", "[out]", "-c:a", "pcm_s16le",
                    str(mix), "-map", "[v2]", str(st / "voz_m.wav"), "-map", "[l2]", str(st / "leito_m.wav"),
                    "-map", "[f2]", str(st / "efeitos_m.wav")], check=True)
    medidas = medir(projeto, plano)
    tmp = mp4.with_name(f"_{mp4.name}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-i", str(mix), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(tmp)],
                   check=True)
    tmp.replace(mp4)
    db = lambda x: float(10 * np.log10(np.mean(x.astype(np.float64) ** 2) + 1e-12))
    info = {"voz_db": round(db(voz), 1), "leito_db": round(db(leito), 1), "efeitos_db": round(db(fx), 1),
            "mp4": str(mp4.relative_to(RAIZ)), "medidas": medidas}
    (pasta / "saida" / "som_final.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Som final aplicado em {info['mp4']} · stems em {st.relative_to(RAIZ)} · "
          f"voz {info['voz_db']} / leito {info['leito_db']} / efeitos {info['efeitos_db']} dB (antes do sidechain)")
    return info


if __name__ == "__main__":
    montar(sys.argv[1])
