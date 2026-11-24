---
description: Garimpa a concorrência (canais ou palavras-chave), acha os vídeos que estouraram e descobre padrões adaptáveis ao DNA do Viitu
argument-hint: <@canais ou links> e/ou --buscar "palavras em pt/en"
---
Rode a coleta com o que o dono passou: `python3 -m viitu.espiar $ARGUMENTS`
(sem canais, use `--buscar` com 2–3 termos em pt e en do nicho). Ela salva `analises_concorrencia/<data>_<alvo>/dados.json`.

Depois, VOCÊ descobre os padrões — sem modelo pronto — lendo títulos, durações, transcrições e comentários reais dos outliers:
1. Gancho (as primeiras palavras e o que elas prometem), estrutura do roteiro, ritmo (palavras/s pela transcrição e duração),
   finalização (como termina: loop, revelação, CTA?), gatilhos de engajamento (o que os comentários com mais likes repetem).
2. Sem transcrição (YouTube bloqueia na nuvem): buscar o mesmo vídeo no TikTok do canal (`yt-dlp`) e transcrever com
   ElevenLabs, ou `vidiq_video_transcript` se houver crédito. Cortes/sons: `rea-video` + `viitu.ouvir_video` no arquivo.
3. Escreva `analises_concorrencia/<pasta>/padroes.md`: o que funciona (com o exemplo e o número real de cada padrão),
   o que dá para adaptar SEM ferir o "DNA e Identidade do Canal" (CLAUDE.md) e o que NÃO serve para o Viitu (e por quê).
4. Atualize as faixas 20% e 10% de `edicao/matriz_702010.md` com o que foi descoberto (com a origem e o número).
5. Todo vídeo citado ao dono passa por `python3 -m viitu.provar <link> --papel referencia`. Resposta curta, para celular.
