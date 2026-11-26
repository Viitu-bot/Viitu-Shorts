---
name: tema
description: Pesquisa e recomenda 3 temas de vídeo para o Viitu Shorts com números reais da YouTube Data API, para o dia da semana pedido. Use quando o usuário digitar /tema, pedir "tema de hoje", "tema para sexta" etc.
---

# /tema <dia>

> **NICHO DE ESTILO (dono 26/11, BÍBLIA §0c):** os 3 temas vêm das categorias fixas (flagrante do cotidiano · habilidade/
> trabalho extremo · história curta de pessoa/personalidade · invenção visual chocante), não da "família do dia" do
> calendário (que vira só sugestão). Cada tema diz se cabe em **12–18 s** e passa na **regra dos 75%+** (1ª cena + 1ª fala
> seguram sozinhas). Precisa de explicação prévia longa → guardar.
> **MÉTODO DO DONO 26/11 (vale sobre o resto):** lacuna PT-BR NÃO é obrigatória — tema que já existe em PT entra com
> ângulo/ritmo diferente. Prova = Short gringo de 30–90 dias com views desproporcionais aos inscritos. Todo tema passa nos
> 3 pilares (curiosidade imediata na 1ª frase · impacto visual sem áudio no 1º quadro · assunto universal) e é marcado
> com o estilo: urbano/cotidiano (perigo oculto) · invenção visual chocante · história intensa de bastidores. Fontes
> extras: comunidades de curiosidades/notícias incomuns (histórias estouram lá antes de virar vídeo).

> **Regras do dono:** `edicao/BIBLIA.md` (manda em tudo; não alterar sem autorização) · planta técnica: `edicao/formato.md`.
> **Formato do dia:** cada tema recomendado vem com o FORMATO (`edicao/formatos.md`: processo, motivo_oculto, por_dentro, erro_perigo, invencao, recorde_historia, tiro_curto). Siga o rodízio de `formatos.json` (nunca o mesmo formato 2 dias seguidos; processo de bruto cronológico tem prioridade).

> Tema bom também precisa de IMAGEM: antes de recomendar, confira que existem ≥ 7 fontes reais prováveis
> (busca web TikTok/X/Instagram, contas oficiais) e que o fato ainda vale hoje. Ver `edicao/reclamacoes.md`.

Objetivo: entregar **3 temas** verificados com números reais, curtos de ler no celular.
O usuário escolhe um e seguimos para `/clipes` e `/roteiro`.

## Passos

1. **Dia:** use o dia que o usuário disse (o dia em que o vídeo será POSTADO). Sem dia, use amanhã.
   Leia `calendario.json` para saber a família do dia.

2. **Chave:** se `python3 -m viitu.tema ...` der erro de chave/permissão, NÃO peça a chave no chat:
   diga ao dono para colocá-la nos secrets do ambiente (ou no `.env`, fora do git) e pare aqui.

3. **Candidatos:**
   ```
   python3 -m viitu.tema candidatos <dia>
   ```
   Se quiser, acrescente buscas com `--extra "termo"` (em inglês/espanhol) para variar.

0a. **Classificação sem Gemini (padrão desde 18/11):** `python3 -m viitu.radar` coleta (cota de busca, guardada em
   cache do dia) e sai com código 2 pedindo classificação. O Claude lê `dados/pesquisas/<hoje>_candidatos.json`,
   classifica cada título com os campos da instrução (categoria, gatilho, tema_pt, buscas_pt, porque, cara_do_canal,
   descartar), grava `dados/pesquisas/<hoje>_classificacao.json` como `{"itens": [...]}` e roda o radar de novo
   (não gasta cota de busca). Gemini só com `--gemini`.
0. **RADAR (pesquisa conjunta, sempre primeiro):** antes, salve os IDs dos outliers/trending do vidIQ em
   `dados/pesquisas/<hoje>_vidiq.json` (lista de IDs). Depois `python3 -m viitu.radar --top 6`: junta Shorts do nicho
   dos últimos 10 dias (views/hora) + 90 dias (validação) + vidIQ + Google Trends, classifica e dá nota 0–100
   (frescor 25 · força 25 · categoria 20 · lacuna PT com 3 buscas 20 · cara do canal 10). Gasta ~5 mil da cota da API
   (10 mil/dia): rode o radar ANTES de outras buscas. Os passos abaixo só refinam os 3 melhores do radar.

   **Cota da API do YouTube acabou? O projeto NÃO para** — radar pelo vidIQ (cota própria): `vidiq_trending_videos`
   (sortBy recentVphEngaged, últimos 10 dias) + `vidiq_outliers` (publishedWithin thisMonth, sort vph) + lacuna com
   `vidiq_youtube_search` (regionCode BR, 2 frases) + `vidiq_instagram_tiktok_outlier_search` (tema em 2+ plataformas =
   hype confirmado). Views continuam pelo `viitu.provar` (videos.list não gasta a cota de busca).

3. **O que está quente AGORA (primeiro passo, sempre — dono: "vídeo que até minha avó já viu não serve"):**
   `python3 -m viitu.quente` → Shorts do nicho publicados nos últimos 7 dias ordenados por views/hora (API do YouTube,
   EN e PT) + Google Trends em alta no BR/EUA. Depois de ter os 3 candidatos: `python3 -m viitu.tendencias "<tema 1>" "<tema 2>"
   "<tema 3>"` (interesse de busca no YouTube BR, 0–100, mesma escala) — desempate, não prova. Tema fresco com porquê forte entra como 🔥 (vale mais que o validado antigo).

3a. **vidIQ (preferência do dono, sempre):**
   - **Base = gringo validado sem versão no Brasil:** `vidiq_outliers` com `contentType: short`,
     `language: en` (e às vezes `es`), keyword da família do dia, `minViews: 1000000`. Breakout ≥ 3x = prova forte.
   - **Tema quente (hype):** `vidiq_trending_videos` e `vidiq_keyword_research` `mode: rising` `period: week`
     (niche "curiosidades"/"engineering"). Se um assunto do momento encaixar no canal (tem "porquê" para
     explicar), ele entra como uma das 3 opções, marcado 🔥, mesmo sem a validação de 2 anos — hype não espera.
   - Cada chamada gasta 5 créditos (150 POR MÊS, renova dia 17: ~20 por semana para tema). Views do vidIQ são pista; o número mostrado ao dono
     sai do `viitu.provar`.

3b. **Pesos de categoria/gatilho já estão na pontuação** (ver "Lógica de escolha" abaixo).
   Priorize: motivo oculto de objeto, recorde/"mais caro", perigo/erro, mito desmentido.
   Evite como tema principal: animal estranho sem "porquê", comida, corpo/saúde, truque, "olha isso".

4. **Agrupe por TEMA**, não por vídeo: o mesmo tema em vários canais = demanda comprovada (bom sinal).
   Descarte:
   - temas em `dados/temas_feitos.md`;
   - datas comemorativas de outros países (ex.: Diwali), temas sem "porquê" a explicar,
     conteúdo que dependa de idioma falado.

5. **Nota 0–12** (critérios abaixo). Fique com os ~6 melhores com nota ≥ 9.

6. **Lacuna PT-BR** para cada um dos ~6:
   ```
   python3 -m viitu.tema lacuna "<tema em português, como um brasileiro buscaria>"
   ```
   **Rode 3 frases diferentes** (o assunto, o objeto + "por que não", o ângulo da pergunta). No vd005 ("pássaro x avião")
   a lacuna deu vazia, mas a A vida é uma maravilha tinha 2,6 mi com "Por que não colocam tela no motor do avião?".
   ATENÇÃO: o veredito do script olha só views. **Leia os títulos em PT** e julgue se são
   o MESMO tema e o MESMO ângulo. Vídeo PT de assunto diferente não conta como concorrência.

7. **Escolha 3**: maior nota + lacuna real + demanda em 2+ canais. Prefira variedade entre os 3.

8. **Responda neste formato** (curto, para celular), sem tabelas largas:

```
📅 <Dia> — <Família>

1️⃣ <TEMA EM UMA FRASE> — nota X/12
• Prova: <views> em <canal> (<N>x a média do canal) — <link>
• Outros canais com o tema: <N> (até <maior views>)
• Em PT-BR: não existe / fraco / forte (<motivo em 5 palavras>)
• Ângulo Viitu: <a pergunta oculta que a narração responde>
• Título: <sugestão, 4–8 palavras, 1 emoji>

2️⃣ ...
3️⃣ ...

👉 Qual você quer? (responde 1, 2 ou 3)
```

9. Registre a pesquisa: os JSON ficam em `dados/pesquisas/` (já salvos pelo script).
   Quando o usuário escolher, adicione o tema em `dados/temas_feitos.md` com a data prevista de postagem,
   faça commit e push.

## Regras
- Antes de mostrar qualquer vídeo ao dono: `python3 -m viitu.provar <link> --papel validacao|bruto` e copiar a linha (rótulo + views conferidas + link).
- **Nunca invente números.** Todo número vem da saída do script.
- Cota: cada `candidatos` gasta ~600 unidades, cada `lacuna` ~100. Limite diário grátis: 10.000.
- O vídeo estrangeiro é **prova de demanda e fonte de informação**; a imagem do nosso vídeo
  vem de outra fonte (ver `/clipes`).


## Lógica de escolha (625 vídeos de 3 canais BR — `hall_da_fama/logica_temas.md`)
1. Fonte = temas evergreen que já viralizaram lá fora (em média 1,5 a 2 anos antes). Pré-validação é
   obrigatória, mas não separa sucesso de fracasso.
2. O que separa é CATEGORIA + GATILHO (mediana de views):
   🥇 motivo oculto de objeto/design (A vida 2,5M · GeneralTV 930k · KSO 2,7M) · 🥈 recorde/escala/"mais caro"
   (2,0M · 1,9M) · 🥉 perigo/erro/segurança (1,4M · 979k). Gatilhos fortes: dinheiro/escala, mito desmentido,
   motivo oculto, perigo/medo, processo revelado. Fracos: animal estranho, comida, corpo/saúde, truque,
   lugar/cultura, "olha isso" sem explicação; título com pergunta direta ("Você conseguiria…?") ou vago.
3. `viitu/tema.py` aplica PESO_CATEGORIA e PESO_GATILHO, busca temas de até 2 anos com ≥ 2M views.
4. Bônus: tema cujo mecanismo dá uma boa ANIMAÇÃO 3D (o canal explica o "porquê" desenhado).

## Nota 0–12 (0 a 2 por critério; produzir só com ≥ 9)
Objeto do dia a dia · pergunta concreta (Por que / Como / O que acontece se) · resposta não aparece na imagem ·
resposta surpreendente · afeta a vida de quem assiste · imagem forte para o frame 0.
Validação: Short em outro idioma com views ≥ 3× a mediana do próprio canal e sem versão forte em PT-BR.

## Tema que já existe em PT-BR: outro ÂNGULO
Se a lacuna mostrar vídeos em português do mesmo tema (mesmo fracos):
`python3 -m viitu.tema angulo "<tema>" "<busca em PT>"` e escolha um ângulo que nenhum usou (outro porquê,
consequência, conexão com o Brasil, mito desmentido, número surpreendente).
