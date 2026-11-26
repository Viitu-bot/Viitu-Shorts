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

# cadeias de tratamento da voz (dono escolhe pelo ouvido; edicao/especificacao.json "voz_cadeia")
CADEIA_VOZ = {
    "tratada": "highpass=f=90,equalizer=f=250:t=q:w=1:g=-3,equalizer=f=3200:t=q:w=1.2:g=3,equalizer=f=9000:t=h:w=2000:g=2,"
               "deesser=i=0.4,acompressor=threshold=0.1:ratio=3:attack=5:release=80:makeup=1.6",
    "suave": "afftdn=nr=8:nf=-50,highpass=f=80,equalizer=f=300:t=q:w=1:g=-1.5,equalizer=f=2500:t=q:w=1.5:g=1.5,"
             "acompressor=threshold=0.125:ratio=2:attack=10:release=150:makeup=1.2",
    "natural": "highpass=f=70",
}

RAIZ = Path(__file__).resolve().parent.parent
SR = 48000
LEITO, FX = mx.LEITO, mx.FX


def _wav(x: np.ndarray, arq: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_f32le", str(arq)], input=np.clip(x, -4, 4).astype(np.float32).tobytes(), check=True)


def _filtrar(x: np.ndarray, af: str) -> np.ndarray:
    """Passa um array por um filtro do ffmpeg (mesmo tamanho na volta)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", af,
                        "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    y = np.frombuffer(r, np.float32)
    return np.pad(y, (0, max(len(x) - len(y), 0)))[: len(x)]


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


def pasta_proj(projeto: str) -> Path:
    return RAIZ / "projetos" / projeto


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
    # o efeito inteiro (o pico de som gerado/gravado pode vir depois de 1 s; antes olhava só 0,7 s)
    picos = [float(F[max(t(e["f"]) - 1, 0):max(t(e["f"]) + int(e.get("dur", 30) / mx.FPS * 10), t(e["f"]) + 6)].max() - vref)
             for e in plano.get("sfx", [])]
    acao_ok = sum(p >= -12 for p in picos)
    imp = [float(F[t(i):t(i) + 6].max() - vref) for i in plano.get("impactos", [])]
    tapa = float(np.percentile((F - V)[fala], 98))
    dg = _ler(st / "ding.wav") if (st / "ding.wav").exists() else np.zeros(1600, np.float32)
    dpk = float(max(db(dg[i:i + w]) for i in range(0, 4 * w, w // 2)) - vref)                 # efeito acima da voz em plena fala
    app = str(json.loads((pasta_proj(projeto) / "cenas.json").read_text(encoding="utf-8")).get("musica", "")).startswith("app:")
    r = {
        "musica_sob_voz_db": ("pelo app" if app else round(sob, 1), app or -19 <= sob <= -12),   # dono 24/11: música AUDÍVEL sob a voz (vd017: −17 não dava pra ouvir)       # BÍBLIA §4: audível no celular
        "musica_respira_db": ("pelo app" if app else round(respira, 1), app or respira >= 3 or pausa.sum() < 3),
        "efeitos_acao_audiveis": (f"{acao_ok}/{len(picos)}", not picos or acao_ok >= 0.7 * len(picos)),   # só os que existem
        "impacto_virada_db": ([round(x, 1) for x in imp], all(x >= -8 for x in imp)),   # som B (dono 24/11): virada entre −8 e 0 da voz
        "efeito_sobre_voz_db": (round(tapa, 1), tapa <= 0),
        "ding_frame0_db": (round(dpk, 1), dpk >= -3),                   # BÍBLIA §2: o ding tem que ser OUVIDO
    }
    print("SOM MEDIDO:")
    for k, (val, ok) in r.items():
        print(f"  {'✅' if ok else '❌'} {k}: {val}")
    return {k: {"valor": val, "ok": bool(ok)} for k, (val, ok) in r.items()}


def montar(projeto: str, limpo: bool = False, saida: Path | None = None, previa: bool = False) -> dict:
    """limpo=True: a RECEITA DOS CANAIS ANALISADOS (logica_editor.md) — trilha constante + whoosh nos cortes + riser/boom
    na virada + ding; sem efeito de ação por cena e sem ambiência (os efeitos escolhidos por CLAP "não encaixavam")."""
    pasta = RAIZ / "projetos" / projeto
    mp4 = RAIZ / "remotion" / "out" / f"{projeto}.mp4"
    plano = json.loads((mx.PUB / "plano.json").read_text(encoding="utf-8"))
    ESP = json.loads((RAIZ / "edicao" / "especificacao.json").read_text(encoding="utf-8"))
    MD = ESP["mix_db"]   # níveis MEDIDOS (35 Shorts)
    if limpo:
        plano = {**plano, "sfx": [e for e in plano.get("sfx", []) if False], "foley_mix": False}
    sr_antigo, mx.SR = mx.SR, SR                         # mesma reconstrução, em qualidade de entrega
    try:
        voz, L = mx._camadas({k: v for k, v in plano.items() if k not in ("duck", "duck_fx")})
    finally:
        mx.SR = sr_antigo
    L.pop("_falando")
    n = int(plano["duracao_frames"] / mx.FPS * SR)
    voz = voz[:n]
    vac = _vacuo(plano, n)
    # AUTONIVELAMENTO (vd010, 18/11): cada trilha/efeito da biblioteca tem um volume; nível fixo enterrava a música de um
    # vídeo e deixava a explosão 12 dB acima da voz no outro. Aqui tudo é medido contra a VOZ e levado ao alvo.
    rms = lambda x: float(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-9)
    win = int(SR * 0.1)
    def env(x):                                         # nível por janela de 0,1 s
        m = len(x) // win
        return np.sqrt(np.mean(x[: m * win].reshape(m, win).astype(np.float64) ** 2, axis=1) + 1e-12)
    ev = env(voz)
    vref = float(np.median(ev[ev > np.percentile(ev, 40)]))                 # nível típico da fala
    fala_m = np.repeat(ev > vref * 0.3, win)[:n]
    fala_m = np.pad(fala_m, (0, n - len(fala_m)))
    def para(x, alvo_db, mascara=None):                 # ganho para o nível (onde há som) ficar alvo_db sob a voz
        sel = x if mascara is None else x[mascara]
        sel = sel[np.abs(sel) > 1e-5]
        return 0.0 if len(sel) == 0 else vref * 10 ** (alvo_db / 20) / rms(sel)
    mus = L["musica"][:n] * para(L["musica"][:n], MD["musica_fala"] + 6, fala_m)   # o sidechain tira ~6 dB → trilha em musica_fala (−24) sob a voz
    amb = L["foley"][:n] + L["ambiente"][:n]
    # CHIADO (dono 25/11, vd017): mar/vento/multidão têm ruído até 20 kHz e, sob a voz, soam como chiado/chuva.
    # A ambiência fica só no corpo grave/médio (passa-baixa 3,5 kHz); o brilho é da voz e da música.
    if np.abs(amb).max() > 1e-5:
        amb = _filtrar(amb, "lowpass=f=3500:p=2,lowpass=f=3500:p=2")
    amb = amb * para(amb, MD["ambiencia"] + 6, fala_m)                                         # ambiência presente, abaixo da música
    leito = (mus + (0 if limpo else amb)) * vac
    # efeitos curtos: cada evento normalizado pelo PICO de 0,1 s → −6 dB da voz (claro, sem passar por cima);
    # a virada (riser/boom) até o nível da voz
    spf = SR / mx.FPS
    fx = np.zeros(n, np.float32)
    for e in plano.get("sfx", []):
        a0 = int(e["f"] * spf)
        if a0 >= n:
            continue
        seg = np.zeros(n, np.float32)
        sr_ant, mx.SR = mx.SR, SR
        try:
            mx._por(mx._ler(mx.PUB / e["som"]), seg, a0, int(e.get("dur", 60) * spf))
        finally:
            mx.SR = sr_ant
        pico = env(seg[a0:a0 + int(e.get("dur", 60) * spf)]).max() if seg.any() else 0
        if pico > 0:
            alvo = max(MD["sfx_min"], min(MD["sfx_max"], 20 * np.log10(max(e.get("vol", 0.5), 1e-3)) - 6))   # dono 24/11 (vd016): −8 a −3 da voz
            fx += seg * (vref * 10 ** (alvo / 20) / pico)
    def pico_para(x, alvo_db):
        p = env(x).max() if np.abs(x).max() > 1e-5 else 0
        return 0.0 if p == 0 else vref * 10 ** (alvo_db / 20) / p
    fx += L["whoosh"][:n] * pico_para(L["whoosh"][:n], MD["whoosh"])
    # DING do frame 0 = identidade (BÍBLIA §2): fora do abaixamento, no nível da voz. Os pops ficam nos efeitos.
    din = L["ding"][:n]
    fx += L["marcas"][:n] * pico_para(L["marcas"][:n], MD["pop"])
    din = din * pico_para(din, 0)
    # cada impacto nivelado SOZINHO (dono 25/11: "momento de impacto sem impacto"): com 2+ viradas, o boom mais alto
    # puxava o ganho e os outros ficavam baixos
    vir = L["virada"][:n].copy()
    cortes = sorted(int(i * spf) for i in plano.get("impactos", []))
    lim = [0] + [(a + b) // 2 for a, b in zip(cortes, cortes[1:])] + [n]
    for a, b in zip(lim, lim[1:]):
        vir[a:b] *= pico_para(vir[a:b], MD["boom"])
    fx += vir                                                                     # boom medido: no nível da voz
    st = pasta / "saida" / "stems"
    st.mkdir(parents=True, exist_ok=True)
    for nome, x in (("voz", voz), ("leito", leito), ("efeitos", fx)):
        _wav(x, st / f"{nome}.wav")
    # ABERTURA DO CANAL (dono, 20/11 — opção D): o ding em DOIS toques colados (0,12 s) + eco estéreo que atravessa
    # a cabeça e some em ~1,3 s. Estéreo de verdade (o resto do mix continua igual nos dois lados). No nível da voz.
    ab_arq = RAIZ / "assets" / "sfx" / "abertura_viitu.wav"
    if ab_arq.exists():
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ab_arq), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
        ab = np.frombuffer(r, np.float32).reshape(-1, 2)[:n]
        ab2 = np.zeros((n, 2), np.float32); ab2[: len(ab)] = ab
        ab2 *= pico_para(ab2.mean(1), 0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a",
                        "pcm_f32le", str(st / "ding.wav")], input=np.clip(ab2, -4, 4).astype(np.float32).tobytes(), check=True)
    else:
        _wav(din, st / "ding.wav")

    mix = st / "mix.wav"
    grafo = (
        # VOZ TRATADA (dono 24/11, vd016): tira grave/embolado, dá presença e brilho, segura o "s" e comprime para ficar na frente
        f"[0:a]{CADEIA_VOZ[ESP.get('voz_cadeia', 'suave')]},asplit=3[v][vk1][vk2];"
        # leito: sidechain real pela voz — abaixa ~10 dB quando a voz fala, sobe nas pausas (soltura 250 ms: sem bombear)
        f"[1:a][vk1]sidechaincompress=threshold=0.05:ratio={ESP.get('duck_ratio', 2)}:attack=15:release=250:knee=4[l];"
        # efeitos curtos: só encostam (ratio baixo), continuam claros
        "[2:a][vk2]sidechaincompress=threshold=0.05:ratio=1.5:attack=5:release=150[f];"
        "[l]asplit=2[l1][l2];[f]asplit=2[f1][f2];[v]asplit=2[v1][v2];"
        # saída ESTÉREO (a abertura tem eco esquerda/direita); voz, leito e efeitos iguais nos dois lados
        "[v1]aformat=channel_layouts=stereo[vs];[l1]aformat=channel_layouts=stereo[ls];[f1]aformat=channel_layouts=stereo[fs];"
        "[3:a]aformat=channel_layouts=stereo[ds];"
        "[vs][ls][fs][ds]amix=inputs=4:normalize=0,alimiter=limit=0.89:level=false,"
        "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[out]"
    )
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(st / "voz.wav"), "-i", str(st / "leito.wav"),
                    "-i", str(st / "efeitos.wav"), "-i", str(st / "ding.wav"), "-filter_complex", grafo, "-map", "[out]", "-c:a", "pcm_s16le",
                    str(mix), "-map", "[v2]", str(st / "voz_m.wav"), "-map", "[l2]", str(st / "leito_m.wav"),
                    "-map", "[f2]", str(st / "efeitos_m.wav")], check=True)
    medidas = medir(projeto, plano)
    if previa:
        # PRÉVIA ANTES DO RENDER (dono 26/11: "todo o vídeo deve ser revisado antes de renderizado"): o som final inteiro
        # (voz, música, efeitos, transições) sobre as partes em baixa resolução já renderizadas pelo viitu.partes
        partes = sorted((pasta / "saida" / "partes").glob("[0-9]_*.mp4"))
        lista = pasta / "saida" / "_partes.txt"
        lista.write_text("".join(f"file '{q.resolve()}'\n" for q in partes), encoding="utf-8")
        out = pasta / "saida" / "previa.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(mix),
                        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "28", "-preset", "veryfast", "-c:a", "aac",
                        "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
        lista.unlink()
        info = {"previa": str(out.relative_to(RAIZ)), "medidas": medidas}
        (pasta / "saida" / "som_previa.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"PRÉVIA (antes do render): {info['previa']} — conferir o vídeo inteiro com o som final antes do npm run render")
        return info
    tmp = mp4.with_name(f"_{mp4.name}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-i", str(mix), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(tmp)],
                   check=True)
    if saida:
        tmp.replace(saida)
    else:
        tmp.replace(mp4)
    db = lambda x: float(10 * np.log10(np.mean(x.astype(np.float64) ** 2) + 1e-12))
    info = {"voz_db": round(db(voz), 1), "leito_db": round(db(leito), 1), "efeitos_db": round(db(fx), 1),
            "mp4": str(mp4.relative_to(RAIZ)), "medidas": medidas}
    (pasta / "saida" / "som_final.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Som final aplicado em {info['mp4']} · stems em {st.relative_to(RAIZ)} · "
          f"voz {info['voz_db']} / leito {info['leito_db']} / efeitos {info['efeitos_db']} dB (antes do sidechain)")
    return info


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("projeto"); a.add_argument("--limpo", action="store_true"); a.add_argument("--saida")
    a.add_argument("--previa", action="store_true", help="som final + partes em baixa resolução, ANTES do render")
    x = a.parse_args()
    montar(x.projeto, x.limpo, Path(x.saida) if x.saida else None, x.previa)
