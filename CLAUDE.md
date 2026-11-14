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
- **10–20 s** na maioria; 3–4 cortes. Muitos cortes só em vídeo de "processo" (etapas).
- Legenda: 1 palavra por vez, branca/amarela. Adesivos de COMENTA/LIKE/INSCRITO no fim.
- Stock (Pixabay) só como complemento. Clipe horizontal cortado para 9:16 fica ruim.

## Protocolo HISA (roteiro)
- **Duração:** 15–30 s (40–75 palavras, ~2,5 palavras/s), acompanhando a duração do clipe-âncora.
- **Ato 1, gancho (0–3 s):** objeto nomeado em ≤ 8 palavras, pergunta/lacuna de curiosidade.
  Voz começa em 0,0 s. Frame 0 = cena mais impressionante. Pergunta escrita na tela.
- **Ato 2, desmistificação:** "A maioria acha X, mas o motivo real é Y."
- **Ato 3, virada:** "Mas tem um porém..." (segundo problema / bastidor).
- **Ato 4, loop:** termina em frase suspensa (`...`, nunca ponto final) que emenda gramaticalmente
  na primeira palavra do gancho.
- **Evidências:** todo fato marcado [CONFIRMADO] (com fonte) ou [INCERTO]. Nada [INCERTO] no texto final.
- **Edição:** corte a cada 1,5–3 s, sempre na borda de uma palavra; palavra-gatilho = cena na tela.

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

## Estrutura do repositório
- `radar/radar.py`: mede outliers de canais via yt-dlp (só funciona fora da nuvem)
- `pesquisa/`: protocolo de mineração e o Gem antigo do Gemini (descontinuado para números)
