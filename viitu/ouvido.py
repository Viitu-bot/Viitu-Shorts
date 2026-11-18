"""OUVIDO: o Gemini escuta o vídeo final e confere o sound design por um CHECKLIST objetivo.
Medir volume não diz se o som "tem cara de edição" (vd009 passou nas medições e o dono ouviu "só narração").
Nota livre não serve: o mesmo arquivo recebeu de 3 a 8,5 (18/11). Por isso: temperatura 0, 10 perguntas de sim/não,
3 escutas e vale a MAIORIA em cada item. Nota = itens aprovados (0–10). A trava de entrega exige ≥ 8.
Uso: python3 -m viitu.ouvido <video.mp4>
"""
from __future__ import annotations

import json
import sys

ITENS = {
    "musica_perceptivel": "Há música de fundo perceptível durante o vídeo todo?",
    "musica_abaixa_e_volta": "A música fica mais baixa sob a voz e volta nas pausas, SEM afundar de repente quando a voz para?",
    "musica_cresce_virada": "A música/som cresce ou ganha energia na virada (por volta dos 75% do vídeo) ou no fim?",
    "impacto_virada": "Há um impacto sonoro claro (boom/hit) na virada do roteiro?",
    "efeitos_acao_claros": "Os sons de ação (avião, metal, líquido, máquina) são claramente audíveis quando a ação aparece?",
    "efeitos_nao_cobrem_voz": "Nenhum efeito ou whoosh cobre/mascara palavras da narração?",
    "whoosh_dosado": "Os whooshes de transição estão dosados (não em todo corte, não cansativos)?",
    "ambiencia_presente": "Há ambiência de fundo que dá sensação de lugar (não soa como estúdio vazio)?",
    "voz_clara": "A narração está clara, à frente, sem distorção?",
    "fim_sem_silencio": "O fim do vídeo não tem silêncio (o som emenda para o loop)?",
}
PROMPT = ("Você é um sound designer exigente de YouTube Shorts virais de curiosidade/engenharia. Escute o ÁUDIO deste "
          "Short e responda cada pergunta com true ou false, sendo rigoroso (na dúvida, false). Responda SÓ em JSON: "
          '{"respostas": {' + ", ".join(f'"{k}": bool' for k in ITENS) + '}, "problemas": ["até 3, curtos"]}\n'
          + "\n".join(f"- {k}: {q}" for k, q in ITENS.items()))


def ouvir(mp4: str, vezes: int = 3) -> tuple[float | None, str]:
    from viitu.assistir import enviar_arquivo, perguntar
    try:
        uri = enviar_arquivo(mp4)
    except Exception as e:
        return None, f"Gemini indisponível: {str(e)[:80]}"
    votos, probs = {k: [] for k in ITENS}, []
    for _ in range(vezes):
        try:
            d = json.loads(perguntar(uri, PROMPT, temperatura=0.0))
        except Exception:                 # uma escuta falhou: segue com as outras
            continue
        for k in ITENS:
            votos[k].append(bool(d.get("respostas", {}).get(k)))
        probs += d.get("problemas", [])
    if not any(votos.values()):
        return None, "Gemini indisponível (nenhuma escuta respondeu)"
    final = {k: sum(v) * 2 > len(v) for k, v in votos.items()}
    nota = float(sum(final.values()))
    txt = "\n".join(f"{'✅' if ok else '❌'} {ITENS[k]}  (votos sim: {sum(votos[k])}/{len(votos[k])})" for k, ok in final.items())
    txt += "\nProblemas citados: " + "; ".join(dict.fromkeys(probs))
    txt += f"\nNOTA: {nota:.0f}/10 (itens aprovados pela maioria de {len(next(iter(votos.values())))} escutas)"
    return nota, txt


if __name__ == "__main__":
    n, t = ouvir(sys.argv[1])
    print(t)
    print("\nNOTA DO OUVIDO:", n)
