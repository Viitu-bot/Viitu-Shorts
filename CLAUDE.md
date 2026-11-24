# Viitu Shorts — instruções para o Claude

Canal de Shorts de curiosidades em PT-BR (@viitushorts). O dono opera **pelo celular**. Fale em **português do Brasil**,
simples e direto, um passo por vez, sem termos técnicos.

## DNA e Identidade do Canal (INEGOCIÁVEL — nenhuma automação apaga ou contraria)
Medido em 24/11 nos 12 vídeos que o dono editou antes da pausa (Drive "Minha edição", transcritos e ouvidos) — detalhe
em `edicao/identidade.md`.
- **Humor:** malandro e adulto, com duplo sentido pontual quando a cena entrega ("antes que ele corte a tua…", "quem não
  der like vai cair no cone"); comparação pop exagerada ("falha na Matrix", "mini Godzilla", "dinossauro aposentado",
  "transformou a moto num caça de guerra", "míssil teleguiado"). Nunca infantil.
- **Fala:** narrador que conversa com o espectador ("Olha o nó que esse cara deu…", "Esquece…", "Meu cachorro tá
  diferente"); gírias leves (maluco, tiozinho, caboclo, paradão, cara de sonso, a parada, todo santo dia); frases curtas,
  ritmo rápido; pergunta direta ao espectador ("Você pegou o truque de primeira ou também bugou?").
- **Estrutura:** gancho que joga você na cena → explicação técnica em linguagem de rua ("o segredo é…", "isso aqui é
  atrito extremo") → virada → fecho que emenda no começo (loop: "…vendo que", "…porque").
- **Som:** música "sans." (Toby Fox) em 7/12 (só pelo app; no arquivo, trilha própria) · abertura = DING (hoje em 2 toques
  com eco estéreo) · whoosh nas trocas · riser antes da revelação.
- **Visual:** legenda de 1 palavra, amarela (às vezes branca), contorno preto forte, grande (30% assiste na TV);
  círculo/seta vermelha no detalhe; corte a cada 2–3 s; clipe real em movimento.

## Padrão-ouro: vd004 bombeiros (90,8% de retenção média, linha reta até 40 s — print do dono)
45,7 s · 130 palavras (2,85/s) · 26 cenas (1,76 s cada) · gancho "de propósito" → "a maioria acha" → mecanismo →
"mas tem um porém" → risco. **Duração alvo 35–45 s.** Público adulto 25+.
- **Gancho (meta 78%+ continuaram assistindo):** sem introdução nem contexto; a 1ª frase abre o loop de curiosidade em
  1,5–2 s, em cima do quadro mais estranho/forte do vídeo. Modelos: "Piscou o olho, perdeu…", "Como sumir do mapa…",
  "Por que esses…".
- **Final (o vd004 caiu nos últimos 5 s):** termina na última palavra da revelação ou emenda no gancho. PROIBIDO resumo,
  moral, "da próxima vez…", CTA de inscrição/like no fim (trava `viitu.montagem` R0, do vd016 em diante). O vídeo corta
  no último som da voz, 0,3 s antes da margem antiga (`viitu/editar.py`).

## Som (regras fixas — `biblioteca_sfx/LEIA.md`)
- Só sons de `biblioteca_sfx/` (4 pastas). PROIBIDO desenho animado, meme, "boing", buzina, risada, "pop" agudo.
- Máx. 1 efeito a cada 3 s (o código pula o whoosh se houver outro efeito perto). O som apoia, não aparece mais que a história.
- Mixagem automática (`viitu/som_final.py`, `edicao/especificacao.json`): voz na frente · efeitos −12 a −18 dB · trilha
  −22 a −26 dB · abertura no nível da voz (identidade). Música SEMPRE dentro do arquivo (trilha própria licenciada).
- Todo efeito passa pelo OUVIDO (`viitu.ouvir`, earshot) na decupagem: som que não soa como o pedido barra o render.

## Aleatoriedade programada 70/20/10 (`edicao/matriz_702010.md`)
- **70%** base provada no canal (100% DNA) · **20%** variação vinda do `/espiar`, no estilo do dono · **10%** teste puro.
- Todo vídeo novo: ler os últimos 5 em `dados/temas_feitos.md`, não repetir o mesmo molde seguido e sugerir a faixa do dia.
- Todo `/espiar`: atualizar as opções de 20% e 10% da matriz.

## Regras que nunca quebram
1. Números só da YouTube Data API ou print do dono; todo vídeo citado passa por `python3 -m viitu.provar <link> --papel …`.
2. Chaves nunca no chat (`.env` / secrets). Dados pessoais do dono nunca vão para fora.
3. Direitos: roteiro próprio, áudio de terceiro desligado, crédito dos @, `viitu.direitos` sem ❌.
4. `edicao/BIBLIA.md` = regras do dono; só muda com autorização dele no chat. Sem achismo: número novo só com base em
   `edicao/fontes_das_regras.md`. Começar toda etapa por `edicao/reclamacoes.md`.

## Fluxo (cada etapa é uma skill)
`/tema` → `/roteiro` → `/clipes` → `/animacao` → `/editar` (decupagem + ouvido → partes conferidas → render →
`viitu.entrega` LIBERADA) → `/publicar` + **kit obrigatório** `projetos/<p>/kit_publicacao.txt` mostrado no chat
(título/descrição do gancho · comentário fixado provocativo · trivia da Comunidade com 4 opções e a correta).
`/analisar <link>` e `/espiar` (concorrência → `analises_concorrencia/`) viram conhecimento.

## Mapa
BÍBLIA `edicao/BIBLIA.md` · identidade `edicao/identidade.md` · nicho `edicao/biblioteca_nicho.md` · formatos
`edicao/formatos.json` · reclamações `edicao/reclamacoes.md` · base das regras `edicao/fontes_das_regras.md` · sons
`biblioteca_sfx/` · projetos `projetos/<vdNNN>/` · código `viitu/` e `remotion/src/`.

## Ambiente
Início de sessão: `python3 -m viitu.saude` (+ `vidiq_balance`; reserva em `dados/plano_b.md`). A nuvem não baixa nem
transcreve do YouTube: TikTok/X pelo `yt-dlp`, arquivos do dono pelo Drive. Ouvido: `uv tool install "earshot[mcp] @
git+https://github.com/Leonxlnx/earshot"` + `earshot doctor --fetch`. Gemini é opcional. Depois de publicar: apagar
`projetos/<p>/clipes`.
