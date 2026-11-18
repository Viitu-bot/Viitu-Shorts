"""RADAR DE TEMAS: todas as fontes de pesquisa num comando, com nota de 0 a 100 para cada tema.

Fontes (cada uma traz candidatos):
  1. Shorts do nicho publicados nos últimos 10 dias, por views/hora (YouTube Data API, EN e PT)  → frescor
  2. Shorts do nicho dos últimos 90 dias com ≥ 1M (YouTube Data API)                              → validação
  3. IDs que o Claude salvou do vidIQ (outliers/trending) em dados/pesquisas/<hoje>_vidiq.json    → breakout
  4. Google Trends em alta no BR/EUA (marca o tema que bate com assunto do momento)              → hype

Cada candidato é classificado (pelo Claude na sessão; Gemini só com --gemini) e pontuado em 5 critérios:
  frescor 25 · força (views × quantas vezes acima do próprio canal) 25 · categoria×gatilho 20 ·
  lacuna PT-BR (3 buscas em português) 20 · cara do canal Viitu (perigo/ação com clipe real, porquê forte) 10

Uso:  python3 -m viitu.radar [--top 8] [--sem-lacuna]
Saída: dados/pesquisas/<hoje>_radar.json e .md
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

from viitu import youtube_api as yt
from viitu.tema import PESO_CATEGORIA, PESO_GATILHO, _em_portugues

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados" / "pesquisas"
NICHO_EN = ["why is it designed", "how it works engineering", "hidden reason everyday object", "dangerous job",
            "giant machine", "you didn't know this", "physics explained", "military engineering"]
NICHO_PT = ["por que", "como funciona", "curiosidades", "trabalho perigoso"]


def _coletar() -> dict[str, dict]:
    vistos: dict[str, dict] = {}
    for termo in NICHO_EN + NICHO_PT:
        lang = "pt" if termo in NICHO_PT else "en"
        for dias, fonte in ((10, "fresco"), (90, "validado")):
            try:
                ids = yt.buscar_ids(termo + " #shorts", dias=dias, maximo=25, idioma=lang)
            except RuntimeError as e:               # cota diária acabou: segue com o que já tem
                print(f"(busca parada: {str(e)[:80]})")
                return _com_vidiq(vistos)
            for vid in ids:
                vistos.setdefault(vid, {"fontes": set()})["fontes"].add(fonte)
    return _com_vidiq(vistos)


def _com_vidiq(vistos: dict[str, dict]) -> dict[str, dict]:
    arq = PASTA / f"{dt.date.today().isoformat()}_vidiq.json"
    if arq.exists():
        for vid in json.loads(arq.read_text(encoding="utf-8")):
            vistos.setdefault(vid, {"fontes": set()})["fontes"].add("vidiq")
    return vistos


def _classificar(titulos: list[str]) -> list[dict]:
    from viitu.logica_temas import CATEGORIAS, GATILHOS, _gemini_texto
    lista = "\n".join(f"{k}. {t}" for k, t in enumerate(titulos))
    prompt = (
        f"Você escolhe temas para um canal BR de Shorts de curiosidade técnica (público adulto, faceless, explica o PORQUÊ "
        f"de objetos, máquinas, engenharia, perigo). Para cada título: categoria ({CATEGORIAS}), gatilho ({GATILHOS}), "
        "tema_pt (o assunto em até 8 palavras), buscas_pt (3 jeitos DIFERENTES que um brasileiro buscaria esse mesmo "
        "assunto no YouTube: 1ª = o OBJETO GENÉRICO sem esporte/marca/país (ex.: 'bola sem ar', não 'bola de futebol americano Wilson'), 2ª = o objeto + 'por que', 3ª = a pergunta), porque (0-2: tem um porquê surpreendente "
        "para explicar?), cara_do_canal (0-2: perigo/ação/máquina com clipe real fácil de achar = 2; meme, pessoa "
        "famosa, comida, dança, desenho, jogo, produto à venda = 0), descartar (true se não é curiosidade explicável). "
        "Devolva só JSON {\"itens\": [{\"i\": n, \"categoria\": .., \"gatilho\": .., \"tema_pt\": .., \"buscas_pt\": [..], "
        "\"porque\": n, \"cara_do_canal\": n, \"descartar\": bool}]}.\n\n" + lista)
    if "--gemini" in sys.argv:
        itens = json.loads(_gemini_texto(prompt))["itens"]
    else:
        # PADRÃO SEM GEMINI (dono 18/11: "não dependa tanto do Gemini"): o Claude classifica na própria sessão.
        hoje = dt.date.today().isoformat()
        arq = PASTA / f"{hoje}_classificacao.json"
        if not arq.exists():
            PASTA.mkdir(parents=True, exist_ok=True)
            (PASTA / f"{hoje}_candidatos.json").write_text(json.dumps(
                {"instrucao": prompt.split("\n\n")[0], "titulos": [{"i": k, "titulo": t} for k, t in enumerate(titulos)]},
                ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"CLASSIFICAR: o Claude lê dados/pesquisas/{hoje}_candidatos.json, grava {arq.name} no formato "
                  "{\"itens\": [...]} e roda o radar de novo (sem gastar cota: a coleta fica em cache).")
            sys.exit(2)
        itens = json.loads(arq.read_text(encoding="utf-8"))["itens"]
    out = [{} for _ in titulos]
    for it in itens:
        k = int(it.get("i", -1))
        if 0 <= k < len(out):
            out[k] = it
    return out


def _lacuna(buscas: list[str]) -> tuple[int, list[str]]:
    """Maior Short em PT nas 3 buscas (últimos 2 anos) + os títulos, para conferir se é o MESMO tema."""
    melhores = []
    for b in buscas[:3]:
        try:
            ids = yt.buscar_ids(b, dias=730, maximo=10, idioma="pt", regiao="BR")
        except RuntimeError:
            return -1, ["(cota acabou: lacuna não medida)"]
        melhores += [v for v in yt.detalhes_videos(ids) if _em_portugues(v)]
    melhores.sort(key=lambda v: -v["views"])
    return (melhores[0]["views"] if melhores else 0), [f"{v['views']:,} | {v['titulo'][:70]}" for v in melhores[:3]]


def _trends() -> str:
    try:
        from viitu.quente import google_trends
        return " ".join(t for _, t, _ in google_trends()).lower()
    except Exception:
        return ""


def _feitos() -> str:
    return (RAIZ / "dados" / "temas_feitos.md").read_text(encoding="utf-8").lower()


def radar(top: int = 8, com_lacuna: bool = True) -> list[dict]:
    cache = PASTA / f"{dt.date.today().isoformat()}_coleta.json"     # 2ª passada do dia não gasta cota de busca
    if cache.exists():
        brutos = {k: {"fontes": set(v)} for k, v in json.loads(cache.read_text(encoding="utf-8")).items()}
    else:
        brutos = _coletar()
        PASTA.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({k: sorted(v["fontes"]) for k, v in brutos.items()}), encoding="utf-8")
    vids = [v for v in yt.detalhes_videos(list(brutos)) if v["views"] >= 300_000]
    agora = dt.datetime.now(dt.timezone.utc)
    for v in vids:
        v["fontes"] = sorted(brutos[v["id"]]["fontes"])
        pub = dt.datetime.fromisoformat(v["publicado"] + "T00:00:00+00:00")
        v["dias"] = max((agora - pub).days, 1)
        v["vph"] = round(v["views"] / (v["dias"] * 24))
    vids.sort(key=lambda v: -v["vph"])
    vids = vids[:60]                                    # os 60 que mais sobem: classificar e medir canal
    cls = _classificar([v["titulo"] for v in vids])
    trends, feitos = _trends(), _feitos()
    bons = []
    for v, c in zip(vids, cls):
        if not c or c.get("descartar"):
            continue
        v.update({k: c.get(k) for k in ("categoria", "gatilho", "tema_pt", "buscas_pt", "porque", "cara_do_canal")})
        if any(w in feitos for w in re.findall(r"\w{6,}", (v["tema_pt"] or "").lower())[:2]):
            continue                                    # tema já feito
        med = (yt.perfil_canal(v["canal_id"]).get("mediana_views") or 0)
        v["x_canal"] = round(v["views"] / med, 1) if med else None
        frescor = 25 if v["dias"] <= 7 else 18 if v["dias"] <= 14 else 10 if v["dias"] <= 45 else 4
        forca = min(25, round(math.log10(v["views"]) * 2.2 * math.sqrt(min(v["x_canal"] or 1, 30)) / 3))
        cat = round(20 * PESO_CATEGORIA.get(v["categoria"], 0.8) * PESO_GATILHO.get(v["gatilho"], 0.8) / (1.5 * 1.4))
        canal = (v["cara_do_canal"] or 0) * 3 + (v["porque"] or 0) * 2
        v["hype"] = any(w in trends for w in re.findall(r"\w{5,}", (v["tema_pt"] or "").lower()))
        v["nota_parcial"] = frescor + forca + cat + min(canal, 10) + (5 if v["hype"] else 0)
        v["criterios"] = {"frescor": frescor, "forca": forca, "categoria": cat, "canal": min(canal, 10)}
        bons.append(v)
    bons.sort(key=lambda v: -v["nota_parcial"])
    finais = bons[: top + 2]
    for v in finais:
        if com_lacuna:
            pt, titulos = _lacuna(v.get("buscas_pt") or [v["tema_pt"]])
            v["pt_maior"], v["pt_titulos"] = pt, titulos
            lac = 10 if pt < 0 else 20 if pt < 100_000 else 10 if pt < 500_000 else 0   # -1 = não medida
        else:
            lac = 10
        v["criterios"]["lacuna"] = lac
        v["nota"] = min(100, v["nota_parcial"] + lac)
    finais.sort(key=lambda v: -v.get("nota", 0))
    finais = finais[:top]
    PASTA.mkdir(parents=True, exist_ok=True)
    hoje = dt.date.today().isoformat()
    (PASTA / f"{hoje}_radar.json").write_text(json.dumps(finais, ensure_ascii=False, indent=1), encoding="utf-8")
    linhas = [f"# Radar de temas — {hoje} (cota usada: {yt.cota_usada})", ""]
    for k, v in enumerate(finais, 1):
        c = v["criterios"]
        linhas += [f"## {k}. {v['tema_pt']} — {v['nota']}/100" + (" 🔥" if v["dias"] <= 7 else ""),
                   f"- {v['views']:,} views em {v['dias']} dias ({v['vph']:,}/h) · {v['x_canal']}x o canal · {v['canal']} · {v['link']}",
                   f"- {v['categoria']} / {v['gatilho']} · fontes: {', '.join(v['fontes'])}" + (" · Google Trends" if v["hype"] else ""),
                   f"- frescor {c['frescor']}/25 · força {c['forca']}/25 · categoria {c['categoria']}/20 · lacuna {c['lacuna']}/20 · canal {c['canal']}/10",
                   f"- PT-BR: maior {v.get('pt_maior', '?'):,} — " + " ; ".join(v.get("pt_titulos", [])) if com_lacuna else "", ""]
    txt = "\n".join(linhas)
    (PASTA / f"{hoje}_radar.md").write_text(txt, encoding="utf-8")
    print(txt)
    return finais


def main() -> None:
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 8
    radar(top, "--sem-lacuna" not in sys.argv)


if __name__ == "__main__":
    main()
