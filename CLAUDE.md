# Viitu Shorts — instruções para o Claude

Canal de YouTube Shorts de curiosidades em PT-BR (@viitushorts). Referência de formato:
@avidamaravilha (curiosidade com narração explicativa). O dono opera **pelo celular**,
nesta sessão cloud. Fale sempre em **português do Brasil**, simples e direto.

## Modo de trabalho
- **Tutorial:** um passo por vez, sem dar várias opções. Decida e explique o porquê em uma linha.
- Passos manuais do usuário: numerados, curtos, com links diretos.
- **Nunca** invente números (views, inscritos). Números só da YouTube Data API ou de print do usuário.
- **TRAVA DE NÚMEROS:** todo vídeo citado ao dono passa por `python3 -m viitu.provar <link> --papel
  validacao|bruto|referencia` NA MESMA RESPOSTA, e é apresentado com o rótulo do papel + link exato
  (a prova do tema ≠ o bruto). Validação e bruto só com ≥ 1M de views.
- **Nunca** peça chave/senha no chat. Chaves ficam nos secrets do ambiente "Viitu".

## Fluxo de produção (meta final)
1. `/tema <dia>` → 3 temas com números reais (YouTube Data API) + lacuna em PT-BR
2. `/clipes` → vídeos que representam o tema (links YouTube + B-roll Pexels)
3. `/roteiro` → roteiro guiado, passo a passo, com técnicas de retenção
4. `/editar` → voz ElevenLabs + cortes sincronizados + flash + SFX + legenda → mp4
5. Usuário agenda no app YouTube Studio (upload via API trava em privado sem auditoria)

Clipes do usuário chegam **anexados no chat** (funciona) ou, se forem grandes, por **link do Google Drive** público (gdown). YouTube e Reddit bloqueiam downloads da nuvem.

## Formato que funciona NO CANAL (análise de 12 vídeos do dono com ~20k views, nov/2026)
- **Clipe-âncora:** UM clipe real, já **vertical**, com início-meio-fim (Reddit/TikTok/Douyin).
  A edição serve ao clipe (zoom no detalhe, círculo/seta animados), não o substitui.
- Os vídeos antigos do dono tinham 10–20 s; a regra de duração atual está em "REGRA DE DURAÇÃO" abaixo.
- Legenda: 1 palavra por vez, branca/amarela. Adesivos de COMENTA/LIKE/INSCRITO no fim.
- Stock (Pixabay) só como complemento. Clipe horizontal cortado para 9:16 fica ruim.

## O que faz um Short dar certo (ordem de peso, definida com o dono)
1. **Tema validado** (maior peso): já fez milhões em outro idioma e não tem versão forte em PT-BR.
2. **Gancho nos 2 primeiros segundos:** a frase manda olhar ("Repara no olho dessa cabra") e o
   frame 0 mostra exatamente isso, em tela cheia, de preferência com contato visual. Abrir uma
   lacuna ("...e ele faz uma coisa que o seu não faz"), nunca entregar a resposta no gancho.
3. **Clipes e edição:** seguram quem ficou. Clipe de terceiros (ex.: NatGeo) entra como PROVA no
   meio, não no gancho; o gancho usa imagem livre sempre que possível.

## Padrões medidos nos canais de referência (raio-X pelo Gemini, nov/2026 — `pesquisa/raiox/`)
- **Seta vermelha no frame 0** apontando para o sujeito: presente nos 3 vídeos analisados (A vida é
  uma maravilha, Polaco sem Polônia, Andre Shorts). Círculo/seta de novo quando aparece um detalhe.
- Gancho = afirmação contraintuitiva + imagem satisfatória/estranha no 1º segundo.
- Ritmo: 1,7 a 2,9 s por cena. Legenda 1–2 palavras, centro-inferior, amarelo/verde com contorno.
- Final com cena satisfatória; CTA simples ("Você experimentaria?") ou lúdico que puxa like
  ("toque duas vezes na tela que aparece um peixinho").
- Imagens: compilação de TikTok/Douyin/Instagram ou documentário de fábrica (um bruto).
- **Base consolidada (9 virais, `hall_da_fama/README.md`):** seta no frame 0 em 77% · 2,5 s por cena ·
  legenda 1 palavra no centro-inferior em 8/9 · sons: pop, woosh, ding · **som original do clipe
  audível sob a narração** (editor: faixa `ambiente` a 35%; `"som_original": false` desliga por cena).

## Protocolo HISA (roteiro)
- **REGRA DE DURAÇÃO (definitiva, nov/2026). Só existem 2 formatos:**
  - **LONGO = 45 a 60 s** (110–150 palavras). **É o padrão.** Exige 1 clipe-âncora + 2 a 4 clipes reais
    de apoio e uma história com virada.
  - **CURTO = 25 a 35 s** (60–85 palavras). **Só quando** há um único clipe forte e o tema se resolve
    em uma ideia. Nunca esticar um curto para virar longo (encher linguiça derruba a retenção).
  - Entre 36 e 44 s não existe: decida um dos dois.
  - **Teste (3 semanas):** a cada 3 vídeos, 2 LONGOS e 1 CURTO. Depois, comparar no Studio
    (visualizado vs. deslizado, % assistido, views em 48 h, inscritos ganhos) e manter o vencedor.
  - Base: @avidamaravilha (300 Shorts, mar–nov/2026): mediana de views 100k (21–30 s), 599k (31–45 s),
    747k (46–60 s), 809k (61–90 s).
- **Ato 1, gancho (0–3 s):** objeto nomeado em ≤ 8 palavras, pergunta/lacuna de curiosidade.
  Voz começa em 0,0 s. Frame 0 = cena mais impressionante. Pergunta escrita na tela.
- **Ato 2, desmistificação:** "A maioria acha X, mas o motivo real é Y."
- **Ato 3, virada:** "Mas tem um porém..." (segundo problema / bastidor).
- **Ato 4, loop:** termina em frase suspensa (`...`, nunca ponto final) que emenda gramaticalmente
  na primeira palavra do gancho.
- **Evidências:** todo fato marcado [CONFIRMADO] (com fonte) ou [INCERTO]. Nada [INCERTO] no texto final.
- **Edição:** um estímulo visual a cada 2–3 s (zoom no detalhe, círculo/seta, corte), sempre na borda
  de uma palavra; palavra-gatilho = o detalhe em destaque na tela. Cortar só quando muda a ideia.

## LÓGICA DE ESCOLHA DE TEMA (medida em 625 vídeos de 3 canais BR — `hall_da_fama/logica_temas.md`)
1. **Fonte = temas evergreen já virais:** quase todo sucesso deles (e também os fracassos) repete um
   tema que já tinha viralizado lá fora, em média **1,5 a 2 anos antes** (não é notícia nem tendência).
   Ou seja, pré-validação é OBRIGATÓRIA, mas não basta: ela não separa sucesso de fracasso.
2. **O que separa sucesso de fracasso é a CATEGORIA + o GATILHO** (mediana de views):
   - 🥇 motivo oculto de objeto/design (A vida 2,5M · GeneralTV 930k · KSO 2,7M)
   - 🥈 recorde/escala/"mais caro do mundo" (2,0M · 1,9M) · 🥉 perigo/erro/segurança (1,4M · 979k)
   - gatilhos fortes: dinheiro/escala, **mito desmentido**, motivo oculto, perigo/medo, processo revelado
   - fracos: animal com comportamento estranho (255k · 171k), comida, corpo/saúde, truque, lugar/cultura,
     e "surpresa visual / olha isso" sem explicação (379k · 213k)
   - título com pergunta direta ao espectador ("Você conseguiria...?", "Você aguenta...?") e assunto vago
     ("O hobby dele é...") aparecem entre os piores.
3. `/tema` aplica esses pesos automaticamente (PESO_CATEGORIA e PESO_GATILHO em `viitu/tema.py`),
   busca temas de até 2 anos com ≥2M views e checa a lacuna em PT-BR.

## Seleção de tema (nota 0–12, 0 a 2 por critério; produzir só com ≥ 9)
Objeto do dia a dia | pergunta concreta (Por que / Como / O que acontece se) |
resposta não aparece na imagem | resposta surpreendente | afeta a vida de quem assiste |
imagem forte para o frame 0.
Validação: Short em outro idioma com views ≥ 3× a mediana do próprio canal, e sem versão
forte em PT-BR.

## Publicação
- **Horário padrão: 06:00** (histórico do dono: funciona). Agendar no app do YouTube.
- Dados dos canais de referência: A vida é uma maravilha posta 1,3/dia às **12h e 18h**; GeneralTV ~1/dia
  entre 17h e 20h (**19h** com a maior mediana: 1,0M); KSO às 11h. Nenhum posta às 6h.
  Teste: alternar 06:00 e 18:00 por 2 semanas e comparar views em 48 h.

## Títulos
- O título repete a LACUNA do gancho e não pressupõe conhecimento ("O olho da cabra faz algo que o
  seu não faz", não "Por que o olho da cabra gira?"). Fórmulas validadas (canais BR de referência):
  "A/O [coisa] que [faz algo incrível]" e "Esse [coisa] [faz algo absurdo]!?".
- 4–8 palavras, pergunta ou afirmação surpreendente sobre um objeto, 1 emoji no fim,
sem CAIXA ALTA gritando. Só em português: o canal tem **dublagem automática** do YouTube ativa (não fazer títulos EN/ES).

## A definir com o usuário
- Subnicho principal e secundário
- Calendário da semana (dias e família de tema de cada dia)
- Estilo de legenda/SFX (referência: palavra única, fonte grossa, contorno; flash 0,2 s nos cortes;
  woosh nos cortes, ding/pak na palavra-gatilho)

## Escolha de cena (definido com o dono): decidir NA ESCOLHA, não consertar depois
1. **Toda cena é escolhida com o cuidado do gancho:** representa exatamente a frase falada E tem
   apelo visual (o melhor trecho do clipe, assunto em destaque, enquadrado). Sem "cena de enchimento".
2. **Contraste com a cena anterior** (o cérebro não se acostuma): mudar pelo menos 1 eixo —
   escala (close ↔ aberto), quantidade (uma galinha ↔ um monte), direção (olhando/indo para a
   esquerda ↔ direita; inverter com `"espelhar": true`), energia (parado ↔ ação).
3. Cena de explicação não precisa de início-meio-fim; precisa de variedade e de força visual.
4. Ferramenta: `python3 -m viitu.contraste <proj>` (relatório) / `--aplicar` (espelha onde a direção
   repete). Nunca espelhar imagem com texto/logo/marca d'água (`"texto_na_imagem": true`).

## De onde vêm as IMAGENS (mesma lógica do tema: material validado)
1. Comece pelo **vídeo viral que validou o tema**: `viitu.assistir perguntar <link> "cenas, origem, marcas d'água"`.
   Descubra de onde vieram as imagens dele e busque esses ORIGINAIS (ou equivalentes) com muitas views/likes.
2. Brutos longos só com **≥ 1M de views** (`viitu.tema brutos` já filtra). Nunca reportagem antiga,
   entrevista ou vídeo com poucas views.
3. Clipes de TikTok/Reddit: só os que viralizaram (centenas de milhares de likes/upvotes).

## Monetização e direitos (fazer do jeito certo)
- Política de conteúdo reutilizado do YouTube: o que vale é **explicação/comentário original e
  edição substancial**; compilação com narração mínima ou narração lida sobre clipes é rejeitada.
  Permissão do criador NÃO basta para monetizar (support.google.com/youtube/answer/1311392).
- Nosso diferencial obrigatório em todo vídeo: roteiro próprio que EXPLICA (não descreve), fatos com
  fonte, edição com efeitos/marcas, cenas escolhidas e reordenadas. Nunca repostar clipe com voz por cima.
- Voz de IA + clipes alheios é zona de risco: variar estrutura, ganchos e trilhas; nada de vídeo em série
  "de molde" idêntico.
- Clipe-âncora de terceiros: pedir permissão por DM (`pesquisa/permissao_clipes.md`), creditar o @.
  Material próprio do dono (gravar no celular) sempre que possível.
- Licenciamento pago (Jukin/Storyful/Newsflare) existe, mas não é necessário agora.

## Pedir bruto ao dono: SÓ DEPOIS DE VERIFICAR
- Nunca pedir para baixar um vídeo escolhido só pelo título. Antes, rodar
  `python3 -m viitu.assistir achar <link> "<cenas necessárias>"` e só pedir se tiver trechos bons
  (nítidos, recentes, com a ação, não entrevista) somando material suficiente.
- Passar ao dono o link + os minutos exatos de cada trecho a gravar/baixar.
- Clipes do TikTok: cortar antes da tela final (logo + @) que aparece nos últimos ~3 s; crédito dos @ na descrição.

## Revisão técnica OBRIGATÓRIA antes de entregar
- `python3 -m viitu.revisar <proj>`: confere o meio de cada cena (`--rigoroso`: início/meio/fim) (assunto `esperado` na tela,
  centralizado, não cortado) e repetição de clipes (âncora ≤ 4 cenas, demais 1). Abrir
  `saida/revisao.jpg` e olhar. Só mandar ao dono com APROVADO ou com cada alerta conferido a olho
  (marcar `"revisao": "manual"` na cena quando o detector não serve, ex.: close extremo).

## Acabamento (Remotion) e identidade
- Pipeline: `python3 -m viitu.editar <proj> --remotion` → `cd remotion && npm run render`.
- Identidade: flash branco→amarelo nos primeiros 0,2 s + "ding" no frame 0. Círculo vermelho perfeito
  que se desenha e segue o objeto, com "pop". Woosh variado nos cortes. Riser + impacto + flash +
  tremida em "impacto_em". Botão INSCREVA-SE no fim. Trilha de fundo a 16% sob a voz.
- **Quando usar cada efeito (biblioteca validada):**
  | Momento | Visual | Som |
  |---|---|---|
  | Frame 0 (identidade) | flash branco→amarelo 0,2 s | ding |
  | Corte comum | glitch RGB de 3 quadros (sem flash branco) | woosh / whip / woosh2 / woosh3 alternados |
  | Frase de impacto ("Mas...", revelação) — `impacto_em` | zoom blur + separação RGB + flash + tremida | drone de tensão antes + boom |
  | Palavra-chave (destaques) | punch de câmera 4,5% + legenda amarela maior | — |
  | Detalhe a observar | círculo vermelho perfeito que se desenha e segue o objeto | pop |
  | Final | botão INSCREVA-SE → ✓ INSCRITO | clique |
  Não usar sons "meme" de direitos incertos (vine boom etc.); usar as versões próprias (boom, scratch).
- **Legenda:** 1 palavra, altura automática longe do ponto de atenção (sujeito em cima → legenda em
  y=1180; senão y=400). Nunca abaixo de ~1400 (interface do YouTube).
- Remotion: `remotion.config.ts` usa WebGL por software (swangle) para os efeitos; skills oficiais em
  `.agents/skills` (remotion-markup, remotion-captions...).
- Sons em `assets/sfx/` (normalizados a −1 dB de pico) e trilhas em `assets/musica/`, gerados no
  ElevenLabs (sound-generation e music), livres de direitos.

## Estrutura do repositório
- `viitu/assistir.py`: Gemini assiste vídeo do YouTube pelo link (`dissecar`, `achar "<momento>"`,
  `perguntar`). Grátis (GEMINI_API_KEY no .env). Use para referências e para achar o minuto exato nos brutos.
- `radar/radar.py`: mede outliers de canais via yt-dlp (só funciona fora da nuvem)
- `pesquisa/`: protocolo de mineração e o Gem antigo do Gemini (descontinuado para números)
