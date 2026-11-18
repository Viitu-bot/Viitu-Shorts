# Reclamações recorrentes do dono → causa → regra → trava automática
Levantamento de 18/11/2026 sobre TODO o histórico (205 mensagens). Antes de montar qualquer vídeo, ler este arquivo.
A trava `python3 -m viitu.montagem <p>` (o `editar` roda sozinho) barra o que dá para medir; o resto está na lista de
conferência no fim.

| # | Padrão (vezes) | Exemplos do dono | Causa raiz encontrada | Regra nova | Trava |
|---|---|---|---|---|---|
| 1 | **Clipe repetido** (6x: vd003, galinha, avião, rodas, vd009) | "repetiu várias vezes o mesmo clipe" · "parece copiar e colar" · "só clipe repetido" | o revisor deixava bruto longo voltar quantas vezes quisesse (vd009: 7 cenas do mesmo avião); faltava fonte e a montagem "tapava buraco" com o mesmo arquivo | cada arquivo ≤ 2 cenas (curto ou longo); fontes diferentes ≥ 60% das cenas reais; faltou fonte → buscar mais (abaixo), nunca repetir | R1 |
| 2 | **Clipe fraco / genérico / baixa qualidade** (7x) | "clipes genéricos" · "mal enquadrado" · "não dá para identificar o estrago" · "logo do TikTok me incomoda" · "ridículo" | escolha pelo que tinha, não pelo melhor; arquivo 480p; não identificável em 1 s | clipe real ≥ 720p, nítido, com movimento, sujeito identificável em 1 s; < 720p nunca no gancho | R4 + triagem |
| 3 | **3D fora da função** (4x) | "3D cortado pelas imagens reais no meio da explicação" · "3D básico" · "avião de ré", "mato verde onde o fogo passou" | a skill /animacao mandava ALTERNAR "real → 3D → real → 3D"; a skill /clipes limitava o 3D a 4 s somados, então a explicação saía picotada e curta | o 3D é A explicação: **um bloco contínuo** do começo ao fim do mecanismo (4 s a 45% do vídeo), nenhum clipe real no meio; real antes (gancho) e depois (prova/virada) | R2 |
| 4 | **Foto parada** (3x) | "não usar tantas imagens estáticas" · "imagem estática de início" | fonte falhou e entrou foto | gancho = vídeo real; ≤ 2 fotos, nunca seguidas | R3, R5 |
| 5 | **Cena não casa com a frase** (5x) | "repara na roda... na curva" (sujeito trocou no meio) · "decolagem tem que sair do chão" · "mostra só o cervo saindo" | clipe escolhido pelo objeto, não pela AÇÃO e emoção da palavra | 1 conceito do roteiro = 1 bloco de cena; a ação acontece NA palavra; gancho = 1 sujeito só | conferência (prancha) |
| 6 | **Roteiro corrido / explicação confusa** (3x) | "nem entendi a explicação e já acabou" · "gancho mais fraco" | muita informação em pouca palavra; explicação sem tempo de tela | ouro parcelado: 1 ideia por frase; explicação cabe no bloco 3D; ler em voz alta antes | /roteiro |
| 7 | **CTA engessado** (2x) | "CTA repetitivo, engessado" | fórmula fixa em todo vídeo | sem CTA por padrão; quando houver, elogio contextual (Martim-pescador) e nunca igual ao anterior | /roteiro |
| 8 | **Som que atrapalha a voz / sem imersão** (5x) | "efeito por cima da voz não pode" · "efeito de errado no meio da frase" · "3D sem sound design" · "sem música" | camadas sem hierarquia | sidechain universal + som de função só com gráfico e na pausa + 3D com foley próprio | `viitu.mixagem` |
| 8b | **Sound design não seguiu o protocolo** (vd009 v3, 18/11) | "parece que só fez a escolha de clipes e roteiro e colocou um em cima do outro" | o editor tinha `animacao.sfx` e `sfx_cena`, mas nada obrigava a usar: o 3D saiu mudo e 0/12 cenas tinham som de ação | trava R8: 3D com sfx em CADA evento + entrada; gancho e ≥ 60% das cenas reais com som de ação (`sfx_cena` com `busca` na Sonniss); virada e música definidas | R8 |
| 5b | **Cena genérica onde cabia gente/peso** (vd009) | "quando fala que vira um escritório, poderia mostrar o presidente" | cena escolhida pelo objeto (avião), não pelo PERSONAGEM da frase | frase com pessoa/papel (presidente, piloto, operário) → mostrar a pessoa de verdade; contas oficiais (Casa Branca, Forças Armadas) | conferência |
| 8c | **Efeitos inaudíveis, trilha errada** (vd009 final, 18/11) | "parece que não foi editado, só clipes e narração" · "e a pesquisa dos áudios de fundo?" | a proteção da voz baixava TUDO 10 dB sob a voz (Otto quase não pausa → efeitos sempre enterrados); trilha genérica em vez da pesquisada; nenhuma trava ESCUTAVA o resultado | 2 grupos de mixagem (leito −10 / efeitos −3); trilha pela tabela de categorias da pesquisa; OUVIDO do Gemini com nota ≥ 8 na trava de entrega | ouvido |
| 8d | **Trilha "sem ducking", bombeando** (vd009, ouvido 6–7/10) | Gemini: "falta ducking, música linear" | a proteção da voz media quadro a quadro: no fim de cada palavra a voz cai e a trilha AFUNDAVA nas pausas (0,19) — o contrário do certo | referência = nível médio da fala; duck suavizado (13 quadros); a trilha sobe nas pausas e cresce na virada | ouvido + `viitu.mixagem` |
| 9 | **Entregue sem revisar** (3x) | "parece que não foi revisado antes de ser enviado" | revisão sem critério de bloqueio | trava R1–R7 antes do render + revisar + auditoria + prancha OLHADA | montagem + revisar |
| 10 | **Análises não aplicadas** (2x) | "você não aplicou o que seria válido?" | conhecimento ficava no Hall sem virar regra | toda análise termina com a regra escrita no arquivo do mapa (CLAUDE.md) | /analisar |

## Estrutura de montagem padrão (Bastidor 20–28 s) — o que a trava espera
```
GANCHO real (1 sujeito, 2–3 cenas de fontes diferentes, ação na palavra)
→ CONTEXTO real (1–2 cenas, fonte nova)
→ EXPLICAÇÃO em 3D: UM bloco contínuo (6–10 s), câmera que acompanha o mecanismo, eventos nas palavras
→ PROVA/VIRADA real (1–2 cenas, fonte nova: a coisa real acontecendo)
→ LOOP = mesmo quadro do gancho
```
Tiro Curto 12–15 s: igual, com o bloco 3D de 3–5 s (ou sem 3D se o clipe real explicar sozinho).

## De onde tirar clipe sem repetir (ordem; desde 18/11 o vidIQ só renova no mês seguinte)
1. **Busca web direcionada** (Claude, `WebSearch` com `allowed_domains: ["tiktok.com", "x.com", "instagram.com"]`,
   termo da AÇÃO em inglês) → `yt-dlp <link>` baixa direto. Contas oficiais (militares dos EUA, NASA, SpaceX,
   fabricantes) = melhor fonte. Ex.: CENTCOM no X tem reabastecimento oficial.
2. Pixabay / Pexels (API) — stock limpo.
3. Internet Archive (NARA = domínio público, mas costuma ser 480p: só como prova, nunca gancho).
4. vidIQ TikTok/IG (quando houver crédito).
5. Dono manda link — último recurso.
- Bilibili: a busca funciona (`yt-dlp "bilisearch8:<termo em chinês>"`), mas o download é bloqueado na nuvem.
- DVIDS (vídeo militar oficial em HD): precisa de chave grátis do dono (`api.dvidshub.net`).
- **Meta por vídeo:** ≥ 7 fontes reais diferentes antes de abrir o editor. Menos que isso → continuar buscando.

## Conferência que a máquina não faz (olhar a prancha 1 quadro/s)
- [ ] Em 1 s dá para entender o que é cada cena? (o "estrago" aparece, o sujeito é óbvio)
- [ ] A ação cai na palavra? (decola em "decola", encaixa em "encaixa")
- [ ] A cena faz SENTIR (perigo, escala, alívio), não só ilustra?
- [ ] O 3D tem física certa (direção do nariz, estado que não volta) e som próprio?
- [ ] Nada de logo/marca d'água/tela de app; legenda não cobre o sujeito.
- [ ] Clipe horizontal recortado: a PESSOA/sujeito está dentro do recorte? (vd009: o recorte pegou o selo e deixou o
      presidente de fora — todas as travas passaram; só a prancha pegou). Use `"foco": [x, 0.5]` + `"seguir": false`.
