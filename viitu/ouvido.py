"""OUVIDO: o Gemini escuta o vídeo final e dá nota ao sound design comparando com virais do nicho.
Medir volume não diz se o som "tem cara de edição" (vd009 passou nas medições e o dono ouviu "só narração").
Uso: python3 -m viitu.ouvido <video.mp4>   → nota 0–10 + problemas. A trava de entrega exige nota ≥ 8.
"""
from __future__ import annotations

import re
import sys

PROMPT = """Você é um sound designer de YouTube Shorts virais de curiosidade/engenharia ("A vida é uma maravilha",
Zack D. Films). Escute SÓ O ÁUDIO e seja exigente. Responda em português:
1) Segundo a segundo: o que se ouve além da narração (música, whoosh nos cortes, impactos, sons de ação, ambiência).
2) A música combina com o tema, é perceptível e tem dinâmica (sobe na virada)?
3) Os efeitos de ação são claros e sincronizados, sem cobrir a voz?
Última linha EXATAMENTE no formato: NOTA: <0-10>/10 — <os 3 problemas mais graves, curtos>"""


def ouvir(mp4: str) -> tuple[float | None, str]:
    from viitu.assistir import enviar_arquivo, perguntar
    try:
        txt = perguntar(enviar_arquivo(mp4), PROMPT, json_saida=False)
    except Exception as e:               # cota do Gemini acabou: a trava avisa, não inventa nota
        return None, f"Gemini indisponível: {str(e)[:80]}"
    m = re.findall(r"NOTA:\s*([\d.,]+)\s*/\s*10", txt)
    return (float(m[-1].replace(",", ".")) if m else None), txt


if __name__ == "__main__":
    n, t = ouvir(sys.argv[1])
    print(t)
    print("\nNOTA DO OUVIDO:", n)
