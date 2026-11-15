---
name: brutos
description: Puxa os vídeos brutos que o usuário subiu na pasta "brutos" do Google Drive para o projeto do vídeo atual e analisa. Use quando o usuário digitar /brutos ou disser que subiu/enviou vídeos na pasta.
---

# /brutos

1. Descubra o projeto atual (o vídeo em produção: último em `dados/temas_feitos.md` sem link publicado,
   ou o que estamos editando na conversa, ex.: `vd003_galinha`).
2. Baixe só os arquivos novos:
   ```
   python3 -m viitu.brutos baixar <projeto>
   ```
   Se der erro de pasta não configurada, peça ao usuário o link da pasta e rode
   `python3 -m viitu.brutos configurar <link>`.
3. Para cada arquivo novo: `ffprobe` (duração, resolução, áudio) e uma prancha com
   `python3 -m viitu.visao clipe <arquivo>` (ou quadros com ffmpeg) para ver o conteúdo.
4. Responda curto: o que chegou, o que tem de bom (com segundos), o que ainda falta, e siga para a
   montagem das cenas.

Arquivos anexados direto no chat também valem: copie de `/root/.claude/uploads/...` para
`projetos/<projeto>/clipes/`.
