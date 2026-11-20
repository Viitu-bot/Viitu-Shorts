"""OUVIR UM VÍDEO PRONTO (nosso ou de referência) — pedido do dono 20/11: "saber qual é aquele efeito, qual é aquela
música de fundo, os nomes em específico, para montar a nossa biblioteca".

Junta 3 ferramentas, nenhuma depende do Gemini:
  1. rea-video decompose (já rodado, pasta rea_*/): tomadas, cortes, BPM, faixa de EFEITOS separada (stems/effects.wav)
  2. Shazam (shazamio): NOME da música de fundo, testado em janelas de 8 s ao longo do vídeo
  3. earshot: timeline da faixa de efeitos (cada efeito com o tipo de som e se cai num corte) + o som de ABERTURA (0–1,5 s)

Uso: python3 -m viitu.ouvir_video <video.mp4> <pasta_rea> [--saida relatorio.json]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

BIN = shutil.which("earshot") or str(Path.home() / ".local" / "bin" / "earshot")


def _dur(arq: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


async def _shazam(arq: Path, janelas: list[tuple[float, float]]) -> list[dict]:
    from shazamio import Shazam
    s, achados = Shazam(), []
    with tempfile.TemporaryDirectory() as td:
        for a, b in janelas:
            tmp = Path(td) / f"j{a:.0f}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{b - a}", "-i", str(arq), "-ac", "1",
                            "-ar", "44100", str(tmp)], check=True)
            try:
                r = await s.recognize(str(tmp))
            except Exception as e:                                   # serviço fora do ar não para a análise
                achados.append({"de": a, "ate": b, "erro": str(e)[:80]})
                continue
            t = r.get("track") or {}
            if t:
                achados.append({"de": a, "ate": b, "musica": t.get("title"), "artista": t.get("subtitle"),
                                "link": t.get("url")})
    return achados


def _earshot(args: list[str]) -> dict:
    env = {**os.environ, "EARSHOT_THREADS": os.environ.get("EARSHOT_THREADS", "3")}
    r = subprocess.run([BIN, *args, "--json"], capture_output=True, text=True, env=env, timeout=900)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"erro": (r.stderr or r.stdout)[-300:]}


def ouvir_video(video: Path, rea: Path) -> dict:
    dur = _dur(video)
    bd = json.loads((rea / "breakdown.json").read_text(encoding="utf-8")) if (rea / "breakdown.json").exists() else {}
    shots = bd.get("shots", [])
    cortes = [round(s.get("start", 0), 2) for s in shots][1:]
    mus = (bd.get("audio") or {}).get("music") or {}
    # 1. música (no áudio inteiro e, se existir, na faixa de música separada)
    fonte_mus = next((p for p in (rea / "stems" / "music.wav", video) if p.exists()), video)
    janelas = [(a, min(a + 8, dur)) for a in [0, max(dur / 2 - 4, 0), max(dur - 8, 0)] if dur - a > 3]
    musica = asyncio.run(_shazam(fonte_mus, janelas))
    if not any(m.get("musica") for m in musica) and fonte_mus != video:
        musica += asyncio.run(_shazam(video, janelas))
    # 2. efeitos: timeline do earshot na faixa de efeitos, com os cortes do próprio vídeo
    fx = rea / "stems" / "effects.wav"
    tl = _earshot(["timeline", str(fx if fx.exists() else video), "--video", str(video)])
    # 3. abertura (a "marca" dos primeiros 1,5 s)
    abertura = _earshot(["describe", str(video), "--start", "0", "--end", "1.5", "--top", "4"])
    return {
        "video": video.name, "duracao_s": round(dur, 1),
        "tomadas": len(shots), "s_por_tomada": round(dur / max(len(shots), 1), 2), "cortes": cortes,
        "musica_bpm": mus.get("tempo_bpm"), "musica_tom": (mus.get("key") or {}).get("tonic"),
        "musica_nome": musica,
        "efeitos_timeline": tl.get("summary") or tl.get("erro"),
        "efeitos_eventos": [{"t": round(e["t"], 2), "tipo": e.get("kind"), "som": e.get("label"),
                             "destaque_db": e.get("prominence_db"),
                             "no_corte": any(abs(e["t"] - c) <= 0.1 for c in (tl.get("cuts") or []))}
                            for e in (tl.get("events") or []) if e.get("label")][:40],
        "cortes_earshot": len(tl.get("cuts") or []),
        "abertura": abertura.get("summary") or abertura.get("erro"),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video"); p.add_argument("rea"); p.add_argument("--saida")
    a = p.parse_args()
    r = ouvir_video(Path(a.video), Path(a.rea))
    txt = json.dumps(r, ensure_ascii=False, indent=1)
    if a.saida:
        Path(a.saida).write_text(txt, encoding="utf-8")
    print(txt)
