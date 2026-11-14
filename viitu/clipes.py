"""Busca e download de imagens/vídeos para representar o tema.

Fontes:
  pixabay  Pixabay: vídeos grátis em HD/4K, uso comercial, sem crédito obrigatório (PIXABAY_API_KEY no .env)
  commons  Wikimedia Commons: fotos e vídeos com licença livre, download direto (sem chave)
  pexels   Pexels: vídeos de stock grátis, uso comercial (precisa de PEXELS_API_KEY no .env)
  youtube  YouTube com licença Creative Commons: só links (a nuvem não baixa do YouTube)

Uso:
  python -m viitu.clipes buscar "goat eye close up" [--fontes pixabay,commons] [--miniaturas pasta]
  python -m viitu.clipes baixar <projeto> pixabay 203476
  python -m viitu.clipes baixar <projeto> commons "File:Closeup of goat eye.jpg"
  python -m viitu.clipes baixar <projeto> pexels 1234567

Arquivos vão para projetos/<projeto>/clipes/ e os créditos para projetos/<projeto>/creditos.txt
"""

from __future__ import annotations

import argparse
import html
import os
import re
from pathlib import Path

import requests

from viitu import youtube_api as yt

RAIZ = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "shorts-editor/0.1 (python-requests; educational use)"}


def _commons_api(**params) -> dict:
    """Chama a API do Commons com espera e nova tentativa em caso de limite (429)."""
    import time
    params.setdefault("format", "json")
    for tentativa in range(5):
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params=params)
        if r.status_code == 429:
            time.sleep(5 * (tentativa + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Wikimedia Commons recusou (limite de requisições). Tente de novo em alguns minutos.")


def _env(nome: str) -> str | None:
    if os.environ.get(nome):
        return os.environ[nome]
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith(nome + "="):
                return linha.split("=", 1)[1].strip()
    return None


def _limpa(txt: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", txt or "")).strip()


# ---------- Wikimedia Commons ----------

def commons_buscar(termo: str, n: int = 8) -> list[dict]:
    r = _commons_api(action="query", generator="search", gsrsearch=termo, gsrnamespace=6,
                     gsrlimit=n, prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=1920)
    saida = []
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        mime = ii.get("mime", "")
        if not (mime.startswith("image/") or mime.startswith("video/")):
            continue
        saida.append({
            "fonte": "commons", "id": p["title"],
            "tipo": "video" if mime.startswith("video/") else "foto",
            "tamanho": f"{ii.get('width')}x{ii.get('height')}",
            "licenca": meta.get("LicenseShortName", {}).get("value", "?"),
            "autor": _limpa(meta.get("Artist", {}).get("value", ""))[:60],
            "link": ii.get("descriptionurl", ""),
        })
    return saida


def commons_baixar(titulo: str, destino: Path) -> tuple[Path, str]:
    r = _commons_api(action="query", titles=titulo, prop="imageinfo",
                     iiprop="url|mime|extmetadata", iiurlwidth=1920)  # tamanho padrão do Wikimedia
    p = next(iter(r["query"]["pages"].values()))
    ii = p["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    # foto: usa a versão redimensionada (thumburl); vídeo: o original
    url = ii.get("thumburl") if ii.get("mime", "").startswith("image/") and ii.get("thumburl") else ii["url"]
    nome = re.sub(r"[^\w.\-]+", "_", titulo.replace("File:", ""))
    if ii.get("thumburl") and url == ii["thumburl"]:
        nome = Path(nome).stem + Path(url.split("?")[0]).suffix
    arq = destino / f"commons_{nome}"
    import time
    for tentativa in range(5):
        resp = requests.get(url, headers=UA, timeout=120)
        tipo = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and (tipo.startswith("image/") or tipo.startswith("video/")):
            break
        time.sleep(5 * (tentativa + 1))
    else:
        raise RuntimeError(f"Wikimedia recusou o download ({resp.status_code}). Tente de novo em alguns minutos.")
    arq.write_bytes(resp.content)
    credito = (f"{titulo.replace('File:', '')} — {_limpa(meta.get('Artist', {}).get('value', ''))} — "
               f"{meta.get('LicenseShortName', {}).get('value', '?')} — via Wikimedia Commons ({ii.get('descriptionurl')})")
    return arq, credito


# ---------- Pixabay (fonte principal) ----------

def pixabay_buscar(termo: str, n: int = 8) -> list[dict]:
    chave = _env("PIXABAY_API_KEY")
    if not chave:
        return [{"fonte": "pixabay", "id": "-", "tipo": "-", "tamanho": "-", "licenca": "-",
                 "autor": "", "link": "SEM CHAVE: adicione PIXABAY_API_KEY ao .env"}]
    r = requests.get("https://pixabay.com/api/videos/", timeout=30,
                     params={"key": chave, "q": termo, "per_page": max(n, 3), "safesearch": "true"}).json()
    saida = []
    for h in r.get("hits", [])[:n]:
        g = h["videos"].get("large") or h["videos"]["medium"]
        saida.append({
            "fonte": "pixabay", "id": str(h["id"]), "tipo": f"video {h['duration']}s",
            "tamanho": f"{g['width']}x{g['height']}", "licenca": "Pixabay (livre)",
            "autor": h.get("user", ""), "link": h.get("pageURL", ""),
            "miniatura": h["videos"]["medium"].get("thumbnail", ""),
            "tags": h.get("tags", ""),
        })
    return saida


def pixabay_baixar(vid: str, destino: Path) -> tuple[Path, str]:
    chave = _env("PIXABAY_API_KEY")
    r = requests.get("https://pixabay.com/api/videos/", timeout=30, params={"key": chave, "id": vid}).json()
    h = r["hits"][0]
    v = h["videos"]
    # prefere ~1080p (leve); 4K só se não houver outra opção
    opcoes = [v[k] for k in ("medium", "large", "small") if v.get(k, {}).get("url")]
    boas = [o for o in opcoes if min(o["width"], o["height"]) >= 1080]
    escolha = min(boas, key=lambda o: o["width"] * o["height"]) if boas else max(opcoes, key=lambda o: o["width"])
    arq = destino / f"pixabay_{vid}.mp4"
    arq.write_bytes(requests.get(escolha["url"], timeout=300).content)
    return arq, f"Vídeo {vid} — {h.get('user', '')} — Pixabay ({h.get('pageURL')})"


# ---------- Pexels ----------

def pexels_buscar(termo: str, n: int = 8) -> list[dict]:
    chave = _env("PEXELS_API_KEY")
    if not chave:
        return [{"fonte": "pexels", "id": "-", "tipo": "-", "tamanho": "-", "licenca": "-",
                 "autor": "", "link": "SEM CHAVE: adicione PEXELS_API_KEY ao .env"}]
    r = requests.get("https://api.pexels.com/videos/search", timeout=30,
                     headers={"Authorization": chave},
                     params={"query": termo, "per_page": n, "orientation": "portrait"}).json()
    saida = []
    for v in r.get("videos", []):
        saida.append({
            "fonte": "pexels", "id": str(v["id"]), "tipo": f"video {v.get('duration')}s",
            "tamanho": f"{v.get('width')}x{v.get('height')}", "licenca": "Pexels (livre)",
            "autor": v.get("user", {}).get("name", ""), "link": v.get("url", ""),
        })
    return saida


def pexels_baixar(vid: str, destino: Path) -> tuple[Path, str]:
    chave = _env("PEXELS_API_KEY")
    v = requests.get(f"https://api.pexels.com/videos/videos/{vid}", timeout=30,
                     headers={"Authorization": chave}).json()
    arquivos = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("height")]
    # o menor arquivo com altura >= 1080 (ou o maior disponível)
    bons = sorted([f for f in arquivos if max(f["width"], f["height"]) >= 1080],
                  key=lambda f: f["width"] * f["height"])
    f = bons[0] if bons else max(arquivos, key=lambda f: f["width"] * f["height"])
    arq = destino / f"pexels_{vid}.mp4"
    arq.write_bytes(requests.get(f["link"], timeout=300).content)
    return arq, f"Vídeo {vid} — {v.get('user', {}).get('name', '')} — Pexels ({v.get('url')})"


# ---------- YouTube Creative Commons ----------

def youtube_cc_buscar(termo: str, n: int = 8) -> list[dict]:
    d = yt._get("search", 100, part="snippet", q=termo, type="video",
                videoLicense="creativeCommon", maxResults=n)
    ids = [i["id"]["videoId"] for i in d.get("items", [])]
    if not ids:
        return []
    det = yt._get("videos", 1, part="contentDetails,statistics,snippet", id=",".join(ids))
    saida = []
    for v in det.get("items", []):
        saida.append({
            "fonte": "youtube-cc", "id": v["id"],
            "tipo": f"video {yt.duracao_segundos(v['contentDetails']['duration'])}s",
            "tamanho": v["contentDetails"].get("definition", "?").upper(),
            "licenca": "CC BY (citar o canal)", "autor": v["snippet"]["channelTitle"][:40],
            "link": f"https://www.youtube.com/watch?v={v['id']}",
        })
    return saida


FONTES = {"pixabay": pixabay_buscar, "commons": commons_buscar,
          "pexels": pexels_buscar, "youtube": youtube_cc_buscar}
BAIXAR = {"pixabay": pixabay_baixar, "commons": commons_baixar, "pexels": pexels_baixar}


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    b = sub.add_parser("buscar")
    b.add_argument("termo")
    b.add_argument("--fontes", default="pixabay")
    b.add_argument("--miniaturas", help="pasta onde salvar as miniaturas (para escolher a cena olhando)")
    b.add_argument("-n", type=int, default=8)
    d = sub.add_parser("baixar")
    d.add_argument("projeto")
    d.add_argument("fonte", choices=list(BAIXAR))
    d.add_argument("id")
    a = p.parse_args()

    if a.modo == "buscar":
        for fonte in a.fontes.split(","):
            print(f"== {fonte}: {a.termo}")
            for r in FONTES[fonte.strip()](a.termo, a.n):
                print(f"  [{r['tipo']}] {r['tamanho']} | {r['licenca']} | {r['autor']} | {r['id']} | "
                      f"{r.get('tags', '')[:60]} | {r['link']}")
                if a.miniaturas and r.get("miniatura"):
                    pasta_m = Path(a.miniaturas)
                    pasta_m.mkdir(parents=True, exist_ok=True)
                    (pasta_m / f"{r['fonte']}_{r['id']}.jpg").write_bytes(
                        requests.get(r["miniatura"], timeout=30).content)
    else:
        pasta = RAIZ / "projetos" / a.projeto
        destino = pasta / "clipes"
        destino.mkdir(parents=True, exist_ok=True)
        arq, credito = BAIXAR[a.fonte](a.id, destino)
        with (pasta / "creditos.txt").open("a", encoding="utf-8") as f:
            f.write(credito + "\n")
        print(f"Baixado: {arq.relative_to(RAIZ)} ({arq.stat().st_size // 1024} KB)\nCrédito: {credito}")


if __name__ == "__main__":
    main()
