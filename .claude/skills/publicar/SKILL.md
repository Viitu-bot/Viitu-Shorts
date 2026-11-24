---
name: publicar
description: Prepara a publicação do Short pronto — título, descrição com créditos, horário, comentário fixado e pedidos de permissão — e registra o vídeo como feito. Use quando o vídeo for aprovado pelo dono, quando ele pedir título/descrição/horário, ou digitar /publicar.
---

# /publicar

O dono agenda no app do YouTube Studio (upload pela API trava em privado sem auditoria).

## 1. Título
- Repete a LACUNA do gancho e não pressupõe conhecimento ("O olho da cabra faz algo que o seu não faz", não
  "Por que o olho da cabra gira?").
- Fórmulas validadas nos canais BR: "A/O [coisa] que [faz algo incrível]" e "Esse [coisa] [faz algo absurdo]!?".
- 3ª fórmula (A vida é uma maravilha: "Por que não colocam tela no motor do avião?" 2,6 mi; "Por que tampa tem anel
  que arrebenta" 2,4 mi): **"Por que [objeto que TODO MUNDO conhece] (não) tem [detalhe/solução óbvia]?"** — é a pergunta
  que o próprio espectador faria. Vale quando o objeto é conhecido; título vago ("O inimigo do avião...") é o pior caso.
- 4–8 palavras, 1 emoji no fim, sem CAIXA ALTA gritando. Só em português (dublagem automática está ativa).

## 1b. Música famosa (cenas.json com "musica": "app:<faixa>")
Passo extra para o dono no envio: **Adicionar som** → buscar a faixa → volume da faixa em ~10–15% e o som original em 100%.
(Nunca embutir música com direitos no arquivo. Faixas livres com crédito, como Kevin MacLeod, vão com o crédito na descrição.)

## 2. Descrição
1–2 frases com o gancho + `creditos_descricao` do cenas.json (todos os @ de terceiros e Pixabay) + fonte dos fatos.

## 3. Horário
Padrão **06:00** (histórico do dono). Teste em curso: alternar 06:00 e 18:00 por 2 semanas e comparar views em 48 h.
Referência: A vida é uma maravilha posta 12h/18h; GeneralTV 17h–20h (19h com maior mediana); KSO 11h.

## 4. Antes de liberar
- `python3 -m viitu.direitos <p>` sem ❌.
- Clipe de terceiro sem permissão: mandar ao dono o texto de DM (`pesquisa/permissao_clipes.md`) com os @;
  quando autorizarem, registrar em `"permissoes"` no cenas.json.
- **Comentário fixado (formato Viitu, sempre):** conferido em 18/11 que A vida é uma maravilha e KSO NÃO fixam comentário
  (0 comentários do dono em 200 recentes) — não existe formato externo validado; este é o nosso, medir no Studio
  (comentários/1000 views) e ajustar. Nos canais deles, os comentários com mais likes são opinião/hipótese engraçada e
  "vontade de…", nunca respostas de múltipla escolha.
  1. **1ª linha = a pergunta que o vídeo deixou no ar** (ex.: "E a nossa pupila, que é redonda?").
  2. **Resposta com fato NOVO** (não está no vídeo), 2–3 linhas, linguagem falada, com fonte conferida: explicação
     técnica, caso brasileiro famoso ou número surpreendente.
  3. **CTA de conversa** (opinião ou história da pessoa, ou pedido do próximo tema): "Você teria coragem…?",
     "Conta aí se…", "Qual bicho você quer que eu explique depois?". NUNCA A/B/C.
  - Para não parecer IA: sem títulos ("Curiosidade extra:"), sem listas, sem travessão longo, no máx. 1–2 emojis,
    sem hashtags, frases curtas como o dono escreveria no celular.

## 5. Registrar
Adicionar em `dados/temas_feitos.md` (tema, projeto, data/horário), commit e push.
Mensagem ao dono: título, descrição pronta para copiar, horário — numerado e curto.

## 6. KIT DE PUBLICAÇÃO (obrigatório, dono 24/11)
Salvar `projetos/<p>/kit_publicacao.txt` E mostrar no chat, nesta ordem:
1. TÍTULO E DESCRIÇÃO CURTA — alinhados ao gancho dos 2 primeiros segundos (+ créditos e fontes).
2. COMENTÁRIO FIXADO — 1 frase curta e provocativa ou pergunta simples, para debate rápido enquanto o Short roda em loop.
3. POST DE TRIVIA (aba Comunidade) — enquete de quiz: pergunta curiosa ligada ao tema + 4 opções, marcando a correta
   (fato conferido, com fonte no arquivo).
