# Viitu Shorts — instruções para o Claude

Canal de Shorts de curiosidades em PT-BR (@viitushorts). O dono opera **pelo celular**. Fale em **português do Brasil**,
simples e direto, um passo por vez, sem termos técnicos.

## DNA e Identidade do Canal (INEGOCIÁVEL — nenhuma automação apaga ou contraria)
Medido em 24/11 nos 12 vídeos que o dono editou antes da pausa (Drive "Minha edição", transcritos e ouvidos) — detalhe
em `edicao/identidade.md`.
- **Humor:** malandro e adulto, com duplo sentido pontual quando a cena entrega ("antes que ele corte a tua…", "quem não
  der like vai cair no cone"); comparação pop exagerada ("falha na Matrix", "mini Godzilla", "dinossauro aposentado",
  "transformou a moto num caça de guerra", "míssil teleguiado"). Nunca infantil.
- **Voz:** a do próprio dono — clone "Minha voz" na ElevenLabs (`viitu/voz.py`, padrão desde 24/11).
- **Fala:** narrador que conversa com o espectador ("Olha o nó que esse cara deu…", "Esquece…", "Meu cachorro tá
  diferente"); gírias leves (maluco, tiozinho, caboclo, paradão, cara de sonso, a parada, todo santo dia); frases curtas,
  ritmo rápido; pergunta direta ao espectador ("Você pegou o truque de primeira ou também bugou?").
- **Estrutura:** gancho que joga você na cena → explicação técnica em linguagem de rua ("o segredo é…", "isso aqui é
  atrito extremo") → virada → fecho que emenda no começo (loop: "…vendo que", "…porque").
- **Som:** música "sans." (Toby Fox) em 7/12 (só pelo app). **No arquivo: biblioteca de música de JOGO ANTIGO livre** (`assets/musica/jogo_antigo/`, clima escolhido pelo gatilho — dono 27/11) · abertura = DING (hoje em 2 toques
  com eco estéreo) · whoosh nas trocas · riser antes da revelação.
- **Visual:** legenda de 1 palavra, amarela (às vezes branca), contorno preto forte, grande (30% assiste na TV);
  círculo/seta vermelha no detalhe; corte a cada 2–3 s; clipe real em movimento; cada fonte UMA vez,
  perto/longe intercalado (travas R1, R9, R10 da `viitu.montagem`).

## Padrão-ouro: vd004 bombeiros (90,8% de retenção média, linha reta até 40 s — print do dono)
45,7 s · 130 palavras (2,85/s) · 26 cenas (1,76 s cada) · gancho "de propósito" → "a maioria acha" → mecanismo →
"mas tem um porém" → risco. **Duração: alvo 12–18 s, teto 30 s só se o tema exigir (dono 26/11: os 4 vídeos > 20 mil tinham < 16 s e > 105% de visualização).** Público adulto 25+.
- **Gancho (meta 78%+ continuaram assistindo):** sem introdução nem contexto; a 1ª frase abre o loop de curiosidade em
  1,5–2 s, em cima do quadro mais estranho/forte do vídeo. Modelos: "Piscou o olho, perdeu…", "Como sumir do mapa…",
  "Por que esses…".
- **Final (o vd004 caiu nos últimos 5 s):** loop NARRATIVO (dono 26/11): a última frase faz sentido ao emendar no gancho, sem precisar repetir a palavra. PROIBIDO resumo,
  moral, "da próxima vez…", CTA de inscrição/like no fim (trava `viitu.montagem` R0, do vd016 em diante). O vídeo corta
  no último som da voz, 0,3 s antes da margem antiga (`viitu/editar.py`).

## Nicho de ESTILO (dono 26/11)
3–4 categorias fixas, não assunto fixo: flagrante/inusitado do cotidiano · habilidade/trabalho extremo · história curta de
pessoa/personalidade · invenção visual chocante. **Regra dos 75%+:** 1ª cena + 1ª fala seguram 75% sozinhas, senão o tema
fica guardado. Assinatura (voz, ritmo, abertura, trilha) igual em qualquer assunto. Detalhe: BÍBLIA §0c.

## Retenção (dono 26/11 — caiu de 76–80% para 58%)
Gancho nos primeiros 2 s + psicologia da retenção em todo o vídeo. **B-roll nunca sem o storyboard** de
`edicao/retencao_storyboard.md` (§0 Diretor de Retenção Visual: 1º quadro = anomalia/perigo/ação no meio; quebra de
escala a cada 1,5–2 s; imagem indireta que antecipa a frase; tensão no meio; último clipe liga no primeiro), mostrado ao dono antes de baixar.

## Som (regras fixas — `biblioteca_sfx/LEIA.md`)
- Só sons de `biblioteca_sfx/` (4 pastas). PROIBIDO desenho animado, meme, "boing", buzina, risada, "pop" agudo.
- Máx. 1 efeito de AÇÃO a cada 3 s; whoosh (−14) em TODA troca, alternando suave/rápido/grave, só pula se um efeito cair a < 0,3 s do corte (dono 27/11); tremida leve nos impactos (tiro/explosão). O som apoia, não aparece mais que a história.
- Mixagem automática (`viitu/som_final.py`, `edicao/especificacao.json`): voz NA FRENTE com tratamento leve · música −16 na mixagem (audível sob a voz contínua) · efeitos −10 a −5 dB
  (dono 24/11: voz B escolhida de ouvido; música subiu no vd017; teste A/B só se ele pedir) · voz ≥ 3,0 palavras/s · abertura no nível da voz (identidade). Música SEMPRE dentro do arquivo (trilha própria licenciada).
- **Imersão (dono 27/11):** ambiência do lugar (`biblioteca_sfx/05_ambiencia`) + foley do que aparece + whoosh em toda troca — as 3 camadas em todo vídeo.
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

## Ordem que não gasta crédito (dono 26/11, BÍBLIA §0d)
Voz só depois do roteiro FINAL aprovado · render completo é o ÚLTIMO passo: cor, tarja, nitidez, decupagem, partes e o SOM
inteiro (voz, efeitos, transições, música) conferidos ANTES, na prévia `viitu.som_final --previa`. Defeito achado depois do render = erro de processo.

## Fluxo (cada etapa é uma skill — dono 27/11: os vídeos andam POR COMANDO; toda resposta termina dizendo o próximo comando, ex.: `/roteiro`, `/clipes`, `/editar`)
`/tema` → `/roteiro` → `/clipes` → `/animacao` → `/editar` (decupagem + ouvido → partes conferidas → render →
`viitu.entrega` LIBERADA) → `/publicar` + **kit obrigatório** `projetos/<p>/kit_publicacao.txt` mostrado no chat + **capa** `projetos/<p>/capa.jpg` (`viitu.capa`)
(título/descrição do gancho · comentário fixado provocativo · trivia da Comunidade com 4 opções e a correta).
`/analisar <link>` e `/espiar` (concorrência → `analises_concorrencia/`) viram conhecimento.

## Mapa
BÍBLIA `edicao/BIBLIA.md` · identidade `edicao/identidade.md` · ganchos `edicao/ganchos_gatilhos.md` · nicho `edicao/biblioteca_nicho.md` · formatos
`edicao/formatos.json` · reclamações `edicao/reclamacoes.md` · base das regras `edicao/fontes_das_regras.md` · sons
`biblioteca_sfx/` · projetos `projetos/<vdNNN>/` · código `viitu/` e `remotion/src/`.

## Ambiente
Início de sessão: `python3 -m viitu.saude` (+ `vidiq_balance`; reserva em `dados/plano_b.md`). A nuvem não baixa nem
transcreve do YouTube: TikTok/X pelo `yt-dlp`, arquivos do dono pelo Drive. Ouvido: `uv tool install "earshot[mcp] @
git+https://github.com/Leonxlnx/earshot"` + `earshot doctor --fetch`. Gemini é opcional. Depois de publicar: apagar
`projetos/<p>/clipes`.
