"""Gera a narração no ElevenLabs com o tempo exato de cada palavra.

Uso:
  python -m viitu.voz <projeto>            # lê o "TEXTO FINAL PARA A VOZ" do roteiro.md
Saída em projetos/<projeto>/:
  voz.mp3        narração
  palavras.json  [{"palavra", "inicio", "fim"}] em segundos

A chave vem do cofre do ambiente (o proxy injeta o cabeçalho xi-api-key).
"""

from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
VOZ_OTTO = "ycxdm1PRMs962FxyyuJ0"
MODELO = "eleven_v4"  # o mais emotivo; o v3 aceita tags de emoção ([curious]...) se precisar


def texto_do_roteiro(projeto: str, com_tags: bool = False) -> str:
    md = (RAIZ / "projetos" / projeto / "roteiro.md").read_text(encoding="utf-8")
    # texto com direção de voz só para o v3; nos outros modelos, o texto final limpo
    m = re.search(r"## 🎙️ TEXTO COM DIREÇÃO DE VOZ.*?\n(.*?)\n## ", md, re.S) if com_tags else None
    if m:
        return "\n".join(l.strip() for l in m.group(1).strip().splitlines() if l.strip())
    m = re.search(r"## ✅ TEXTO FINAL PARA A VOZ.*?\n(.*?)\n## ", md, re.S)
    if not m:
        raise SystemExit("Não achei a seção '## ✅ TEXTO FINAL PARA A VOZ' no roteiro.md")
    return " ".join(l.strip() for l in m.group(1).strip().splitlines() if l.strip())


def caracteres_para_palavras(al: dict) -> list[dict]:
    chars, ini, fim = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    palavras, atual, t0, t1 = [], "", None, None
    dentro_tag = False
    for c, a, b in zip(chars, ini, fim):
        # ignora as tags de direção [curious], [short pause]...
        if c == "[":
            dentro_tag = True
            continue
        if dentro_tag:
            if c == "]":
                dentro_tag = False
            continue
        if c.isspace():
            if atual:
                palavras.append({"palavra": atual, "inicio": round(t0, 3), "fim": round(t1, 3)})
            atual, t0 = "", None
            continue
        if t0 is None:
            t0 = a
        atual += c
        t1 = b
    if atual:
        palavras.append({"palavra": atual, "inicio": round(t0, 3), "fim": round(t1, 3)})
    return palavras


def auto_cut(arq: Path, palavras: list[dict], max_pausa: float = 0.12) -> list[dict]:
    """AUTO-CUT (formato do dono): toda pausa entre palavras maior que `max_pausa` vira `max_pausa`.
    Corta o áudio e reajusta os tempos das palavras (legenda continua sincronizada)."""
    import subprocess
    if not palavras:
        return palavras
    blocos, ini = [], 0.0
    for a, b in zip(palavras, palavras[1:] + [None]):
        fim = a["fim"]
        if b is None or b["inicio"] - fim > max_pausa:
            blocos.append((ini, fim + (0.06 if b else 0.15)))
            ini = (b["inicio"] - 0.03) if b else 0
    # novos tempos
    novos, deslocado, bi = [], 0.0, 0
    cortes = []
    t_saida = 0.0
    for (b0, b1) in blocos:
        cortes.append((b0, b1, t_saida))
        t_saida += b1 - b0
    for w in palavras:
        for (b0, b1, ts) in cortes:
            if b0 - 1e-6 <= w["inicio"] <= b1 + 1e-6:
                novos.append({**w, "inicio": round(ts + w["inicio"] - b0, 3), "fim": round(ts + min(w["fim"], b1) - b0, 3)})
                break
    filtros = "".join(f"[0:a]atrim={b0:.3f}:{b1:.3f},asetpts=PTS-STARTPTS[a{i}];" for i, (b0, b1) in enumerate(blocos))
    filtros += "".join(f"[a{i}]" for i in range(len(blocos))) + f"concat=n={len(blocos)}:v=0:a=1[s]"
    tmp = arq.with_name("voz_autocut.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(arq), "-filter_complex", filtros, "-map", "[s]", str(tmp)], check=True)
    tmp.replace(arq)
    antes = palavras[-1]["fim"]
    print(f"Auto-cut: {antes:.1f}s → {novos[-1]['fim']:.1f}s ({len(blocos)} blocos)")
    return novos


def gerar(projeto: str, voz: str, estabilidade: float, velocidade: float, modelo: str = MODELO) -> None:
    texto = texto_do_roteiro(projeto, com_tags=(modelo == "eleven_v3"))
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps",
        headers={"xi-api-key": "proxy-injected", "Content-Type": "application/json"},
        json={
            "text": texto,
            "model_id": modelo,
            "language_code": "pt",
            "voice_settings": ({"stability": estabilidade, "similarity_boost": 0.8}
                               if modelo == "eleven_v3" else
                               {"stability": estabilidade, "similarity_boost": 0.8, "style": 0.35,
                                "use_speaker_boost": True, "speed": velocidade}),
        },
        timeout=180,
    )
    if r.status_code != 200:
        raise SystemExit(f"ElevenLabs recusou ({r.status_code}): {r.text[:300]}")
    d = r.json()
    pasta = RAIZ / "projetos" / projeto
    (pasta / "voz.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
    palavras = caracteres_para_palavras(d.get("normalized_alignment") or d["alignment"])
    palavras = auto_cut(pasta / "voz.mp3", palavras)
    (pasta / "palavras.json").write_text(json.dumps(palavras, ensure_ascii=False, indent=1), encoding="utf-8")
    dur = palavras[-1]["fim"] if palavras else 0
    print(f"Voz gerada: {len(texto)} caracteres, {len(palavras)} palavras, {dur:.1f} s")
    print(f"Arquivos: projetos/{projeto}/voz.mp3 e palavras.json")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("projeto")
    p.add_argument("--voz", default=VOZ_OTTO)
    p.add_argument("--estabilidade", type=float, default=0.5,
                   help="v3 aceita só 0.0 (criativo), 0.5 (natural) ou 1.0 (estável)")
    p.add_argument("--velocidade", type=float, default=1.0)
    p.add_argument("--modelo", default=MODELO)
    a = p.parse_args()
    gerar(a.projeto, a.voz, a.estabilidade, a.velocidade, a.modelo)


if __name__ == "__main__":
    main()
