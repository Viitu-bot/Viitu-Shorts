# Viitu Shorts — automação

Pipeline de produção do canal @viitushorts (curiosidades em PT-BR), operado pelo Claude Code na nuvem.
As regras e o mapa do projeto estão em `CLAUDE.md`; cada etapa é uma skill em `.claude/skills/`
(`/tema`, `/roteiro`, `/clipes`, `/brutos`, `/animacao`, `/editar`, `/publicar`, `/analisar`).

| Pasta | O que é |
|---|---|
| `viitu/` | código Python (temas, voz, editor, som, revisão, direitos, auditoria) |
| `remotion/src/` | acabamento do vídeo e animações 3D |
| `edicao/` | `REGRAS.md` (manual único) + `inventario.json` (números, formatos, mídia) + bibliotecas de roteiro |
| `hall_da_fama/`, `analises_concorrencia/` | referências analisadas (saída do /analisar e /espiar) |
| `arquivo/` | histórico aposentado em 24/11 (regras antigas, pesquisa antiga, pranchas vd002–vd016) — fora do contexto |
| `projetos/vdNNN_*` | roteiro, cenas e créditos de cada vídeo (clipes e renders não vão para o git) |
| `assets/` | sons, trilhas, fontes e catálogos (caches baixados ficam fora do git) |
