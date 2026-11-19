"""TRAVA DE ENTREGA: nenhum vídeo vai para o dono sem passar aqui. Junta TODAS as verificações do projeto num
comando só (antes eram 4 soltas e dependiam de lembrar):

  1. planta da montagem (viitu.montagem: R1–R8 — repetição, 3D em bloco, gancho, qualidade, fotos, loop, SOM)
  2. revisão de enquadramento e telas de app (viitu.revisar)
  3. direitos e créditos (viitu.direitos)
  4b. SOM: pós-produção (viitu.som_final: mixagem depois do render, sidechain real, −14 LUFS) + SOM MEDIDO (bloqueia)
  4c. OUVIDO do Gemini: só com --gemini, 2ª opinião (não bloqueia: deu de 3 a 8,5 para o mesmo arquivo)
  Nada aqui depende do Gemini: todas as travas são medições próprias.
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

    # VÍDEO DESATUALIZADO (vd010, 19/11): o editor falhou em silêncio, o render usou o plano antigo e a trava liberou
    plano_pub = RAIZ / "remotion" / "public" / "plano.json"
    cen = pasta / "cenas.json"
    from viitu.montagem import hash_cenas
    pl = json.loads(plano_pub.read_text(encoding="utf-8")) if plano_pub.exists() else {}
    if pl.get("_cenas_hash"):          # compara o CONTEÚDO que muda o vídeo (anotar formato/créditos não exige render)
        velho = [] if pl["_cenas_hash"] == hash_cenas(json.loads(cen.read_text(encoding="utf-8"))) else ["cenas.json mudou depois do editar"]
    else:
        velho = [n for n, arq in (("plano de som/cenas (editar)", plano_pub), ("vídeo final (render)", mp4))
                 if not arq.exists() or arq.stat().st_mtime < cen.stat().st_mtime]
    if not pl.get("_cenas_hash") and mp4.exists() and plano_pub.exists() and mp4.stat().st_mtime < plano_pub.stat().st_mtime:
        velho.append("vídeo final mais velho que o plano (renderizar de novo)")   # com impressão: só o SOM mudou, a imagem é a mesma
    res["atualizado"] = not velho
    print(("✅" if not velho else "❌"), "0. Vídeo gerado a partir do cenas.json atual" + (f" — desatualizado: {velho}" if velho else ""))
    # DECUPAGEM (cérebro de editor, dono 19/11): a folha de cenas tem que existir e ser do cenas.json atual
    dec = pasta / "saida" / "decupagem.jpg"
    res["decupagem"] = dec.exists() and dec.stat().st_mtime >= cen.stat().st_mtime
    print(("✅" if res["decupagem"] else "❌"), "0b. Decupagem conferida antes do render"
          + ("" if res["decupagem"] else f" — rode: python3 -m viitu.decupagem {projeto} e CONFIRA a folha"))
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
        # 4b. SOM: pós-produção (mixagem depois do render) + medição objetiva — bloqueia. Gemini = 2ª opinião.
        from viitu.som_final import montar
        info = montar(projeto)
        falhas = [k for k, m in info["medidas"].items() if not m["ok"]]
        res["som_medido"] = not falhas
        print(("✅" if not falhas else "❌"), "4b. Som medido (música sob a voz, respira, efeitos, impacto, nada sobre a voz)"
              + (f" — falhou: {falhas}" if falhas else ""))
        ok, txt = _rodar("auditoria", ["viitu.auditoria", projeto, str(mp4)] + ([] if "--gemini" in sys.argv else ["--sem-gemini"]))
        aud = pasta / "saida" / "auditoria.md"
        graves = [l for l in aud.read_text(encoding="utf-8").splitlines() if "❌" in l] if aud.exists() else []
        res["auditoria"] = ok and not graves
        print(("✅" if res["auditoria"] else "❌"), "4. Auditoria técnica (som, loudness, ritmo, loop)")
        for g in graves[:8]:
            print("     ", g.strip())
        if "--gemini" in sys.argv:                       # 2ª opinião só quando pedida (dono: "não dependa do Gemini")
            from viitu.ouvido import ouvir
            nota, txt = ouvir(str(mp4))
            (pasta / "saida" / "ouvido.md").write_text(txt, encoding="utf-8")
            print(f"ℹ️ 4c. Ouvido do Gemini (2ª opinião, não bloqueia): {nota}/10 — saida/ouvido.md")
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
    sys.exit(0 if entregar([a for a in sys.argv[1:] if not a.startswith('--')][0]) else 1)
