"""O que está quente AGORA (não o que estourou meses atrás).

Duas fontes, as duas de graça:
1. Shorts publicados nos últimos N dias, ordenados por views (YouTube Data API), com buscas do nicho em EN e PT.
   Mostra views/hora: quem ganha muito por hora está subindo agora.
2. Google Trends "em alta agora" (RSS) do Brasil e dos EUA, sem futebol/loteria/celebridade.

Uso:  python3 -m viitu.quente [--dias 7] [--min 300000]
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
BUSCAS = {
    "en": ["how it works engineering", "why is it designed", "dangerous job", "giant machine", "hidden reason",
           "satisfying process factory", "physics explained", "you didn't know this"],
    "pt": ["como funciona", "por que", "curiosidades engenharia", "trabalho perigoso", "você sabia"],
}
FORA = re.compile(r" x |vs\.?| fc|futebol|jogo|mega.?sena|lotof|quina|resultado|bbb|novela|nba|nfl|ufc|"
                  r"palmeiras|corinthians|flamengo|santos|grêmio|cruzeiro|botafogo|vasco|são paulo|playing|score",
                  re.I)


def _chave() -> str:
    arq = RAIZ / ".env"
    for l in (arq.read_text().splitlines() if arq.exists() else []):
        if l.startswith("YOUTUBE_API_KEY="):
            return l.split("=", 1)[1].strip()
    return os.environ.get("YOUTUBE_API_KEY", "")


def shorts_recentes(dias: int = 7, minimo: int = 300_000) -> list[dict]:
    k = _chave()
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids: dict[str, str] = {}
    for lang, qs in BUSCAS.items():
        for q in qs:
            r = requests.get("https://www.googleapis.com/youtube/v3/search", timeout=30, params={
                "part": "id", "q": q + " #shorts", "type": "video", "videoDuration": "short", "order": "viewCount",
                "publishedAfter": desde, "maxResults": 25, "relevanceLanguage": lang, **({"key": k} if k else {})}).json()
            for it in r.get("items", []):
                ids[it["id"]["videoId"]] = lang
    out, lista = [], list(ids)
    for i in range(0, len(lista), 50):
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", timeout=30, params={
            "part": "snippet,statistics,contentDetails", "id": ",".join(lista[i:i + 50]), **({"key": k} if k else {})}).json()
        for v in r.get("items", []):
            views = int(v["statistics"].get("viewCount", 0))
            if views < minimo:
                continue
            pub = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            horas = max((dt.datetime.now(dt.timezone.utc) - pub).total_seconds() / 3600, 1)
            out.append({"id": v["id"], "titulo": v["snippet"]["title"], "canal": v["snippet"]["channelTitle"],
                        "views": views, "vph": round(views / horas), "dias": round(horas / 24, 1),
                        "idioma": ids[v["id"]], "link": f"https://youtube.com/shorts/{v['id']}"})
    return sorted(out, key=lambda x: -x["vph"])


def google_trends() -> list[tuple[str, str, str]]:
    out = []
    for geo in ("BR", "US"):
        t = requests.get(f"https://trends.google.com/trending/rss?geo={geo}", timeout=30).text
        for item in re.findall(r"<item>(.*?)</item>", t, re.S):
            ti = re.search(r"<title>(.*?)</title>", item)
            tr = re.search(r"<ht:approx_traffic>(.*?)</ht:approx_traffic>", item)
            nt = re.search(r"<ht:news_item_title>(.*?)</ht:news_item_title>", item)
            if ti and not FORA.search(ti.group(1) + " " + (nt.group(1) if nt else "")):
                out.append((geo, ti.group(1), (tr.group(1) if tr else "?") + " | " + (nt.group(1)[:90] if nt else "")))
    return out


def main() -> None:
    dias = int(sys.argv[sys.argv.index("--dias") + 1]) if "--dias" in sys.argv else 7
    minimo = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 300_000
    s = shorts_recentes(dias, minimo)
    hoje = dt.date.today().isoformat()
    (RAIZ / "dados" / "pesquisas").mkdir(parents=True, exist_ok=True)
    (RAIZ / "dados" / "pesquisas" / f"{hoje}_quente.json").write_text(json.dumps(s, ensure_ascii=False, indent=1))
    print(f"## Shorts dos últimos {dias} dias com ≥ {minimo:,} views (ordem: views por hora)")
    for x in s[:30]:
        print(f"{x['vph']:>8,}/h | {x['views']:>11,} | {x['dias']:>4}d | {x['idioma']} | {x['canal'][:18]} | {x['titulo'][:70]} | {x['link']}")
    print("\n## Google Trends agora (sem esporte/loteria)")
    for geo, t, info in google_trends()[:20]:
        print(f"{geo} | {t} | {info}")


if __name__ == "__main__":
    main()
