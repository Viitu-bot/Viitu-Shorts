---
name: tema
description: Pesquisa e recomenda 3 temas de vídeo para o Viitu Shorts com números reais da YouTube Data API, para o dia da semana pedido. Use quando o usuário digitar /tema, pedir "tema de hoje", "tema para sexta" etc.
---

# /tema <dia>

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

3a. **vidIQ (preferência do dono, sempre):**
   - **Base = gringo validado sem versão no Brasil:** `vidiq_outliers` com `contentType: short`,
     `language: en` (e às vezes `es`), keyword da família do dia, `minViews: 1000000`. Breakout ≥ 3x = prova forte.
   - **Tema quente (hype):** `vidiq_trending_videos` e `vidiq_keyword_research` `mode: rising` `period: week`
     (niche "curiosidades"/"engineering"). Se um assunto do momento encaixar no canal (tem "porquê" para
     explicar), ele entra como uma das 3 opções, marcado 🔥, mesmo sem a validação de 2 anos — hype não espera.
   - Cada chamada gasta 5 créditos (150/dia grátis). Views do vidIQ são pista; o número mostrado ao dono
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
