"""Puxa os vídeos brutos que o dono sobe na pasta "brutos" do Google Drive (compartilhada por link).

Uso:
  python -m viitu.brutos configurar <link da pasta do Drive>
  python -m viitu.brutos baixar <projeto>      baixa só os arquivos NOVOS de brutos/<projeto>/ para projetos/<projeto>/clipes/
  python -m viitu.brutos listar                mostra o que tem na pasta e o que já foi baixado
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import gdown

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "dados" / "config.json"
REGISTRO = RAIZ / "dados" / "brutos_baixados.json"
CACHE = RAIZ / "dados" / "brutos_cache"          # fora do git (mídia)


def _cfg() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}


def configurar(link: str) -> None:
    c = _cfg()
    c["pasta_brutos"] = link
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Pasta de brutos configurada.")
    listar()


def _arquivos() -> list:
    link = _cfg().get("pasta_brutos")
    if not link:
        raise SystemExit("Pasta ainda não configurada: python -m viitu.brutos configurar <link>")
    itens = gdown.download_folder(link, skip_download=True, quiet=True)
    if itens is None:
        raise SystemExit("Não consegui ler a pasta. Ela está como 'Qualquer pessoa com o link'?")
    return itens


def _registro() -> dict:
    return json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists() else {}


def listar() -> None:
    reg = _registro()
    for it in _arquivos():
        nome = Path(it.path).name
        print(f"  {'✓ baixado → ' + reg[it.id] if it.id in reg else '• NOVO'} | {nome}")


def baixar(projeto: str) -> None:
    reg = _registro()
    destino = RAIZ / "projetos" / projeto / "clipes"
    destino.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    # cada vídeo tem a sua subpasta: brutos/<projeto>/ (arquivos soltos na raiz são ignorados)
    novos = [it for it in _arquivos() if it.id not in reg and projeto in Path(it.path).parts]
    if not novos:
        print(f"Nenhum arquivo novo em brutos/{projeto}/.")
        return
    for it in novos:
        nome = Path(it.path).name.replace(" ", "_")
        tmp = CACHE / nome
        gdown.download(id=it.id, output=str(tmp), quiet=True)
        final = destino / f"bruto_{nome}"
        shutil.move(str(tmp), final)
        reg[it.id] = f"{projeto}/clipes/{final.name}"
        print(f"  ↓ {final.relative_to(RAIZ)} ({final.stat().st_size // 1_000_000} MB)")
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    c = sub.add_parser("configurar"); c.add_argument("link")
    b = sub.add_parser("baixar"); b.add_argument("projeto")
    sub.add_parser("listar")
    a = p.parse_args()
    if a.modo == "configurar":
        configurar(a.link)
    elif a.modo == "baixar":
        baixar(a.projeto)
    else:
        listar()


if __name__ == "__main__":
    main()
