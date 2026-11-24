# Viitu Shorts — instruções para o Claude

Canal de Shorts de curiosidades em PT-BR (@viitushorts). O dono opera **pelo celular**. Fale em **português do Brasil**,
simples e direto, um passo por vez, sem termos técnicos.

## Os 3 arquivos que mandam (nada fora deles vale como regra)
1. **`edicao/REGRAS.md`** — manual único: DNA do canal, retenção (padrão-ouro vd004, 35–45 s), imagem sem take parado,
   som em camadas (transição em toda troca, efeito na palavra, ambiente contínuo), travas e conferência.
2. **`edicao/inventario.json`** — todo número (volumes, zoom, ritmo), formatos e mídia aprovada. O código lê daqui.
3. **Código:** `viitu/editar.py` (imagem + plano) · `viitu/som_final.py` (som final) · `remotion/src/Short.tsx`
   (legenda, seta, flash, 3D). Unificação do som em um motor só: pendente (ver REGRAS §4).
Mudar regra ou número = só com autorização do dono no chat. `arquivo/` é histórico: não ler como regra.

## Regras que nunca quebram
1. Números só da YouTube Data API ou print do dono; vídeo citado passa por `python3 -m viitu.provar <link> --papel …`.
2. Chaves nunca no chat (`.env` / secrets). Dados pessoais do dono nunca vão para fora.
3. Direitos: roteiro próprio, áudio de terceiro desligado, crédito dos @, `viitu.direitos` sem ❌.
4. Nenhum render sem o dono aprovar quando ele pedir plano antes.

## Fluxo (cada etapa é uma skill)
`/tema` → `/roteiro` → `/clipes` → `/animacao` → `/editar` (decupagem + ouvido → partes conferidas → render →
`viitu.entrega` LIBERADA) → `/publicar` + kit `projetos/<p>/kit_publicacao.txt` mostrado no chat + capa
`projetos/<p>/capa.jpg` (`viitu.capa`). `/analisar <link>` e `/espiar` viram conhecimento (`hall_da_fama/`,
`analises_concorrencia/`; `/espiar` atualiza `edicao/matriz_702010.md`). Todo vídeo novo: ler os últimos 5 de
`dados/temas_feitos.md` e não repetir o molde.

## Ambiente
Início de sessão: `python3 -m viitu.saude` (+ `vidiq_balance`; reserva em `dados/plano_b.md`). A nuvem não baixa nem
transcreve do YouTube: TikTok/X pelo `yt-dlp`, arquivos do dono pelo Drive. Ouvido: `uv tool install "earshot[mcp] @
git+https://github.com/Leonxlnx/earshot"` + `earshot doctor --fetch`. Gemini é opcional. Depois de publicar: apagar
`projetos/<p>/clipes`.
