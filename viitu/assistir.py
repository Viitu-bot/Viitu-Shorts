"""Assiste vídeos do YouTube pelo LINK usando a API do Gemini (plano grátis).

Uso:
  python -m viitu.assistir dissecar <link>        raio-X da edição (cortes, efeitos, sons, texto, gancho)
  python -m viitu.assistir achar <link> "<o que procurar>"   em que minuto acontece X (para brutos)
  python -m viitu.assistir perguntar <link> "<pergunta livre>"

A chave fica em GEMINI_API_KEY no .env (fora do git). Só funciona com vídeos PÚBLICOS.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
MODELO = "gemini-3.8-flash"

PROMPT_DISSECAR = """Você é um editor profissional de YouTube Shorts. Assista este vídeo inteiro e faça
um RAIO-X DA EDIÇÃO em português do Brasil. Use marcação de tempo MM:SS em tudo. Responda em JSON com:
{
 "duracao_s": número,
 "gancho": {"frase_falada": "...", "o_que_aparece_no_frame_0": "...", "texto_na_tela": "...", "por_que_prende": "..."},
 "estrutura": [{"inicio": "MM:SS", "fim": "MM:SS", "funcao": "gancho|desmistificacao|explicacao|virada|cta|loop", "narracao": "...", "imagem": "..."}],
 "cortes": [{"tempo": "MM:SS", "tipo": "seco|transicao|zoom|..."}],
 "efeitos_visuais": [{"tempo": "MM:SS", "efeito": "zoom rápido|tremida|flash|glitch|texto animado|seta|círculo|câmera lenta|...", "em_qual_palavra": "...", "para_que": "..."}],
 "efeitos_sonoros": [{"tempo": "MM:SS", "som": "woosh|boom|ding|pop|...", "momento": "..."}],
 "musica": "descrição (estilo, volume relativo à voz)",
 "legenda": {"estilo": "...", "posicao": "...", "palavras_por_vez": número, "cores": "..."},
 "ritmo": {"segundos_medios_por_cena": número, "observacao": "..."},
 "cta": "...",
 "loop": "como o final emenda no começo, se emenda",
 "origem_das_imagens": "parece um bruto único? de que tipo (fábrica, documentário, TikTok...)? sinais de marca d'água/créditos",
 "licoes_para_copiar": ["...", "..."]
}"""

PROMPT_ACHAR = """Assista este vídeo e encontre TODOS os momentos em que acontece: "{alvo}".
Responda em JSON: {{"achados": [{{"inicio": "MM:SS", "fim": "MM:SS", "descricao": "...", "qualidade_visual": "ótima|boa|ruim", "enquadramento": "close|médio|aberto"}}], "melhor": "MM:SS"}}.
Seja preciso nos tempos. Se não acontecer, devolva lista vazia."""


def _chave() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith("GEMINI_API_KEY="):
            return l.split("=", 1)[1].strip()
    raise SystemExit("Falta GEMINI_API_KEY no .env")


def enviar_arquivo(caminho: str) -> str:
    """Sobe um vídeo local para a File API do Gemini e devolve o file_uri (espera ficar ACTIVE)."""
    import time
    from pathlib import Path as P
    dados = P(caminho).read_bytes()
    ini = requests.post("https://generativelanguage.googleapis.com/upload/v1beta/files", params={"key": _chave()},
                        headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                                 "X-Goog-Upload-Header-Content-Length": str(len(dados)),
                                 "X-Goog-Upload-Header-Content-Type": "video/mp4", "Content-Type": "application/json"},
                        json={"file": {"display_name": P(caminho).name}}, timeout=60)
    url = ini.headers["X-Goog-Upload-URL"]
    info = requests.post(url, headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"},
                         data=dados, timeout=600).json()["file"]
    while info.get("state") == "PROCESSING":
        time.sleep(5)
        info = requests.get(f"https://generativelanguage.googleapis.com/v1beta/{info['name']}", params={"key": _chave()}).json()
    return info["uri"]


def perguntar(link: str, prompt: str, modelo: str = MODELO, json_saida: bool = True, fps: float | None = None) -> str:
    if not link.startswith("http"):
        link = enviar_arquivo(link)          # arquivo local (ex.: nosso vídeo renderizado)
    corpo = {
        "contents": [{"parts": [{"file_data": {"file_uri": link, "mime_type": "video/mp4"},
                                 **({"video_metadata": {"fps": fps}} if fps else {})}, {"text": prompt}]}],
        "generationConfig": {"temperature": 0.2,
                             **({"responseMimeType": "application/json"} if json_saida else {})},
    }
    import time
    reservas = [modelo, "gemini-3-flash-preview", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
    for tentativa in range(8):
        modelo = reservas[min(tentativa // 2, len(reservas) - 1)]     # cota/lotado → próximo modelo grátis
        try:
            d = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                              params={"key": _chave()}, json=corpo, timeout=600).json()
        except requests.RequestException as e:      # queda de rede/proxy: espera e tenta de novo
            d = {"error": {"message": str(e)[:120], "code": 503}}
        msg = d.get("error", {}).get("message", "")
        if "high demand" in msg or "quota" in msg.lower() or d.get("error", {}).get("code") in (429, 500, 503):
            time.sleep(5 if "quota" in msg.lower() else 15)     # servidor ocupado: espera e tenta de novo
            continue
        break
    if "error" in d:
        raise SystemExit(f"Gemini recusou: {d['error'].get('message')}")
    partes = d["candidates"][0]["content"]["parts"]
    uso = d.get("usageMetadata", {})
    print(f"(tokens: {uso.get('totalTokenCount')})", file=sys.stderr)
    return "".join(p.get("text", "") for p in partes)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="modo", required=True)
    d = sub.add_parser("dissecar"); d.add_argument("link"); d.add_argument("--salvar")
    a = sub.add_parser("achar"); a.add_argument("link"); a.add_argument("alvo")
    q = sub.add_parser("perguntar"); q.add_argument("link"); q.add_argument("pergunta")
    for s in (d, a, q):
        s.add_argument("--modelo", default=MODELO)
    args = p.parse_args()
    if args.modo == "dissecar":
        txt = perguntar(args.link, PROMPT_DISSECAR, args.modelo)
        if args.salvar:
            Path(args.salvar).parent.mkdir(parents=True, exist_ok=True)
            Path(args.salvar).write_text(txt, encoding="utf-8")
    elif args.modo == "achar":
        txt = perguntar(args.link, PROMPT_ACHAR.format(alvo=args.alvo), args.modelo)
    else:
        txt = perguntar(args.link, args.pergunta, args.modelo, json_saida=False)
    try:
        print(json.dumps(json.loads(txt), ensure_ascii=False, indent=1))
    except Exception:
        print(txt)


if __name__ == "__main__":
    main()
