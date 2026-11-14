"""Monta o Short: cortes sincronizados com a voz, 9:16, flash, zoom, SFX e legenda.

Uso:
  python -m viitu.editar <projeto>
Entrada em projetos/<projeto>/:
  voz.mp3, palavras.json (de viitu.voz) e cenas.json (lista de cenas, ver abaixo)
Saída:
  projetos/<projeto>/saida/short_final.mp4   (com legenda)
  projetos/<projeto>/saida/short_base.mp4    (sem legenda, para finalizar no CapCut)
  projetos/<projeto>/saida/legenda.srt

cenas.json:
{
  "cenas": [
    {"em": "Repara", "clipe": "foto.jpg", "foco": [0.5, 0.5], "zoom": [1.0, 1.3]},
    {"em": "quem caça", "clipe": "croc.mp4", "inicio": 2.0},
    {"em": "inclinada", "clipe": "foto.jpg", "efeito": "girar", "angulo": 40},
    {"em": "gira", "clipe": "foto.jpg", "efeito": "desgirar", "angulo": 40}
  ],
  "impacto_em": ["Mas tem um porém"],
  "destaques": ["gato", "crocodilo"]     # palavras da legenda em amarelo (opcional)
}
"em" = trecho da narração onde a cena COMEÇA (procura depois da cena anterior).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
MAX_CENA = 3.2      # cena maior que isso é dividida (regra dos 2–3 s)
FONTES = RAIZ / "assets" / "fontes"
SFX = RAIZ / "assets" / "sfx"


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", t)


def achar_palavra(palavras: list[dict], trecho: str, depois_de: int) -> int:
    alvo = [_norm(x) for x in trecho.split() if _norm(x)]
    nomes = [_norm(p["palavra"]) for p in palavras]
    for i in range(depois_de, len(palavras) - len(alvo) + 1):
        if nomes[i:i + len(alvo)] == alvo:
            return i
    raise SystemExit(f"Não achei '{trecho}' na narração (depois da palavra {depois_de}).")


def montar_linha_do_tempo(palavras: list[dict], cfg: dict, fim_audio: float) -> list[dict]:
    """Converte as cenas em segmentos com início/fim em FRAMES, sempre na borda de uma palavra."""
    segs, ultimo = [], 0
    for c in cfg["cenas"]:
        i = achar_palavra(palavras, c["em"], ultimo)
        ultimo = i
        segs.append({**c, "palavra_i": i, "t0": 0.0 if not segs else palavras[i]["inicio"]})
    for a, b in zip(segs, segs[1:] + [None]):
        a["t1"] = b["t0"] if b else fim_audio

    # divide cenas longas na borda da palavra mais perto do meio (corte seco + punch-in)
    final = []
    for s in segs:
        pendentes = [s]
        while pendentes:
            x = pendentes.pop(0)
            if x["t1"] - x["t0"] <= MAX_CENA or x.get("efeito") or x.get("manter"):
                final.append(x)
                continue
            meio = (x["t0"] + x["t1"]) / 2
            cand = [p["inicio"] for p in palavras if x["t0"] + 1.2 < p["inicio"] < x["t1"] - 1.2]
            if not cand:
                final.append(x)
                continue
            corte = min(cand, key=lambda t: abs(t - meio))
            z = x.get("zoom", [1.0, 1.12])
            a = {**x, "t1": corte}
            b = {**x, "t0": corte, "inicio": x.get("inicio", 0) + (corte - x["t0"]),
                 "zoom": [z[1] + 0.12, z[1] + 0.2], "dividida": True}
            pendentes[:0] = [a, b]
    for s in final:
        s["f0"], s["f1"] = round(s["t0"] * FPS), round(s["t1"] * FPS)
    return [s for s in final if s["f1"] > s["f0"]]


def _lento(s: dict) -> str:
    v = float(s.get("velocidade", 1.0))
    return "" if v == 1.0 else f"setpts=PTS/{v},framerate=fps={FPS}:interp_start=0:interp_end=255,"


def _filtro_cena(s: dict, entrada: str, eh_foto: bool, n_frames: int, primeira: bool) -> str:
    fx, fy = s.get("foco", [0.5, 0.5])
    sx, sy = s.get("alvo", [0.5, 0.5])        # ponto do sujeito dentro do recorte (para o zoom)
    z0, z1 = s.get("zoom", [1.0, 1.12])
    efeito = s.get("efeito")
    if efeito in ("girar", "desgirar"):
        ang = float(s.get("angulo", 40)) * 3.14159265 / 180
        dur = n_frames / FPS
        expr = f"{ang}" if efeito == "girar" else f"{ang}*pow(1-min(t/{dur:.3f}\\,1)\\,2)"
        # fundo borrado + imagem inteira girando por cima (mostra a pupila "torta")
        f = (f"[{entrada}]split=2[bg][fg];"
             f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,"
             f"eq=brightness=-0.15[bgb];"
             f"[fg]scale={int(W * 1.15)}:-2,format=rgba,rotate='{expr}':c=black@0:ow=hypot(iw\\,ih):oh=ow[fgr];"
             f"[bgb][fgr]overlay=(W-w)/2:(H-h)/2:shortest=1,fps={FPS}")
    elif s.get("layout") == "inteiro":
        # clipe inteiro (sem cortar nada, logo/crédito visível) sobre ele mesmo desfocado
        fh = s["_fh"]
        zexpr = f"{z0}+({z1}-{z0})*on/{max(n_frames - 1, 1)}"
        f = (f"[{entrada}]{_lento(s)}split=2[bg][fg];"
             f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:3,"
             f"eq=brightness=0.04:saturation=1.15[bgb];"
             f"[fg]scale={W * 2}:{fh * 2}:flags=lanczos,"
             f"zoompan=z='{zexpr}':x='max(0\\,min(iw-iw/zoom\\,iw*{sx}-iw/zoom/2))'"
             f":y='max(0\\,min(ih-ih/zoom\\,ih*{sy}-ih/zoom/2))':d=1:s={W}x{fh}:fps={FPS}[fgz];"
             f"[bgb][fgz]overlay=0:{(H - fh) // 2}:shortest=1,fps={FPS}")
    else:
        # recorte 9:16 no ponto de foco, depois zoom suave (Ken Burns) com zoompan
        crop = (f"crop='min(iw\\,ih*{W}/{H})':'min(ih\\,iw*{H}/{W})':"
                f"'(iw-min(iw\\,ih*{W}/{H}))*{fx}':'(ih-min(ih\\,iw*{H}/{W}))*{fy}'")
        zexpr = f"{z0}+({z1}-{z0})*on/{max(n_frames - 1, 1)}"
        f = (f"[{entrada}]{_lento(s)}{crop},scale={W * 2}:{H * 2}:flags=lanczos,"
             f"zoompan=z='{zexpr}':x='max(0\\,min(iw-iw/zoom\\,iw*{sx}-iw/zoom/2))'"
             f":y='max(0\\,min(ih-ih/zoom\\,ih*{sy}-ih/zoom/2))':d=1:s={W}x{H}:fps={FPS}")
    f += ",vignette=PI/5,setsar=1,format=yuv420p"     # bordas escuras guiam o olhar
    if not primeira:
        f += ",fade=t=in:st=0:d=0.12:color=white"   # flash nos cortes
    return f + "[v]"


def _para_tela(s: dict, ex: float, ey: float, z: float, iw: float, ih: float) -> tuple[float, float, float]:
    """Converte ponto (0–1 no clipe original) para pixels na tela 1080x1920. Retorna (x, y, escala)."""
    sx, sy = s.get("alvo", [0.5, 0.5])
    j = 1 / z
    if s.get("layout") == "inteiro":
        fh = s["_fh"]
        x0 = min(max(sx - j / 2, 0), 1 - j)
        y0 = min(max(sy - j / 2, 0), 1 - j)
        return (ex - x0) / j * W, (H - fh) / 2 + (ey - y0) / j * fh, W / j
    fx, fy = s.get("foco", [0.5, 0.5])
    cw = min(1.0, ih * W / H / iw)
    ch = min(1.0, iw * H / W / ih)
    cx0, cy0 = (1 - cw) * fx, (1 - ch) * fy
    px, py = (ex - cx0) / cw, (ey - cy0) / ch
    x0 = min(max(sx - j / 2, 0), 1 - j)
    y0 = min(max(sy - j / 2, 0), 1 - j)
    return (px - x0) / j * W, (py - y0) / j * H, W / cw / j


def marca_que_segue(s: dict, clipe: Path, n: int, pasta: Path, idx: int) -> Path | None:
    """Localiza o objeto descrito (OWLv2), rastreia e desenha o círculo animado em cima dele."""
    import cv2
    from viitu.animacao import circulo_animado
    from viitu.inteligencia import localizar
    m = s["marca_auto"]
    vel = float(s.get("velocidade", 1.0))
    t0 = s.get("inicio", 0)
    t1 = t0 + n / FPS * vel
    pontos = localizar(clipe, m["texto"], t0, t1, passos=max(4, min(10, int((t1 - t0) * 3) + 2)))
    if not pontos:
        print(f"    aviso: não achei '{m['texto']}' em {clipe.name}")
        return None
    cap = cv2.VideoCapture(str(clipe))
    iw, ih = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    cap.release()
    ts = [p["t"] for p in pontos]
    z0, z1 = s.get("zoom", [1.0, 1.12])
    pos = []
    for i in range(n):
        t = t0 + i / FPS * vel
        cx = float(np.interp(t, ts, [p["x"] + p["w"] / 2 for p in pontos]))
        cy = float(np.interp(t, ts, [p["y"] + p["h"] / 2 for p in pontos]))
        tam = float(np.interp(t, ts, [max(p["w"], p["h"] * ih / iw) for p in pontos]))
        z = z0 + (z1 - z0) * i / max(n - 1, 1)
        x, y, esc = _para_tela(s, cx, cy, z, iw, ih)
        pos.append((x, y, min(max(tam * esc * 0.62, 70), 320)))
    # suaviza o tremido da detecção (média móvel)
    k = 7
    xs = np.convolve([p[0] for p in pos], np.ones(k) / k, mode="same")
    ys = np.convolve([p[1] for p in pos], np.ones(k) / k, mode="same")
    for i in range(min(k // 2, n)):
        xs[i], ys[i] = pos[i][0], pos[i][1]
        xs[-1 - i], ys[-1 - i] = pos[-1 - i][0], pos[-1 - i][1]
    pos = [(float(a), float(b), p[2]) for a, b, p in zip(xs, ys, pos)]
    saida = pasta / "saida" / "cenas" / f"{idx:03d}_marca.mov"
    return circulo_animado(pos, saida, atraso_frames=int(m.get("atraso", 0.15) * FPS))


def enquadrar_por_texto(s: dict, clipe: Path, n_frames: int) -> bool:
    """Enquadra no objeto descrito (ex.: 'the head of a goat') com OWLv2. Mais preciso que o YOLO
    quando o importante é uma parte do animal (cabeça, olho) e não o corpo inteiro."""
    import cv2
    from viitu.inteligencia import localizar
    t0 = s.get("inicio", 0)
    t1 = t0 + n_frames / FPS * float(s.get("velocidade", 1.0))
    pts = localizar(clipe, s["sujeito"], t0, t1, passos=3)
    if not pts:
        print(f"    aviso: não achei '{s['sujeito']}' em {clipe.name}; usando YOLO")
        return False
    cap = cv2.VideoCapture(str(clipe))
    iw, ih = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    cap.release()
    cx = sum(p["x"] + p["w"] / 2 for p in pts) / len(pts)
    cy = sum(p["y"] + p["h"] / 2 for p in pts) / len(pts)
    h = sum(p["h"] for p in pts) / len(pts)
    if "eye" in s["sujeito"]:
        h = h * 4          # a cabeça tem ~4x a altura do olho
    cw = min(iw, ih * W / H) / iw
    fx = min(max((cx - cw / 2) / (1 - cw), 0), 1) if cw < 1 else 0.5
    x0 = fx * (1 - cw)
    s.setdefault("foco", [round(fx, 3), 0.5])
    # cabeça um pouco acima do centro (regra dos terços: olhos na linha de cima)
    s.setdefault("alvo", [round(min(max((cx - x0) / cw, 0.2), 0.8), 3), round(min(max(cy + 0.04, 0.25), 0.75), 3)])
    if "zoom" not in s:
        z = min(max(0.38 / max(h, 0.05), 1.0), 1.7)      # cabeça ocupando ~38% da altura
        s["zoom"] = [round(z, 2), round(min(z + 0.1, 1.8), 2)]
    return True


def auto_enquadrar(s: dict, clipe: Path, n_frames: int) -> None:
    """Acha o sujeito (animal/pessoa) no trecho usado e centraliza o recorte 9:16 nele."""
    import cv2
    from viitu.visao import detectar
    if s.get("sujeito") and enquadrar_por_texto(s, clipe, n_frames):
        return
    cap = cv2.VideoCapture(str(clipe))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    iw, ih = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    dur = n_frames / FPS
    caixas = []
    for frac in (0.15, 0.5, 0.85):
        t = s.get("inicio", 0) + dur * frac
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps) % max(int(total), 1))
        ok, img = cap.read()
        if ok:
            d = detectar(img)
            if d:
                caixas.append(d[0]["caixa"])
    cap.release()
    if not caixas or not iw:
        return
    x, y, w, h = (sum(c[i] for c in caixas) / len(caixas) for i in range(4))
    cx = x + w / 2                      # centro do sujeito (0–1 na largura original)
    cy = y + h * s.get("cabeca", 0.3)   # um pouco acima do centro: onde costuma estar a cabeça
    cw = min(iw, ih * W / H) / iw       # largura do recorte 9:16 (fração da largura original)
    if cw < 1:
        fx = min(max((cx - cw / 2) / (1 - cw), 0), 1)
        x0 = fx * (1 - cw)
        s.setdefault("foco", [round(fx, 3), 0.5])
        s.setdefault("alvo", [round(min(max((cx - x0) / cw, 0.2), 0.8), 3), round(min(max(cy, 0.2), 0.8), 3)])
    else:
        s.setdefault("alvo", [round(cx, 3), round(min(max(cy, 0.2), 0.8), 3)])
    # sujeito pequeno no quadro → aproxima mais (sem passar de 1,6x)
    if "zoom" not in s:
        alvo_h = 0.55
        z = min(max(alvo_h / max(h, 0.05), 1.0), 1.6)
        s["zoom"] = [round(z, 2), round(min(z + 0.12, 1.75), 2)]


def renderizar_cena(s: dict, pasta: Path, idx: int) -> Path:
    clipe = pasta / "clipes" / s["clipe"]
    eh_foto = clipe.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    n = s["f1"] - s["f0"]
    if s.get("layout") == "inteiro":
        import cv2
        cap = cv2.VideoCapture(str(clipe))
        iw, ih = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        cap.release()
        s["_fh"] = int(round(W * ih / iw / 2) * 2)
    elif not eh_foto and not s.get("efeito") and "foco" not in s:
        auto_enquadrar(s, clipe, n)
    saida = pasta / "saida" / "cenas" / f"{idx:03d}.mp4"
    entrada = (["-loop", "1", "-framerate", str(FPS), "-i", str(clipe)] if eh_foto else
               ["-stream_loop", "-1", "-ss", f"{s.get('inicio', 0):.3f}", "-i", str(clipe)])
    filtro = _filtro_cena(s, "0:v", eh_foto, n, idx == 0)
    cmd = ["ffmpeg", "-v", "error", "-y", *entrada, "-filter_complex", filtro, "-map", "[v]",
           "-frames:v", str(n), "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", str(saida)]
    subprocess.run(cmd, check=True)
    if s.get("marca_auto") and not s.get("dividida"):
        mov = marca_que_segue(s, clipe, n, pasta, idx)
        if mov:
            tmp = saida.with_name(saida.stem + "_m.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(saida), "-i", str(mov),
                            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[v]",
                            "-map", "[v]", "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "18", str(tmp)], check=True)
            tmp.replace(saida)
    return saida


def _ass_tempo(t: float) -> str:
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _circulo(r: int) -> str:
    """Círculo desenhado de 0 a 2r (o libass centraliza a caixa no \\pos com \\an5)."""
    k = int(r * 0.5523)
    c = r
    return (f"m {c} 0 b {c + k} 0 {2 * r} {c - k} {2 * r} {c} b {2 * r} {c + k} {c + k} {2 * r} {c} {2 * r} "
            f"b {c - k} {2 * r} 0 {c + k} 0 {c} b 0 {c - k} {c - k} 0 {c} 0")


def marcas_ass(segs: list[dict]) -> list[str]:
    """Círculo vermelho que 'pula' em cima do detalhe, para guiar o olho do espectador."""
    linhas = []
    for s in segs:
        m = s.get("marca")
        if not m or s.get("dividida"):
            continue
        t0, t1 = s["f0"] / FPS + m.get("atraso", 0.15), s["f1"] / FPS
        r = int(m.get("r", 200))
        desenho = (rf"{{\an5\pos({m['x']},{m['y']})\1a&HFF&\3c&H0000FF&\bord12\shad0"
                   rf"\fscx40\fscy40\t(0,180,\fscx105\fscy105)\t(180,260,\fscx100\fscy100)\p1}}"
                   f"{_circulo(r)}{{\\p0}}")
        linhas.append(f"Dialogue: 1,{_ass_tempo(t0)},{_ass_tempo(t1)},Viitu,,0,0,0,,{desenho}")
    return linhas


def gerar_legendas(palavras: list[dict], destaques: set[str], pasta: Path, fim: float,
                   segs: list[dict] | None = None) -> tuple[Path, Path]:
    cab = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Viitu,Anton,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,"
        "7,3,5,60,60,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    linhas, srt = [], []
    for i, p in enumerate(palavras):
        ini = p["inicio"]
        fim_p = palavras[i + 1]["inicio"] if i + 1 < len(palavras) else fim
        txt = re.sub(r"[.,:;!…]+$", "", p["palavra"]).replace("...", "").upper()
        if not txt:
            continue
        cor = r"{\c&H00D7FF&}" if _norm(p["palavra"]) in destaques else ""
        pop = r"{\pos(540,680)\fscx75\fscy75\t(0,90,\fscx100\fscy100)}"
        linhas.append(f"Dialogue: 0,{_ass_tempo(ini)},{_ass_tempo(fim_p)},Viitu,,0,0,0,,{pop}{cor}{txt}")
        srt.append((ini, fim_p, txt))
    ass = pasta / "saida" / "legenda.ass"
    linhas = marcas_ass(segs or []) + linhas
    ass.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    def ts(t):
        ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    srt_arq = pasta / "saida" / "legenda.srt"
    srt_arq.write_text("\n".join(f"{k + 1}\n{ts(a)} --> {ts(b)}\n{t}\n" for k, (a, b, t) in enumerate(srt)),
                       encoding="utf-8")
    return ass, srt_arq


def mixar_audio(pasta: Path, segs: list[dict], palavras: list[dict], cfg: dict, dur: float) -> Path:
    saida = pasta / "saida" / "audio_final.wav"
    entradas = ["-i", str(pasta / "voz.mp3")]
    filtros = [f"[0:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-1.5:LRA=11,"
               f"aresample=48000[voz]"]
    rotulos = ["[voz]"]
    k = 1
    impactos = set()
    for trecho in cfg.get("impacto_em", []):
        impactos.add(round(palavras[achar_palavra(palavras, trecho, 0)]["inicio"] * FPS))
    for s in segs[1:]:
        som, vol = ("impacto", 0.55) if s["f0"] in impactos else ("woosh", 0.22)
        atraso = max(int(s["f0"] / FPS * 1000) - (80 if som == "woosh" else 0), 0)
        entradas += ["-i", str(SFX / f"{som}.mp3")]
        filtros.append(f"[{k}:a]volume={vol},adelay={atraso}|{atraso},aresample=48000[s{k}]")
        rotulos.append(f"[s{k}]")
        k += 1
    filtros.append(f"{''.join(rotulos)}amix=inputs={len(rotulos)}:normalize=0:duration=first,"
                   f"atrim=0:{dur:.3f}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros),
                    "-map", "[a]", "-ac", "2", str(saida)], check=True)
    return saida


def editar(projeto: str) -> None:
    pasta = RAIZ / "projetos" / projeto
    palavras = json.loads((pasta / "palavras.json").read_text(encoding="utf-8"))
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    (pasta / "saida" / "cenas").mkdir(parents=True, exist_ok=True)

    fim_audio = palavras[-1]["fim"] + 0.02           # corta o silêncio final (loop perfeito)
    segs = montar_linha_do_tempo(palavras, cfg, fim_audio)
    dur = segs[-1]["f1"] / FPS
    print(f"{len(segs)} cortes em {dur:.2f} s (média {dur / len(segs):.2f} s por cena)")

    arquivos = []
    for i, s in enumerate(segs):
        arquivos.append(renderizar_cena(s, pasta, i))
        print(f"  cena {i + 1:02d} {s['t0']:6.2f}-{s['t1']:6.2f}s  {s['clipe']}"
              f"{'  [' + s['efeito'] + ']' if s.get('efeito') else ''}")

    lista = pasta / "saida" / "cenas" / "lista.txt"
    lista.write_text("".join(f"file '{a.name}'\n" for a in arquivos), encoding="utf-8")
    video = pasta / "saida" / "video_mudo.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-c", "copy", str(video)], check=True)

    audio = mixar_audio(pasta, segs, palavras, cfg, dur)
    destaques = {_norm(x) for x in cfg.get("destaques", [])}
    ass, srt = gerar_legendas(palavras, destaques, pasta, dur, segs)

    base = pasta / "saida" / "short_base.mp4"
    final = pasta / "saida" / "short_final.mp4"
    comum = ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest",
             "-movflags", "+faststart"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(audio),
                    "-c:v", "copy", *comum, str(base)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(audio),
                    "-vf", f"ass={ass}:fontsdir={FONTES}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-pix_fmt", "yuv420p", *comum, str(final)], check=True)
    print(f"\nPronto:\n  {final.relative_to(RAIZ)}\n  {base.relative_to(RAIZ)}\n  {srt.relative_to(RAIZ)}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("projeto")
    editar(p.parse_args().projeto)


if __name__ == "__main__":
    main()
