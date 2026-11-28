---
name: conselho
description: Conselho do canal (igual ao LLM Council do Karpathy, adaptado ao projeto) — 4 conselheiros de IA leem as regras e os dados do canal, opinam, se revisam anonimamente e um presidente decide com base. Use SEMPRE que o dono propuser uma regra nova, mudança de processo, ideia de edição/som/roteiro, ou digitar /conselho; e com "--faxina" para achar contradições entre as regras.
---

# /conselho: decisão embasada antes de mudar qualquer regra (dono 28/11)

Por quê (dono): "muitas das coisas são ideias minhas… faço sem muito embasamento, porque eu sou leigo… gostaria que essa
parte do conselho fosse embasada para crescer o canal". E as regras acumulavam contradições (whoosh −3 × −14 etc.).

## Quando usar
- O dono pede algo que muda o JEITO de fazer (regra, volume, duração, voz, música, estrutura, processo) → ANTES de gravar
  em qualquer arquivo, rodar o conselho com a proposta nas palavras do dono.
- `/conselho --faxina` → lista as contradições que já existem; resolver uma a uma com o dono.
- Pedido pontual do vídeo do dia (trocar um clipe, corrigir um corte) NÃO precisa de conselho.

## Como rodar
`python3 -m viitu.conselho "<proposta do dono>"` (≈ 1–3 min) → relatório em `dados/conselho/`.
Etapas: 1) 4 opiniões independentes (Analista de Retenção, Guardião do DNA, Caçador de Contradições, Estrategista de
Crescimento — modelos diferentes) · 2) revisão ANÔNIMA com ranking · 3) Presidente: veredito, contradições, base, como gravar.

## Depois do conselho (o Claude é quem fala com o dono)
0. **Conferir cada item no CÓDIGO e nos arquivos antes de aplicar** — o conselho erra (faxina de 28/11: mandou tirar a
   legenda de baixo, que o editor usa para não cobrir o sujeito, e tratou o `max_cena`, que muda a divisão das cenas, como
   simples texto). Só aplica sem perguntar o que é texto velho que não muda comportamento.
1. Mostrar ao dono, em linguagem simples: veredito, o que contradiz (com o arquivo), o que tem base e o que é "sem base".
2. Se houver escolha real → AskUserQuestion com as opções (recomendada primeiro).
3. Gravar a decisão num lugar só e APAGAR a versão antiga em todos os arquivos citados (não deixar duas regras).
4. A BÍBLIA só muda com o "sim" do dono no chat (regra 4 do CLAUDE.md).
5. Terminar com o próximo comando.

Limites: o conselho usa o Gemini (chave já configurada, sem custo extra). Ele não vê vídeos do canal nem o YouTube Studio;
número novo só entra com base em `edicao/fontes_das_regras.md` ou print do dono.
