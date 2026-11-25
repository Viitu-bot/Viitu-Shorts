"""SAÚDE DO PROJETO: testa em segundos cada serviço de que o pipeline depende e diz o plano B de quem falhar.
Rodar no começo de cada sessão (e quando algo engasgar):  python3 -m viitu.saude
Plano B completo: dados/plano_b.md. O vidIQ é conferido pelo Claude com `vidiq_balance` (não tem API em Python).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "ViituBot/1.0 (educational research)"}


def _env(nome: str) -> str:
    import os
    if os.environ.get(nome):        # variáveis do ambiente da nuvem valem primeiro (iguais às outras partes do código)
        return os.environ[nome]
    arq = RAIZ / ".env"
    if arq.exists():
        for l in arq.read_text().splitlines():
            if l.startswith(nome + "="):
                return l.split("=", 1)[1].strip()
    return ""


def _t(fn):
    try:
        ok, info = fn()
    except Exception as e:      # qualquer falha de rede/chave vira FALHA com o motivo
        ok, info = False, str(e)[:90]
    return ok, info


def yt_videos():
    r = requests.get("https://www.googleapis.com/youtube/v3/videos", timeout=20,
                     params={"part": "id", "id": "dQw4w9WgXcQ", "key": _env("YOUTUBE_API_KEY")}).json()
    return ("items" in r), r.get("error", {}).get("message", "ok")[:90]


def yt_busca():
    r = requests.get("https://www.googleapis.com/youtube/v3/search", timeout=20,
                     params={"part": "id", "q": "teste", "maxResults": 1, "type": "video", "key": _env("YOUTUBE_API_KEY")}).json()
    return ("items" in r), r.get("error", {}).get("message", "ok (gastou 100 da cota)")[:90]


def gemini():
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent",
                      params={"key": _env("GEMINI_API_KEY")}, timeout=40,
                      json={"contents": [{"parts": [{"text": "responda só: ok"}]}]}).json()
    return ("candidates" in r), r.get("error", {}).get("message", "ok")[:90]


def elevenlabs():
    # /v1/models responde rápido; /v1/user/subscription trava às vezes mesmo com a voz funcionando (18/11)
    r = requests.get("https://api.elevenlabs.io/v1/models", headers={"xi-api-key": "proxy-injected"}, timeout=30)
    return r.status_code == 200, f"HTTP {r.status_code}"


def pixabay():
    r = requests.get("https://pixabay.com/api/videos/", timeout=20, params={"key": _env("PIXABAY_API_KEY"), "q": "plane", "per_page": 3})
    return r.status_code == 200, f"HTTP {r.status_code}"


def pexels():
    r = requests.get("https://api.pexels.com/videos/search", timeout=20, params={"query": "plane", "per_page": 1},
                     headers={"Authorization": "proxy-injected"})
    return r.status_code == 200, f"HTTP {r.status_code}" + (" (chave salva errada: precisa ser a chave pura, sem 'Bearer')" if r.status_code == 401 else "")


def commons():
    r = requests.head("https://upload.wikimedia.org/wikipedia/commons/8/82/Nocturne_in_E_flat_major%2C_Op._9_no._2.mp3",
                      headers=UA, timeout=20)
    return r.status_code == 200, f"download HTTP {r.status_code}" + (" (bloqueio temporário por excesso de pedidos)" if r.status_code == 429 else "")


def archive():
    r = requests.get("https://archive.org/metadata/AirForceOneVc-25", timeout=20)
    return r.status_code == 200, f"HTTP {r.status_code}"


def sketchfab():
    r = requests.get("https://api.sketchfab.com/v3/me", timeout=20, headers={"Authorization": "proxy-injected"})
    return r.status_code == 200, f"HTTP {r.status_code}"


def ytdlp_tiktok():
    p = subprocess.run(["yt-dlp", "--simulate", "--quiet", "--no-warnings",
                        "https://www.tiktok.com/@usa.navy.seal1/video/7677460421040803102"], capture_output=True, text=True, timeout=90)
    return p.returncode == 0, (p.stderr.strip()[:90] or "ok")


def disco():
    livre = shutil.disk_usage(RAIZ).free / 1e9
    return livre > 3, f"{livre:.1f} GB livres"


TESTES = [
    ("API do YouTube (views/provar)", yt_videos, "sem plano B para views reais: esperar a cota zerar (~5h BRT)"),
    ("API do YouTube (busca/radar)", yt_busca, "radar pelo vidIQ (trending/outliers/youtube_search)"),
    ("Gemini (classificar/analisar)", gemini, "pular a crítica; classificar temas à mão"),
    ("ElevenLabs (voz/sons/música)", elevenlabs, "sem plano B de voz: avisar o dono"),
    ("Pixabay (clipes)", pixabay, "busca automática TikTok/Instagram pelo vidIQ + yt-dlp"),
    ("Pexels (clipes)", pexels, "Pixabay / TikTok; dono corrige a chave nas configurações do ambiente"),
    ("Wikimedia Commons (clipes/fotos)", commons, "Internet Archive, NASA, TikTok/X via yt-dlp"),
    ("Internet Archive (clipes antigos)", archive, "Commons / TikTok"),
    ("Sketchfab (modelos 3D)", sketchfab, "Poly Haven / modelo em código"),
    ("yt-dlp TikTok/X/Instagram", ytdlp_tiktok, "pedir o arquivo ao dono (Drive /brutos)"),
    ("Disco", disco, "apagar clipes e renders de vídeos já postados"),
]


def main() -> None:
    print("## Saúde do projeto\n")
    falhas = []
    for nome, fn, plano_b in TESTES:
        ok, info = _t(fn)
        print(f"{'✅' if ok else '❌'} {nome}: {info}")
        if not ok:
            falhas.append(f"   → plano B: {plano_b}")
            print(falhas[-1])
    print("\nvidIQ: conferir com vidiq_balance (o Claude faz). São 150 créditos POR MÊS (renova dia 17).")
    print("Clipes não dependem dele: busca web (TikTok/X/Instagram) + yt-dlp.")
    print(f"\n{len(falhas)} serviço(s) com falha." if falhas else "\nTudo funcionando.")


if __name__ == "__main__":
    main()
