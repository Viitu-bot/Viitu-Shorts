"""Baixa um clipe de TikTok/X/Instagram para o projeto.

Uso: python3 -m viitu.baixar <link> <arquivo_destino.mp4>

Ordem: yt-dlp → (só TikTok) ssstik.io.
Por quê (24/11): o TikTok entrega a página para servidores na nuvem, mas com o endereço do vídeo vazio
("No video formats found" no yt-dlp, mesmo com --impersonate). O ssstik baixa do lado dele e devolve o
arquivo sem marca d'água, na resolução original do post.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/136.0 Safari/537.36"}


def _ytdlp(link: str, destino: Path) -> bool:
    p = subprocess.run(["yt-dlp", "--quiet", "--no-warnings", "-f", "mp4/best", "-o", str(destino), link],
                       capture_output=True, text=True, timeout=300)
    return p.returncode == 0 and destino.exists() and destino.stat().st_size > 50_000


def ssstik_link(link: str) -> str:
    """Endereço direto do mp4 sem marca d'água (TikTok)."""
    s = requests.Session()
    s.headers.update(UA)
    casa = s.get("https://ssstik.io/", timeout=30).text
    tt = re.search(r"s_tt\s*=\s*'([^']+)'", casa)
    if not tt:
        raise RuntimeError("ssstik mudou a página (token não encontrado)")
    m = None
    for _ in range(4):          # a 1ª resposta às vezes vem vazia (24/11); repetir resolve
        r = s.post("https://ssstik.io/abc?url=dl", timeout=60,
                   headers={"HX-Request": "true", "HX-Target": "target", "Origin": "https://ssstik.io",
                            "Referer": "https://ssstik.io/"},
                   data={"id": link, "locale": "en", "tt": tt.group(1)})
        m = re.search(r'href="(https://tikcdn\.io/ssstik/\d+[^"]*)"', r.text)
        if m:
            break
        time.sleep(3)
    if not m:
        raise RuntimeError("ssstik não devolveu o vídeo (post apagado/privado ou site mudou)")
    return m.group(1).replace("&amp;", "&")


def _ssstik(link: str, destino: Path) -> bool:
    url = ssstik_link(link)
    with requests.get(url, headers=UA, timeout=180, stream=True) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for parte in r.iter_content(1 << 16):
                f.write(parte)
    return destino.stat().st_size > 50_000


def baixar(link: str, destino: str | Path) -> str:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if _ytdlp(link, destino):
        return "yt-dlp"
    if "tiktok.com" in link and _ssstik(link, destino):
        return "ssstik"
    raise RuntimeError(f"não consegui baixar {link}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    via = baixar(sys.argv[1], sys.argv[2])
    print(f"✅ {sys.argv[2]} (via {via})")
