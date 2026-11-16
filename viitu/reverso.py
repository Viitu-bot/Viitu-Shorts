"""ENGENHARIA REVERSA da lógica de edição dos canais de referência.

Para cada canal: os 4 Shorts de maior sucesso do último ano + 1 mediano (padrão × exceção).
O Gemini assiste cada vídeo e lista CADA efeito sonoro/visual com o tempo, a frase falada naquele instante,
se cai na PAUSA ou SOBRE a fala, o que aparece na tela e a FUNÇÃO. Também mede a música (presença, estilo,
volume relativo à voz). Saída: pesquisa/reverso/<id>.json + amostra.json.
Uso: python -m viitu.reverso amostra   |   python -m viitu.reverso analisar
"""

from __future__ import annotations

import datetime as dt
import json
import statistics as st
import sys
import time
from pathlib import Path

from viitu import youtube_api as yt

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "pesquisa" / "reverso"
# canal: id de um vídeo conhecido (para achar o canal) ou handle
CANAIS = {"A vida é uma maravilha": "@avidamaravilha", "GeneralTV": "@ivangeneraltv", "KSO Descobre": "@ksodescobre",
          "Polaco sem Polônia": "v:-qFObICKecA", "Andre Shorts Br": "v:uKT5iq4_YMY", "Zack D. Films": "@zackdfilms"}

PROMPT = """Você é um editor de som e vídeo sênior fazendo ENGENHARIA REVERSA deste YouTube Short.
Escute o ÁUDIO com atenção (separe voz, música e efeitos) e veja a imagem. Responda SÓ o que você tem
certeza; se não tiver, responda "incerto". Em JSON, em português:
{
 "duracao_s": n,
 "musica": {"tem": true/false, "estilo": "...", "volume_vs_voz": "alta|media|baixa|inaudivel", "db_estimado_abaixo_da_voz": n,
   "entra_no_inicio": true/false, "para_ou_muda_em": ["MM:SS motivo"], "cortes_na_batida": "sim|nao|incerto"},
 "whoosh_nos_cortes": "todos|maioria|metade|poucos|nenhum",
 "cortes_total_aprox": n,
 "efeitos_caem": "maioria_nas_pausas|maioria_sobre_a_fala|misto",
 "som_por_palavra_da_legenda": "sim|nao",
 "pop_em_seta_ou_circulo": "sim|nao|nao_tem_seta",
 "riser_antes_da_revelacao": {"tem": true/false, "exemplos": ["MM:SS frase"]},
 "boom_ou_impacto": {"quantos": n, "exemplos": [{"tempo": "MM:SS", "fala": "...", "na_tela": "...", "por_que": "..."}]},
 "ding_ou_notificacao": {"quantos": n, "exemplos": [{"tempo": "MM:SS", "fala": "...", "na_tela": "..."}]},
 "sons_de_meme": ["quais (nome) ou vazio"],
 "foley_do_que_aparece": {"tem": true/false, "exemplos": [{"tempo": "MM:SS", "som": "...", "na_tela": "...", "original_ou_adicionado": "..."}]},
 "som_original_do_clipe": "alto|baixo|desligado|incerto",
 "silencio_ou_vacuo_dramatico": {"tem": true/false, "exemplos": ["MM:SS"]},
 "animacao_2d_3d": {"tem": true/false, "tipo": "3D|2D|mapa|grafico", "inicio": "MM:SS", "duracao_s": n, "o_que_explica": "...", "som_na_animacao": "..."},
 "texto_e_graficos": ["setas, círculos, emojis, números, X/✓ ... com o momento em que aparecem"],
 "assinatura_sonora": "há algum som que se repete como marca do canal? qual e quando",
 "regras_do_editor": ["5 a 8 regras concretas e verificáveis que explicam QUANDO ele coloca cada som/efeito neste vídeo"]
}"""


def _uploads(ref: str) -> tuple[str, list[dict]]:
    if ref.startswith("v:"):
        cid = yt._get("videos", 1, part="snippet", id=ref[2:])["items"][0]["snippet"]["channelId"]
        c = yt._get("channels", 1, part="snippet,contentDetails", id=cid)["items"][0]
    else:
        c = yt._get("channels", 1, part="snippet,contentDetails", forHandle=ref.lstrip("@"))["items"][0]
    up = c["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while len(ids) < 200:
        r = yt._get("playlistItems", 1, part="contentDetails", playlistId=up, maxResults=50, **({"pageToken": tok} if tok else {}))
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break
    vids = []
    for i in range(0, len(ids), 50):
        for v in yt._get("videos", 1, part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))["items"]:
            d = yt.duracao_segundos(v["contentDetails"]["duration"])
            pub = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            if 0 < d <= 180 and (dt.datetime.now(dt.timezone.utc) - pub).days <= 365:
                vids.append({"id": v["id"], "titulo": v["snippet"]["title"], "views": int(v["statistics"].get("viewCount", 0)),
                             "dur": d, "data": pub.date().isoformat()})
    return c["snippet"]["title"], vids


def amostra() -> dict:
    PASTA.mkdir(parents=True, exist_ok=True)
    out = {}
    for nome, ref in CANAIS.items():
        titulo, vids = _uploads(ref)
        if not vids:
            continue
        vids.sort(key=lambda v: -v["views"])
        med = st.median(v["views"] for v in vids)
        mediano = min(vids, key=lambda v: abs(v["views"] - med))
        esc = vids[:4] + ([mediano] if mediano not in vids[:4] else [])
        out[nome] = {"canal": titulo, "n_shorts_ano": len(vids), "mediana_views": med,
                     "videos": [{**v, "papel": "top" if i < 4 else "mediano"} for i, v in enumerate(esc)]}
        print(f"{nome}: {len(vids)} Shorts no ano, mediana {med:,.0f} → " + ", ".join(f"{v['views']:,}" for v in esc))
    (PASTA / "amostra.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


PROMPT_EDICAO = """Você é um editor sênior de YouTube Shorts fazendo ENGENHARIA REVERSA COMPLETA da edição deste vídeo
(imagem e som). Responda SÓ o que tem certeza; senão "incerto". JSON, em português:
{
 "mix_volumes_vs_voz": {"musica_sob_fala_db": n, "musica_nas_pausas_db": n, "whoosh_db": n, "pop_db": n, "boom_db": n,
   "riser_db": n, "foley_ambiencia_db": n, "foley_detalhe_db": n,
   "obs": "dB RELATIVO à voz (0 = mesmo volume da voz; -12 = bem mais baixo; +3 = mais alto). Estime pelo que ouve."},
 "ritmo": {"segundos_por_cena_media": n, "cena_mais_longa_s": n, "corta_no_inicio_de_frase": "sim|nao|misto"},
 "gancho_3s": {"o_que_aparece_no_frame0": "...", "texto_na_tela": "...", "seta_ou_circulo": true/false, "movimento": "...", "frase": "..."},
 "zoom_e_camera": {"zoom_constante_lento": true/false, "punch_in_em_palavra": true/false, "tremida": true/false, "camera_lenta": true/false},
 "marcacoes": {"seta": {"cor": "...", "estilo": "...", "quantas": n, "quando": "..."}, "circulo": {"cor": "...", "quantos": n},
   "outros": ["emojis, X, ✓, números, lupa..."]},
 "legenda": {"palavras_por_vez": n, "fonte": "grossa|fina|...", "cor_base": "...", "cor_destaque": "...", "contorno": true/false,
   "posicao": "topo|centro|centro-inferior|inferior", "animacao": "pop|nenhuma|...", "destaca_palavra_chave": true/false},
 "texto_extra_na_tela": ["título/pergunta/números com o momento"],
 "transicoes": {"tipos": ["corte seco|zoom|whip|glitch|flash|..."], "mais_comum": "..."},
 "efeitos_visuais": ["flash, RGB, blur, shake, brilho... e quando"],
 "cor": "natural|saturada|contrastada|quente|fria|filtro",
 "imagens": {"origem": "TikTok/Douyin/stock/documentário/3D/próprias", "marca_dagua_visivel": true/false, "bordas_ou_fundo_desfocado": true/false},
 "animacao_2d_3d": {"tem": true/false, "estilo": "...", "inicio": "MM:SS", "duracao_s": n, "o_que_explica": "..."},
 "final": {"cta": "...", "loop": "como o fim emenda no começo", "ultima_cena": "..."},
 "o_que_mais_contribui_para_reter": ["3 elementos de edição deste vídeo que mais seguram o espectador"]
}"""


def analisar_edicao(extras: list[str] | None = None) -> None:
    """Questionário COMPLETO de edição (som + imagem) na amostra + vídeos que o dono mandou (hall_da_fama)."""
    from viitu.assistir import perguntar
    am = json.loads((PASTA / "amostra.json").read_text(encoding="utf-8"))
    alvos = [(n, v) for n, c in am.items() for v in c["videos"]]
    for f in sorted((RAIZ / "hall_da_fama" / "videos").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        alvos.append((d.get("canal", "?"), {"id": f.stem, "titulo": d.get("titulo", ""), "views": d.get("views", 0), "papel": "enviado_pelo_dono"}))
    (PASTA / "edicao").mkdir(exist_ok=True)
    if "--reverso" in sys.argv:
        alvos = alvos[::-1]
    for nome, v in alvos:
        arq = PASTA / "edicao" / f"{v['id']}.json"
        if arq.exists():
            continue
        try:
            d = json.loads(perguntar(f"https://www.youtube.com/watch?v={v['id']}", PROMPT_EDICAO, fps=2))
            arq.write_text(json.dumps({"canal": nome, **v, "analise": d}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"✅ {nome} | {v['titulo'][:50]}", flush=True)
        except BaseException as e:
            print(f"❌ {nome} | {v['id']} | {str(e)[:120]}", flush=True)
        time.sleep(8)


def analisar() -> None:
    from viitu.assistir import perguntar
    am = json.loads((PASTA / "amostra.json").read_text(encoding="utf-8"))
    for nome, c in am.items():
        for v in c["videos"]:
            arq = PASTA / f"{v['id']}.json"
            if arq.exists():
                continue
            try:
                txt = perguntar(f"https://www.youtube.com/watch?v={v['id']}", PROMPT, fps=2)
                d = json.loads(txt)
                arq.write_text(json.dumps({"canal": nome, **v, "analise": d}, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"✅ {nome} | {v['views']:,} | {v['titulo'][:50]}", flush=True)
            except BaseException as e:
                print(f"❌ {nome} | {v['id']} | {str(e)[:120]}", flush=True)
            time.sleep(8)


def resumo() -> str:
    """Consolida as respostas: % de vídeos que fazem cada coisa (geral, por canal, top × mediano)."""
    import collections
    am = json.loads((PASTA / "amostra.json").read_text(encoding="utf-8"))
    linhas = {}
    for nome, c in am.items():
        for v in c["videos"]:
            arq = PASTA / f"{v['id']}.json"
            if arq.exists():
                linhas.setdefault(nome, []).append(json.loads(arq.read_text(encoding="utf-8")))
    todos = [x for l in linhas.values() for x in l]

    def g(d, *ks):
        for k in ks:
            d = d.get(k) if isinstance(d, dict) else None
        return d

    def tab(grupo):
        A = [x["analise"] for x in grupo]
        n = len(A) or 1
        cnt = lambda f: sum(1 for a in A if f(a))
        db = [g(a, "musica", "db_estimado_abaixo_da_voz") for a in A if isinstance(g(a, "musica", "db_estimado_abaixo_da_voz"), (int, float))]
        anim = [a for a in A if g(a, "animacao_2d_3d", "tem")]
        return {
            "videos": len(A),
            "musica_presente_%": round(100 * cnt(lambda a: g(a, "musica", "tem")) / n),
            "musica_db_abaixo_voz_mediana": st.median(db) if db else None,
            "whoosh_nos_cortes": dict(collections.Counter(a.get("whoosh_nos_cortes") for a in A)),
            "efeitos_caem": dict(collections.Counter(a.get("efeitos_caem") for a in A)),
            "som_por_palavra_%": round(100 * cnt(lambda a: a.get("som_por_palavra_da_legenda") == "sim") / n),
            "pop_em_seta_%": round(100 * cnt(lambda a: a.get("pop_em_seta_ou_circulo") == "sim") / n),
            "riser_%": round(100 * cnt(lambda a: g(a, "riser_antes_da_revelacao", "tem")) / n),
            "boom_mediana": st.median([g(a, "boom_ou_impacto", "quantos") or 0 for a in A]),
            "ding_mediana": st.median([g(a, "ding_ou_notificacao", "quantos") or 0 for a in A]),
            "memes": dict(collections.Counter(m for a in A for m in (a.get("sons_de_meme") or []) if m)),
            "foley_%": round(100 * cnt(lambda a: g(a, "foley_do_que_aparece", "tem")) / n),
            "som_original": dict(collections.Counter(a.get("som_original_do_clipe") for a in A)),
            "vacuo_%": round(100 * cnt(lambda a: g(a, "silencio_ou_vacuo_dramatico", "tem")) / n),
            "animacao_%": round(100 * len(anim) / n),
            "animacao": [f"{g(a,'animacao_2d_3d','tipo')} {g(a,'animacao_2d_3d','duracao_s')}s em {g(a,'animacao_2d_3d','inicio')}: {g(a,'animacao_2d_3d','o_que_explica')}" for a in anim],
        }
    out = {"GERAL": tab(todos), "TOP": tab([x for x in todos if x["papel"] == "top"]),
           "MEDIANO": tab([x for x in todos if x["papel"] == "mediano"]),
           **{k: tab(v) for k, v in linhas.items()}}
    out["_assinaturas"] = {x["canal"] + " | " + x["titulo"][:40]: x["analise"].get("assinatura_sonora") for x in todos}
    out["_regras"] = [r for x in todos for r in (x["analise"].get("regras_do_editor") or [])]
    (PASTA / "resumo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return json.dumps({k: v for k, v in out.items() if not k.startswith("_")}, ensure_ascii=False, indent=1)


def resumo_edicao() -> str:
    """Consolida o questionário completo: mediana dos volumes por camada e padrões visuais mais comuns."""
    import collections
    xs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((PASTA / "edicao").glob("*.json"))]

    def num(a, *ks):
        for k in ks:
            a = a.get(k) if isinstance(a, dict) else None
        return a if isinstance(a, (int, float)) and not isinstance(a, bool) else None

    def med(vals):
        v = [x for x in vals if x is not None]
        return (round(st.median(v), 1), len(v)) if v else (None, 0)

    def mais(vals, n=4):
        return collections.Counter(str(v).lower() for v in vals if v not in (None, "", "incerto")).most_common(n)

    def tab(g):
        A = [x["analise"] for x in g]
        m = {k: med([num(a, "mix_volumes_vs_voz", k) for a in A]) for k in
             ["musica_sob_fala_db", "musica_nas_pausas_db", "whoosh_db", "pop_db", "boom_db", "riser_db", "foley_ambiencia_db", "foley_detalhe_db"]}
        return {"videos": len(A), "mix_mediana_db(n)": m,
                "seg_por_cena": med([num(a, "ritmo", "segundos_por_cena_media") for a in A]),
                "corta_inicio_frase": mais([(a.get("ritmo") or {}).get("corta_no_inicio_de_frase") for a in A]),
                "frame0_seta_%": round(100 * sum(1 for a in A if (a.get("gancho_3s") or {}).get("seta_ou_circulo") is True) / max(len(A), 1)),
                "zoom_lento_%": round(100 * sum(1 for a in A if (a.get("zoom_e_camera") or {}).get("zoom_constante_lento") is True) / max(len(A), 1)),
                "punch_%": round(100 * sum(1 for a in A if (a.get("zoom_e_camera") or {}).get("punch_in_em_palavra") is True) / max(len(A), 1)),
                "tremida_%": round(100 * sum(1 for a in A if (a.get("zoom_e_camera") or {}).get("tremida") is True) / max(len(A), 1)),
                "camera_lenta_%": round(100 * sum(1 for a in A if (a.get("zoom_e_camera") or {}).get("camera_lenta") is True) / max(len(A), 1)),
                "seta_cor": mais([((a.get("marcacoes") or {}).get("seta") or {}).get("cor") for a in A]),
                "setas_por_video": med([num(a, "marcacoes", "seta", "quantas") for a in A]),
                "legenda_palavras": mais([(a.get("legenda") or {}).get("palavras_por_vez") for a in A]),
                "legenda_cor": mais([(a.get("legenda") or {}).get("cor_base") for a in A]),
                "legenda_destaque": mais([(a.get("legenda") or {}).get("cor_destaque") for a in A]),
                "legenda_posicao": mais([(a.get("legenda") or {}).get("posicao") for a in A]),
                "legenda_animacao": mais([(a.get("legenda") or {}).get("animacao") for a in A]),
                "transicao_mais_comum": mais([(a.get("transicoes") or {}).get("mais_comum") for a in A]),
                "efeitos_visuais": mais([e for a in A for e in (a.get("efeitos_visuais") or [])], 8),
                "cor": mais([a.get("cor") for a in A]),
                "marca_dagua_%": round(100 * sum(1 for a in A if (a.get("imagens") or {}).get("marca_dagua_visivel") is True) / max(len(A), 1)),
                "fundo_desfocado_%": round(100 * sum(1 for a in A if (a.get("imagens") or {}).get("bordas_ou_fundo_desfocado") is True) / max(len(A), 1)),
                "animacao_%": round(100 * sum(1 for a in A if (a.get("animacao_2d_3d") or {}).get("tem") is True) / max(len(A), 1)),
                "cta": mais([(a.get("final") or {}).get("cta") for a in A], 6),
                "retencao": mais([r for a in A for r in (a.get("o_que_mais_contribui_para_reter") or [])], 10)}
    por = collections.defaultdict(list)
    for x in xs:
        por[x["canal"]].append(x)
    out = {"GERAL": tab(xs), "TOP": tab([x for x in xs if x.get("papel") == "top"]),
           "ENVIADOS_PELO_DONO": tab([x for x in xs if x.get("papel") == "enviado_pelo_dono"]),
           **{k: tab(v) for k, v in por.items()}}
    (PASTA / "resumo_edicao.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return json.dumps(out["GERAL"], ensure_ascii=False, indent=1)


if __name__ == "__main__":
    r = {"amostra": amostra, "analisar": analisar, "edicao": analisar_edicao, "resumo": resumo, "resumo_edicao": resumo_edicao}[sys.argv[1]]()
    if isinstance(r, str):
        print(r)
