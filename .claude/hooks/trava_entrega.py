#!/usr/bin/env python3
"""Hook PreToolUse (SendUserFile): bloqueia enviar ao dono um mp4 de remotion/out/ sem a trava de entrega
LIBERADA para AQUELE render (projetos/<p>/saida/entrega.json todo true e mais novo que o mp4)."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
d = json.load(sys.stdin)
for f in d.get("tool_input", {}).get("files", []):
    p = Path(f) if Path(f).is_absolute() else RAIZ / f
    if p.suffix != ".mp4" or "remotion/out" not in str(p):
        continue
    ent = RAIZ / "projetos" / p.stem / "saida" / "entrega.json"
    ok = ent.exists() and all(json.loads(ent.read_text()).values()) and ent.stat().st_mtime >= p.stat().st_mtime
    if not ok:
        print(f"BLOQUEADO: rode `python3 -m viitu.entrega {p.stem}` e só envie com ENTREGA LIBERADA "
              f"(a trava precisa ser posterior ao render).", file=sys.stderr)
        sys.exit(2)
sys.exit(0)
