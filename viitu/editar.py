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
MAX_CENA = __import__("json").loads((Path(__file__).resolve().parent.parent / "edicao" / "especificacao.json").read_text(encoding="utf-8"))["visual"]["max_cena"]   # da engenharia reversa (1,5 s/cena nos canais)
MODO_REMOTION = False   # True: não queima legenda/marcas; exporta plano para o Remotion      # cena maior que isso é dividida (regra dos 2–3 s)
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
            cand = [p["inicio"] for p in palavras if x["t0"] + 0.7 < p["inicio"] < x["t1"] - 0.7]
            if not cand:
                final.append(x)
                continue
            corte = min(cand, key=lambda t: abs(t - meio))
            z = x.get("zoom", [1.0, 1.12])
            a = {**x, "t1": corte}
            b = {**x, "t0": corte, "inicio": x.get("inicio", 0) + (corte - x["t0"]),
                 "zoom": [z[1] + 0.12, z[1] + 0.2], "dividida": True}
            if x.get("bumerangue"):
                # BUMERANGUE: a 2ª parte começa no último quadro da 1ª e toca AO CONTRÁRIO (sem pulo de "copiar e colar")
                vel = float(x.get("velocidade", 1.0))
                la, lb = (corte - x["t0"]) * vel, (x["t1"] - corte) * vel
                b.update(inicio=max(x.get("inicio", 0) + la - lb, 0), reverso=not x.get("reverso", False),
                         zoom=[z[1], z[1] + 0.06], bumerangue=False)
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
    elif s.get("_cam"):
        c = s["_cam"]
        f = (f"[{entrada}]{_lento(s)}setpts=PTS-STARTPTS,"
             f"crop={c['w']}:{c['h']}:'{_expr_keyframes(c['t'], c['x'])}':'{_expr_keyframes(c['t'], c['y'])}',"
             f"scale={W}:{H}:flags=lanczos,fps={FPS}")
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
    if s.get("espelhar"):
        f += ",hflip"                       # inverte o lado (o cérebro não se acostuma)
    if s.get("reverso"):
        f += f",trim=end_frame={n_frames},reverse"   # corta o trecho exato e toca ao contrário (clipe reaproveitado vira "continuação", não repetição)
    if s.get("_escura"):
        f += ",eq=gamma=1.35:brightness=0.04"   # cena escura demais: levanta as sombras sem estourar o fogo
    f += ",eq=contrast=1.06:saturation=1.12,unsharp=5:5:0.5,vignette=PI/5,setsar=1,format=yuv420p"     # bordas escuras guiam o olhar
    if not primeira and not MODO_REMOTION:
        f += ",fade=t=in:st=0:d=0.12:color=white"   # flash nos cortes (no Remotion: glitch RGB)
    return f + "[v]"


def _para_tela(s: dict, ex: float, ey: float, z: float, iw: float, ih: float,
               t_cena: float = 0.0) -> tuple[float, float, float]:
    """Converte ponto (0–1 no clipe original) para pixels na tela 1080x1920. Retorna (x, y, escala)."""
    if s.get("_cam"):
        c = s["_cam"]
        x0 = float(np.interp(t_cena, c["t"], c["x"]))
        y0 = float(np.interp(t_cena, c["t"], c["y"]))
        return (ex * iw - x0) / c["w"] * W, (ey * ih - y0) / c["h"] * H, iw / c["w"] * W
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
        x, y, esc = _para_tela(s, cx, cy, z, iw, ih, i / FPS)
        pos.append((x, y, min(max(tam * esc * 0.62, 70), 320)))
    # suaviza o tremido da detecção (média móvel)
    k = 7
    xs = np.convolve([p[0] for p in pos], np.ones(k) / k, mode="same")
    ys = np.convolve([p[1] for p in pos], np.ones(k) / k, mode="same")
    for i in range(min(k // 2, n)):
        xs[i], ys[i] = pos[i][0], pos[i][1]
        xs[-1 - i], ys[-1 - i] = pos[-1 - i][0], pos[-1 - i][1]
    pos = [(float(a), float(b), p[2]) for a, b, p in zip(xs, ys, pos)]
    if s.get("espelhar"):
        pos = [(W - a, b, c) for a, b, c in pos]
    s["_marca_pos"] = [[round(a, 1), round(b, 1), round(c, 1)] for a, b, c in pos]
    if MODO_REMOTION:
        return None
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


def camera_virtual(s: dict, clipe: Path, n_frames: int) -> bool:
    """Câmera que acompanha o ponto de atenção ao longo da cena (keyframes suavizados).
    Atenção = sujeito principal; em cena de ação com 2 sujeitos grandes, o centro entre eles.
    Com "sujeito" (texto), usa o OWLv2 nessa parte do animal."""
    import cv2
    from viitu.visao import detectar
    vel = float(s.get("velocidade", 1.0))
    t0 = s.get("inicio", 0)
    dur = n_frames / FPS
    cap = cv2.VideoCapture(str(clipe))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    iw, ih = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    amostras = max(4, min(int(dur * 5), 16))          # ~5 leituras por segundo
    tempos = [dur * k / (amostras - 1) for k in range(amostras)]   # tempo na cena (saída)
    pontos = []
    if s.get("sujeito"):
        from viitu.inteligencia import localizar
        cap.release()
        achados = localizar(clipe, s["sujeito"], t0, t0 + dur * vel, passos=min(amostras, 8))
        for a in achados:
            mult = 8 if "eye" in s["sujeito"] else 1.3   # olho → cabeça inteira com folga
            pontos.append(((a["t"] - t0) / vel, a["x"] + a["w"] / 2, a["y"] + a["h"] / 2, a["h"] * mult))
    else:
        for tc in tempos:
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(int((t0 + tc * vel) * fps), max(total - 1, 0)))
            ok, img = cap.read()
            if not ok:
                continue
            d = detectar(img)
            if not d:
                continue
            x, y, w, h = d[0]["caixa"]
            if len(d) > 1 and d[1]["caixa"][2] * d[1]["caixa"][3] > 0.3 * w * h:   # ação entre dois
                x2, y2, w2, h2 = d[1]["caixa"]
                xa, ya = min(x, x2), min(y, y2)
                w, h = max(x + w, x2 + w2) - xa, max(y + h, y2 + h2) - ya
                x, y = xa, ya
            pontos.append((tc, x + w / 2, y + h * s.get("cabeca", 0.35), h))
        cap.release()
    if len(pontos) < 2:
        return False
    # suavização: média ponderada no tempo (sem tremer) e limite de velocidade de pan
    ts = np.array([p[0] for p in pontos])
    cx = np.array([p[1] for p in pontos])
    cy = np.array([p[2] for p in pontos])
    hs = np.array([p[3] for p in pontos])
    kt = np.linspace(0, dur, max(int(dur * 4) + 1, 2))           # keyframe a cada 0,25 s
    kx = np.interp(kt, ts, cx)
    ky = np.interp(kt, ts, cy)
    for _ in range(2):                                            # duas passadas de suavização
        kx = np.convolve(np.pad(kx, 2, mode="edge"), np.ones(5) / 5, mode="valid")
        ky = np.convolve(np.pad(ky, 2, mode="edge"), np.ones(5) / 5, mode="valid")
    # tamanho do recorte: sujeito ocupando ~55% da altura (ou o zoom pedido), sempre 9:16
    z = s["zoom"][0] if "zoom" in s else float(min(max(0.55 / max(np.median(hs), 0.05), 1.0), 1.8))
    ch = ih / z
    cw = ch * W / H
    if cw > iw:
        cw, ch = iw, iw * H / W
    xs = np.clip(kx * iw - cw / 2, 0, iw - cw)
    ys = np.clip(ky * ih - ch / 2, 0, ih - ch)
    s["_alvo_y_out"] = float(np.mean((ky * ih - ys) / ch * H))
    if "eye" in s.get("sujeito", ""):
        s["_alvo_y_out"] += 0.18 * H      # o rosto fica abaixo do olho
    s["_cam"] = {"t": kt.round(3).tolist(), "x": xs.round(1).tolist(), "y": ys.round(1).tolist(),
                 "w": round(cw / 2) * 2, "h": round(ch / 2) * 2}
    return True


def _expr_keyframes(ts: list, vs: list) -> str:
    """Expressão FFmpeg piecewise-linear (interpolação entre keyframes) em função de t."""
    e = f"{vs[-1]}"
    for i in range(len(ts) - 2, -1, -1):
        t0, t1, v0, v1 = ts[i], ts[i + 1], vs[i], vs[i + 1]
        e = f"if(lt(t\\,{t1})\\,{v0}+({v1 - v0:.1f})*(t-{t0})/{max(t1 - t0, 0.001):.3f}\\,{e})"
    return e


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


_FIM_UTIL: dict = {}


def eh_tela_final(img) -> bool:
    """Tela de encerramento de TikTok/Reels: fundo escuro quase uniforme (azul-marinho/preto)."""
    import cv2
    g = cv2.resize(img, (72, 128))
    hsv = cv2.cvtColor(g, cv2.COLOR_BGR2HSV)
    escuro = (hsv[..., 2] < 60)
    if escuro.mean() < 0.75:
        return False
    quente = ((hsv[..., 0] < 30) & (hsv[..., 1] > 120) & (hsv[..., 2] > 120)).mean()   # fogo/luz laranja
    b, r = g[..., 0][escuro].astype(int).mean(), g[..., 2][escuro].astype(int).mean()
    return quente < 0.005 and b > r + 4          # fundo azul-marinho, sem nenhuma chama


def fim_util(clipe: Path) -> float:
    """Último segundo utilizável do clipe (antes da tela final do TikTok/Reels), com 0,4 s de folga."""
    import cv2
    if clipe in _FIM_UTIL:
        return _FIM_UTIL[clipe]
    cap = cv2.VideoCapture(str(clipe))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fim = n / fps
    for f in range(n - 1, max(n - int(8 * fps), 0), -2):     # procura do fim para trás (até 8 s)
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, img = cap.read()
        if ok and not eh_tela_final(img):
            fim = (f + 2) / fps
            break
    cap.release()
    _FIM_UTIL[clipe] = max(fim - 0.4, 0.5) if fim < n / fps - 0.5 else n / fps
    return _FIM_UTIL[clipe]


def _clipe_vertical(clipe: Path) -> tuple[bool, float]:
    import cv2
    cap = cv2.VideoCapture(str(clipe))
    w, h = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    d = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    cap.release()
    return (h > 0 and abs(w / h - W / H) < 0.04), d


def renderizar_cena(s: dict, pasta: Path, idx: int) -> Path:
    clipe = pasta / "clipes" / s["clipe"]
    eh_foto = clipe.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    n = s["f1"] - s["f0"]
    if not eh_foto:
        import cv2
        cap = cv2.VideoCapture(str(clipe))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((s.get("inicio", 0) + n / FPS / 2) * (cap.get(cv2.CAP_PROP_FPS) or 30)))
        ok, amostra = cap.read()
        cap.release()
        if ok and cv2.cvtColor(cv2.resize(amostra, (90, 160)), cv2.COLOR_BGR2GRAY).mean() < 45:
            s["_escura"] = True
        if s["clipe"].startswith("pixabay") and "zoom" not in s and not s.get("seguir", True) is False:
            s.setdefault("zoom", [1.0, 1.12])       # banco de imagem costuma ser estático: Ken Burns leve
        vertical, dur_clipe = _clipe_vertical(clipe)
        if vertical and not s.get("efeito"):
            # clipe já 9:16 (TikTok/Reels): sem câmera virtual e sem zoom forte — zoom amplia a marca
            # d'água ("logo estourado") e borra vídeo de baixa resolução
            s.setdefault("foco", [0.5, 0.5]); s.setdefault("alvo", [0.5, 0.5]); s.setdefault("zoom", [1.0, 1.04])
        # TRIAGEM: a cena tem que caber num trecho aprovado do clipe (sem tela de app, preto, corte interno)
        tri = pasta / "clipes" / "triagem.json"
        if tri.exists():
            t = json.loads(tri.read_text(encoding="utf-8")).get(s["clipe"])
            uso = n / FPS * float(s.get("velocidade", 1.0))
            if t and not any(a <= s.get("inicio", 0) and s.get("inicio", 0) + uso <= b + 0.01 for a, b in t["trechos_utilizaveis"]):
                cabem = [(a, b) for a, b in t["trechos_utilizaveis"] if b - a >= uso]
                if not cabem:
                    raise SystemExit(f"Cena '{s['em']}': nenhum trecho aprovado de {s['clipe']} tem {uso:.1f}s — escolha outro clipe")
                a, b = min(cabem, key=lambda ab: abs(min(max(s.get('inicio', 0), ab[0]), ab[1] - uso) - s.get('inicio', 0)))
                novo = min(max(s.get("inicio", 0), a), b - uso)
                print(f"    triagem: cena '{s['em']}' movida de {s.get('inicio', 0):.2f}s para {novo:.2f}s (trecho aprovado {a}–{b})")
                s["inicio"] = round(novo, 2)
        if True:
            # nunca usar a tela final (logo + @) de TikTok/Reels: detectada no próprio clipe
            limite = fim_util(clipe)
            uso = n / FPS * float(s.get("velocidade", 1.0))
            if s.get("inicio", 0) + uso > limite:
                s["inicio"] = max(limite - uso, 0)
                print(f"    aviso: cena '{s['em']}' recuada para não pegar o fim do clipe ({limite:.1f}s)")
    if s.get("layout") == "inteiro":
        import cv2
        cap = cv2.VideoCapture(str(clipe))
        iw, ih = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        cap.release()
        s["_fh"] = int(round(W * ih / iw / 2) * 2)
    elif not eh_foto and not s.get("efeito") and "foco" not in s:
        if not (s.get("seguir", True) and camera_virtual(s, clipe, n)):
            auto_enquadrar(s, clipe, n)
    saida = pasta / "saida" / "cenas" / f"{idx:03d}.mp4"
    entrada = (["-loop", "1", "-framerate", str(FPS), "-i", str(clipe)] if eh_foto else
               ["-stream_loop", "-1", "-ss", f"{s.get('inicio', 0):.3f}", "-i", str(clipe)])
    filtro = _filtro_cena(s, "0:v", eh_foto, n, idx == 0)
    cmd = ["ffmpeg", "-v", "error", "-y", *entrada, "-filter_complex", filtro, "-map", "[v]",
           "-frames:v", str(n), "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", str(saida)]
    subprocess.run(cmd, check=True)
    if s.get("seta") and not s.get("dividida"):
        # seta FIXA (x, y, r em pixels da tela 1080x1920) — quando o detector acha o objeto errado
        x, y, r = s["seta"]
        s["_seta_pos"] = [[x, y, r]] * n
    elif s.get("seta_auto") and not s.get("dividida"):
        s2 = dict(s, marca_auto=s["seta_auto"])
        global MODO_REMOTION
        _m = MODO_REMOTION
        MODO_REMOTION = True                 # só calcula as posições (a seta é desenhada no Remotion)
        marca_que_segue(s2, clipe, n, pasta, idx)
        MODO_REMOTION = _m
        if s2.get("_marca_pos"):
            s["_seta_pos"] = s2["_marca_pos"]
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


def som_ambiente(pasta: Path, segs: list[dict], dur: float) -> Path:
    """Som original de cada clipe (chiado, raspagem, bicho...) cortado igual às cenas.
    Padrão dos virais do Hall: o som real fica audível por baixo da narração."""
    partes = []
    for i, s in enumerate(segs):
        n = s["f1"] - s["f0"]
        d = n / FPS
        out = pasta / "saida" / "cenas" / f"{i:03d}_amb.wav"
        clipe = pasta / "clipes" / s["clipe"]
        vel = float(s.get("velocidade", 1.0))
        tem_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                    "-of", "csv=p=0", str(clipe)], capture_output=True, text=True).stdout.strip()
        if tem_audio and clipe.suffix.lower() not in (".jpg", ".png") and s.get("som_original", True):
            filtro = f"atempo={max(vel, 0.5)}," if vel != 1.0 else ""
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-ss", f"{s.get('inicio', 0):.3f}",
                            "-i", str(clipe), "-t", f"{d * vel:.3f}", "-af",
                            f"{filtro}apad,atrim=0:{d:.3f},afade=t=in:d=0.04,afade=t=out:st={max(d - 0.06, 0):.3f}:d=0.06",
                            "-ar", "48000", "-ac", "2", str(out)], check=True)
        else:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                            "-t", f"{d:.3f}", str(out)], check=True)
        partes.append(out)
    lista = pasta / "saida" / "cenas" / "amb.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in partes), encoding="utf-8")
    saida = pasta / "saida" / "ambiente.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-af", f"atrim=0:{dur:.3f},loudnorm=I=-14:TP=-2", str(saida)], check=True)
    return saida


def _inicio_musica(arq: Path) -> float:
    """Primeiro segundo em que a trilha já está a até 4 dB do volume típico dela (pula a intro quase muda)."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(arq), "-af",
                          "aresample=48000,asetnsamples=48000,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    rms = [float(x) for x in re.findall(r"RMS_level=(-?[\d.]+)", out)]
    if not rms:
        return 0.0
    alvo = float(np.median(rms)) - 4
    return float(next((i for i, r in enumerate(rms) if r >= alvo), 0))


NUMERO = re.compile(r"^\d|^(mil|milh[aã]o|milh[oõ]es|bilh[aã]o|bilh[oõ]es|dobro|metade)$", re.I)
DINHEIRO = re.compile(r"^(reais|real|d[oó]lar(es)?|caro|cara|preço|custa|r\$)", re.I)


def _kit_e_sfx(cfg: dict, palavras: list[dict], pub: Path) -> tuple[dict, list[dict]]:
    """Copia o kit de identidade (assets/kit) para o Remotion e monta os sons de FUNÇÃO:
    - automáticos: número → ding_fato · dinheiro → dinheiro (máx. 4, ≥ 3 s entre eles)
    - manuais: cfg["sfx_em"] = [{"em": "acha", "som": "errado_mito", "vol": 0.5}]"""
    import shutil
    kj = RAIZ / "assets" / "kit" / "kit.json"
    if not kj.exists():
        return {}, []
    from viitu.kit import baixar
    kit = json.loads(kj.read_text(encoding="utf-8"))
    nomes = {}
    for func, v in kit.items():
        nomes[func] = []
        for i, sm in enumerate(v["sons"]):
            dst = f"kit_{func}_{i}.mp3"
            from viitu.mix import normalizar
            normalizar(baixar(sm), pub / dst, "pontual")
            nomes[func].append(dst)
    eventos, ultimo = [], -99.0
    if cfg.get("sfx_auto", False):      # só ligar quando houver gráfico de número/dinheiro na tela
        for p in palavras:
            w = re.sub(r"[^\wR$]", "", p["palavra"])
            func = "dinheiro" if DINHEIRO.match(w) else ("ding_fato" if NUMERO.match(w) else None)
            if func and p["inicio"] - ultimo >= 3 and len(eventos) < 4 and p["inicio"] > 1.0:
                eventos.append({"f": round(p["inicio"] * FPS), "som": nomes[func][len(eventos) % 3], "vol": 0.45})
                ultimo = p["inicio"]
    for e in cfg.get("sfx_em", []):
        i = achar_palavra(palavras, e["em"], 0)
        # regra: som de função só na PAUSA (fim da frase onde está a palavra), nunca sobre a fala
        j = i
        while j + 1 < len(palavras) and palavras[j + 1]["inicio"] - palavras[j].get("fim", palavras[j + 1]["inicio"]) < 0.25:
            j += 1
        t = palavras[j].get("fim", palavras[j]["inicio"] + 0.3)
        eventos.append({"f": round(t * FPS), "som": nomes[e["som"]][e.get("var", 0) % 3],
                        "vol": e.get("vol", 0.5)})
    return nomes, eventos


def _sons_da_cena(segs: list[dict], palavras: list[dict], pub: Path) -> list[dict]:
    """Foley de AÇÃO em cena de clipe real (não é som de função): toca NA palavra, não na pausa.
    "sfx_cena": [{"em": "pegou", "arquivo": "assets/sfx/x.mp3", "db": -4, "dur": 2, "desloc": 0}]"""
    from viitu.mix import normalizar
    out = []
    for s in segs:
        for k, e in enumerate(s.get("sfx_cena", [])):
            f = round(palavras[achar_palavra(palavras, e["em"], 0)]["inicio"] * FPS) + int(e.get("desloc", 0) * FPS)
            nome = f"cena_sfx_{s['f0']}_{k}.mp3"
            dur = e.get("dur", 3)
            corte = pub / f"_tmpc_{k}.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(RAIZ / e["arquivo"]), "-t", f"{dur:.2f}",
                            "-af", f"afade=t=out:st={max(dur - 0.4, 0):.2f}:d=0.4", str(corte)], check=True)
            normalizar(corte, pub / nome, "pontual")
            corte.unlink(missing_ok=True)
            out.append({"f": max(f, 0), "som": nome, "vol": round(10 ** (e.get("db", -6) / 20), 4), "dur": int(dur * FPS) + 10})
    return out


def _sons_da_animacao(segs: list[dict], animacoes: list[dict], pub: Path) -> list[dict]:
    """SOUND DESIGN DO 3D: cada cena de animação declara seus efeitos amarrados aos eventos dela:
    "animacao": {..., "sfx": [{"evento": "batesse", "busca": "<som em inglês>", "exigir": "regex", "db": -4,
                               "desloc": 0, "dur": 3}]}
    O som vem da biblioteca Sonniss (CLAP escuta e escolhe; escolha guardada em escolhas.json), normalizado à
    referência da voz (viitu/mix.py) e tocado no quadro do evento com o nível "db" relativo à voz."""
    from viitu.foley import _som_sonniss
    from viitu.mix import normalizar
    out, n = [], 0
    for s, a in zip([g for g in segs if g.get("animacao")], animacoes):
        for e in s["animacao"].get("sfx", []):
            arq = str(RAIZ / e["arquivo"]) if e.get("arquivo") else _som_sonniss(e["busca"], e.get("min", 0.5), e.get("exigir"))
            if not arq:
                continue
            ev = e.get("evento")
            f = a["f0"] + (a["eventos"].get(ev, 0) if ev else 0) + int(e.get("desloc", 0) * FPS)
            nome = f"anim_sfx_{n}.mp3"
            dur = e.get("dur", 4)
            corte = pasta_tmp = pub / f"_tmp_{n}.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{e.get('ini', 0):.2f}", "-i", arq, "-t", f"{dur:.2f}",
                            "-af", f"afade=t=out:st={max(dur - 0.4, 0):.2f}:d=0.4", str(corte)], check=True)
            normalizar(corte, pub / nome, "pontual")
            corte.unlink(missing_ok=True)
            out.append({"f": max(f, 0), "som": nome, "vol": round(10 ** (e.get("db", -6) / 20), 4),
                        "dur": int(dur * FPS) + 10})
            n += 1
    if out:
        print("Sons do 3D:", ", ".join(f"{o['som']}@{o['f'] / FPS:.1f}s" for o in out))
    return out


def exportar_remotion(pasta: Path, segs: list[dict], palavras: list[dict], cfg: dict,
                      video: Path, audio: Path, dur: float) -> None:
    import shutil
    pub = RAIZ / "remotion" / "public"
    pub.mkdir(parents=True, exist_ok=True)
    shutil.copy(video, pub / "fundo.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-c:a", "aac", "-b:a", "192k",
                    str(pub / "audio.m4a")], check=True)
    from viitu.mix import normalizar, ganho, espec
    if (RAIZ / "assets" / "texturas").exists():          # texturas CC0 (Poly Haven) para o 3D
        shutil.copytree(RAIZ / "assets" / "texturas", pub / "tex", dirs_exist_ok=True)
    for som in SFX.glob("*.mp3"):          # sons próprios: normalizados à referência da voz
        normalizar(som, pub / som.name, "pontual")
    # som original só de clipes livres (Pixabay/próprios): áudio de TikTok/Reels costuma ter música com direitos
    for g in segs:
        if g["clipe"].startswith(("tiktok", "bruto_", "ancora")) and "som_original" not in g:
            g["som_original"] = False
    amb = som_ambiente(pasta, segs, dur)
    from viitu.foley import escolher, mixar, x_movimento
    faixas_foley = escolher(segs, pasta, FPS)
    for f in faixas_foley:          # pan pelo lado onde a ação acontece NA TELA (vídeo final)
        f["x"] = x_movimento(video, f["f0"], f["f1"])
    print("Foley:", ", ".join(f"{f['_som']} {f['f0'] / FPS:.1f}-{f['f1'] / FPS:.1f}s pan {f['x']:.2f}" for f in faixas_foley))
    from viitu.foley import camadas
    faixas_foley = camadas(faixas_foley)
    fol = mixar(faixas_foley, FPS, dur, pasta / "saida" / "foley.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(fol), "-c:a", "aac", "-b:a", "192k",
                    str(pub / "foley.m4a")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(amb), "-c:a", "aac", "-b:a", "160k",
                    str(pub / "ambiente.m4a")], check=True)
    musica = cfg.get("musica", "curioso_documentario.mp3")
    ini_mus = _inicio_musica(RAIZ / "assets" / "musica" / musica)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini_mus:.2f}", "-i", str(RAIZ / "assets" / "musica" / musica),
                    "-c:a", "libmp3lame", "-q:a", "2", str(pasta / "saida" / "musica_crua.mp3")], check=True)
    normalizar(pasta / "saida" / "musica_crua.mp3", pub / "musica.mp3", "leito")
    kit_plano, sfx_plano = _kit_e_sfx(cfg, palavras, pub)
    destaques = {_norm(x) for x in cfg.get("destaques", [])}

    def y_legenda(f: int) -> int:
        """Legenda longe do ponto de atenção: sujeito na metade de cima → legenda embaixo."""
        seg = next((g for g in segs if g["f0"] <= f < g["f1"]), segs[-1])
        if seg.get("layout") == "inteiro":
            alvo = H / 2
        elif "_alvo_y_out" in seg:
            alvo = seg["_alvo_y_out"]
        else:
            alvo = seg.get("alvo", [0.5, 0.5])[1] * H
        # padrão dos virais do Hall: legenda no centro-inferior (logo acima da interface do YouTube);
        # só sobe para o terço de cima quando o sujeito está na parte de baixo da tela
        # formato do dono: legenda no TERÇO SUPERIOR; só desce se o sujeito estiver em cima (não cobrir o sujeito)
        v = espec()["visual"]
        return v.get("legenda_y", 560) if alvo > 760 else v.get("legenda_y_alternativa", 1250)

    plano = {
        "fps": FPS, "duracao_frames": segs[-1]["f1"],
        "palavras": [{"texto": re.sub(r"[.,:;!…]+$", "", p["palavra"]).replace("...", "").upper(),
                      "f0": round(p["inicio"] * FPS),
                      "f1": round((palavras[i + 1]["inicio"] if i + 1 < len(palavras) else dur) * FPS),
                      "destaque": _norm(p["palavra"]) in destaques,
                      "y": y_legenda(round(p["inicio"] * FPS))}
                     for i, p in enumerate(palavras)],
        "marcas": [{"f0": s["f0"] + int(s["marca_auto"].get("atraso", 0.15) * FPS), "cena_f0": s["f0"], "f1": s["f1"],
                    "pos": s["_marca_pos"], "tipo": "circulo"} for s in segs if s.get("_marca_pos")]
                  + [{"f0": s["f0"] + int(s.get("seta_auto", {}).get("atraso", 0.0) * FPS), "cena_f0": s["f0"], "f1": s["f1"],
                      "pos": s["_seta_pos"], "tipo": "seta"} for s in segs if s.get("_seta_pos")],
        "cortes": [s["f0"] for s in segs[1:]],
        "impactos": [round(palavras[achar_palavra(palavras, t, 0)]["inicio"] * FPS)
                     for t in cfg.get("impacto_em", [])],
        "foley": [{"f0": f["f0"], "f1": f["f1"], "som": f["som"], "vol": f["vol"]} for f in faixas_foley],
        "foley_mix": True,
        "kit": kit_plano,
        "visual": {k: v for k, v in espec()["visual"].items() if isinstance(v, (bool, int, float))},
        # volume da trilha: sob a fala / nas pausas (cfg "mix" sobrescreve) — ver logica_editor.md
        # MIXAGEM POR REGRA: ganhos tirados de edicao/especificacao.json (dB relativos à voz; viitu/mix.py)
        "mix": {k: round(10 ** (v / 20), 4) for k, v in {**espec()["mix_db"], **cfg.get("mix_db", {})}.items()},
        "sfx": sfx_plano,
        # animação explicativa própria: {"animacao": {"nome", "fase", "eventos": {evento: "palavra"}}} na cena
        "animacoes": [{"nome": s["animacao"]["nome"], "fase": s["animacao"].get("fase", ""), "f0": s["f0"], "f1": s["f1"],
                       "eventos": {k: round(palavras[achar_palavra(palavras, w, s["palavra_i"])]["inicio"] * FPS) - s["f0"]
                                   for k, w in s["animacao"].get("eventos", {}).items()}}
                      for s in segs if s.get("animacao")],
        "cta": (lambda c: {"f0": round(palavras[achar_palavra(palavras, c["em"], 0)]["inicio"] * FPS),
                           "texto": c.get("texto", "💬 COMENTA")} if isinstance(c, dict)
                else ({"f0": segs[-1]["f0"] + 6, "texto": "INSCREVA-SE"} if c else None))(cfg.get("cta", False)),   # canais: sem CTA explícito na maioria
    }
    plano["sfx"] += _sons_da_animacao(segs, plano["animacoes"], pub)
    plano["sfx"] += _sons_da_cena(segs, palavras, pub)
    (pub / "plano.json").write_text(json.dumps(plano, ensure_ascii=False), encoding="utf-8")
    print(f"Plano Remotion exportado: {pub.relative_to(RAIZ)}/plano.json")


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

    if MODO_REMOTION:
        audio = pasta / "saida" / "voz_limpa.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pasta / "voz.mp3"), "-af",
                        f"atrim=0:{dur:.3f},loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", str(audio)], check=True)
    else:
        audio = mixar_audio(pasta, segs, palavras, cfg, dur)
    destaques = {_norm(x) for x in cfg.get("destaques", [])}
    ass, srt = gerar_legendas(palavras, destaques, pasta, dur, segs)

    if MODO_REMOTION:
        exportar_remotion(pasta, segs, palavras, cfg, video, audio, dur)
        return
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
    p.add_argument("--remotion", action="store_true", help="exporta vídeo limpo + plano para o Remotion")
    a = p.parse_args()
    global MODO_REMOTION
    MODO_REMOTION = a.remotion
    editar(a.projeto)


if __name__ == "__main__":
    main()
