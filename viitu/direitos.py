"""Revisão de DIREITOS AUTORAIS de todas as partes do vídeo (obrigatória antes de entregar).

Gera projetos/<p>/saida/direitos.md com cada elemento, a origem e o status:
  ✅ livre/licenciado · ⚠️ terceiro com crédito (pedir permissão) · ❌ bloqueia a entrega
Regras:
  - Voz: ElevenLabs (plano pago = uso comercial) ✅
  - Trilha, SFX e foley: gerados no ElevenLabs (assets/) ✅ · qualquer outro arquivo de áudio ❌
  - Fonte: Anton (licença OFL) ✅
  - Clipes: pixabay_* ✅ (licença Pixabay) · commons_* ✅ (ver creditos.txt) · próprio_* ✅
            tiktok_*/bruto_*/ancora_* ⚠️ terceiro: precisa de crédito na descrição e, de preferência, permissão
  - Áudio ORIGINAL de clipe de terceiro ligado ❌ (risco de música com Content ID)
Uso: python -m viitu.direitos <projeto>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def revisar(projeto: str) -> bool:
    pasta = RAIZ / "projetos" / projeto
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    permissoes = cfg.get("permissoes", {})        # {"tiktok_1.mp4": "@user autorizou em 16/11 (print no Drive)"}
    creditos = cfg.get("creditos_descricao", "")
    linhas, bloqueia = [], False
    L = lambda st, item, origem: linhas.append(f"| {st} | {item} | {origem} |")
    L("✅", "Voz (narração)", "ElevenLabs, plano Starter com licença comercial")
    musica = cfg.get("musica", "curioso_documentario.mp3")
    if (RAIZ / "assets" / "musica" / musica).exists():
        L("✅", f"Trilha: {musica}", "gerada no ElevenLabs Music (própria)")
    else:
        L("❌", f"Trilha: {musica}", "arquivo fora da biblioteca própria"); bloqueia = True
    L("✅", "Efeitos sonoros e foley", "assets/sfx e assets/foley, gerados no ElevenLabs (próprios)")
    L("✅", "Fonte da legenda", "Anton, licença SIL Open Font License")
    vistos = set()
    for c in cfg["cenas"]:
        cl = c["clipe"]
        if cl in vistos:
            continue
        vistos.add(cl)
        if cl.startswith(("pixabay_", "commons_", "proprio_")):
            L("✅", cl, "Pixabay (licença livre)" if cl.startswith("pixabay") else ("Wikimedia Commons (ver creditos.txt)" if cl.startswith("commons") else "gravação própria"))
        else:
            perm = permissoes.get(cl)
            if perm:
                L("✅", cl, f"terceiro COM permissão: {perm}")
            else:
                L("⚠️", cl, "terceiro SEM permissão registrada: crédito obrigatório na descrição; pedir permissão")
            if any(x["clipe"] == cl and x.get("som_original") is True for x in cfg["cenas"]):
                L("❌", f"áudio original de {cl}", "ligado: pode ter música com Content ID → desligar"); bloqueia = True
    if any(not c["clipe"].startswith(("pixabay_", "commons_", "proprio_")) for c in cfg["cenas"]) and not creditos:
        L("❌", "créditos na descrição", "faltam (campo creditos_descricao no cenas.json)"); bloqueia = True
    md = ["# Direitos autorais — " + projeto, "", "| status | elemento | origem |", "|---|---|---|", *linhas, "",
          "**RESULTADO:** " + ("❌ NÃO ENTREGAR" if bloqueia else "✅ liberado (⚠️ = crédito na descrição + pedir permissão)")]
    if creditos:
        md += ["", "**Créditos para a descrição:** " + creditos]
    (pasta / "saida" / "direitos.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return not bloqueia


if __name__ == "__main__":
    sys.exit(0 if revisar(sys.argv[1]) else 1)
