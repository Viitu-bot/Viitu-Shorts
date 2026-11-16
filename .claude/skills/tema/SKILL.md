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

2. **Chave:** se `python3 -m viitu.tema ...` der erro de chave/permissão, peça ao usuário
   para mandar a chave da YouTube Data API e salve em `.env` como `YOUTUBE_API_KEY=...`
   (o `.env` está no .gitignore; nunca faça commit dele).

3. **Candidatos:**
   ```
   python3 -m viitu.tema candidatos <dia>
   ```
   Se quiser, acrescente buscas com `--extra "termo"` (em inglês/espanhol) para variar.

3b. **Pesos de categoria/gatilho já estão na pontuação** (ver "LÓGICA DE ESCOLHA DE TEMA" no CLAUDE.md).
   Priorize: motivo oculto de objeto, recorde/"mais caro", perigo/erro, mito desmentido.
   Evite como tema principal: animal estranho sem "porquê", comida, corpo/saúde, truque, "olha isso".

4. **Agrupe por TEMA**, não por vídeo: o mesmo tema em vários canais = demanda comprovada (bom sinal).
   Descarte:
   - temas em `dados/temas_feitos.md`;
   - datas comemorativas de outros países (ex.: Diwali), temas sem "porquê" a explicar,
     conteúdo que dependa de idioma falado.

5. **Nota 0–12** (critérios em `CLAUDE.md`). Fique com os ~6 melhores com nota ≥ 9.

6. **Lacuna PT-BR** para cada um dos ~6:
   ```
   python3 -m viitu.tema lacuna "<tema em português, como um brasileiro buscaria>"
   ```
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
