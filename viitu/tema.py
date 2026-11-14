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

    lista.sort(key=lambda x: x["pontuacao"], reverse=True)
    PASTA.mkdir(parents=True, exist_ok=True)
    arq = PASTA / f"{dt.date.today().isoformat()}_{d}_candidatos.json"
    arq.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(lista)} Shorts com >= {_fmt(min_views)} views nos últimos {dias} dias "
          f"(cota usada: {yt.cota_usada})\n")
    print("pont | views | x canal | idioma | data | canal (inscritos) | título | link")
    for v in lista[:30]:
        mult = f"{v['multiplicador']}x" if v["multiplicador"] else "?"
        print(f"{v['pontuacao']:>4} | {_fmt(v['views']):>6} | {mult:>6} | {v['idioma']:>5} | "
              f"{v['publicado']} | {v['canal'][:22]} ({_fmt(v['inscritos_canal'])}) | "
              f"{v['titulo'][:70]} | {v['link']}")
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


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    c = sub.add_parser("candidatos")
    c.add_argument("dia")
    c.add_argument("--dias", type=int, default=60)
    c.add_argument("--extra", action="append", default=[])
    c.add_argument("--min-views", type=int, default=300_000)
    lac = sub.add_parser("lacuna")
    lac.add_argument("termo")
    lac.add_argument("--dias", type=int, default=730)
    a = p.parse_args()
    if a.modo == "candidatos":
        candidatos(a.dia, a.dias, a.extra, a.min_views)
    else:
        lacuna(a.termo, a.dias)


if __name__ == "__main__":
    main()
