"""OUVIDO DE VERDADE (earshot, github.com/Leonxlnx/earshot — modelos CLAP + AST locais, sem chave): antes do render,
cada efeito do vídeo é ESCUTADO e comparado com o que ele deveria ser. Era o furo que deixou passar galo numa fábrica,
"golfe embaixo d'água" para bola quicando e "passos de inseto" para ar vazando (a conferência era só pelo NOME do arquivo).

Veredito do earshot por efeito: strong ✅ · plausible ⚠️ (passa, mas é candidato a troca) · weak/no match ❌ (barra).
Teste em 20/11 (18 efeitos gerados, 6 pedidos): o som certo em 1º lugar em 5/6; "galo" = nenhum efeito (certo); e
achou fraco o estouro da lata do vd011 ("parece estalo de boca").

Descrição de cada efeito: campo "desc" do efeito no cenas.json; senão a "busca"; senão o nome do arquivo gerado
(gen_<descrição>.mp3) ou o nome do arquivo na Sonniss. Resultados guardados em cache (o modelo leva ~30 s por chamada).

Uso: python3 -m viitu.ouvir <projeto>   (a decupagem chama sozinha)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "assets" / "sfx" / "earshot_cache.json"
BIN = shutil.which("earshot") or str(Path.home() / ".local" / "bin" / "earshot")


def _descricao(e: dict) -> str:
    if e.get("desc"):
        return e["desc"]
    if e.get("busca"):
        return e["busca"]
    nome = Path(str(e.get("arquivo", ""))).stem
    if nome.startswith("gen_"):
        return nome[4:].replace("_", " ")
    m = re.match(r"(\d+)$", nome)
    if m:                                                    # cache Sonniss: o nome real está no catálogo
        cat = json.loads((RAIZ / "assets" / "sonniss" / "catalogo.json").read_text(encoding="utf-8"))
        itens = cat if isinstance(cat, list) else cat.get("itens", [])
        for x in itens:
            if str(x.get("id")) == m.group(1):
                return re.sub(r"[_\-]+", " ", Path(x["nome"]).stem)
    return nome.replace("_", " ")


def _match(arq: Path, desc: str, cache: dict) -> dict:
    chave = f"{arq.name}|{arq.stat().st_mtime_ns}|{desc}"
    if chave in cache:
        return cache[chave]
    env = {**os.environ, "EARSHOT_THREADS": os.environ.get("EARSHOT_THREADS", "3")}
    r = subprocess.run([BIN, "match", str(arq), desc, "--json"], capture_output=True, text=True, env=env, timeout=300)
    d = json.loads(r.stdout)
    alt = [c.get("term") or c.get("text") or str(c) for c in (d.get("closest_vocab") or [])[:2]] if isinstance(d.get("closest_vocab"), list) else []
    res = {"verdict": d["verdict"], "z": round(d["z"], 1), "parece": alt}
    cache[chave] = res
    return res


def ouvir(projeto: str) -> tuple[list[str], list[str], list[str]]:
    """→ (erros, avisos, linhas para a decupagem)."""
    if not Path(BIN).exists():
        return [], ["OUVIDO indisponível: instale com uv tool install \"earshot[mcp] @ git+https://github.com/Leonxlnx/earshot\" "
                    "e rode earshot doctor --fetch"], []
    cfg = json.loads((RAIZ / "projetos" / projeto / "cenas.json").read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    erros, avisos, linhas = [], [], []
    for k, c in enumerate(cfg["cenas"]):
        efeitos = list(c.get("sfx_cena", [])) + list((c.get("animacao") or {}).get("sfx", []))
        for e in efeitos:
            if not e.get("arquivo"):                          # "busca" sem arquivo = whoosh do kit, escolhido na hora
                continue
            arq = RAIZ / e["arquivo"]
            desc = _descricao(e)
            r = _match(arq, desc, cache)
            marca = {"strong": "✅", "plausible": "⚠️"}.get(r["verdict"], "❌")
            txt = f"{marca} cena {k + 1}: {arq.name} — pedido \"{desc}\" → {r['verdict']} (z {r['z']})" + \
                  (f"; soa como: {', '.join(r['parece'])}" if r["parece"] and r["verdict"] != "strong" else "")
            linhas.append(txt)
            if marca == "❌":
                erros.append(txt)
            elif marca == "⚠️":
                avisos.append(txt)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return erros, avisos, linhas


if __name__ == "__main__":
    e, a, l = ouvir(sys.argv[1])
    print("OUVIDO (earshot):")
    print("\n".join("  " + x for x in l) or "  (nenhum efeito com arquivo)")
    for x in a[:1] if not l else []:
        print("  " + x)
    print("RESULTADO:", "❌ trocar os sons marcados" if e else "✅ todos os efeitos soam como o pedido")
    sys.exit(1 if e else 0)
