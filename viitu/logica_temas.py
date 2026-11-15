"""Engenharia reversa da ESCOLHA DE TEMAS dos canais de referência.

1. Classifica todos os títulos (Gemini, texto) em categoria / gatilho / objeto + busca em inglês.
2. Para os maiores sucessos e fracassos de cada canal, procura no YouTube se o MESMO tema já tinha
   viralizado ANTES (outro idioma) e quanto tempo antes (atraso).
3. Mede: % de temas "pré-validados" nos sucessos x nos fracassos; desempenho por categoria e gatilho.

Uso:
  python -m viitu.logica_temas classificar @handle [@handle ...]
  python -m viitu.logica_temas prevalidacao @handle --top 12 --piores 6
  python -m viitu.logica_temas relatorio
Saída: hall_da_fama/logica_temas.md (+ JSONs em hall_da_fama/canais/)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

import requests

from viitu import youtube_api as yt
from viitu.assistir import _chave, MODELO

RAIZ = Path(__file__).resolve().parent.parent
CANAIS = RAIZ / "hall_da_fama" / "canais"

CATEGORIAS = ["como é feito (processo/fábrica)", "motivo oculto de objeto/design", "animal com comportamento estranho",
              "lugar/cultura de outro país", "truque/hack do dia a dia", "perigo/erro/segurança",
              "recorde/escala/mais caro do mundo", "invenção/tecnologia", "corpo humano/saúde",
              "comida/culinária curiosa", "pessoa/feito extraordinário", "natureza/fenômeno", "outro"]
GATILHOS = ["motivo oculto (por que é assim)", "processo revelado (como fazem)", "surpresa visual (olha isso)",
            "perigo/medo", "dinheiro/escala", "nojo/estranheza", "fofura/emoção", "utilidade (truque)", "mito desmentido"]


def _gemini_texto(prompt: str) -> str:
    import time
    corpo = {"contents": [{"parts": [{"text": prompt}]}],
             "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}}
    for tentativa in range(6):
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent",
                              params={"key": _chave()}, json=corpo, timeout=300).json()
        except requests.RequestException as e:      # queda de rede/proxy: espera e tenta de novo
            r = {"error": {"message": str(e)[:120]}}
        if "error" in r:
            time.sleep(15 * (tentativa + 1))
            continue
        return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])
    raise SystemExit(f"Gemini indisponível: {r.get('error', {}).get('message')}")


def classificar(handle: str) -> None:
    arq = CANAIS / f"{handle.lstrip('@')}.json"
    d = json.loads(arq.read_text(encoding="utf-8"))
    vids = d["videos"]
    for i in range(0, len(vids), 80):
        lote = vids[i:i + 80]
        lista = "\n".join(f'{k}. {v["titulo"]}' for k, v in enumerate(lote))
        prompt = (f"Classifique cada título de YouTube Shorts de curiosidade (em português). Categorias: {CATEGORIAS}. "
                  f"Gatilhos: {GATILHOS}. Para cada um devolva um objeto com: i (número), categoria (uma da lista), "
                  "gatilho (um da lista), objeto (o assunto em 1–3 palavras), busca_en (busca curta em inglês para achar "
                  "vídeos do MESMO tema no YouTube, 3–6 palavras). Responda só JSON: {\"itens\": [...]}.\n\n" + lista)
        itens = json.loads(_gemini_texto(prompt))["itens"]
        for it in itens:
            k = int(it["i"])
            if 0 <= k < len(lote):
                lote[k].update({x: it.get(x) for x in ("categoria", "gatilho", "objeto", "busca_en")})
        print(f"  {handle}: {min(i + 80, len(vids))}/{len(vids)} classificados")
    arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def prevalidacao(handle: str, n_top: int, n_piores: int) -> None:
    arq = CANAIS / f"{handle.lstrip('@')}.json"
    d = json.loads(arq.read_text(encoding="utf-8"))
    vids = [v for v in d["videos"] if v.get("busca_en")]
    ordem = sorted(vids, key=lambda v: -v["views"])
    alvo = [("top", v) for v in ordem[:n_top]] + [("pior", v) for v in ordem[-n_piores:]]
    for grupo, v in alvo:
        if "previo" in v:
            continue
        antes = f"{v['data']}T00:00:00Z"
        r = yt._get("search", 100, part="id", q=v["busca_en"], type="video", videoDuration="short",
                    order="viewCount", publishedBefore=antes, maxResults=10)
        ids = [i["id"]["videoId"] for i in r.get("items", [])]
        melhor = None
        if ids:
            det = yt._get("videos", 1, part="snippet,statistics", id=",".join(ids))["items"]
            det = [x for x in det if x["snippet"]["channelTitle"] != d["info"]["nome"]]
            if det:
                x = max(det, key=lambda x: int(x["statistics"].get("viewCount", 0)))
                melhor = {"views": int(x["statistics"].get("viewCount", 0)), "titulo": x["snippet"]["title"],
                          "canal": x["snippet"]["channelTitle"], "data": x["snippet"]["publishedAt"][:10],
                          "idioma": x["snippet"].get("defaultAudioLanguage"),
                          "atraso_dias": (dt.date.fromisoformat(v["data"]) - dt.date.fromisoformat(x["snippet"]["publishedAt"][:10])).days,
                          "link": f"https://youtube.com/shorts/{x['id']}"}
        v["previo"] = melhor
        v["grupo"] = grupo
        txt = f"{melhor['views']:,} ({melhor['atraso_dias']} dias antes)" if melhor else "nada antes"
        print(f"  [{grupo}] {v['views']:>10,} | {v['titulo'][:55]:<55} | prévio: {txt}")
    arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"(cota usada: {yt.cota_usada})")


def _fmt(n):
    return f"{n / 1e6:.1f}M" if n >= 1e6 else (f"{n / 1e3:.0f}k" if n >= 1e3 else str(n))


def relatorio() -> None:
    L = ["# 🧠 Lógica de escolha de temas — engenharia reversa (dados reais)\n"]
    todos_prev = defaultdict(list)
    for arq in sorted(CANAIS.glob("*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        vids = [v for v in d["videos"] if v.get("categoria")]
        if not vids:
            continue
        L.append(f"## {d['info']['nome']} ({len(vids)} vídeos classificados)\n")
        for campo, rotulo in (("categoria", "Categoria"), ("gatilho", "Gatilho")):
            g = defaultdict(list)
            for v in vids:
                g[v[campo]].append(v["views"])
            L.append(f"| {rotulo} | vídeos | % do canal | mediana views | ≥1M |\n|---|---|---|---|---|")
            for k, xs in sorted(g.items(), key=lambda kv: -st.median(kv[1])):
                L.append(f"| {k} | {len(xs)} | {100 * len(xs) // len(vids)}% | {_fmt(int(st.median(xs)))} | "
                         f"{100 * sum(x >= 1e6 for x in xs) // len(xs)}% |")
            L.append("")
        prev = [v for v in d["videos"] if "previo" in v]
        if prev:
            L.append("**Pré-validação (o mesmo tema já tinha viralizado antes, em outro canal?)**\n")
            L.append("| grupo | vídeos | com tema prévio ≥1M | mediana views do prévio | atraso mediano |\n|---|---|---|---|---|")
            for grupo in ("top", "pior"):
                xs = [v for v in prev if v.get("grupo") == grupo]
                if not xs:
                    continue
                com = [v for v in xs if v["previo"] and v["previo"]["views"] >= 1e6]
                vp = [v["previo"]["views"] for v in xs if v["previo"]]
                at = [v["previo"]["atraso_dias"] for v in xs if v["previo"]]
                todos_prev[grupo] += xs
                L.append(f"| {grupo} | {len(xs)} | {len(com)} ({100 * len(com) // len(xs)}%) | "
                         f"{_fmt(int(st.median(vp))) if vp else '—'} | {int(st.median(at)) if at else '—'} dias |")
            L.append("\nExemplos (sucessos):\n")
            for v in [v for v in prev if v.get("grupo") == "top"][:8]:
                p = v["previo"]
                L.append(f"- **{v['titulo']}** ({_fmt(v['views'])}) ← "
                         + (f"\"{p['titulo'][:60]}\" de {p['canal']} ({_fmt(p['views'])}, {p['atraso_dias']} dias antes)" if p else "nada antes"))
            L.append("")
    if todos_prev:
        L.append("## ✅ Conclusão geral (3 canais somados)\n")
        for grupo in ("top", "pior"):
            xs = todos_prev[grupo]
            com = [v for v in xs if v["previo"] and v["previo"]["views"] >= 1e6]
            L.append(f"- **{grupo}**: {len(com)}/{len(xs)} ({100 * len(com) // max(len(xs), 1)}%) tinham o tema já viral (≥1M) antes")
    (RAIZ / "hall_da_fama" / "logica_temas.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    c = sub.add_parser("classificar"); c.add_argument("handles", nargs="+")
    pv = sub.add_parser("prevalidacao"); pv.add_argument("handle"); pv.add_argument("--top", type=int, default=12)
    pv.add_argument("--piores", type=int, default=6)
    sub.add_parser("relatorio")
    a = p.parse_args()
    if a.modo == "classificar":
        for h in a.handles:
            classificar(h)
    elif a.modo == "prevalidacao":
        prevalidacao(a.handle, a.top, a.piores)
    else:
        relatorio()


if __name__ == "__main__":
    main()
