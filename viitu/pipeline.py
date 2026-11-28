"""PIPELINE AUTOMÁTICO (dono 28/11: "auditoria completa… para a gente definir de vez e deixar no automático").
Junta, na ordem certa e parando no primeiro ❌, as etapas técnicas que antes eram 8 comandos soltos. As decisões
criativas continuam com o dono (ganchos → roteiro → storyboard aprovados ANTES; voz só depois do "aprovado").

  python3 -m viitu.pipeline previa <projeto>
      triagem → montagem (R0–R17) → decupagem + ouvido → editar --remotion → partes (todas) → som final + SOM MEDIDO
      → faixa preta. Termina com as pranchas que o Claude TEM que olhar antes do render.
  python3 -m viitu.pipeline final <projeto> "TÍTULO DA CAPA" [--cena N --t T]
      render (último passo) → entrega (trava completa) → capa → copia o mp4 para projetos/<p>/.

Saída 0 = tudo passou; 1 = parou num ❌ (a mensagem diz onde e por quê).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PY = sys.executable


def _rodar(nome: str, cmd: list[str], cwd: Path = RAIZ, barra: str | None = r"❌") -> str:
    print(f"\n▶ {nome}", flush=True)
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    saida = (r.stdout or "") + (r.stderr or "")
    linhas = [l for l in saida.splitlines() if l.strip()]
    for l in linhas[-12:]:
        print("   " + l)
    if r.returncode != 0 or (barra and re.search(barra, saida)):
        print(f"\n⛔ PAROU em: {nome}. Corrigir o que está acima e rodar de novo.")
        sys.exit(1)
    return saida


def previa(p: str) -> None:
    pasta = RAIZ / "projetos" / p
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    _rodar("1/7 triagem dos clipes", [PY, "-m", "viitu.triagem", p], barra=None)
    _rodar("2/7 montagem (travas R0–R17)", [PY, "-m", "viitu.montagem", p])
    _rodar("3/7 decupagem + ouvido", [PY, "-m", "viitu.decupagem", p])
    _rodar("4/7 editor (Remotion)", [PY, "-m", "viitu.editar", p, "--remotion"])
    partes = list(dict.fromkeys(c.get("_parte", "GANCHO") for c in cfg["cenas"]))
    for nome in partes:
        _rodar(f"5/7 parte {nome}", [PY, "-m", "viitu.partes", p, nome], barra=None)
    _rodar("6/7 som final + SOM MEDIDO", [PY, "-m", "viitu.som_final", p, "--previa"])
    r = subprocess.run([PY, "-c", f"from viitu.entrega import _tarjas; print(_tarjas('{p}'))"], cwd=RAIZ,
                       capture_output=True, text=True).stdout.strip()
    print(f"\n▶ 7/7 faixa preta: {r or '[]'}")
    if r not in ("", "[]"):
        print("⛔ PAROU em: faixa preta na tela.")
        sys.exit(1)
    print("\n✅ PRÉVIA PRONTA. Antes do render, o Claude OLHA:")
    print(f"   projetos/{p}/saida/decupagem.jpg")
    for f in sorted((pasta / "saida" / "partes").glob("*.jpg")):
        print(f"   {f.relative_to(RAIZ)}")
    print(f"   projetos/{p}/saida/previa.mp4 (vídeo inteiro com o som final)")


def final(p: str, titulo: str, cena: int = 0, t: float = 0.6) -> None:
    pasta = RAIZ / "projetos" / p
    _rodar("1/4 render (último passo)", ["npm", "run", "render"], cwd=RAIZ / "remotion", barra=None)
    shutil.move(str(RAIZ / "remotion" / "out" / "short_remotion.mp4"), str(RAIZ / "remotion" / "out" / f"{p}.mp4"))
    _rodar("2/4 entrega (trava completa)", [PY, "-m", "viitu.entrega", p], barra=r"ENTREGA: BLOQUEADA")
    _rodar("3/4 capa", [PY, "-m", "viitu.capa", p, titulo, "--cena", str(cena), "--t", str(t), "--zoom", "1.0"], barra=None)
    shutil.copy(RAIZ / "remotion" / "out" / f"{p}.mp4", pasta / f"{p}.mp4")
    print(f"\n✅ 4/4 PRONTO: projetos/{p}/{p}.mp4 · capa.jpg · kit_publicacao.txt — olhar a prancha e a capa e mandar ao dono.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "previa":
        previa(a[1])
    elif len(a) >= 3 and a[0] == "final":
        cena = int(a[a.index("--cena") + 1]) if "--cena" in a else 0
        t = float(a[a.index("--t") + 1]) if "--t" in a else 0.6
        final(a[1], a[2], cena, t)
    else:
        print(__doc__)
