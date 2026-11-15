"""Análise algorítmica de um canal (números reais da YouTube Data API).

Uso:
  python -m viitu.canal @handle [--n 200]
Gera hall_da_fama/canais/<handle>.md e .json com:
  ritmo de postagem, dia/horário (Brasília) x views, duração x views, padrões de título
  (palavra inicial, emoji, CAIXA ALTA, pergunta, número, "Esse/Essa"), engajamento, top e piores vídeos.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

from viitu import youtube_api as yt

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "hall_da_fama" / "canais"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def coletar(handle: str, n: int) -> tuple[dict, list[dict]]:
    c = yt._get("channels", 1, part="snippet,statistics,contentDetails", forHandle=handle.lstrip("@"))["items"][0]
    up = c["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while len(ids) < n:
        r = yt._get("playlistItems", 1, part="contentDetails", playlistId=up, maxResults=50,
                    **({"pageToken": tok} if tok else {}))
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break
    vids = []
    for i in range(0, len(ids[:n]), 50):
        r = yt._get("videos", 1, part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
        for v in r["items"]:
            d = yt.duracao_segundos(v["contentDetails"]["duration"])
            if not 0 < d <= 180:
                continue
            t = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00")) - dt.timedelta(hours=3)
            s = v["statistics"]
            vids.append({"id": v["id"], "titulo": v["snippet"]["title"], "dur": d, "views": int(s.get("viewCount", 0)),
                         "likes": int(s.get("likeCount", 0)), "coment": int(s.get("commentCount", 0)),
                         "data": t.strftime("%Y-%m-%d"), "hora": t.hour, "dia": DIAS[t.weekday()],
                         "tags": v["snippet"].get("tags", [])})
    info = {"nome": c["snippet"]["title"], "handle": handle, "inscritos": int(c["statistics"].get("subscriberCount", 0)),
            "videos_total": int(c["statistics"].get("videoCount", 0)), "criado": c["snippet"]["publishedAt"][:10]}
    return info, vids


def _med(xs):
    return int(st.median(xs)) if xs else 0


def _fmt(n):
    return f"{n / 1e6:.1f}M" if n >= 1e6 else (f"{n / 1e3:.0f}k" if n >= 1e3 else str(n))


def analisar(info: dict, vids: list[dict]) -> str:
    L = []
    views = [v["views"] for v in vids]
    datas = sorted(v["data"] for v in vids)
    dias_periodo = max((dt.date.fromisoformat(datas[-1]) - dt.date.fromisoformat(datas[0])).days, 1)
    L.append(f"# {info['nome']} ({info['handle']})\n")
    L.append(f"- {info['inscritos']:,} inscritos · {info['videos_total']} vídeos · criado em {info['criado']}")
    L.append(f"- Amostra: {len(vids)} Shorts de {datas[0]} a {datas[-1]} → **{len(vids) / dias_periodo:.2f} vídeos/dia**")
    L.append(f"- Views: mediana **{_fmt(_med(views))}** · {100 * sum(x >= 100_000 for x in views) // len(views)}% ≥100k · "
             f"{100 * sum(x >= 1_000_000 for x in views) // len(views)}% ≥1M")
    lk = [v["likes"] / v["views"] for v in vids if v["views"] > 1000]
    cm = [v["coment"] / v["views"] for v in vids if v["views"] > 1000]
    L.append(f"- Engajamento: likes/view mediana **{100 * st.median(lk):.2f}%** · comentários/view {100 * st.median(cm):.3f}%\n")

    def tabela(titulo, grupos):
        L.append(f"## {titulo}\n| grupo | vídeos | mediana views | ≥100k |\n|---|---|---|---|")
        for g, xs in grupos:
            if xs:
                L.append(f"| {g} | {len(xs)} | {_fmt(_med(xs))} | {100 * sum(x >= 100_000 for x in xs) // len(xs)}% |")
        L.append("")

    faixas = [(0, 20), (21, 30), (31, 45), (46, 60), (61, 90), (91, 180)]
    tabela("Duração x views", [(f"{a}–{b} s", [v["views"] for v in vids if a <= v["dur"] <= b]) for a, b in faixas])
    horas = defaultdict(list)
    for v in vids:
        horas[v["hora"]].append(v["views"])
    tabela("Horário de postagem (Brasília) x views", [(f"{h:02d}h", horas[h]) for h in sorted(horas)])
    dias = defaultdict(list)
    for v in vids:
        dias[v["dia"]].append(v["views"])
    tabela("Dia da semana x views", [(d, dias[d]) for d in DIAS])

    feats = {
        "começa com 'Esse/Essa/Esses/Essas'": lambda t: re.match(r"(?i)^ess[ea]s?\b", t),
        "começa com 'O/A/Os/As'": lambda t: re.match(r"^(O|A|Os|As)\b", t),
        "começa com 'Por que/Como/O que'": lambda t: re.match(r"(?i)^(por ?que|como|o que)\b", t),
        "tem palavra em CAIXA ALTA (≥4 letras)": lambda t: re.search(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{4,}\b", t),
        "termina com '?' ou '!?'": lambda t: re.search(r"\?\s*\S*$", EMOJI.sub("", t).strip()),
        "tem número": lambda t: re.search(r"\d", t),
        "tem emoji": lambda t: EMOJI.search(t),
        "tem hashtag no título": lambda t: "#" in t,
    }
    L.append("## Padrões de título x views\n| padrão | com (n · mediana) | sem (n · mediana) | efeito |\n|---|---|---|---|")
    for nome, f in feats.items():
        com = [v["views"] for v in vids if f(v["titulo"])]
        sem = [v["views"] for v in vids if not f(v["titulo"])]
        if com and sem:
            ef = _med(com) / max(_med(sem), 1)
            L.append(f"| {nome} | {len(com)} · {_fmt(_med(com))} | {len(sem)} · {_fmt(_med(sem))} | {ef:.1f}x |")
    pal = [len(EMOJI.sub("", v["titulo"]).split()) for v in vids]
    L.append(f"\n- Título: mediana de **{st.median(pal):.0f} palavras**; emojis mais usados: "
             f"{' '.join(e for e, _ in Counter(e for v in vids for e in EMOJI.findall(v['titulo'])).most_common(8))}")
    prim = Counter(EMOJI.sub("", v["titulo"]).split()[0].lower() for v in vids if v["titulo"].split())
    L.append(f"- Palavras iniciais mais comuns: {', '.join(f'{p} ({n})' for p, n in prim.most_common(10))}\n")

    ordem = sorted(vids, key=lambda v: -v["views"])
    L.append("## Top 15\n| views | dur | data | título |\n|---|---|---|---|")
    for v in ordem[:15]:
        L.append(f"| {_fmt(v['views'])} | {v['dur']}s | {v['data']} {v['hora']:02d}h | [{v['titulo']}](https://youtube.com/shorts/{v['id']}) |")
    L.append("\n## Piores 8\n| views | dur | título |\n|---|---|---|")
    for v in ordem[-8:]:
        L.append(f"| {_fmt(v['views'])} | {v['dur']}s | {v['titulo']} |")
    return "\n".join(L)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("handle")
    p.add_argument("--n", type=int, default=200)
    a = p.parse_args()
    info, vids = coletar(a.handle, a.n)
    PASTA.mkdir(parents=True, exist_ok=True)
    nome = a.handle.lstrip("@")
    (PASTA / f"{nome}.json").write_text(json.dumps({"info": info, "videos": vids}, ensure_ascii=False, indent=1), encoding="utf-8")
    md = analisar(info, vids)
    (PASTA / f"{nome}.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"\n(cota usada: {yt.cota_usada})")


if __name__ == "__main__":
    main()
