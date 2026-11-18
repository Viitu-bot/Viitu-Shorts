"""TRAVA DE ENTREGA: nenhum vídeo vai para o dono sem passar aqui. Junta TODAS as verificações do projeto num
comando só (antes eram 4 soltas e dependiam de lembrar):

  1. planta da montagem (viitu.montagem: R1–R8 — repetição, 3D em bloco, gancho, qualidade, fotos, loop, SOM)
  2. revisão de enquadramento e telas de app (viitu.revisar)
  3. direitos e créditos (viitu.direitos)
  4. auditoria técnica do mp4 (viitu.auditoria: loudness, efeito sobre a fala, cenas escuras, ritmo, loop;
     com Gemini se houver cota, sem ele se não houver)
  5. prancha 1 quadro/s em saida/prancha.jpg + a lista de conferência visual de edicao/reclamacoes.md

Resultado em saida/entrega.json. Código 1 = NÃO entregar.
Uso: python3 -m viitu.entrega <projeto>   (mp4 esperado em remotion/out/<projeto>.mp4)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _rodar(nome: str, cmd: list[str]) -> tuple[bool, str]:
    p = subprocess.run([sys.executable, "-m", *cmd], cwd=RAIZ, capture_output=True, text=True)
    saida = (p.stdout + p.stderr).strip()
    linhas = [l for l in saida.splitlines() if "HF Hub" not in l and "Warning" not in l]
    return p.returncode == 0, "\n".join(linhas[-12:])


def entregar(projeto: str) -> bool:
    pasta = RAIZ / "projetos" / projeto
    mp4 = RAIZ / "remotion" / "out" / f"{projeto}.mp4"
    res = {}
    print(f"## Trava de entrega: {projeto}\n")

    from viitu.montagem import checar
    erros, avisos = checar(projeto)
    res["montagem"] = not erros
    print(("✅" if not erros else "❌"), "1. Planta da montagem (R1–R8)")
    for e in erros:
        print("     ❌", e)
    for a in avisos:
        print("     ⚠️", a)

    ok, txt = _rodar("revisar", ["viitu.revisar", projeto])
    res["revisar"] = ok
    print(("✅" if ok else "❌"), "2. Revisão de enquadramento/telas de app")
    if not ok:
        print("    " + txt.replace("\n", "\n    "))

    ok, txt = _rodar("direitos", ["viitu.direitos", projeto])
    res["direitos"] = ok and "❌" not in txt.split("RESULTADO")[-1]
    print(("✅" if res["direitos"] else "❌"), "3. Direitos e créditos")

    if not mp4.exists():
        res["auditoria"] = False
        print("❌ 4. Auditoria: mp4 não encontrado em", mp4.relative_to(RAIZ))
    else:
        ok, txt = _rodar("auditoria", ["viitu.auditoria", projeto, str(mp4)])
        if not ok:                                           # Gemini sem cota: audita só as medições
            ok, txt = _rodar("auditoria", ["viitu.auditoria", projeto, str(mp4), "--sem-gemini"])
        aud = pasta / "saida" / "auditoria.md"
        graves = [l for l in aud.read_text(encoding="utf-8").splitlines() if "❌" in l] if aud.exists() else []
        res["auditoria"] = ok and not graves
        print(("✅" if res["auditoria"] else "❌"), "4. Auditoria técnica (som, loudness, ritmo, loop)")
        for g in graves[:8]:
            print("     ", g.strip())
        prancha = pasta / "saida" / "prancha.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vf", "fps=1,scale=180:-1,tile=9x4",
                        "-frames:v", "1", str(prancha)], check=False)
        print(f"👁 5. Prancha para OLHAR: {prancha.relative_to(RAIZ)}")
        print("     Conferir (edicao/reclamacoes.md): cena entendida em 1 s · ação na palavra · pessoa real quando a "
              "frase fala de alguém · 3D com física certa · sem logo/legenda de terceiro · legenda sem cobrir o sujeito")

    tudo = all(res.values())
    (pasta / "saida" / "entrega.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nENTREGA:", "LIBERADA ✅ (depois de olhar a prancha)" if tudo else "BLOQUEADA ❌ — corrigir antes de mandar ao dono")
    return tudo


if __name__ == "__main__":
    sys.exit(0 if entregar(sys.argv[1]) else 1)
