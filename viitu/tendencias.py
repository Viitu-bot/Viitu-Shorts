"""Radar de tendências do BRASIL (Google Trends, via trendspyg — MIT, github.com/flack0x/trendspyg).

Complementa o /tema: compara o INTERESSE DE BUSCA no YouTube BR dos temas candidatos (mesma escala 0–100). O "em alta
agora" já está no `viitu.quente`. Não substitui a prova do tema (views reais da YouTube Data API).

Uso:
  python3 -m viitu.tendencias                       # em alta agora no Brasil (Google)
  python3 -m viitu.tendencias "banheiro do trem" "bola de gude"   # interesse no YouTube BR, 12 meses (0–100)
Instalar 1x: pip install "trendspyg[cli]"
"""
from __future__ import annotations

import sys


def em_alta(n: int = 25) -> list[dict]:
    from trendspyg import download_google_trends_rss
    out = []
    for t in download_google_trends_rss(geo="BR")[:n]:
        manchete = (t.get("news_articles") or [{}])[0].get("headline", "")
        out.append({"termo": t["trend"], "buscas": t.get("traffic", ""), "manchete": manchete[:110]})
    return out


def interesse_youtube(termos: list[str]) -> dict[str, float]:
    """Média de interesse (0–100, mesma escala para todos) nas buscas do YouTube no Brasil, últimos 12 meses."""
    import os
    # o chromedriver do node (/opt/node22) é de outra versão do Chrome: deixar o selenium baixar o certo
    os.environ["PATH"] = ":".join(p for p in os.environ["PATH"].split(":") if "node22" not in p)
    from trendspyg.compat.request import TrendReq
    tr = TrendReq(hl="pt-BR", tz=180)
    tr.build_payload(termos[:5], timeframe="today 12-m", geo="BR", gprop="youtube")
    df = tr.interest_over_time()
    return {t: round(float(df[t].mean()), 1) for t in termos[:5] if t in df}


def main() -> None:
    termos = sys.argv[1:]
    if not termos:
        print("EM ALTA NO BRASIL AGORA (Google Trends):")
        for t in em_alta():
            print(f"  {t['buscas']:>7}  {t['termo']}  — {t['manchete']}")
        return
    try:
        for t, v in sorted(interesse_youtube(termos).items(), key=lambda x: -x[1]):
            print(f"  {v:5.1f}  {t}  (interesse médio no YouTube BR, 12 meses)")
    except Exception as e:                       # o Google limita consultas seguidas: avisar, não inventar
        print(f"Google Trends recusou agora ({type(e).__name__}: {str(e)[:120]}). Tentar de novo mais tarde.")


if __name__ == "__main__":
    main()
