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
- 4–8 palavras, 1 emoji no fim, sem CAIXA ALTA gritando. Só em português (dublagem automática está ativa).

## 2. Descrição
1–2 frases com o gancho + `creditos_descricao` do cenas.json (todos os @ de terceiros e Pixabay) + fonte dos fatos.

## 3. Horário
Padrão **06:00** (histórico do dono). Teste em curso: alternar 06:00 e 18:00 por 2 semanas e comparar views em 48 h.
Referência: A vida é uma maravilha posta 12h/18h; GeneralTV 17h–20h (19h com maior mediana); KSO 11h.

## 4. Antes de liberar
- `python3 -m viitu.direitos <p>` sem ❌.
- Clipe de terceiro sem permissão: mandar ao dono o texto de DM (`pesquisa/permissao_clipes.md`) com os @;
  quando autorizarem, registrar em `"permissoes"` no cenas.json.
- Comentário fixado opcional (curiosidade extra que puxa resposta).

## 5. Registrar
Adicionar em `dados/temas_feitos.md` (tema, projeto, data/horário), commit e push.
Mensagem ao dono: título, descrição pronta para copiar, horário — numerado e curto.
