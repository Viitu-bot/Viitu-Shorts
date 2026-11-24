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
3b. **MEDIÇÃO TOMADA POR TOMADA (rea-video, sem Gemini, sem chave)** quando houver o ARQUIVO do vídeo (o dono manda
   no chat/Drive, ou a versão do mesmo vídeo no TikTok/X baixada com `yt-dlp`; a nuvem não baixa do YouTube):
   `rea-video decompose <ref.mp4> -o hall_da_fama/rea/<id>` (instalação, 1x por sessão:
   `pip install "rea-video[ocr] @ git+https://github.com/JuneYaooo/rea-video"`). Ler `breakdown.json`:
   `shots` (início/fim de cada tomada), `audio.music` (BPM, onde a música entra/some), `audio.voice`,
   `audio.sfx.events` (instante de cada efeito e se cai num corte ou num texto). Teste no nosso vd013 (20/11):
   **10/10 cortes no décimo de segundo**; efeitos: 7/10 no instante certo, mas o NOME do tipo ("ding", "pop") erra —
   o instante vale, o rótulo não. A classificação "filmado/IA/3D" sem VLM não serve (deu "IA" num clipe real).
   Os números medidos (s/tomada, efeitos por corte, BPM) entram em `edicao/REGRAS.md` como **M** (só com autorização do dono) com a
   amostra. Os sons de `sfx/` e `stems/` do vídeo de terceiro servem SÓ para ouvir/medir — nunca entram no nosso vídeo.
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
