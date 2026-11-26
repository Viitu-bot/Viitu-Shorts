"""AMPLIAÇÃO POR IA (Real-ESRGAN x4, pesos oficiais em assets/ia/RealESRGAN_x4plus.pth) para clipe de arquivo em baixa
resolução (dono 26/11: "a qualidade está me incomodando"). Roda na CPU: recorta ANTES só a janela 9:16 usada na cena, para
ser rápido, e devolve um clipe novo em clipes/ (a cena passa a apontar para ele, inicio 0, sem foco).

Uso: python3 -m viitu.ampliar <projeto> <clipe> <inicio> <dur> <foco_x> <saida.mp4>
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

RAIZ = Path(__file__).resolve().parent.parent
PESOS = RAIZ / "assets" / "ia" / "RealESRGAN_x4plus.pth"


class RDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
        self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
        self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        return self.conv5(torch.cat((x, x1, x2, x3, x4), 1)) * 0.2 + x


class RRDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.rdb1, self.rdb2, self.rdb3 = RDB(nf, gc), RDB(nf, gc), RDB(nf, gc)

    def forward(self, x):
        return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(self, nf=64, nb=23, gc=32):
        super().__init__()
        self.conv_first = nn.Conv2d(3, nf, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        feat = self.conv_first(x)
        feat = feat + self.conv_body(self.body(feat))
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))


def _modelo() -> RRDBNet:
    if not PESOS.exists():                       # pesos fora do git (67 MB): baixa da versão oficial
        PESOS.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sL", "-o", str(PESOS),
                        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"], check=True)
    m = RRDBNet()
    sd = torch.load(PESOS, map_location="cpu")
    m.load_state_dict(sd.get("params_ema", sd.get("params", sd)), strict=True)
    torch.set_num_threads(max(1, torch.get_num_threads()))
    return m.eval()


def ampliar(projeto: str, clipe: str, inicio: float, dur: float, foco_x: float, saida: str) -> Path:
    pasta = RAIZ / "projetos" / projeto / "clipes"
    src = pasta / clipe
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                    "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip().split(","))
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip()
    cw = (h * 9 // 16) // 2 * 2
    cx = int((w - cw) * foco_x) // 2 * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{inicio:.2f}", "-t", f"{dur:.2f}", "-i", str(src),
                          "-vf", f"crop={cw}:{h}:{cx}:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (cw * h * 3)
    quadros = np.frombuffer(raw[: n * cw * h * 3], np.uint8).reshape(n, h, cw, 3)
    m = _modelo()
    out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cw * 4}x{h * 4}",
                            "-r", fps, "-i", "-", "-c:v", "libx264", "-crf", "15", "-pix_fmt", "yuv420p", str(pasta / saida)],
                           stdin=subprocess.PIPE)
    with torch.no_grad():
        for i, q in enumerate(quadros):
            t = torch.from_numpy(q.astype(np.float32) / 255).permute(2, 0, 1)[None]
            y = m(t).clamp(0, 1)[0].permute(1, 2, 0).numpy()
            out.stdin.write((y * 255 + 0.5).astype(np.uint8).tobytes())
            print(f"  quadro {i + 1}/{n}", flush=True)
    out.stdin.close()
    out.wait()
    print(f"Ampliado: clipes/{saida} ({cw * 4}x{h * 4}, {n} quadros)")
    return pasta / saida


if __name__ == "__main__":
    p, c, i, d, fx, s = sys.argv[1:7]
    ampliar(p, c, float(i), float(d), float(fx), s)
