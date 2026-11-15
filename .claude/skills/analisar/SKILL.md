---
name: analisar
description: Analisa um vídeo ou canal do YouTube enviado pelo usuário (link de Short/vídeo ou @canal), disseca a edição com o Gemini, mede o canal com a YouTube Data API e arquiva tudo no Hall da Fama. Use SEMPRE que o usuário mandar um link de vídeo/canal para análise, referência ou inspiração, ou digitar /analisar.
---

# /analisar <link ou @canal>

Todo link enviado pelo dono vira conhecimento do projeto. Não responda "de cabeça": meça e arquive.

## Vídeo (link de Short/vídeo)
1. `python3 -m viitu.hall adicionar <link> --origem "enviado pelo dono"`
   (metadados reais + raio-X do Gemini em `hall_da_fama/videos/<id>.json`; atualiza o README do Hall)
2. Se o canal ainda não tem relatório: `python3 -m viitu.canal @handle --n 250`
   e `python3 -m viitu.hall top @handle --n 4` (os 4 maiores sucessos do canal entram no Hall).
3. Se for um vídeo montado de um bruto: `python3 -m viitu.tema brutos "<tema em inglês>"` para achar a origem.
4. Responda curto, para celular:
   - números (views, likes/view, duração, canal, data)
   - gancho (frase + frame 0), ritmo (s/cena), efeitos e sons com o momento em que entram, CTA, loop
   - de onde veio o material
   - **o que entra no Viitu** (no máximo 3 itens) e, se for o caso, o que muda no CLAUDE.md, na
     biblioteca de efeitos (`remotion/src/Short.tsx`) ou no `/clipes`.

## Canal (@handle)
`python3 -m viitu.canal @handle --n 250` → relatório em `hall_da_fama/canais/<handle>.md`
(vídeos/dia, horário x views, dia da semana, duração x views, padrões de título, top e piores).
Depois `python3 -m viitu.hall top @handle --n 4`.

## Sons e músicas
O raio-X descreve os sons e a trilha. Quando aparecer um efeito novo e recorrente nos vídeos do Hall,
gere a versão própria no ElevenLabs (sound-generation; música com /v1/music), normalize a −1 dB de
pico e salve em `assets/sfx/` ou `assets/musica/`. Registre em `hall_da_fama/biblioteca.md`
(nome do arquivo → quando usar → de qual referência veio). Nunca baixar o áudio de terceiros.

## Nossos vídeos
Quando um vídeo do Viitu bater recorde de views ou de likes/view, adicione com `--origem "nosso"`.

## Regras
- Números só da API ou de print do dono. O Gemini descreve, mas pode errar detalhes: quando uma
  conclusão for mudar o projeto, confirme com 2 ou mais vídeos do Hall.
- Atualize "Lições consolidadas" com `python3 -m viitu.hall resumo` e faça commit.
