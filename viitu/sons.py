"""Biblioteca profissional de sons (Sonniss GDC 2015–2026, ~7.400 sons, royalty-free para YouTube
monetizado, sem crédito obrigatório; proibido só usar para TREINAR IA).

Não baixa tudo: o catálogo (nomes, duração, link) fica em assets/sonniss/catalogo.json e cada som é
baixado do Internet Archive só quando escolhido (cache em assets/sonniss/cache/, fora do git).

Busca em 2 etapas:
  1. pelo NOME (CLIP texto) → 12 candidatos
  2. o CLAP ESCUTA os candidatos e escolhe o que mais soa como a descrição
Uso:
  python -m viitu.sons catalogo                      (re)gera o catálogo a partir do archive.org
  python -m viitu.sons buscar "close campfire crackling" [--min 3 --max 60] [-n 3]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.parse
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "assets" / "sonniss"
CATALOGO = PASTA / "catalogo.json"
CACHE = PASTA / "cache"
ANOS = [2015, 2016, 2017, 2018, 2019, 2020, 2023, 2024, 2026]
LICENCA = "Sonniss GDC Game Audio Bundle: royalty-free, uso comercial (inclui YouTube monetizado), sem atribuição"


def _dur(x) -> float:
    x = str(x or "0")
    if ":" in x:
        return sum(float(v) * 60 ** i for i, v in enumerate(reversed(x.split(":"))))
    return float(x)


def _limpar(nome: str) -> str:
    """'Pack - Lib/Fire_Crackle_Close_01.mp3' → 'Lib fire crackle close' (texto para o CLIP)."""
    pacote, _, arq = nome.rpartition("/")
    t = re.sub(r"\.(mp3|wav|flac)$", "", arq, flags=re.I)
    t = re.sub(r"[_,\-\.]+", " ", t)
    t = re.sub(r"\b\d+\b|\b(st|ms|mono|stereo|mkh\w*|neumann|sd\d+|kmr\w*)\b", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", f"{pacote.split(' - ')[-1]} {t}").strip().lower()


def gerar_catalogo() -> list[dict]:
    itens = []
    for a in ANOS:
        it = f"sonniss-gdc-{a}-game-audio-bundle-normalized"
        fs = json.loads(subprocess.run(["curl", "-sS", f"https://archive.org/metadata/{it}/files"],
                                       capture_output=True, text=True).stdout)["result"]
        for f in fs:
            n = f["name"]
            if not n.lower().endswith(".mp3") or re.search(r"5\.1|ambisonic|wxyz|lcrlsrs|quad", n, re.I):
                continue
            itens.append({"id": len(itens), "ano": a, "item": it, "nome": n, "texto": _limpar(n),
                          "dur": round(_dur(f.get("length")), 1), "tam": int(f.get("size", 0))})
    PASTA.mkdir(parents=True, exist_ok=True)
    CATALOGO.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
    print(f"Catálogo: {len(itens)} sons → {CATALOGO.relative_to(RAIZ)}")
    return itens


def _catalogo() -> list[dict]:
    return json.loads(CATALOGO.read_text(encoding="utf-8")) if CATALOGO.exists() else gerar_catalogo()


def _emb_textos(cat: list[dict]) -> np.ndarray:
    arq = CACHE / "emb_nomes.npy"
    if arq.exists() and np.load(arq).shape[0] == len(cat):
        return np.load(arq)
    import torch
    from viitu.inteligencia import _clip
    modelo, _, tok = _clip()
    out = []
    with torch.no_grad():
        for i in range(0, len(cat), 256):
            e = modelo.encode_text(tok([c["texto"][:200] for c in cat[i:i + 256]]))
            out.append((e / e.norm(dim=-1, keepdim=True)).numpy())
    E = np.concatenate(out).astype(np.float32)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(arq, E)
    return E


def baixar(som: dict) -> Path:
    destino = CACHE / f"{som['id']}.mp3"
    if not destino.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        url = f"https://archive.org/download/{som['item']}/" + urllib.parse.quote(som["nome"])
        subprocess.run(["curl", "-sSL", "--retry", "3", "-o", str(destino), url], check=True)
    return destino


_CLAP = None


def _clap():
    global _CLAP
    if _CLAP is None:
        from transformers import ClapModel, ClapProcessor
        _CLAP = (ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(),
                 ClapProcessor.from_pretrained("laion/clap-htsat-unfused"))
    return _CLAP


def _audio48k(arq: Path, ini: float = 0.0, dur: float = 10.0) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ini:.2f}", "-t", f"{dur:.2f}", "-i", str(arq),
                          "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


EXCLUIR = r"firework|firecracker|gun|rifle|pistol|shotgun|weapon|ammo|robot|voice|vocal|ice|bread|pizza|lava|cartoon|toy|game ?ui|sci ?fi|alien|magic|spell"


def buscar(texto: str, dur_min: float = 0.0, dur_max: float = 9999.0, n: int = 1,
           candidatos: int = 12, imagem_emb: np.ndarray | None = None, exigir: str | None = None) -> list[dict]:
    """Devolve os n melhores sons (com 'arquivo' local) para a descrição em inglês."""
    import torch
    cat = _catalogo()
    E = _emb_textos(cat)
    if imagem_emb is not None:
        q = imagem_emb / np.linalg.norm(imagem_emb)
    else:
        from viitu.inteligencia import _clip
        modelo, _, tok = _clip()
        with torch.no_grad():
            q = modelo.encode_text(tok([texto]))
            q = (q / q.norm(dim=-1, keepdim=True)).numpy()[0]
    ok = np.array([dur_min <= c["dur"] <= dur_max and c["tam"] > 0 and not re.search(EXCLUIR, c["texto"])
                   and (not exigir or re.search(exigir, c["texto"])) for c in cat])
    sim = np.where(ok, E @ q, -1)
    top = [cat[i] for i in np.argsort(-sim)[:candidatos]]
    # etapa 2: o CLAP escuta (5 s do meio de cada candidato)
    modelo, proc = _clap()
    audios, validos = [], []
    for c in top:
        try:
            a = _audio48k(baixar(c), max(c["dur"] / 2 - 2.5, 0), 5.0)
        except subprocess.CalledProcessError:
            continue
        if len(a) > 4800:
            audios.append(a)
            validos.append(c)
    with torch.no_grad():
        ent = proc(text=[texto], audio=audios, sampling_rate=48000, return_tensors="pt", padding=True)
        out = modelo(**ent)
        p = out.logits_per_text[0].softmax(-1).numpy()
    ordem = np.argsort(-p)[:n]
    return [{**validos[i], "arquivo": str(CACHE / f"{validos[i]['id']}.mp3"), "nota": round(float(p[i]), 3)}
            for i in ordem]


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="modo", required=True)
    sub.add_parser("catalogo")
    b = sub.add_parser("buscar")
    b.add_argument("texto")
    b.add_argument("--min", type=float, default=0)
    b.add_argument("--max", type=float, default=9999)
    b.add_argument("-n", type=int, default=3)
    b.add_argument("--exigir", default=None, help="regex que o nome precisa ter (ex.: 'fire|flame')")
    a = ap.parse_args()
    if a.modo == "catalogo":
        gerar_catalogo()
    else:
        for r in buscar(a.texto, a.min, a.max, a.n, exigir=a.exigir):
            print(f"{r['nota']:.3f} | {r['dur']:>6.1f}s | {r['nome']} | {r['arquivo']}")


if __name__ == "__main__":
    main()
