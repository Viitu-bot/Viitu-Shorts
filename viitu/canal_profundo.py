"""Análise PROFUNDA da edição de um canal de referência, com filtro.

1. Filtra os Shorts do relatório do canal (hall_da_fama/canais/<handle>.json) pelas categorias do nicho do Viitu
   e pega os N de mais views.
2. Cada vídeo passa pela mesma FICHA DE EDIÇÃO no Gemini (cena a cena: imagem, origem, efeito com nome técnico,
   som no corte e dentro da cena, música, 3D).
3. Junta tudo e conta o que se repete (consenso entre vídeos — uma observação isolada do Gemini pode estar errada).

Uso:
  python3 -m viitu.canal_profundo analisar @avidamaravilha --n 12
  python3 -m viitu.canal_profundo resumo @avidamaravilha
"""
from __future__ import annotations

import collections
import json
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NICHO = {"invenção/tecnologia", "como é feito (processo/fábrica)", "perigo/erro/segurança",
         "motivo oculto de objeto/design", "recorde/escala/mais caro do mundo"}

FICHA = """Você é um editor sênior de YouTube Shorts fazendo ENGENHARIA REVERSA da EDIÇÃO deste vídeo para que outro
editor consiga REPRODUZIR igual. Assista inteiro, com áudio. Use os NOMES TÉCNICOS padrão do mercado para efeitos
(ex.: punch-in, zoom in lento/Ken Burns, speed ramp, camera shake, whip pan, freeze frame, flash branco, glitch,
RGB split, motion blur, máscara/recorte, split screen, picture-in-picture, slow motion, reverse, match cut, J-cut,
L-cut, sound bridge, riser, whoosh, swoosh, hit/impacto, boom/sub drop, pop, ding, tape stop, reverse cymbal,
silêncio dramático, ducking). Quando souber, diga o nome que o efeito tem no CapCut. Responda SÓ o que viu/ouviu;
se não tiver certeza escreva "incerto". JSON em português:
{
 "cenas": [ {"inicio": "MM:SS", "fim": "MM:SS", "narracao": "trecho falado",
   "imagem": "o que aparece",
   "tipo": "clipe real|3D realista|3D cartoon|foto|gráfico/texto|tela gravada",
   "origem_provavel": "stock (Pexels/Storyblocks...)|reportagem/TV|vídeo viral (TikTok/Douyin/Instagram)|câmera do fabricante/empresa|simulação 3D comprada/canal de 3D|filme de arquivo|incerto",
   "pistas_da_origem": "marca d'água, logo, crédito, legenda em outro idioma, proporção, qualidade",
   "enquadramento": "vertical nativo|horizontal recortado|horizontal com fundo desfocado|tela dividida",
   "movimento": "parado|zoom in lento|zoom out|pan|punch-in|tremida|câmera lenta|acelerado",
   "efeito_na_entrada": "nome técnico do efeito/transição no corte (ou corte seco)",
   "efeitos_dentro": ["nome técnico + em qual palavra"],
   "marcacao_na_tela": "seta|círculo|texto|emoji|nenhuma (+ cor/estilo)",
   "som_no_corte": "nome técnico do som que entra NO corte (ou nenhum)",
   "som_dentro": ["som + o que acontece na imagem nesse instante (ex.: impacto quando o pássaro bate)"],
   "som_original_do_clipe": "mantido alto|mantido baixo|removido|incerto",
   "musica": "continua|sobe|abaixa|para (silêncio)|troca"} ],
 "musica": {"estilo": "...", "andamento": "lento|médio|rápido", "volume_vs_voz": "bem baixo|baixo|médio",
            "momentos_em_que_muda": ["MM:SS o que muda e por quê"]},
 "camadas_de_som": {"diegetico_dos_clipes": "usa?|como", "foley_adicionado": "usa?|quais", "sfx_de_transicao": "quais",
                    "sfx_de_enfase": "quais e em que tipo de palavra"},
 "tres_d": {"tem": true, "estilo": "realista|semi-realista|cartoon|low-poly", "parece_feito_em": "Blender|Unreal|After Effects|stock 3D|IA de vídeo|incerto",
            "assinatura_visual": "luz, materiais, câmera, partículas que caracterizam", "como_alterna_com_real": "..."},
 "legenda": {"palavras_por_vez": 1, "cor_base": "...", "cor_destaque": "...", "posicao": "...", "animacao": "..."},
 "estrutura_do_roteiro": ["função de cada bloco em ordem: gancho, pergunta, mito, explicação, prova, virada, fecho/loop"],
 "assinatura_do_canal": ["5 coisas de edição que se repetem e fazem este vídeo parecer deste canal"]
}"""


def _canal(handle: str) -> dict:
    return json.loads((RAIZ / "hall_da_fama" / "canais" / f"{handle.lstrip('@')}.json").read_text(encoding="utf-8"))


def _pasta(handle: str) -> Path:
    p = RAIZ / "pesquisa" / "canais" / handle.lstrip("@")
    p.mkdir(parents=True, exist_ok=True)
    return p


def filtrar(handle: str, n: int) -> list[dict]:
    vids = [v for v in _canal(handle)["videos"] if v.get("categoria") in NICHO]
    return sorted(vids, key=lambda v: -v["views"])[:n]


def analisar(handle: str, n: int) -> None:
    from viitu.assistir import perguntar
    pasta = _pasta(handle)
    alvos = filtrar(handle, n)
    print(f"{len(alvos)} vídeos do nicho (de {len(_canal(handle)['videos'])}) → {pasta}")
    for v in alvos:
        arq = pasta / f"{v['id']}.json"
        if arq.exists():
            continue
        try:
            d = json.loads(perguntar(f"https://www.youtube.com/watch?v={v['id']}", FICHA, fps=2))
            arq.write_text(json.dumps({**v, "ficha": d}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"✅ {v['views']:>11,} | {v['titulo'][:60]}", flush=True)
        except BaseException as e:      # cota/erro: segue para o próximo
            print(f"❌ {v['id']} | {str(e)[:120]}", flush=True)
        time.sleep(6)


def _seg(t: str) -> float:
    try:
        m, s = str(t).split(":")
        return int(m) * 60 + float(s)
    except ValueError:
        return 0.0


def resumo(handle: str) -> str:
    pasta = _pasta(handle)
    fichas = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(pasta.glob("*.json"))]
    if not fichas:
        return "nenhuma ficha"
    C = collections.Counter
    tipos, origens, enq, mov, ent, dentro, marc, som_c, som_d, orig_som, mus = C(), C(), C(), C(), C(), C(), C(), C(), C(), C(), C()
    durs, por_video = [], []
    for fi in fichas:
        cenas = fi["ficha"].get("cenas", [])
        por_video.append(len(cenas))
        for c in cenas:
            d = _seg(c.get("fim")) - _seg(c.get("inicio"))
            if 0 < d < 30:
                durs.append(d)
            tipos[c.get("tipo", "?")] += 1
            origens[c.get("origem_provavel", "?")] += 1
            enq[c.get("enquadramento", "?")] += 1
            mov[c.get("movimento", "?")] += 1
            ent[c.get("efeito_na_entrada", "?")] += 1
            for e in c.get("efeitos_dentro", []) or []:
                dentro[str(e).split(" em ")[0].split("(")[0].strip().lower()[:40]] += 1
            marc[str(c.get("marcacao_na_tela", "?")).split("(")[0].strip().lower()[:30]] += 1
            som_c[str(c.get("som_no_corte", "?")).strip().lower()[:30]] += 1
            for s in c.get("som_dentro", []) or []:
                som_d[str(s)[:90]] += 1
            orig_som[c.get("som_original_do_clipe", "?")] += 1
            mus[c.get("musica", "?")] += 1
    total = sum(tipos.values())
    top = lambda c, k=8: " · ".join(f"{a} ({b})" for a, b in c.most_common(k))
    l = [f"# Edição a fundo: {fichas[0].get('canal', handle)} ({handle})", "",
         f"- {len(fichas)} vídeos do nicho (filtro: {', '.join(sorted(NICHO))}), os de mais views",
         f"- {total} cenas · mediana **{statistics.median(durs):.1f} s por cena** · {statistics.median(por_video):.0f} cenas por vídeo", "",
         "## Imagem", f"- Tipo: {top(tipos)}", f"- Origem provável: {top(origens)}", f"- Enquadramento: {top(enq)}",
         f"- Movimento: {top(mov)}", f"- Efeito no corte: {top(ent, 10)}", f"- Efeitos dentro da cena: {top(dentro, 12)}",
         f"- Marcação na tela: {top(marc)}", "", "## Som",
         f"- Som no corte: {top(som_c, 10)}", f"- Som original dos clipes: {top(orig_som)}", f"- Música por cena: {top(mus)}", ""]
    for chave, titulo in (("camadas_de_som", "Camadas de som"), ("tres_d", "3D"), ("legenda", "Legenda"), ("musica", "Música")):
        l.append(f"## {titulo} (por vídeo)")
        for fi in fichas:
            l.append(f"- **{fi['titulo'][:50]}** ({fi['views'] / 1e6:.1f} mi): {json.dumps(fi['ficha'].get(chave, {}), ensure_ascii=False)[:400]}")
        l.append("")
    l.append("## Estrutura do roteiro (por vídeo)")
    for fi in fichas:
        l.append(f"- **{fi['titulo'][:50]}**: {' → '.join(map(str, fi['ficha'].get('estrutura_do_roteiro', [])))[:300]}")
    l += ["", "## Assinatura do canal (o que o Gemini viu se repetir)"]
    ass = C(str(a)[:120] for fi in fichas for a in fi["ficha"].get("assinatura_do_canal", []))
    l += [f"- {a}" for a, _ in ass.most_common(25)]
    l += ["", "## Exemplos de som sincronizado com a imagem"]
    l += [f"- {s}" for s, _ in som_d.most_common(30)]
    txt = "\n".join(l) + "\n"
    (RAIZ / "pesquisa" / "canais" / f"{handle.lstrip('@')}_edicao.md").write_text(txt, encoding="utf-8")
    return txt


def main() -> None:
    cmd, handle = sys.argv[1], sys.argv[2]
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 12
    if cmd == "analisar":
        analisar(handle, n)
    elif cmd == "filtrar":
        for v in filtrar(handle, n):
            print(f"{v['views']:>11,} | {v['dur']}s | {v['categoria'][:20]} | {v['titulo'][:60]} | {v['id']}")
    else:
        print(resumo(handle))


if __name__ == "__main__":
    main()
