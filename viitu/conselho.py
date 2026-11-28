"""CONSELHO DO CANAL (dono 28/11: "algo que funcionasse igual ao LLM Council, adaptado ao projeto… embasado, tudo em prol
do canal"). Mesmo método do llm-council do Karpathy, mas cada conselheiro LÊ as regras e os dados do projeto:

  1. OPINIÕES  — 4 conselheiros (modelos diferentes, papéis diferentes) respondem sozinhos à proposta do dono.
  2. REVISÃO   — cada um recebe as respostas dos outros SEM saber de quem são (A, B, C…) e ranqueia por embasamento.
  3. PRESIDENTE — junta tudo, pesa o ranking e entrega: veredito, contradições com o que já existe, base de cada ponto e
                  exatamente o que mudar/apagar para não sobrar regra contraditória.
Regra de ouro: opinião sem base no projeto (arquivo, dado do canal, print do dono) é marcada "SEM BASE" e pesa menos.

Uso:
  python3 -m viitu.conselho "proposta ou dúvida do dono"          → relatório em dados/conselho/
  python3 -m viitu.conselho --faxina                               → lista as contradições que JÁ existem entre as regras
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "dados" / "conselho"

# arquivos que formam a "memória" do canal (o que o conselho precisa conhecer para não contradizer)
CONTEXTO = ["CLAUDE.md", "edicao/BIBLIA.md", "edicao/reclamacoes.md", "edicao/fontes_das_regras.md",
            "edicao/especificacao.json", "edicao/identidade.md", "edicao/retencao_storyboard.md",
            "edicao/ganchos_gatilhos.md", "edicao/matriz_702010.md", "biblioteca_sfx/LEIA.md",
            "assets/musica/jogo_antigo/LEIA.md", "dados/temas_feitos.md"]

CONSELHEIROS = [
    ("gemini-3.1-pro-preview", "ANALISTA DE RETENÇÃO",
     "Você só aceita o que tem dado: retenção, views, % assistido, prints do dono, medições em fontes_das_regras.md. "
     "Diz o efeito provável na retenção e no alcance do Short, com número quando existir."),
    ("gemini-3.6-flash", "GUARDIÃO DO DNA",
     "Você protege a identidade do canal (voz, humor malandro adulto, abertura, trilha, legenda, ritmo). Aponta quando a "
     "proposta apaga ou contradiz o DNA e o que se perde."),
    ("gemini-2.5-pro", "CAÇADOR DE CONTRADIÇÕES",
     "Você procura, linha por linha, regras do projeto que a proposta contradiz ou duplica (cite arquivo e o trecho exato) "
     "e diz qual versão deve ficar e qual apagar."),
    ("gemma-4-31b-it", "ESTRATEGISTA DE CRESCIMENTO",
     "Você pensa em crescer o canal de Shorts (algoritmo, gancho, loop, frequência, custo de produção e crédito gasto). "
     "Quando usar conhecimento geral de YouTube, marque 'conhecimento geral, sem dado do canal'."),
]
PRESIDENTE = "gemini-3.1-pro-preview"
RESERVA = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-flash-latest"]


def _chave() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    env = RAIZ / ".env"
    for l in env.read_text(encoding="utf-8").splitlines() if env.exists() else []:
        if l.startswith("GEMINI_API_KEY="):
            return l.split("=", 1)[1].strip()
    raise SystemExit("Falta GEMINI_API_KEY")


def _contexto(limite: int = 60000) -> str:
    """As regras do projeto, cada arquivo com o nome (para o conselheiro citar a fonte)."""
    partes = []
    for rel in CONTEXTO:
        p = RAIZ / rel
        if p.exists():
            txt = p.read_text(encoding="utf-8", errors="ignore")
            partes.append(f"=== ARQUIVO: {rel} ===\n{txt[:limite]}")
    return "\n\n".join(partes)


def _perguntar(modelo: str, prompt: str, temperatura: float = 0.4) -> str:
    for m in [modelo] + RESERVA:
        for tentativa in range(2):
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                                  params={"key": _chave()}, timeout=300,
                                  json={"contents": [{"parts": [{"text": prompt}]}],
                                        "generationConfig": {"temperature": temperatura}})
                if r.status_code == 200:
                    c = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                    txt = "".join(x.get("text", "") for x in c).strip()
                    if txt:
                        return txt if m == modelo else f"[respondido por {m}, reserva]\n{txt}"
                time.sleep(3 + 4 * tentativa)
            except requests.RequestException:
                time.sleep(3)
    return "(sem resposta: todos os modelos falharam)"


BASE = ("Você faz parte do CONSELHO do canal de YouTube Shorts @viitushorts (curiosidades em PT-BR, dono leigo que opera pelo "
        "celular). Abaixo estão TODAS as regras, reclamações, medições e dados do canal. Responda em português do Brasil, "
        "simples, direto. TODA afirmação precisa de base: cite o ARQUIVO (e o trecho) ou o dado do canal; o que vier de "
        "conhecimento geral, escreva 'SEM BASE NO CANAL'. Não invente números.\n\n")


def opiniao(proposta: str, ctx: str, papel: tuple) -> str:
    modelo, nome, foco = papel
    prompt = (BASE + f"SEU PAPEL: {nome}. {foco}\n\n{ctx}\n\n=== PROPOSTA/DÚVIDA DO DONO ===\n{proposta}\n\n"
              "Responda com estas seções curtas:\n1. VEREDITO: aprovar / aprovar com ajuste / reprovar (1 linha)\n"
              "2. O QUE A PROPOSTA CONTRADIZ OU DUPLICA (arquivo + trecho), ou 'nada'\n3. BASE (dados/arquivos que sustentam "
              "ou derrubam)\n4. RISCO PARA O CANAL\n5. COMO FARIA (o ajuste concreto)")
    return _perguntar(modelo, prompt)


def revisao(proposta: str, respostas: dict[str, str], papel: tuple) -> str:
    modelo, nome, _ = papel
    blocos = "\n\n".join(f"--- RESPOSTA {k} ---\n{v}" for k, v in respostas.items())
    prompt = (BASE + f"SEU PAPEL nesta etapa: revisor anônimo ({nome}).\nPROPOSTA DO DONO: {proposta}\n\n"
              f"Abaixo, respostas de outros conselheiros (anônimas):\n{blocos}\n\n"
              "Avalie cada uma: está embasada no projeto? acertou as contradições? ajuda o canal a crescer? Termine com a linha "
              "exata 'RANKING: X > Y > Z' (melhor primeiro) e 1 frase por resposta.")
    return _perguntar(modelo, prompt, 0.2)


def presidente(proposta: str, ctx: str, ops: dict[str, str], revs: dict[str, str], legenda: dict[str, str]) -> str:
    o = "\n\n".join(f"--- {legenda[k]} (resposta {k}) ---\n{v}" for k, v in ops.items())
    r = "\n\n".join(f"--- revisão de {k} ---\n{v}" for k, v in revs.items())
    prompt = (BASE + f"SEU PAPEL: PRESIDENTE DO CONSELHO. Junte as opiniões pesando o ranking das revisões e o embasamento.\n\n"
              f"{ctx}\n\n=== PROPOSTA DO DONO ===\n{proposta}\n\n=== OPINIÕES ===\n{o}\n\n=== REVISÕES ANÔNIMAS ===\n{r}\n\n"
              "Entregue, curto e para leigo:\n## Veredito\n(aprovar / aprovar com ajuste / reprovar + por quê em 2 linhas)\n"
              "## Contradições com o que já existe\n(arquivo → trecho → o que fica e o que sai)\n## Base\n(o que tem dado do "
              "canal e o que é SEM BASE NO CANAL)\n## Como gravar\n(exatamente quais arquivos mudar e o que apagar, para não "
              "sobrar regra contraditória)\n## Pergunta para o dono\n(se houver escolha real, 2–3 opções, a recomendada "
              "primeiro)\n## Confiança\n(alta/média/baixa e por quê)")
    return _perguntar(PRESIDENTE, prompt, 0.2)


def _salvar(nome: str, texto: str) -> Path:
    SAIDA.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", nome.lower())[:50].strip("_") or "consulta"
    arq = SAIDA / f"{datetime.now():%Y-%m-%d_%H%M}_{slug}.md"
    arq.write_text(texto, encoding="utf-8")
    return arq


def conselho(proposta: str) -> Path:
    ctx = _contexto()
    print(f"Conselho reunido: {len(CONSELHEIROS)} conselheiros, contexto de {len(ctx) // 1000} mil caracteres.")
    with ThreadPoolExecutor(len(CONSELHEIROS)) as ex:
        ops_lista = list(ex.map(lambda p: opiniao(proposta, ctx, p), CONSELHEIROS))
    letras = [chr(65 + i) for i in range(len(CONSELHEIROS))]
    ordem = list(range(len(CONSELHEIROS)))
    random.shuffle(ordem)                                   # anônimo: a letra não revela o papel
    ops = {letras[j]: ops_lista[i] for j, i in enumerate(ordem)}
    legenda = {letras[j]: CONSELHEIROS[i][1] for j, i in enumerate(ordem)}
    print("Etapa 1 (opiniões) ok. Etapa 2: revisão anônima…")
    with ThreadPoolExecutor(len(CONSELHEIROS)) as ex:
        revs_lista = list(ex.map(lambda i: revisao(proposta, {k: v for k, v in ops.items() if legenda[k] != CONSELHEIROS[i][1]},
                                                   CONSELHEIROS[i]), range(len(CONSELHEIROS))))
    revs = {CONSELHEIROS[i][1]: revs_lista[i] for i in range(len(CONSELHEIROS))}
    print("Etapa 2 ok. Etapa 3: presidente…")
    final = presidente(proposta, ctx, ops, revs, legenda)
    rel = (f"# Conselho do canal — {datetime.now():%d/%m/%Y %H:%M}\n\n**Proposta do dono:** {proposta}\n\n"
           f"# DECISÃO DO PRESIDENTE\n\n{final}\n\n---\n# Opiniões (anônimas na revisão)\n\n"
           + "\n\n".join(f"## {k} — {legenda[k]}\n{v}" for k, v in ops.items())
           + "\n\n---\n# Revisões\n\n" + "\n\n".join(f"## {k}\n{v}" for k, v in revs.items()))
    arq = _salvar(proposta, rel)
    print(f"\n{final}\n\nRelatório completo: {arq.relative_to(RAIZ)}")
    return arq


def faxina() -> Path:
    ctx = _contexto()
    prompt = (BASE + "TAREFA: FAXINA DAS REGRAS. Leia todos os arquivos e liste TODAS as contradições ou duplicações entre eles "
              "(mesmo assunto com valores/instruções diferentes: volumes em dB, duração, número de efeitos, voz, música, "
              "legenda, ritmo, CTA…). Para cada uma: ASSUNTO · arquivo A → trecho · arquivo B → trecho · qual parece mais "
              "recente/vigente (datas do dono) · o que fazer. Ordene da que mais afeta o vídeo para a que menos afeta.\n\n" + ctx)
    with ThreadPoolExecutor(2) as ex:
        a, b = ex.map(lambda m: _perguntar(m, prompt, 0.1), [PRESIDENTE, "gemini-2.5-pro"])
    junta = _perguntar(PRESIDENTE, BASE + "Duas auditorias independentes listaram contradições nas regras do canal. Junte as duas "
                       "numa lista única, sem repetir, mantendo só o que aparece com trecho citado. Para cada item diga a "
                       "recomendação e se precisa de decisão do dono (SIM/NÃO).\n\n=== AUDITORIA 1 ===\n" + a +
                       "\n\n=== AUDITORIA 2 ===\n" + b, 0.1)
    arq = _salvar("faxina das regras", f"# Faxina das regras — {datetime.now():%d/%m/%Y %H:%M}\n\n{junta}\n\n---\n## Auditoria 1\n{a}\n\n## Auditoria 2\n{b}")
    print(f"{junta}\n\nRelatório: {arq.relative_to(RAIZ)}")
    return arq


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--faxina":
        faxina()
    elif len(sys.argv) > 1:
        conselho(" ".join(sys.argv[1:]))
    else:
        print(__doc__)
