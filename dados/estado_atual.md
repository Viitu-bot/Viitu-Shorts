# Estado atual (atualizado em 18/11/2026) — leia primeiro numa sessão nova

## Vídeos
- vd005 Pássaros x aviões — POSTADO 17/11 12:00 (45 s). Concorrente: A vida é uma maravilha fez o mesmo tema em 19/10
  ("Por que não colocam tela no motor do avião?").
- vd006 Diferencial — AGENDADO 18/11 06:00 (v1).
- vd007 Starship pego pela torre (🔥 tema quente) — PRONTO, v3 em `remotion/out/vd007_starship.mp4` (20,6 s, Bastidor).
  Falta só `/publicar`: título "Por que a SpaceX pega o foguete no ar? 🚀", quinta 19/11 18:00.
  Créditos: vídeo SpaceX (x.com/SpaceX) + foto Ship 42 (SpaceX, CC BY 4.0, Commons).
- 48 h depois de cada vídeo: puxar retenção do Studio pelo vidIQ (`vidiq_channel_analytics`, report audience_retention).

## O que mudou no projeto em 17–18/11 (já aplicado)
- **vidIQ conectado** (plano grátis, 150 créditos/dia): `/tema` usa outliers gringos + tema quente (🔥).
- **X baixa direto** na nuvem (`yt-dlp <link do post>`).
- **Auditoria das análises** (Hall + reverso + A vida é uma maravilha a fundo, `pesquisa/canais/avidamaravilha_edicao.md`):
  - ~80% clipe real, 3D só em 1–2 inserções curtas (`/clipes`, `/animacao`).
  - Foley da AÇÃO em cada cena real (`sfx_cena`), hit automático nas palavras fortes (`_hits`), música SOBE no loop.
  - Fórmulas de gancho/estrutura no `/roteiro` (seção 2b); título "Por que [objeto] (não) tem…?" no `/publicar`.
  - Lacuna PT-BR com 3 frases diferentes no `/tema`.
- **3D:** iluminação HDRI (céu real Poly Haven) obrigatória; modelos prontos do **Sketchfab** (token salvo no ambiente,
  header `Authorization: Token`), Poly Haven, Quaternius. Já baixado: `assets/modelos/gaivota.glb` (CC BY, crédito em
  `assets/modelos/LICENCAS.txt`). Ainda falta o componente que carrega GLB no Remotion (fazer só quando um vídeo precisar).

## Pendências com o dono
- Drive: conector aceita só ~3 MB por envio — escolher (1) só textos ou (2) versões leves. Sem resposta.
- Base do algoritmo do YouTube Shorts (pesquisa + checklist) — combinada, ainda não feita.
- Testar Blender (apt) para inserções 3D de alta qualidade — só quando o dono pedir.
