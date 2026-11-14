# Viitu Shorts — instruções para o Claude

Canal de YouTube Shorts de curiosidades em PT-BR (@viitushorts). Referência de formato:
@avidamaravilha (curiosidade com narração explicativa). O dono opera **pelo celular**,
nesta sessão cloud. Fale sempre em **português do Brasil**, simples e direto.

## Modo de trabalho
- **Tutorial:** um passo por vez, sem dar várias opções. Decida e explique o porquê em uma linha.
- Passos manuais do usuário: numerados, curtos, com links diretos.
- **Nunca** invente números (views, inscritos). Números só da YouTube Data API ou de print do usuário.
- **Nunca** peça chave/senha no chat. Chaves ficam nos secrets do ambiente "Viitu".

## Fluxo de produção (meta final)
1. `/tema <dia>` → 3 temas com números reais (YouTube Data API) + lacuna em PT-BR
2. `/clipes` → vídeos que representam o tema (links YouTube + B-roll Pexels)
3. `/roteiro` → roteiro guiado, passo a passo, com técnicas de retenção
4. `/editar` → voz ElevenLabs + cortes sincronizados + flash + SFX + legenda → mp4
5. Usuário agenda no app YouTube Studio (upload via API trava em privado sem auditoria)

Clipes do usuário chegam por **link do Google Drive** (YouTube e Reddit bloqueiam a nuvem).

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

## Seleção de tema (nota 0–12, 0 a 2 por critério; produzir só com ≥ 9)
Objeto do dia a dia | pergunta concreta (Por que / Como / O que acontece se) |
resposta não aparece na imagem | resposta surpreendente | afeta a vida de quem assiste |
imagem forte para o frame 0.
Validação: Short em outro idioma com views ≥ 3× a mediana do próprio canal, e sem versão
forte em PT-BR.

## Títulos
4–8 palavras, pergunta ou afirmação surpreendente sobre um objeto, 1 emoji no fim,
sem CAIXA ALTA gritando. Sempre com tradução EN/ES no YouTube Studio.

## A definir com o usuário
- Subnicho principal e secundário
- Calendário da semana (dias e família de tema de cada dia)
- Estilo de legenda/SFX (referência: palavra única, fonte grossa, contorno; flash 0,2 s nos cortes;
  woosh nos cortes, ding/pak na palavra-gatilho)

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
- `radar/radar.py`: mede outliers de canais via yt-dlp (só funciona fora da nuvem)
- `pesquisa/`: protocolo de mineração e o Gem antigo do Gemini (descontinuado para números)
