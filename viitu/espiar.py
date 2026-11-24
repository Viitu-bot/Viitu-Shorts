"""/espiar — garimpo aberto da concorrência (dono, 24/11). Coleta DADOS REAIS; os padrões quem descobre é o Claude.

Entrada: canais (@handle, link de canal) e/ou palavras-chave (pt/en, para achar canais parecidos).
Para cada canal: últimos N Shorts (YouTube Data API) → OUTLIERS = views ≥ 3× a mediana do próprio canal → dos melhores:
título, views, duração, data, transcrição (youtube-transcript-api; o YouTube bloqueia na nuvem — no PC do dono funciona;
fallback: o vídeo do mesmo canal no TikTok via yt-dlp + transcrição ElevenLabs) e os comentários mais relevantes.
Saída: analises_concorrencia/<data>_<alvo>/dados.json + base.md (tabelas). O Claude escreve padroes.md por cima.

Uso:
  python3 -m viitu.espiar @avidamaravilha @ivangeneraltv
  python3 -m viitu.espiar --buscar "curiosidades engenharia" "how it's made" --canais 4
  opções: --n 60 (Shorts por canal) · --top 5 (outliers por canal) · --x 3 (quantas vezes a mediana)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
from pathlib import Path

from viitu import youtube_api as yt
from viitu.canal import coletar

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "analises_concorrencia"


def _handle(x: str) -> str:
    m = re.search(r"youtube\.com/(@[\w.\-]+)", x)
    return m.group(1) if m else (x if x.startswith("@") else "@" + x)


def canais_por_busca(termos: list[str], quantos: int) -> list[str]:
    """Canais dos Shorts mais vistos de cada termo (últimos 90 dias)."""
    vistos: dict[str, int] = {}
    for t in termos:
        ids = yt.buscar_ids(t, dias=90, maximo=25)
        for v in yt.detalhes_videos(ids):
            cid = v.get("canal_id") or v.get("channelId")
            if cid:
                vistos[cid] = vistos.get(cid, 0) + int(v.get("views", 0))
    melhores = sorted(vistos, key=vistos.get, reverse=True)[:quantos]
    handles = []
    for cid in melhores:
        it = yt._get("channels", 1, part="snippet", id=cid).get("items", [])
        if it:
            handles.append(it[0]["snippet"].get("customUrl") or cid)
    return handles


def transcricao(video_id: str) -> tuple[str, str]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        t = YouTubeTranscriptApi().fetch(video_id, languages=["pt", "pt-BR", "en", "es"])
        return " ".join(s.text for s in t), "youtube"
    except Exception as e:                                           # na nuvem o YouTube bloqueia: registrar e seguir
        return "", f"sem transcrição ({type(e).__name__}) — rodar no PC do dono ou usar vidiq_video_transcript"


def comentarios(video_id: str, n: int = 20) -> list[dict]:
    try:
        r = yt._get("commentThreads", 1, part="snippet", videoId=video_id, order="relevance", maxResults=n, textFormat="plainText")
    except RuntimeError:
        return []
    out = []
    for i in r.get("items", []):
        s = i["snippet"]["topLevelComment"]["snippet"]
        out.append({"texto": s["textDisplay"][:300], "likes": s.get("likeCount", 0)})
    return sorted(out, key=lambda c: -c["likes"])


def espiar(alvos: list[str], n: int, top: int, x: float) -> Path:
    data = dt.date.today().isoformat()
    slug = re.sub(r"[^\w]+", "_", "_".join(a.lstrip("@") for a in alvos))[:40]
    pasta = SAIDA / f"{data}_{slug}"
    pasta.mkdir(parents=True, exist_ok=True)
    resultado, linhas = [], [f"# /espiar {data} — {', '.join(alvos)}", ""]
    for a in alvos:
        h = _handle(a)
        try:
            info, vids = coletar(h, n)
        except Exception as e:
            linhas.append(f"## {h}: erro {e}")
            continue
        med = statistics.median([v["views"] for v in vids]) if vids else 0
        outl = sorted([v for v in vids if med and v["views"] >= x * med], key=lambda v: -v["views"])[:top]
        for v in outl:
            v["vezes_mediana"] = round(v["views"] / med, 1)
            v["link"] = f"https://youtube.com/shorts/{v['id']}"
            v["transcricao"], v["fonte_transcricao"] = transcricao(v["id"])
            v["comentarios"] = comentarios(v["id"])
        resultado.append({"canal": info, "mediana_views": med, "shorts_analisados": len(vids), "outliers": outl})
        linhas += [f"## {info['nome']} ({h}) — {info['inscritos']:,} inscritos · mediana {med:,.0f} views em {len(vids)} Shorts", "",
                   "| views | ×mediana | dur | data | título |", "|---|---|---|---|---|"]
        linhas += [f"| {v['views']:,} | {v['vezes_mediana']}× | {v['dur']}s | {v['data']} | [{v['titulo'][:70]}]({v['link']}) |" for v in outl]
        linhas.append("")
    (pasta / "dados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / "base.md").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print(f"\nDados: {pasta.relative_to(RAIZ)}/dados.json (cota usada: {yt.cota_usada})")
    return pasta


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("alvos", nargs="*")
    p.add_argument("--buscar", nargs="*", default=[])
    p.add_argument("--canais", type=int, default=4)
    p.add_argument("--n", type=int, default=60)
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--x", type=float, default=3.0)
    a = p.parse_args()
    alvos = list(a.alvos) + (canais_por_busca(a.buscar, a.canais) if a.buscar else [])
    if not alvos:
        p.error("passe canais (@handle/link) ou --buscar \"palavras\"")
    espiar(alvos, a.n, a.top, a.x)


if __name__ == "__main__":
    main()
