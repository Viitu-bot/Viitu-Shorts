"""Hall da Fama: arquivo de vídeos de referência (enviados pelo dono ou top de canais) e dos nossos melhores.

Uso:
  python -m viitu.hall adicionar <link> [--origem "enviado pelo dono" | "top do canal" | "nosso"]
  python -m viitu.hall top @handle --n 5        disseca os N vídeos mais vistos do canal
  python -m viitu.hall resumo                   reconstrói hall_da_fama/README.md e as lições consolidadas

Cada vídeo vira hall_da_fama/videos/<id>.json (metadados reais + raio-X do Gemini).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as st
from collections import Counter
from pathlib import Path

from viitu import youtube_api as yt
from viitu.assistir import PROMPT_DISSECAR, perguntar

RAIZ = Path(__file__).resolve().parent.parent
HALL = RAIZ / "hall_da_fama"
VIDEOS = HALL / "videos"


def _id(link: str) -> str:
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", link)
    return m.group(1) if m else link


def adicionar(link: str, origem: str) -> dict:
    vid = _id(link)
    VIDEOS.mkdir(parents=True, exist_ok=True)
    destino = VIDEOS / f"{vid}.json"
    if destino.exists():
        print(f"já no Hall: {vid}")
        return json.loads(destino.read_text(encoding="utf-8"))
    v = yt._get("videos", 1, part="snippet,statistics,contentDetails", id=vid)["items"][0]
    sn, sti = v["snippet"], v["statistics"]
    c = yt._get("channels", 1, part="snippet,statistics", id=sn["channelId"])["items"][0]
    meta = {"id": vid, "link": f"https://youtube.com/shorts/{vid}", "titulo": sn["title"],
            "canal": sn["channelTitle"], "handle": c["snippet"].get("customUrl"),
            "inscritos_canal": int(c["statistics"].get("subscriberCount", 0)),
            "publicado": sn["publishedAt"][:16], "duracao_s": yt.duracao_segundos(v["contentDetails"]["duration"]),
            "views": int(sti.get("viewCount", 0)), "likes": int(sti.get("likeCount", 0)),
            "comentarios": int(sti.get("commentCount", 0)), "origem": origem}
    raiox = json.loads(perguntar(meta["link"], PROMPT_DISSECAR))
    reg = {"meta": meta, "raiox": raiox}
    destino.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"+ Hall: {meta['titulo']} ({meta['canal']}, {meta['views']:,} views)")
    return reg


def top(handle: str, n: int) -> None:
    arq = HALL / "canais" / f"{handle.lstrip('@')}.json"
    if not arq.exists():
        raise SystemExit(f"Rode antes: python -m viitu.canal {handle}")
    vids = json.loads(arq.read_text(encoding="utf-8"))["videos"]
    for v in sorted(vids, key=lambda x: -x["views"])[:n]:
        try:
            adicionar(v["id"], f"top do canal {handle}")
        except SystemExit as e:
            print(f"  falhou {v['id']}: {e}")


def resumo() -> None:
    regs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(VIDEOS.glob("*.json"))]
    L = ["# 🏆 Hall da Fama — Viitu Shorts\n",
         "Vídeos de referência dissecados (raio-X do Gemini + números reais da API) e os nossos melhores.",
         "Adicionar: `python -m viitu.hall adicionar <link>` (ou peça no chat: `/analisar <link>`).\n",
         "## Vídeos\n| views | likes/view | dur | s/cena | canal | título | origem |\n|---|---|---|---|---|---|---|"]
    for r in sorted(regs, key=lambda r: -r["meta"]["views"]):
        m, x = r["meta"], r["raiox"]
        lv = f"{100 * m['likes'] / max(m['views'], 1):.1f}%"
        L.append(f"| {m['views']:,} | {lv} | {m['duracao_s']}s | {x.get('ritmo', {}).get('segundos_medios_por_cena', '?')} | "
                 f"{m['canal']} | [{m['titulo']}]({m['link']}) | {m['origem']} |")
    # lições consolidadas (estatística sobre todos os raio-X)
    n = len(regs) or 1
    seta0 = sum(1 for r in regs if re.search(r"seta", json.dumps(r["raiox"].get("gancho", {}), ensure_ascii=False)
                                              + json.dumps([e for e in r["raiox"].get("efeitos_visuais", []) if e.get("tempo", "") in ("00:00", "00:01")], ensure_ascii=False), re.I))
    circ = sum(1 for r in regs if re.search(r"c[ií]rculo", json.dumps(r["raiox"].get("efeitos_visuais", []), ensure_ascii=False), re.I))
    ritmos = [r["raiox"].get("ritmo", {}).get("segundos_medios_por_cena") for r in regs]
    ritmos = [x for x in ritmos if isinstance(x, (int, float))]
    pos = Counter(str(r["raiox"].get("legenda", {}).get("posicao", "?")).lower() for r in regs)
    ppv = Counter(r["raiox"].get("legenda", {}).get("palavras_por_vez") for r in regs)
    efeitos = Counter(e.get("efeito", "").lower().split("(")[0].strip() for r in regs for e in r["raiox"].get("efeitos_visuais", []))
    sons = Counter(e.get("som", "").lower().split("/")[0].strip() for r in regs for e in r["raiox"].get("efeitos_sonoros", []))
    L += ["\n## 📊 Lições consolidadas (calculadas sobre todos os vídeos do Hall)\n",
          f"- Vídeos analisados: **{len(regs)}**",
          f"- **Seta vermelha no frame 0:** {seta0}/{len(regs)} ({100 * seta0 // n}%) · círculo em algum momento: {circ}/{len(regs)}",
          f"- **Ritmo:** mediana de **{st.median(ritmos):.1f} s por cena**" if ritmos else "- Ritmo: —",
          f"- **Legenda — posição:** {', '.join(f'{k} ({v})' for k, v in pos.most_common(4))}",
          f"- **Legenda — palavras por vez:** {', '.join(f'{k} ({v})' for k, v in ppv.most_common(3))}",
          f"- **Efeitos visuais mais usados:** {', '.join(f'{k} ({v})' for k, v in efeitos.most_common(10))}",
          f"- **Sons mais usados:** {', '.join(f'{k} ({v})' for k, v in sons.most_common(10))}",
          "\n## 🎵 Músicas observadas\n"]
    for r in regs:
        L.append(f"- **{r['meta']['canal']}** — {r['raiox'].get('musica', '?')}")
    L.append("\n## 🎯 Lições para copiar (de cada vídeo)\n")
    for r in sorted(regs, key=lambda r: -r["meta"]["views"]):
        L.append(f"**{r['meta']['titulo']}** ({r['meta']['canal']})")
        for l in r["raiox"].get("licoes_para_copiar", []):
            L.append(f"- {l}")
        L.append("")
    (HALL / "README.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:12 + len(regs)]))
    print("\n".join(L[L.index("\n## 📊 Lições consolidadas (calculadas sobre todos os vídeos do Hall)\n"):][:10]))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    a = sub.add_parser("adicionar"); a.add_argument("link"); a.add_argument("--origem", default="enviado pelo dono")
    t = sub.add_parser("top"); t.add_argument("handle"); t.add_argument("--n", type=int, default=5)
    sub.add_parser("resumo")
    x = p.parse_args()
    if x.modo == "adicionar":
        adicionar(x.link, x.origem)
    elif x.modo == "top":
        top(x.handle, x.n)
    resumo()


if __name__ == "__main__":
    main()
