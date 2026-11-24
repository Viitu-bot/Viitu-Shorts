"""PLANTA DA MONTAGEM: trava automática ANTES do render, feita das reclamações recorrentes do dono.

Cada regra aqui nasceu de uma reclamação real (catálogo completo: edicao/reclamacoes.md). Roda sobre o cenas.json +
palavras.json (tempos reais da voz) e os arquivos dos clipes. Com qualquer ❌ o editor NÃO monta o vídeo.

  R1 REPETIÇÃO   cada arquivo de clipe entra em no máximo 2 cenas (curto ou longo, tanto faz: o dono vê o mesmo
                 avião/cenário e sente repetição). Exceção: a última cena (loop) copia a primeira. Variedade mínima:
                 fontes diferentes ≥ 60% das cenas reais.
  R2 3D EM BLOCO o 3D é a EXPLICAÇÃO: um bloco contínuo só (nenhum clipe real no meio), de 4 s a 45% do vídeo.
                 Clipe real vem ANTES (gancho/contexto) e DEPOIS (prova/virada), nunca cortando o 3D.
  R3 GANCHO      1ª cena = vídeo real (nunca foto, nunca 3D), sujeito grande, clipe ≥ 720p.
  R4 QUALIDADE   todo clipe real ≥ 720 px no lado menor, nítido e com movimento no trecho usado; < 720p só com
                 "baixa_res_ok": "<motivo>" e nunca no gancho.
  R5 FOTO        no máximo 2 fotos, nunca no gancho, nunca seguidas.
  R6 LOOP        a última cena é o mesmo clipe e o mesmo segundo da primeira.
  R8 SOM         sound design é parte da planta, não enfeite: todo bloco 3D tem sfx amarrado a CADA evento + entrada;
                 o gancho tem som de AÇÃO; nas outras cenas, só quando o som certo EXISTE (BÍBLIA §4); há virada
                 (impacto_em → riser/vácuo/boom) e música definida. Dono (18/11): "parece que só pôs um em cima do outro".
  R9 RITMO      cena real > 3 s (sem "acao_continua") e vista 3D > 3,5 s barram: corte a cada 2–3 s (vd004).
  R10 PARECIDAS duas cenas seguidas com quadro parecido (forma+cor ≥ 0,85) barram — intercalar perto/longe (dono 24/11).
  R11 VOZ LENTA < 3,0 palavras/s barra (dono 24/11, mediana 3,07 nos vídeos dele).
  R7 CENA LONGA  cena real ≥ 4 s sem "manter" vira o mesmo plano parado na tela (o editor divide, mas repete o clipe).

Exceção registrada: "bloco_3d_longo": "<pedido do dono>" no cenas.json (vd008: o dono pediu o tanque aberto em 3D).

Uso: python3 -m viitu.montagem <projeto>       (o editar chama sozinho; --forcar pula a trava, só com aval do dono)
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
FOTO = (".jpg", ".jpeg", ".png", ".webp")
MAX_USOS = 1          # dono 24/11 (vd016): "imagens muito próximas" — cada fonte entra UMA vez (loop/bruto à parte)
MIN_VARIEDADE = 0.6
CORTE_MAX = 3.0       # BÍBLIA/CLAUDE.md: corte a cada 2–3 s
CORTE_MAX_3D = 3.5
PARECIDO_MAX = 0.85
RITMO_MIN = 3.0
MIN_RES = 600          # px úteis no lado menor da tela vertical (horizontal 1080p recortado = 607)


def _dimensoes(arq: Path) -> tuple[int, int]:
    s = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True).stdout.strip().split(",")
    try:
        return int(s[0]), int(s[1])
    except (ValueError, IndexError):
        return 0, 0


def _nitidez_movimento(arq: Path, t0: float, dur: float) -> tuple[float, float]:
    """Nitidez (variância do Laplaciano, em 540 px) e movimento médio (diferença entre quadros) no trecho usado."""
    cap = cv2.VideoCapture(str(arq))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    nit, mov, ant = [], [], None
    for k in range(6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((t0 + dur * k / 5) * fps))
        ok, img = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(cv2.resize(img, (540, int(540 * img.shape[0] / img.shape[1]))), cv2.COLOR_BGR2GRAY)
        nit.append(cv2.Laplacian(g, cv2.CV_64F).var())
        if ant is not None and ant.shape == g.shape:
            mov.append(float(np.mean(cv2.absdiff(g, ant))))
        ant = g
    cap.release()
    return (float(np.median(nit)) if nit else 0.0, float(np.mean(mov)) if mov else 0.0)


def _tempos(pasta: Path, cenas: list[dict]) -> list[tuple[float, float]]:
    from viitu.editar import achar_palavra
    palavras = json.loads((pasta / "palavras.json").read_text(encoding="utf-8"))
    ini, ult = [], 0
    for c in cenas:
        i = achar_palavra(palavras, c["em"], ult)
        ult = i
        ini.append(0.0 if not ini else palavras[i]["inicio"])
    fim = palavras[-1]["fim"]
    return [(a, (ini[k + 1] if k + 1 < len(ini) else fim)) for k, a in enumerate(ini)]


def hash_cenas(cfg: dict) -> str:
    """Impressão digital do que MUDA O VÍDEO (cenas, música, CTA, destaques…); ignora anotações (formato, _funcao,
    créditos). A entrega compara com a impressão guardada no plano na hora do editar."""
    import hashlib
    ign = {"formato", "creditos_descricao", "permissoes"}
    limpo = {k: v for k, v in cfg.items() if not k.startswith("_") and k not in ign}
    limpo["cenas"] = [{k: v for k, v in c.items() if not k.startswith("_")} for c in cfg.get("cenas", [])]
    return hashlib.sha1(json.dumps(limpo, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def checar(projeto: str) -> tuple[list[str], list[str]]:
    pasta = RAIZ / "projetos" / projeto
    cfg = json.loads((pasta / "cenas.json").read_text(encoding="utf-8"))
    cenas = cfg["cenas"]
    tempos = _tempos(pasta, cenas)
    total = tempos[-1][1]
    erros, avisos = [], []
    eh_3d = [bool(c.get("animacao")) for c in cenas]
    eh_foto = [c["clipe"].lower().endswith(FOTO) and not eh_3d[k] for k, c in enumerate(cenas)]
    ultima = len(cenas) - 1
    loop_ok = cenas[ultima]["clipe"] == cenas[0]["clipe"]

    # RF formato (edicao/formatos.json): declarado e com as exigências do formato
    fmts = json.loads((RAIZ / "edicao" / "formatos.json").read_text(encoding="utf-8"))
    fmt = cfg.get("formato")
    if fmt not in fmts or fmt.startswith("_"):
        erros.append(f"RF FORMATO: declare \"formato\" no cenas.json ({', '.join(k for k in fmts if not k.startswith('_'))}).")
    else:
        F = fmts[fmt]
        dmin, dmax = F["duracao_s"]
        if not dmin - 1 <= total <= dmax + 2:
            avisos.append(f"RF {fmt}: duração {total:.1f} s fora de {dmin}–{dmax} s.")
        for ex in F.get("exige", []):
            if ex == "bruto_cronologico" and not cfg.get("bruto_cronologico"):
                erros.append(f"RF {fmt}: exige \"bruto_cronologico\" (um bruto em ordem).")
            if ex == "marca_erro" and not any(c.get("marca_erro") == "x" for c in cenas):
                erros.append(f"RF {fmt}: exige o X vermelho no jeito errado (\"marca_erro\": \"x\").")
            if ex == "numero_na_tela" and not any(c.get("contador") for c in cenas):
                erros.append(f"RF {fmt}: exige o contador no número principal (\"contador\").")
            if ex == "rehook_6s" and not any(4.5 <= tempos[k][0] <= 7.5 for k, c in enumerate(cenas)
                                            if any(i in c["em"] for i in cfg.get("impacto_em", []))):
                erros.append(f"RF {fmt}: exige re-hook (impacto_em) entre 4,5 e 7,5 s.")
    # R0 roteiro em partes (BÍBLIA §1): [GANCHO] [INÍCIO] [MEIO] [FINAL] [CTA] e loop sem ponto final
    rot = pasta / "roteiro.md"
    if rot.exists():
        txt = rot.read_text(encoding="utf-8")
        import re as _re
        _num = _re.match(r"vd(\d+)", projeto)
        regras_24_11 = bool(_num) and int(_num.group(1)) >= 16          # regras do dono de 24/11 valem do vd016 em diante
        partes = ("[GANCHO]", "[INÍCIO]", "[MEIO]", "[FINAL]") + (() if regras_24_11 else ("[CTA]",))
        faltam = [p for p in partes if p not in txt]
        if faltam:
            erros.append(f"R0 ROTEIRO SEM AS PARTES DO DONO: faltam {faltam} (edicao/BIBLIA.md §1).")
        if regras_24_11:
            # FINAL SEM ENCERRAMENTO (dono 24/11, queda nos últimos 5 s do vd004): termina na revelação ou emenda no gancho;
            # proibido resumo, moral, "da próxima vez", CTA pedindo inscrição/like no fim
            try:
                fim_voz = txt.split("TEXTO FINAL PARA A VOZ")[1].split("##")[0].strip().splitlines()[-1].lower()
            except IndexError:
                fim_voz = ""
            proib = [w for w in ("inscrev", "like", "curt", "segue", "comenta", "da próxima vez", "lembra", "moral", "resumindo")
                     if w in fim_voz]
            if proib or "[CTA]" in txt:
                erros.append(f"R0 FINAL COM ENCERRAMENTO: a última frase tem {proib or ['[CTA]']} — o vídeo termina na última palavra "
                             "da revelação ou emenda no gancho (dono 24/11).")
        try:
            voz_txt = txt.split("TEXTO FINAL PARA A VOZ")[1].split("##")[0].strip()
            if voz_txt.rstrip().endswith("."):
                erros.append("R0 LOOP: o texto da voz termina em ponto final; tem que fechar em conjunção suspensa.")
        except IndexError:
            pass

    # R1 repetição
    usos = defaultdict(list)
    for k, c in enumerate(cenas):
        if eh_3d[k] or (k == ultima and loop_ok):
            continue
        usos[c["clipe"]].append(k + 1)
    # BRUTO CRONOLÓGICO (BÍBLIA §5): o arquivo marcado pode estar em muitas cenas SE cada uma for uma etapa nova:
    # inícios sempre crescentes e ≥ 1,5 s de distância (nada de voltar ao mesmo trecho)
    # ARQUIVO LIVRE (vd017): filme longo de arquivo usado fora de ordem — vale se cada trecho for OUTRO momento (≥ 2,5 s
    # de distância entre os inícios; nada de repetir o mesmo plano)
    for livre in cfg.get("bruto_livre", []):
        if livre in usos:
            ts = sorted(cenas[k - 1].get("inicio", 0) for k in usos[livre])
            try:                                       # tomadas diferentes (cortes internos do vídeo) = momentos diferentes
                tr = json.loads((pasta / "clipes" / "triagem.json").read_text(encoding="utf-8"))[livre]["trechos_utilizaveis"]
            except (OSError, KeyError, ValueError):
                tr = []
            mesmo = lambda x, y: any(a0 <= x < a1 and a0 <= y < a1 for a0, a1 in tr) if tr else True
            if any(b2 - a2 < 2.5 and mesmo(a2, b2) for a2, b2 in zip(ts, ts[1:])):
                erros.append(f"R1 ARQUIVO REPETIDO: {livre} usa trechos colados (inícios {ts}); cada cena = outro momento do filme.")
            usos.pop(livre)
    brutos = cfg.get("bruto_cronologico") or []
    for bruto in ([brutos] if isinstance(brutos, str) else brutos):     # um arquivo ou uma lista de vídeos longos
        if bruto not in usos:
            continue
        ts = [cenas[k - 1].get("inicio", 0) for k in usos[bruto]]
        if any(b2 - a2 < 1.5 for a2, b2 in zip(ts, ts[1:])):
            erros.append(f"R1 BRUTO FORA DE ORDEM: {bruto} volta ou repete trecho (inícios {ts}); cada cena = etapa NOVA, em ordem.")
        usos.pop(bruto)
    for cl, ks in usos.items():
        if len(ks) > MAX_USOS:
            erros.append(f"R1 REPETIÇÃO: {cl} aparece em {len(ks)} cenas ({ks}); máximo {MAX_USOS}. Buscar outra fonte.")
    reais = sum(len(v) for v in usos.values())          # (o bruto cronológico não entra na conta de variedade)
    if reais and len(usos) < math.ceil(reais * MIN_VARIEDADE):
        erros.append(f"R1 VARIEDADE: {len(usos)} fontes para {reais} cenas reais (mínimo {math.ceil(reais * MIN_VARIEDADE)}).")

    # R2 3D em bloco único
    idx3d = [k for k, v in enumerate(eh_3d) if v]
    if idx3d:
        blocos = [[idx3d[0]]]
        for k in idx3d[1:]:
            (blocos[-1].append(k) if k == blocos[-1][-1] + 1 else blocos.append([k]))
        if len(blocos) > 1:
            erros.append(f"R2 3D PICOTADO: {len(blocos)} blocos de 3D separados por clipe real "
                         f"(cenas {[[b[0] + 1, b[-1] + 1] for b in blocos]}). A explicação 3D é UM bloco contínuo.")
        dur3d = sum(tempos[k][1] - tempos[k][0] for k in idx3d)
        if dur3d < 4:
            erros.append(f"R2 3D CURTO: {dur3d:.1f} s de 3D; a explicação precisa de ≥ 4 s para ser entendida.")
        lim3d = json.loads((RAIZ / "edicao" / "formatos.json").read_text(encoding="utf-8")).get(cfg.get("formato", ""), {}).get("max_3d_pct", 0.45)
        if dur3d > lim3d * total and not cfg.get("bloco_3d_longo"):     # só quando o dono pediu o 3D longo
            avisos.append(f"R2 3D DEMAIS (hipótese, não bloqueia): {dur3d:.1f} s ({dur3d / total:.0%}); máximo {lim3d:.0%} neste formato.")
        ini3d = tempos[idx3d[0]][0] / total
        if not 0.25 <= ini3d <= 0.6 and 0 not in idx3d:
            avisos.append(f"R2 3D FORA DO MEIO (hipótese, não bloqueia): o bloco 3D começa em {ini3d:.0%} do vídeo; a explicação fica entre 25% e 60% "
                         "(edicao/formato.md).")
        if 0 in idx3d:
            erros.append("R3 GANCHO EM 3D: o gancho é sempre clipe real.")

    # R3 gancho / R5 fotos
    if eh_foto[0]:
        erros.append("R3 GANCHO COM FOTO: a 1ª cena precisa ser vídeo real em movimento.")
    fotos = [k for k, v in enumerate(eh_foto) if v and not (k == ultima and loop_ok)]
    if len(fotos) > 2:
        erros.append(f"R5 FOTOS DEMAIS: {len(fotos)} (máximo 2).")
    if any(b - a == 1 for a, b in zip(fotos, fotos[1:])):
        erros.append("R5 FOTOS SEGUIDAS: duas fotos em sequência parecem slide.")

    # R6 loop
    if not loop_ok or abs(cenas[ultima].get("inicio", 0) - cenas[0].get("inicio", 0)) > 0.3:
        erros.append("R6 LOOP: a última cena precisa ser o mesmo clipe e o mesmo segundo da primeira.")

    # R8 som
    for k in idx3d:
        a = cenas[k]["animacao"]
        sfx = a.get("sfx", [])
        faltam = [ev for ev in a.get("eventos", {}) if not any(e.get("evento") == ev for e in sfx)]
        if len(sfx) < 2 or faltam:
            erros.append(f"R8 3D SEM SOUND DESIGN: cena {k + 1} tem {len(sfx)} sfx" + (f"; eventos sem som: {faltam}" if faltam else "")
                         + " (animacao.sfx: entrada + 1 por evento).")
    reais_idx = [k for k in range(len(cenas)) if not eh_3d[k] and not (k == ultima and loop_ok)]
    com_acao = [k for k in reais_idx if cenas[k].get("sfx_cena")]
    tempos_r8 = _tempos(RAIZ / "projetos" / projeto, cenas)
    if reais_idx and not any(k in com_acao and tempos_r8[k][0] < 3.0 for k in reais_idx):
        erros.append("R8 GANCHO SEM SOM DE AÇÃO: alguma cena dos 3 primeiros segundos precisa de sfx_cena (o som do que aparece).")
    # SOM NA AÇÃO (dono, vd011: "os efeitos não encaixam"): som de clipe real cai no instante da ação NA IMAGEM
    for k in com_acao:
        sem = [e.get("em") for e in cenas[k]["sfx_cena"] if "no_clipe" not in e]
        if sem:
            erros.append(f"R8 SOM FORA DA AÇÃO: cena {k + 1} tem som sem \"no_clipe\" {sem} — ver na prancha o segundo do clipe "
                         "em que a ação acontece (encaixe, estalo, golpe) e marcar no_clipe.")
    if reais_idx and len(com_acao) < math.ceil(0.4 * len(reais_idx)):
        avisos.append(f"R8 pouco som de ação: {len(com_acao)}/{len(reais_idx)} cenas reais com sfx_cena (conferir se falta som que EXISTE na cena). "
                     f"Sem som: cenas {[k + 1 for k in reais_idx if k not in com_acao]}.")
    if not cfg.get("impacto_em"):
        erros.append("R8 SEM VIRADA SONORA: defina impacto_em (riser → vácuo → boom).")
    if str(cfg.get("musica", "")).startswith("app:"):
        erros.append("R8 MÚSICA FORA DO ARQUIVO: o dono reprovou 2x vídeo sem trilha (reclamação #18). Use trilha própria "
                     "licenciada em \"musica\" (assets/musica/); a música conhecida vai só como sugestão no /publicar.")
    if not cfg.get("musica"):
        erros.append("R8 SEM MÚSICA: defina musica (biblioteca própria ou app:<faixa>).")
    # R8 AMBIÊNCIA (dono 24/11, vd017: "parece filme mudo narrado"): o lugar tem que SOAR — fundo ("foley") ou som
    # original na maior parte do vídeo, não só efeitos soltos
    com_amb = sum(tempos[k][1] - tempos[k][0] for k, c in enumerate(cenas) if c.get("foley") or c.get("som_original"))
    if total and com_amb < 0.7 * total:
        erros.append(f"R8 SEM AMBIÊNCIA: só {com_amb / total:.0%} do vídeo tem som de lugar; marcar \"foley\" (mar_costa, vento, "
                     f"casamata, tropa_forte, artilharia_longe, aviao, oficina, multidao…) em ≥ 70% das cenas.")

    # R4 qualidade + R7 cena longa (por cena real)
    medidos = {}
    for k, c in enumerate(cenas):
        if eh_3d[k] or eh_foto[k] or (k == ultima and loop_ok):
            continue
        arq = pasta / "clipes" / c["clipe"]
        if not arq.exists():
            erros.append(f"R4 ARQUIVO FALTANDO: {c['clipe']} (cena {k + 1}).")
            continue
        w, h = medidos.setdefault(c["clipe"], _dimensoes(arq))
        dur = tempos[k][1] - tempos[k][0]
        lado = min(w, h)
        if w > h and c.get("layout") != "inteiro":     # horizontal recortado para 9:16: sobra só h*9/16 de largura
            lado = min(lado, int(h * 9 / 16) + 1)
        if lado < MIN_RES:
            msg = f"R4 BAIXA RESOLUÇÃO: {c['clipe']} tem {w}x{h} → {lado} px úteis na tela vertical (cena {k + 1})"
            if k == 0:
                erros.append(msg + " — proibido no gancho.")
            elif not c.get("baixa_res_ok"):
                erros.append(msg + " — trocar ou justificar com \"baixa_res_ok\".")
        usado = max(dur * float(c.get("velocidade", 1.0)), 0.5)          # trecho do CLIPE realmente usado (câmera lenta usa menos)
        nit, mov = _nitidez_movimento(arq, float(c.get("inicio", 0)), usado)
        if nit < 40:
            erros.append(f"R4 DESFOCADO: cena {k + 1} ({c['clipe']}@{c.get('inicio', 0)}s) nitidez {nit:.0f}.")
        if mov < 1.0 and not c.get("parado_ok"):
            avisos.append(f"R4 PARADO: cena {k + 1} ({c['clipe']}) quase sem movimento ({mov:.1f}); parece foto.")
        lim_cena = 6.0 if cfg.get("formato") == "processo" else 4.0           # processo: deixar a ação satisfatória rodar
        if dur >= lim_cena:
            avisos.append(f"R7 cena longa: cena {k + 1} dura {dur:.1f} s com um clipe só — ok SE a ação prende (BÍBLIA §3); senão, trocar.")
        if dur > CORTE_MAX and not c.get("acao_continua") and not (k == ultima and loop_ok):
            erros.append(f"R9 RITMO: cena {k + 1} dura {dur:.1f} s; corte a cada ≤ {CORTE_MAX} s (vd004: 1,76 s). Dividir com OUTRA fonte.")
    # R9 ritmo no 3D: o bloco é um só (R2), mas troca de câmera (fase) a cada ≤ 3,5 s
    _pal = json.loads((pasta / "palavras.json").read_text(encoding="utf-8"))
    _pal = _pal if isinstance(_pal, list) else _pal["palavras"]
    for k in [k for k, v in enumerate(eh_3d) if v]:
        a0, a1 = tempos[k]
        marcas = [a0]                                   # cortes de câmera ("cortes": [{"em": palavra, "zoom", "foco"}])
        for c in cenas[k]["animacao"].get("cortes", []):
            alvo = [w for w in c["em"].lower().split()]
            for i in range(len(_pal) - len(alvo) + 1):
                if a0 <= _pal[i]["inicio"] < a1 and [p["palavra"].lower().strip('.,:;!?') for p in _pal[i:i + len(alvo)]] == alvo:
                    marcas.append(_pal[i]["inicio"]); break
        marcas = sorted(marcas) + [a1]
        d = max(b - a for a, b in zip(marcas, marcas[1:]))
        if d > CORTE_MAX_3D and not cfg.get("bloco_3d_longo"):
            erros.append(f"R9 RITMO 3D: cena 3D {k + 1} fica {d:.1f} s no mesmo enquadramento; dividir com \"cortes\" "
                         f"(zoom/foco) ou vistas (fase) de ≤ {CORTE_MAX_3D} s.")
    # R10 IMAGENS PARECIDAS: duas cenas seguidas com o mesmo quadro (cor/forma) = o olho não sente o corte
    quadros = {}
    for k in range(len(cenas) - 1):
        a, b = cenas[k], cenas[k + 1]
        if eh_3d[k] or eh_3d[k + 1] or eh_foto[k] or eh_foto[k + 1]:
            continue
        qa = quadros.setdefault(k, _quadro(pasta / "clipes" / a["clipe"], float(a.get("inicio", 0)) + 0.4))
        qb = quadros.setdefault(k + 1, _quadro(pasta / "clipes" / b["clipe"], float(b.get("inicio", 0)) + 0.4))
        if qa is not None and qb is not None:
            sim = _parecido(qa, qb)
            if sim >= PARECIDO_MAX:
                erros.append(f"R10 IMAGENS PARECIDAS: cenas {k + 1} e {k + 2} ({sim:.2f}); intercalar plano (perto/longe), cor ou movimento.")
    # R11 VOZ LENTA (dono 24/11): ritmo mínimo medido nos 12 vídeos editados pelo dono
    try:
        pal = json.loads((pasta / "palavras.json").read_text(encoding="utf-8"))
        pal = pal if isinstance(pal, list) else pal["palavras"]
        rps = len(pal) / pal[-1]["fim"]
        if rps < RITMO_MIN:
            erros.append(f"R11 VOZ LENTA: {rps:.2f} palavras/s; mínimo {RITMO_MIN} (dono: mediana 3,07). Rodar viitu.voz (ajusta sozinho).")
    except (OSError, KeyError, IndexError, ZeroDivisionError):
        pass
    return erros, avisos


def _quadro(arq: Path, t: float):
    """Quadro 48x85 (vertical) em cinza + cor média, para comparar cenas vizinhas."""
    import numpy as np
    if not arq.exists():
        return None
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(arq), "-frames:v", "1",
                        "-vf", "crop=ih*9/16:ih,scale=48:85", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    if len(r.stdout) < 48 * 85 * 3:
        return None
    return np.frombuffer(r.stdout[:48 * 85 * 3], dtype=np.uint8).reshape(85, 48, 3).astype(float)


def _parecido(a, b) -> float:
    """0..1: média de (forma: correlação do cinza) e (cor: 1 − distância das médias de cor)."""
    import numpy as np
    ga, gb = a.mean(2).ravel(), b.mean(2).ravel()
    forma = float(np.corrcoef(ga, gb)[0, 1]) if ga.std() > 1 and gb.std() > 1 else 1.0
    cor = 1 - float(np.abs(a.mean((0, 1)) - b.mean((0, 1))).mean()) / 128
    return max(0.0, (forma + cor) / 2)


def main() -> None:
    projeto = [a for a in sys.argv[1:] if not a.startswith("--")][0]
    erros, avisos = checar(projeto)
    print("PLANTA DA MONTAGEM:", "APROVADA ✅" if not erros else f"{len(erros)} erro(s) ❌")
    for e in erros:
        print("  ❌", e)
    for a in avisos:
        print("  ⚠️", a)
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
