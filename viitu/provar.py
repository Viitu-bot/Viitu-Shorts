"""Trava contra número errado: confere AO VIVO na YouTube Data API todo vídeo citado ao dono.

Uso: python -m viitu.provar <link ou id> [<link ou id> ...] --papel validacao|bruto|referencia
Imprime a linha pronta para colar na resposta (papel + título + canal + views + link) e registra em
dados/provas.jsonl. REGRA: nenhum número de views vai para o dono sem passar por aqui na mesma resposta,
e cada vídeo vem rotulado pelo PAPEL dele (a prova do tema é uma coisa; o bruto é outra).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from viitu import youtube_api as yt

RAIZ = Path(__file__).resolve().parent.parent
ROTULO = {"validacao": "✅ PROVA DO TEMA", "bruto": "🎬 BRUTO (material)", "referencia": "📌 REFERÊNCIA"}


def _id(x: str) -> str:
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", x)
    return m.group(1) if m else x


def provar(links: list[str], papel: str) -> list[dict]:
    ids = [_id(x) for x in links]
    itens = yt._get("videos", 1, part="snippet,statistics,contentDetails", id=",".join(ids)).get("items", [])
    achados = {i["id"]: i for i in itens}
    out = []
    for vid in ids:
        if vid not in achados:
            print(f"❌ {vid}: não encontrado na API — NÃO citar")
            continue
        v = achados[vid]
        reg = {"quando": dt.datetime.now().isoformat(timespec="seconds"), "papel": papel, "id": vid,
               "titulo": v["snippet"]["title"], "canal": v["snippet"]["channelTitle"],
               "views": int(v["statistics"].get("viewCount", 0)), "publicado": v["snippet"]["publishedAt"][:10],
               "duracao_s": yt.duracao_segundos(v["contentDetails"]["duration"]),
               "link": f"https://youtube.com/shorts/{vid}" if yt.duracao_segundos(v["contentDetails"]["duration"]) <= 180
               else f"https://youtu.be/{vid}"}
        out.append(reg)
        print(f"{ROTULO[papel]} | \"{reg['titulo']}\" ({reg['canal']}) | {reg['views']:,} views (conferido agora) | {reg['link']}")
        if papel in ("validacao", "bruto") and reg["views"] < 1_000_000:
            print(f"   ⚠️ menos de 1 milhão de views: não serve como {papel}")
    with (RAIZ / "dados" / "provas.jsonl").open("a", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("links", nargs="+")
    ap.add_argument("--papel", choices=list(ROTULO), required=True)
    a = ap.parse_args()
    provar(a.links, a.papel)
