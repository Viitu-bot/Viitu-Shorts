"""
Radar de Temas — Viitu Shorts

Mede os números REAIS dos canais que o Gemini (ou você) encontrou no YouTube.
Não usa API paga nem chave: só o yt-dlp.

Modos:
  python radar/radar.py canais  radar/canais.txt      -> outliers dos Shorts de cada canal
  python radar/radar.py buscar  radar/buscas.txt      -> descobre canais que aparecem nas buscas

Saídas (abrem direto no Excel / Google Sheets), na pasta radar/saida/:
  outliers_AAAA-MM-DD.csv   cada Short com views, mediana do canal e "multiplicador"
  canais_AAAA-MM-DD.csv     resumo de cada canal (serve para avaliar SUBNICHO)
  buscas_AAAA-MM-DD.csv     canais encontrados nas buscas, para você/Gemini avaliar
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import statistics
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

try:
    import yt_dlp
except ImportError:
    sys.exit("Falta o yt-dlp. Rode:  pip install -r requirements.txt")

PASTA_SAIDA = Path(__file__).parent / "saida"
PAUSA_ENTRE_CANAIS = 4  # segundos, para o YouTube não bloquear (erro 429)


def ler_lista(caminho: str) -> list[str]:
    """Lê um .txt ignorando linhas vazias e comentários (#)."""
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    return [l.split("#")[0].strip() for l in linhas if l.split("#")[0].strip()]


def normalizar_canal(entrada: str) -> str:
    """Aceita @handle, link do canal ou link de /shorts e devolve a URL da aba Shorts."""
    e = entrada.strip().rstrip("/")
    if e.startswith("@"):
        return f"https://www.youtube.com/{e}/shorts"
    if "youtube.com" in e:
        e = e.split("?")[0]
        return e if e.endswith("/shorts") else e + "/shorts"
    return f"https://www.youtube.com/@{e}/shorts"


def listar_shorts(url: str, limite: int) -> list[dict]:
    opcoes = {
        "extract_flat": True,
        "playlistend": limite,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=False) or {}
    itens = []
    for e in info.get("entries") or []:
        if not e or e.get("view_count") is None:
            continue
        itens.append(
            {
                "id": e.get("id"),
                "titulo": (e.get("title") or "").strip(),
                "views": int(e["view_count"]),
            }
        )
    return itens


def modo_canais(arquivo: str, limite: int, min_mult: float) -> None:
    canais = ler_lista(arquivo)
    hoje = dt.date.today().isoformat()
    PASTA_SAIDA.mkdir(exist_ok=True)

    linhas_outliers, linhas_canais = [], []
    for i, canal in enumerate(canais, 1):
        url = normalizar_canal(canal)
        print(f"[{i}/{len(canais)}] {canal} ...", end=" ", flush=True)
        try:
            shorts = listar_shorts(url, limite)
        except Exception as erro:  # canal inexistente, bloqueio etc.
            print(f"ERRO: {erro}")
            continue
        if len(shorts) < 5:
            print(f"poucos dados ({len(shorts)} shorts), pulando")
            continue

        views = [s["views"] for s in shorts]
        mediana = statistics.median(views)
        n = len(views)
        linhas_canais.append(
            {
                "canal": canal,
                "shorts_analisados": n,
                "mediana_views": int(mediana),
                "pct_100k": round(100 * sum(v >= 100_000 for v in views) / n),
                "pct_1M": round(100 * sum(v >= 1_000_000 for v in views) / n),
                "maior_views": max(views),
                # mediana dos 10 mais recentes vs geral: >1 = canal em alta
                "tendencia": round(statistics.median(views[:10]) / mediana, 2) if mediana else 0,
                "link": url,
            }
        )
        for s in shorts:
            mult = s["views"] / mediana if mediana else 0
            if mult >= min_mult:
                linhas_outliers.append(
                    {
                        "multiplicador": round(mult, 1),
                        "views": s["views"],
                        "titulo": s["titulo"],
                        "canal": canal,
                        "mediana_canal": int(mediana),
                        "link": f"https://www.youtube.com/shorts/{s['id']}",
                        "nota_0a12": "",
                        "existe_em_ptbr": "",
                    }
                )
        print(f"ok — {n} shorts, mediana {int(mediana):,}".replace(",", "."))
        time.sleep(PAUSA_ENTRE_CANAIS)

    linhas_outliers.sort(key=lambda r: (r["multiplicador"], r["views"]), reverse=True)
    linhas_canais.sort(key=lambda r: r["mediana_views"], reverse=True)
    salvar_csv(PASTA_SAIDA / f"outliers_{hoje}.csv", linhas_outliers)
    salvar_csv(PASTA_SAIDA / f"canais_{hoje}.csv", linhas_canais)


def modo_buscar(arquivo: str, por_busca: int) -> None:
    buscas = ler_lista(arquivo)
    hoje = dt.date.today().isoformat()
    PASTA_SAIDA.mkdir(exist_ok=True)
    achados: dict[str, dict] = {}

    opcoes = {"extract_flat": True, "quiet": True, "no_warnings": True, "ignoreerrors": True}
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        for i, termo in enumerate(buscas, 1):
            print(f"[{i}/{len(buscas)}] buscando: {termo}")
            # sp=EgIYAQ%3D%3D = filtro "menos de 4 minutos" da busca do YouTube
            url = ("https://www.youtube.com/results?search_query="
                   f"{quote_plus(termo)}&sp=EgIYAQ%253D%253D")
            info = ydl.extract_info(url, download=False) or {}
            for e in (info.get("entries") or [])[:por_busca]:
                if not e:
                    continue
                canal = e.get("channel") or e.get("uploader") or "?"
                url_canal = e.get("channel_url") or e.get("uploader_url") or ""
                reg = achados.setdefault(
                    canal,
                    {"canal": canal, "aparicoes": 0, "soma_views": 0, "buscas": set(),
                     "exemplo": "", "link_canal": url_canal},
                )
                reg["aparicoes"] += 1
                reg["soma_views"] += int(e.get("view_count") or 0)
                reg["buscas"].add(termo)
                if not reg["exemplo"]:
                    reg["exemplo"] = (e.get("title") or "")[:90]
            time.sleep(PAUSA_ENTRE_CANAIS)

    linhas = []
    for r in achados.values():
        r["buscas"] = " | ".join(sorted(r["buscas"]))
        linhas.append(r)
    linhas.sort(key=lambda r: (r["aparicoes"], r["soma_views"]), reverse=True)
    salvar_csv(PASTA_SAIDA / f"buscas_{hoje}.csv", linhas)
    print("\nDica: copie os canais promissores para radar/canais.txt e rode o modo 'canais'.")


def salvar_csv(caminho: Path, linhas: list[dict]) -> None:
    if not linhas:
        print(f"(nada para salvar em {caminho.name})")
        return
    # utf-8-sig = acentos aparecem certos no Excel do Windows
    with caminho.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    print(f"Salvo: {caminho}  ({len(linhas)} linhas)")


def main() -> None:
    p = argparse.ArgumentParser(description="Radar de Temas — Viitu Shorts")
    sub = p.add_subparsers(dest="modo", required=True)

    c = sub.add_parser("canais", help="mede outliers dos Shorts de uma lista de canais")
    c.add_argument("arquivo", help="txt com um canal por linha (@handle ou link)")
    c.add_argument("--limite", type=int, default=150, help="quantos Shorts recentes por canal")
    c.add_argument("--min-mult", type=float, default=3.0,
                   help="só lista Shorts com views >= X vezes a mediana do canal")

    b = sub.add_parser("buscar", help="descobre canais a partir de termos de busca")
    b.add_argument("arquivo", help="txt com um termo de busca por linha")
    b.add_argument("--por-busca", type=int, default=40)

    a = p.parse_args()
    if a.modo == "canais":
        modo_canais(a.arquivo, a.limite, a.min_mult)
    else:
        modo_buscar(a.arquivo, a.por_busca)


if __name__ == "__main__":
    main()
