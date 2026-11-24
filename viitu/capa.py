"""CAPA do Short (dono 24/11: "me envia junto um arquivo de imagem para ser a capa").

Pega o quadro mais forte do GANCHO já recortado (saida/cenas/000.mp4 — sem legenda), desenha a seta/círculo da cena
(mesmo alvo medido do vídeo) e um título curto e grande no terço de cima (o pé da tela fica coberto pelo app).
Saída: projetos/<p>/capa.jpg (1080x1920) — sobe no app do YouTube em "Editar capa"/"Miniatura".

Uso: python3 -m viitu.capa <projeto> "TÍTULO CURTO" [--t 0.6] [--cena 0]
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "assets" / "fontes" / "Anton-Regular.ttf"


def _quadro(mp4: Path, t: float) -> Image.Image:
    png = mp4.with_suffix(".capa.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920", str(png)], check=True)
    im = Image.open(png).convert("RGB")
    png.unlink()
    return im


def _seta(d: ImageDraw.ImageDraw, x: float, y: float, r: float) -> None:
    """Mesma seta do vídeo (Short.tsx SetaMarca): vem da diagonal e a PONTA encosta na borda do alvo."""
    lado = 1 if x < 420 else -1
    ang = math.radians(315 if lado == 1 else 225)
    dist = r + 12
    px, py = x - math.cos(ang) * dist, y + math.sin(ang) * dist          # ponta
    ux, uy = math.cos(ang), -math.sin(ang)                                # direção ponta → alvo (tela)
    vx, vy = -uy, ux
    s = 1.45 * 1.25
    pts = [(-210, -20), (-80, -20), (-80, -52), (0, 0), (-80, 52), (-80, 20), (-210, 20)]   # ponta em (0,0)
    poli = [(px + (a * ux + b * vx) * s, py + (a * uy + b * vy) * s) for a, b in pts]
    d.polygon([(a + 6, b + 8) for a, b in poli], fill=(0, 0, 0, 110))
    d.polygon(poli, fill=(255, 30, 30, 255), outline=(255, 255, 255, 255), width=10)


def _titulo(im: Image.Image, texto: str) -> None:
    linhas = texto.upper().split("|") if "|" in texto else _quebrar(texto.upper())
    tam = 150 if max(len(l) for l in linhas) <= 12 else 120
    f = ImageFont.truetype(str(FONTE), tam)
    d = ImageDraw.Draw(im)
    y = 230
    for k, l in enumerate(linhas):
        w = d.textlength(l, font=f)
        cor = (255, 215, 0) if k == len(linhas) - 1 else (255, 255, 255)      # última linha amarela (identidade)
        d.text(((1080 - w) / 2, y), l, font=f, fill=cor, stroke_width=12, stroke_fill=(0, 0, 0))
        y += int(tam * 1.12)


def _quebrar(t: str) -> list[str]:
    ws, linhas, atual = t.split(), [], ""
    for w in ws:
        if len(atual) + len(w) + 1 > 13 and atual:
            linhas.append(atual)
            atual = w
        else:
            atual = (atual + " " + w).strip()
    return linhas + [atual]


def capa(projeto: str, titulo: str, t: float = 0.6, cena: int = 0, zoom: float = 1.1) -> Path:
    pasta = RAIZ / "projetos" / projeto
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    im = _quadro(pasta / "saida" / "cenas" / f"{cena:03d}.mp4", t)
    # zoom leve: tira texto queimado e fio de borda do clipe de origem; a seta acompanha o mesmo zoom
    oy = 1920 * 0.55
    im = im.resize((round(1080 * zoom), round(1920 * zoom)), Image.LANCZOS)
    x0, y0 = round(540 * zoom - 540), round(oy * zoom - oy)
    im = im.crop((x0, y0, x0 + 1080, y0 + 1920))
    im = Image.blend(im, im.filter(ImageFilter.UnsharpMask(3, 120)), 0.6)          # mais nítida na miniatura
    topo = Image.new("L", (1, 1920))                                                # escurece o topo (título legível)
    for y in range(1920):
        topo.putpixel((0, y), int(150 * max(0, 1 - y / 900)))
    im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, topo.resize(im.size))
    camada = Image.new("RGBA", im.size, (0, 0, 0, 0))
    seta = cfg["cenas"][cena].get("seta")
    if seta:
        x, y, r = seta
        _seta(ImageDraw.Draw(camada), (x - 540) * zoom + 540, (y - oy) * zoom + oy, r * zoom)
    im = Image.alpha_composite(im.convert("RGBA"), camada).convert("RGB")
    _titulo(im, titulo)
    out = pasta / "capa.jpg"
    im.save(out, quality=92)
    print(f"Capa: {out.relative_to(RAIZ)}")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("projeto")
    p.add_argument("titulo", help='curto, 2–5 palavras; "|" força a quebra de linha')
    p.add_argument("--t", type=float, default=0.6)
    p.add_argument("--cena", type=int, default=0)
    p.add_argument("--zoom", type=float, default=1.1)
    a = p.parse_args()
    capa(a.projeto, a.titulo, a.t, a.cena, a.zoom)


if __name__ == "__main__":
    main()
