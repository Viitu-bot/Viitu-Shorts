# Protocolo de Mineração de Temas — Viitu Shorts

**Regra de ouro:** o Gemini **descobre** (canais, temas, links) e o `radar.py` **mede** (views reais).
O Gemini costuma inventar números e links. Nada entra na fila de produção sem ter passado pelo radar.

```
FASE A (uma vez, ~1 semana)        FASE B (toda semana, ~1h)
Escolher o SUBNICHO       ──►      Minerar TEMAS dentro do subnicho
Prompt 1 → radar → Prompt 2        Prompt 3 → radar → Prompt 4 → fila da semana
```

---

## FASE A — Escolher o subnicho

Canal de curiosidade "geral" compete com gigantes. Canal de **subnicho** (só frutas, só máquinas,
só Japão...) vira referência mais rápido, porque o algoritmo entende para quem mostrar e quem se
inscreve sabe o que vai receber.

### Nota do subnicho (0 a 2 em cada critério; escolha o de maior soma)

| Critério | 0 | 1 | 2 | Como medir |
|---|---|---|---|---|
| **Demanda provada** | nenhum canal de subnicho com >1M | alguns hits soltos | vários canais com `pct_1M` > 10% | `canais_*.csv` |
| **Canal jovem que explodiu** | não existe | 1 caso | 2+ canais com <1 ano e mediana >100k | Gemini + radar |
| **Concorrência em PT-BR** | 3+ canais BR fortes | 1–2 canais | ninguém faz bem em PT | Prompt 2 |
| **Oferta de vídeo bruto** | <30 temas possíveis | ~100 | 300+ (dá para postar 1/dia por um ano) | Reddit/TikTok/stock |
| **Encaixa na identidade** (Otto, adulto 25+, explicação) | não | mais ou menos | sim, a narração explica algo oculto | você |
| **Você aguenta 200 vídeos disso?** | não | talvez | sim | você |

> A **oferta de vídeo bruto** é o critério que mais derruba canais. Canal de frutas funciona porque
> nunca falta imagem de fruta. Antes de escolher, confira se há imagem para 300 vídeos.

### Subnichos candidatos (ponto de partida; teste 3 ou 4 com o radar)
- **Como é feito:** fábricas, linhas de produção, comida industrial
- **Por que é assim:** design oculto de objetos do dia a dia (tampinha, agulha, tomada)
- **Máquinas pesadas e obras gigantes:** escala absurda
- **Japão/China engenharia:** soluções urbanas, infraestrutura
- **Ofícios extremos:** profissões perigosas ou artesanais impressionantes
- **Física do cotidiano:** experimentos visuais com explicação

### PROMPT 1 — Descoberta de canais de subnicho (cole no Gemini)

```
Pesquise diretamente no YouTube (use a busca do YouTube, não a memória).

Quero encontrar canais de YouTube Shorts de CURIOSIDADES com SUBNICHO ESTREITO
(ex.: só frutas, só fábricas, só máquinas, só Japão, só objetos do dia a dia),
em inglês, espanhol ou português, que tenham Shorts com mais de 1 milhão de views.

Priorize canais JOVENS (criados há menos de 18 meses) ou com POUCOS vídeos
e MUITAS views, porque isso prova demanda com pouca concorrência.

Para cada canal, me dê uma tabela com:
| @handle | link do canal | subnicho em 3 palavras | idioma | 2 exemplos de títulos que viralizaram |

Regras:
- Só inclua canais que você abriu de verdade na busca. Se não tiver certeza
  de que o @handle existe, escreva [VERIFICAR].
- NÃO invente número de views ou inscritos (eu meço com uma ferramenta).
- Mínimo 25 canais, agrupados por subnicho.
- No final, liste os 5 subnichos que mais se repetiram.
```

**Depois:** cole os @handles em `radar/canais.txt` e rode:
```
python radar/radar.py canais radar/canais.txt
```
Abra `radar/saida/canais_DATA.csv`. As colunas que importam:
- `mediana_views`: o "piso" do subnicho
- `pct_1M`: com que frequência o subnicho estoura
- `tendencia`: >1 significa que o canal está em alta agora

### PROMPT 2 — Avaliar os subnichos com os números reais

```
Sou criador do canal Viitu Shorts (curiosidades em PT-BR, narração explicativa,
público adulto 25+, voz masculina calma e curiosa).

Abaixo está a planilha com números REAIS medidos dos canais que você encontrou:
[cole aqui o conteúdo de canais_DATA.csv]

Para os 5 subnichos mais fortes, avalie cada critério de 0 a 2:
1. Demanda provada (use pct_1M e mediana_views da planilha)
2. Existe canal jovem que explodiu?
3. Concorrência em PT-BR: pesquise no YouTube em português e diga quais canais
   brasileiros já fazem isso bem (com link)
4. Oferta de vídeo bruto: dá para achar imagem para 300 vídeos? Onde?
   (Reddit, TikTok, Pexels, canais oficiais de fábricas etc.)
5. Encaixa em narração explicativa ("o porquê oculto")?

Monte a tabela com a soma e recomende 1 subnicho principal + 1 secundário.
Dê 10 exemplos de temas de vídeo para o subnicho escolhido.
```

**Decisão:** escolha **1 subnicho principal** (70% dos vídeos) e **1 secundário** (30%).
Mantenha por **60 vídeos** antes de avaliar. Trocar antes disso zera o aprendizado do algoritmo.

---

## FASE B — Minerar temas toda semana (dentro do subnicho)

### Passo 1: Lista de vigia
Mantenha em `radar/canais.txt` de **20 a 40 canais** do seu subnicho, em qualquer idioma.
Toda segunda-feira, rode:
```
python radar/radar.py canais radar/canais.txt --min-mult 3
```
O arquivo `outliers_DATA.csv` traz os Shorts que fizeram **3× ou mais** a mediana do próprio canal.
Ali estão os **temas validados**: o tema puxou a audiência, não o tamanho do canal.

### Passo 2: Ampliar com busca (opcional)
Coloque termos do subnicho em `radar/buscas.txt` e rode:
```
python radar/radar.py buscar radar/buscas.txt
```
Os canais novos que aparecerem bem você adiciona à lista de vigia.

### PROMPT 3 — Filtrar os outliers e checar a concorrência em PT-BR

```
Abaixo estão Shorts de canais estrangeiros que fizeram 3x ou mais a média do
próprio canal (números reais medidos):
[cole as 30 primeiras linhas de outliers_DATA.csv]

Para cada um:
1. Qual é o TEMA em uma frase (o objeto + a pergunta oculta)?
2. Pesquise no YouTube EM PORTUGUÊS se já existe versão brasileira com muitas
   views. Responda: "não existe" / "existe fraca" / "existe forte (link)".
3. Dê nota de 0 a 2 em cada critério:
   - Objeto do dia a dia (todo mundo conhece)
   - Pergunta concreta (Por que / Como / O que acontece se)
   - A resposta NÃO aparece na imagem (só a narração revela)
   - Resposta surpreendente
   - Afeta a vida de quem assiste
   - Imagem forte para o frame 0
4. Some a nota (0 a 12).

Devolva a tabela ordenada pela nota, só com temas de nota >= 8 e que
"não existe" ou "existe fraca" em PT-BR.
Para os 7 melhores, sugira 3 títulos em PT-BR (4 a 8 palavras, 1 emoji no fim).
```

### PROMPT 4 — Raio-X de evidências e roteiro
Segue o seu Protocolo HISA normal ([OBSERVADO] / [CONFIRMADO] / [INCERTO]), com dois acréscimos:
- Use o vídeo estrangeiro original **só como prova de demanda e referência de informação.**
  A imagem vem de outra fonte (Reddit, stock, oficial), para não virar conteúdo reutilizado.
- Duração-alvo de 30 a 45 s (80 a 110 palavras), salvo quando houver imagem para mais.

---

## Rotina semanal (resumo)

| Quando | O quê | Tempo |
|---|---|---|
| Segunda | `radar.py canais` → Prompt 3 → escolher 7 temas | 45 min |
| Segunda | Para cada tema: achar o vídeo bruto (Reddit/TikTok/stock) | 30 min |
| Ter–Dom | Roteiro (Gemini) → pipeline → postar 1 por dia | — |
| Domingo | YouTube Studio: anotar views 48h, "visualizado vs. deslizado" e inscritos de cada vídeo da semana na planilha | 15 min |
| A cada 4 semanas | Ver quais **famílias de tema** ganharam e dobrar a aposta nelas | 30 min |

## Truques de busca manual no YouTube (para você ou o Gemini)
- Pesquise **em inglês** (onde está a demanda provada) e depois o mesmo tema **em português**
  (para ver se há concorrência).
- Na página do canal: aba **Shorts → Populares**. Os 10 primeiros mostram o que o público dele quer.
- Canal com **poucos vídeos e muitas views** = tema forte, concorrência baixa. É o sinal mais valioso.
- O mesmo tema viralizou em **3+ canais diferentes**? Então o tema é validado; não foi sorte.
