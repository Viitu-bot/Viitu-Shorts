# Viitu Shorts — automação

Pipeline de produção do canal @viitushorts (curiosidades em PT-BR), operado pelo Claude Code na nuvem.
As regras e o mapa do projeto estão em `CLAUDE.md`; cada etapa é uma skill em `.claude/skills/`
(`/tema`, `/roteiro`, `/clipes`, `/brutos`, `/animacao`, `/editar`, `/publicar`, `/analisar`).

| Pasta | O que é |
|---|---|
| `viitu/` | código Python (temas, voz, editor, som, revisão, direitos, auditoria) |
| `remotion/src/` | acabamento do vídeo e animações 3D |
| `edicao/` | especificação fixa, lógica do editor, manual de técnicas, biblioteca de sons |
| `hall_da_fama/`, `pesquisa/` | referências analisadas e engenharia reversa dos canais |
| `projetos/vdNNN_*` | roteiro, cenas e créditos de cada vídeo (clipes e renders não vão para o git) |
| `assets/` | sons, trilhas, fontes e catálogos (caches baixados ficam fora do git) |
