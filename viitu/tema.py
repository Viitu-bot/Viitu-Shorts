"""Pesquisa de temas com números reais (YouTube Data API).

Uso (o Claude roda isso dentro da skill /tema):
  python -m viitu.tema candidatos segunda           # Shorts que bombaram na família do dia
  python -m viitu.tema candidatos segunda --extra "termo"   # busca adicional
  python -m viitu.tema lacuna "por que a tampinha tem anel"  # já existe em PT-BR?

Saída: tabela no terminal + JSON em dados/pesquisas/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import unicodedata
from pathlib import Path

from viitu import youtube_api as yt

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados" / "pesquisas"


def _dia(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome.lower()).encode("ascii", "ignore").decode()
    return s.replace("-feira", "").strip()


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


PESO_CATEGORIA = {   # mediana de views relativa (A vida é uma maravilha + GeneralTV + KSO), nov/2026
    "motivo oculto de objeto/design": 1.5, "recorde/escala/mais caro do mundo": 1.4, "perigo/erro/segurança": 1.3,
    "invenção/tecnologia": 1.0, "como é feito (processo/fábrica)": 1.0, "natureza/fenômeno": 0.9,
    "pessoa/feito extraordinário": 0.8, "truque/hack do dia a dia": 0.7, "lugar/cultura de outro país": 0.7,
    "comida/culinária curiosa": 0.6, "corpo humano/saúde": 0.6, "animal com comportamento estranho": 0.5, "outro": 0.4}
PESO_GATILHO = {"dinheiro/escala": 1.4, "mito desmentido": 1.4, "motivo oculto (por que é assim)": 1.3,
                "perigo/medo": 1.3, "processo revelado (como fazem)": 1.1, "nojo/estranheza": 0.9,
                "utilidade (truque)": 0.7, "surpresa visual (olha isso)": 0.7, "fofura/emoção": 0.5}


def classificar_titulos(titulos: list[str]) -> list[dict]:
    """Categoria + gatilho de cada título (Gemini, texto, grátis)."""
    from viitu.logica_temas import CATEGORIAS, GATILHOS, _gemini_texto
    lista = "\n".join(f"{k}. {t}" for k, t in enumerate(titulos))
    prompt = (f"Classifique cada título de Short de curiosidade. Categorias: {CATEGORIAS}. Gatilhos: {GATILHOS}. "
              "Devolva só JSON {\"itens\": [{\"i\": n, \"categoria\": ..., \"gatilho\": ..., \"tema_pt\": "
              "\"o tema em português em até 8 palavras\"}]}.\n\n" + lista)
    itens = json.loads(_gemini_texto(prompt))["itens"]
    out = [{} for _ in titulos]
    for it in itens:
        k = int(it.get("i", -1))
        if 0 <= k < len(out):
            out[k] = it
    return out


def candidatos(dia: str, dias: int, extras: list[str], min_views: int) -> None:
    cal = json.loads((RAIZ / "calendario.json").read_text(encoding="utf-8"))
    d = _dia(dia)
    if d not in cal:
        raise SystemExit(f"Dia '{dia}' não está no calendario.json")
    fam = cal[d]
    buscas = fam["buscas"] + extras
    print(f"Família de {d}: {fam['familia']} ({fam['descricao']})")

    vistos: dict[str, dict] = {}
    for termo in buscas:
        ids = yt.buscar_ids(termo, dias=dias, maximo=25)
        for v in yt.detalhes_videos(ids):
            v["busca"] = termo
            vistos.setdefault(v["id"], v)

    lista = []
    for v in vistos.values():
        if v["views"] < min_views:
            continue
        p = yt.perfil_canal(v["canal_id"])
        med = p.get("mediana_views") or 0
        v["mediana_canal"] = med
        v["inscritos_canal"] = p.get("inscritos", 0)
        v["canal_criado"] = p.get("criado", "")
        v["multiplicador"] = round(v["views"] / med, 1) if med else None
        # pontuação: quanto acima do próprio canal (tema puxou) x tamanho absoluto
        mult = min(v["multiplicador"] or 1, 50)
        v["pontuacao"] = round(math.log10(max(v["views"], 1)) * math.sqrt(mult), 2)
        lista.append(v)

    # peso da categoria/gatilho (o que historicamente rende mais nos canais BR de referência)
    try:
        cls = classificar_titulos([v["titulo"] for v in lista])
        for v, c in zip(lista, cls):
            v["categoria"], v["gatilho"], v["tema_pt"] = c.get("categoria"), c.get("gatilho"), c.get("tema_pt")
            peso = PESO_CATEGORIA.get(v["categoria"], 0.8) * PESO_GATILHO.get(v["gatilho"], 0.8)
            v["pontuacao"] = round(v["pontuacao"] * peso, 2)
    except SystemExit as e:
        print(f"(classificação indisponível: {e}; seguindo sem pesos)")
    lista.sort(key=lambda x: x["pontuacao"], reverse=True)
    PASTA.mkdir(parents=True, exist_ok=True)
    arq = PASTA / f"{dt.date.today().isoformat()}_{d}_candidatos.json"
    arq.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(lista)} Shorts com >= {_fmt(min_views)} views nos últimos {dias} dias "
          f"(cota usada: {yt.cota_usada})\n")
    print("pont | views | x canal | categoria / gatilho | tema | link")
    for v in lista[:30]:
        mult = f"{v['multiplicador']}x" if v["multiplicador"] else "?"
        print(f"{v['pontuacao']:>5} | {_fmt(v['views']):>6} | {mult:>6} | {str(v.get('categoria'))[:28]} / "
              f"{str(v.get('gatilho'))[:22]} | {str(v.get('tema_pt') or v['titulo'])[:60]} | {v['link']}")
    print(f"\nJSON completo: {arq.relative_to(RAIZ)}")


_PT = re.compile(r"ã|õ|ç|\bvocê\b|\bnão\b|\bisso\b|\bé\b|\besse\b|\bessa\b|\bmuito\b|\bfeit[oa]s?\b|\bsão\b|\bpra\b",
                 re.IGNORECASE)


def _em_portugues(v: dict) -> bool:
    return v["idioma"].lower().startswith("pt") or bool(_PT.search(v["titulo"]))


def lacuna(termo_pt: str, dias: int) -> None:
    ids = yt.buscar_ids(termo_pt, dias=dias, maximo=25, idioma="pt", regiao="BR")
    todos = sorted(yt.detalhes_videos(ids), key=lambda v: v["views"], reverse=True)
    vids = [v for v in todos if _em_portugues(v)]
    topo = vids[0]["views"] if vids else 0
    if topo < 100_000:
        veredito = "NÃO EXISTE (nenhum Short em PT com 100k+)"
    elif topo < 500_000:
        veredito = "EXISTE FRACO (melhor Short em PT < 500k)"
    else:
        veredito = "EXISTE FORTE"
    print(f"Lacuna PT-BR para '{termo_pt}' (últimos {dias} dias): {veredito}  (cota usada: {yt.cota_usada})")
    for v in vids[:5]:
        print(f"  PT {_fmt(v['views']):>6} | {v['publicado']} | {v['canal'][:22]} | {v['titulo'][:70]} | {v['link']}")
    estrangeiros = [v for v in todos if not _em_portugues(v)][:3]
    if estrangeiros:
        print("  (estrangeiros que aparecem para o público BR nessa busca:)")
        for v in estrangeiros:
            print(f"  -- {_fmt(v['views']):>6} | {v['canal'][:22]} | {v['titulo'][:70]}")


def brutos(termo: str, dias: int, min_views: int = 1_000_000) -> None:
    """Procura vídeos LONGOS (4–60 min) sobre o tema: os 'brutos' de onde saem vários Shorts.
    Só lista material que já provou que prende (>= min_views). Bruto com poucas views não serve."""
    vistos = []
    for dur in ("medium", "long"):
        depois = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
        d = yt._get("search", 100, part="id", q=termo, type="video", order="viewCount",
                    videoDuration=dur, publishedAfter=depois, maxResults=10)
        ids = [i["id"]["videoId"] for i in d.get("items", [])]
        if ids:
            for v in yt._get("videos", 1, part="snippet,statistics,contentDetails", id=",".join(ids))["items"]:
                vistos.append((int(v["statistics"].get("viewCount", 0)), yt.duracao_segundos(v["contentDetails"]["duration"]),
                               v["snippet"]["channelTitle"], v["snippet"]["publishedAt"][:10], v["snippet"]["title"], v["id"]))
    vistos = [v for v in vistos if v[0] >= min_views]
    vistos.sort(reverse=True)
    print(f"Brutos para '{termo}' com >= {_fmt(min_views)} views (cota usada: {yt.cota_usada})")
    if not vistos:
        print("  nenhum bruto validado: use a ORIGEM das imagens do viral (viitu.assistir) ou clipes virais do TikTok/Reddit")
    for views, dur, canal, data, tit, vid in vistos[:12]:
        print(f"  {_fmt(views):>6} | {dur // 60:>3} min | {data} | {canal[:24]:<24} | {tit[:60]} | https://youtu.be/{vid}")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    c = sub.add_parser("candidatos")
    c.add_argument("dia")
    c.add_argument("--dias", type=int, default=730)   # temas evergreen: os sucessos reciclam virais de ~2 anos
    c.add_argument("--extra", action="append", default=[])
    c.add_argument("--min-views", type=int, default=2_000_000)
    lac = sub.add_parser("lacuna")
    lac.add_argument("termo")
    lac.add_argument("--dias", type=int, default=730)
    br = sub.add_parser("brutos")
    br.add_argument("termo")
    br.add_argument("--dias", type=int, default=2000)
    a = p.parse_args()
    if a.modo == "candidatos":
        candidatos(a.dia, a.dias, a.extra, a.min_views)
    elif a.modo == "brutos":
        brutos(a.termo, a.dias)
    else:
        lacuna(a.termo, a.dias)


if __name__ == "__main__":
    main()
