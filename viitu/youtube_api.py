"""Cliente mínimo da YouTube Data API v3 (números reais, direto do Google).

A chave vem de YOUTUBE_API_KEY (variável de ambiente ou arquivo .env na raiz).
Se o ambiente injetar a chave pelo proxy (Network secrets), funciona sem variável.

Custo de cota (grátis: 10.000 unidades/dia):
  search.list = 100 | videos.list, channels.list, playlistItems.list = 1
"""

from __future__ import annotations

import datetime as dt
import os
import re
import statistics
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
BASE = "https://www.googleapis.com/youtube/v3"
cota_usada = 0


def _chave() -> str | None:
    if os.environ.get("YOUTUBE_API_KEY", "").strip():
        return os.environ["YOUTUBE_API_KEY"].strip()
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith("YOUTUBE_API_KEY="):
                return linha.split("=", 1)[1].strip()
    return None


def _get(recurso: str, custo: int, **params) -> dict:
    global cota_usada
    headers = {}
    chave = _chave()
    if chave:
        headers["X-Goog-Api-Key"] = chave
    r = requests.get(f"{BASE}/{recurso}", params=params, headers=headers, timeout=30)
    cota_usada += custo
    dados = r.json()
    if "error" in dados:
        raise RuntimeError(f"YouTube API ({recurso}): {dados['error'].get('message')}")
    return dados


def duracao_segundos(iso: str) -> int:
    m = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def buscar_ids(termo: str, dias: int = 60, maximo: int = 25,
               idioma: str | None = None, regiao: str | None = None) -> list[str]:
    """IDs dos vídeos curtos (<4 min) mais vistos para o termo, publicados nos últimos `dias`."""
    depois = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = dict(part="id", q=termo, type="video", videoDuration="short",
                  order="viewCount", publishedAfter=depois, maxResults=maximo)
    if idioma:
        params["relevanceLanguage"] = idioma
    if regiao:
        params["regionCode"] = regiao
    dados = _get("search", 100, **params)
    return [i["id"]["videoId"] for i in dados.get("items", []) if i.get("id", {}).get("videoId")]


def detalhes_videos(ids: list[str]) -> list[dict]:
    """Views, título, canal, data e duração. Filtra só Shorts (<= 3 min)."""
    saida = []
    for i in range(0, len(ids), 50):
        lote = ids[i:i + 50]
        dados = _get("videos", 1, part="snippet,statistics,contentDetails", id=",".join(lote))
        for v in dados.get("items", []):
            dur = duracao_segundos(v["contentDetails"].get("duration", ""))
            if dur == 0 or dur > 180:
                continue
            sn, st = v["snippet"], v.get("statistics", {})
            saida.append({
                "id": v["id"],
                "titulo": sn.get("title", ""),
                "canal": sn.get("channelTitle", ""),
                "canal_id": sn.get("channelId", ""),
                "publicado": sn.get("publishedAt", "")[:10],
                "idioma": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "?",
                "duracao_s": dur,
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)) if st.get("likeCount") else None,
                "link": f"https://www.youtube.com/shorts/{v['id']}",
            })
    return saida


_cache_canais: dict[str, dict] = {}


def perfil_canal(canal_id: str, amostra: int = 50) -> dict:
    """Inscritos e mediana de views dos últimos `amostra` uploads do canal."""
    if canal_id in _cache_canais:
        return _cache_canais[canal_id]
    dados = _get("channels", 1, part="statistics,contentDetails,snippet", id=canal_id)
    if not dados.get("items"):
        return {}
    c = dados["items"][0]
    uploads = c["contentDetails"]["relatedPlaylists"]["uploads"]
    itens = _get("playlistItems", 1, part="contentDetails", playlistId=uploads, maxResults=amostra)
    ids = [i["contentDetails"]["videoId"] for i in itens.get("items", [])]
    views = []
    if ids:
        st = _get("videos", 1, part="statistics", id=",".join(ids))
        views = [int(v["statistics"].get("viewCount", 0)) for v in st.get("items", [])]
    perfil = {
        "inscritos": int(c["statistics"].get("subscriberCount", 0)),
        "total_videos": int(c["statistics"].get("videoCount", 0)),
        "criado": c["snippet"].get("publishedAt", "")[:10],
        "mediana_views": int(statistics.median(views)) if views else 0,
    }
    _cache_canais[canal_id] = perfil
    return perfil
