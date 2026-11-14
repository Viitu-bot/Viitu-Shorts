"""Animações desenhadas quadro a quadro (Cairo), com fundo transparente.

circulo_animado: círculo vermelho "à mão" que se desenha como um traço de caneta em ~0,35 s,
segue a posição do objeto (rastreada) e dá um leve pulso. Saída: .mov com canal alfa.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import cairo

W, H, FPS = 1080, 1920, 30


def _traco(ctx, cx, cy, r, progresso, fase):
    """Elipse levemente irregular, desenhada até `progresso` (0–1.15 voltas)."""
    inicio = -math.pi * 0.6 + fase
    fim = inicio + 2 * math.pi * progresso
    passos = max(int(80 * progresso), 2)
    for k in range(passos + 1):
        a = inicio + (fim - inicio) * k / passos
        # irregularidade de "mão": raio varia um pouco ao longo da volta
        rr = r * (1 + 0.06 * math.sin(3 * a + fase) + 0.03 * math.sin(7 * a))
        x, y = cx + rr * 1.08 * math.cos(a), cy + rr * 0.92 * math.sin(a)
        (ctx.move_to if k == 0 else ctx.line_to)(x, y)


def circulo_animado(posicoes: list[tuple[float, float, float]], saida: Path,
                    atraso_frames: int = 4, desenho_frames: int = 11) -> Path:
    """posicoes[i] = (x, y, raio) em pixels 1080x1920 para cada quadro da cena."""
    n = len(posicoes)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "qtrle", str(saida)], stdin=subprocess.PIPE)
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for i in range(n):
        ctx = cairo.Context(sup)
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        k = i - atraso_frames
        if k >= 0:
            x, y, r = posicoes[i]
            p = min(k / desenho_frames, 1.0)
            p = 1 - (1 - p) ** 3                       # desaceleração no fim do traço
            escala = 0.85 + 0.15 * p                   # "pop" enquanto desenha
            if k > desenho_frames:                     # pulso suave depois de desenhado
                escala *= 1 + 0.025 * math.sin((k - desenho_frames) / FPS * 2 * math.pi * 1.5)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            # sombra escura (dá leitura em fundo claro)
            ctx.set_source_rgba(0, 0, 0, 0.45)
            ctx.set_line_width(20)
            _traco(ctx, x + 3, y + 4, r * escala, 1.12 * p, 0.0)
            ctx.stroke()
            # traço vermelho
            ctx.set_source_rgba(1.0, 0.13, 0.13, 1.0)
            ctx.set_line_width(12)
            _traco(ctx, x, y, r * escala, 1.12 * p, 0.0)
            ctx.stroke()
        proc.stdin.write(bytes(sup.get_data()))
    proc.stdin.close()
    proc.wait()
    return saida
