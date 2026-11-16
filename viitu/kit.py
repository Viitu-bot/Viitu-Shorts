"""KIT DE IDENTIDADE SONORA do Viitu (efeitos de EDIÇÃO), montado do Mixkit.

Licença Mixkit Sound Effects Free License: uso comercial e YouTube monetizado, sem crédito obrigatório;
não pode redistribuir os sons soltos (por isso os arquivos ficam fora do git: assets/kit/ é baixado aqui).

Cada FUNÇÃO da edição tem 3 sons (o editor alterna — variedade sem perder a identidade). Escolha:
candidatos das categorias do Mixkit → exclui cartoon/meme/arcade → o CLAP escuta e ranqueia pela descrição.
Uso:
  python -m viitu.kit montar        baixa/escolhe tudo e grava assets/kit/kit.json
  python -m viitu.kit listar        mostra o kit
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "assets" / "kit"
KIT = PASTA / "kit.json"

# função: (categorias do Mixkit, descrição para o CLAP escutar, para que serve / quando usar)
FUNCOES = {
    "whoosh_corte": (["whoosh", "swoosh", "woosh", "swish", "transition"], "short smooth air whoosh transition",
                     "corte com movimento ou entrada de gráfico; alternar os 3; nunca em todo corte"),
    "impacto_revelacao": (["impact", "cinematic", "boom", "bass"], "deep cinematic boom impact with sub bass",
                          "a revelação/virada ('Mas...'): 1 a 2 por vídeo, depois do vácuo"),
    "riser_tensao": (["swell", "sweep", "cinematic", "suspense-music"], "cinematic tension riser building up",
                     "1 a 2 s antes da revelação; prepara o susto"),
    "pop_marca": (["pop", "bubbles", "click"], "soft clean pop",
                  "círculo/seta/adesivo aparecendo; chama o olho para o detalhe"),
    "ding_fato": (["ding", "notification", "bell", "chimes"], "bright clean notification ding",
                  "fato surpreendente, número na tela, 'você sabia'"),
    "shutter_foto": (["camera"], "camera shutter click",
                     "foto/imagem parada que entra, 'registro' de um momento"),
    "glitch_tech": (["glitch", "static"], "short digital glitch",
                    "tecnologia, erro, transição para animação/gráfico"),
    "digitar_texto": (["keyboard", "type", "typewriter"], "fast keyboard typing",
                      "texto/título sendo escrito na tela"),
    "relogio_tempo": (["clock", "countdown"], "clock ticking",
                      "tempo passando, contagem, urgência"),
    "coracao_tensao": (["heartbeat"], "slow heartbeat",
                       "perigo, medo, suspense (sob a voz, baixo)"),
    "dinheiro": (["money", "coin"], "cash register money",
                 "preço, 'mais caro do mundo', economia"),
    "errado_mito": (["wrong", "error", "buzzer"], "wrong answer buzzer",
                    "mito desmentido ('A maioria acha X...' → errado)"),
    "certo_resposta": (["correct", "win"], "correct answer chime",
                       "a resposta certa / o motivo real"),
    "rewind": (["rewind", "tape-machine"], "tape rewind",
               "voltar no tempo, 'mas antes...', loop"),
    "scratch_quebra": (["dj-record-scratch"], "record scratch",
                       "quebra de expectativa (usar pouco: datado se repetido)"),
    "zoom_in": (["zoom"], "fast zoom in whoosh",
                "zoom rápido no detalhe"),
    "brilho_revela": (["sparkle", "magic"], "sparkle shimmer reveal",
                      "algo bonito/satisfatório sendo revelado"),
}
EXCLUIR_FUNCAO = {
    "relogio_tempo": r"alarm|beep|bleep", "brilho_revela": r"melody|christmas|festive|tones",
    "impacto_revelacao": r"heartbeat|space|underground", "errado_mito": r"basketball|hockey|apartment|door|sport",
    "ding_fato": r"remove|interface|magic", "zoom_in": r"ghost", "pop_marca": r"deep water",
}
EXCLUIR = r"cartoon|funny|comic|arcade|8 ?bit|retro|game|fart|laugh|meme|kid|child|toy|cute|baby|fairy|scream|horror|monster|laser|sci ?fi|space ?shooter"


def _pagina(cat: str, pag: int = 1) -> list[dict]:
    url = f"https://mixkit.co/free-sound-effects/{cat}/" + (f"?page={pag}" if pag > 1 else "")
    h = subprocess.run(["curl", "-sSL", url], capture_output=True, text=True).stdout
    itens = []
    for m in re.finditer(r'data-audio-player-preview-url-value="([^"]+)"[\s\S]*?data-audio-player-item-id-value="(\d+)"', h):
        resto = h[m.end():m.end() + 6000]
        t = re.search(r'item-grid-card__title">\s*([^<]+?)\s*</h2>', resto)
        d = re.search(r'(\d+):(\d\d)', resto)
        itens.append({"id": int(m.group(2)), "url": m.group(1), "titulo": t.group(1) if t else "",
                      "dur": int(d.group(1)) * 60 + int(d.group(2)) if d else 0, "categoria": cat})
    return itens


def baixar(item: dict) -> Path:
    arq = PASTA / "cache" / f"{item['id']}.mp3"
    if not arq.exists():
        arq.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sSL", "--retry", "3", "-o", str(arq), item["url"]], check=True)
    return arq


def montar(so: list[str] | None = None) -> dict:
    import torch
    from viitu.sons import _clap, _audio48k
    modelo, proc = _clap()
    kit = json.loads(KIT.read_text(encoding="utf-8")) if (so and KIT.exists()) else {}
    for func, (cats, desc, uso) in FUNCOES.items():
        if so and func not in so:
            continue
        cand, vistos = [], set()
        for c in cats:
            for it in _pagina(c):
                ex = EXCLUIR_FUNCAO.get(func)
                if it["id"] in vistos or re.search(EXCLUIR, it["titulo"], re.I) or not (0 < it["dur"] <= 8) \
                        or (ex and re.search(ex, it["titulo"], re.I)):
                    continue
                vistos.add(it["id"])
                cand.append(it)
        cand = cand[:30]
        audios, ok = [], []
        for it in cand:
            try:
                a = _audio48k(baixar(it), 0, 5)
            except subprocess.CalledProcessError:
                continue
            if len(a) > 2400:
                audios.append(a)
                ok.append(it)
        if not ok:
            print(f"{func}: nenhum candidato")
            continue
        with torch.no_grad():
            p = modelo(**proc(text=[desc], audio=audios, sampling_rate=48000, return_tensors="pt",
                              padding=True)).logits_per_text[0].softmax(-1).numpy()
        top = [ok[i] | {"nota": round(float(p[i]), 3), "arquivo": str(PASTA / "cache" / f"{ok[i]['id']}.mp3")}
               for i in np.argsort(-p)[:3]]
        kit[func] = {"uso": uso, "descricao": desc, "sons": top}
        print(f"{func:18} → " + " | ".join(f"{t['titulo']} ({t['nota']})" for t in top))
    KIT.write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    return kit


def som(funcao: str, i: int = 0) -> Path:
    """Arquivo do i-ésimo som da função (alterna entre os 3). Baixa se faltar."""
    k = json.loads(KIT.read_text(encoding="utf-8"))[funcao]["sons"]
    return baixar(k[i % len(k)])


if __name__ == "__main__":
    if sys.argv[1:2] == ["montar"]:
        montar(sys.argv[2:] or None)
    else:
        for f, v in json.loads(KIT.read_text(encoding="utf-8")).items():
            print(f"{f}: {v['uso']}\n   " + " | ".join(s["titulo"] for s in v["sons"]))
