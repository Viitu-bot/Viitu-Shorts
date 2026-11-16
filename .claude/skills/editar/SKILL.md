---
name: editar
description: Edita o Short do Viitu do roteiro aprovado até o mp4 final (voz, cenas, animação, sound design, Remotion) e passa por TODAS as verificações antes de entregar ao dono. Use quando o usuário digitar /editar, pedir para gerar/renderizar/refazer o vídeo.
---

# /editar: do roteiro aprovado ao mp4 conferido

Leia antes: `edicao/manual_edicao.md`, `edicao/logica_editor.md`, `edicao/biblioteca_sons.md`.

## 1. Montagem
1. Voz: `viitu.voz` (Otto, eleven_v4) → `projetos/<p>/voz.mp3` + `palavras.json`.
2. Triagem dos clipes: `python3 -m viitu.triagem <p>` (clipe reprovado não entra).
3. `cenas.json`: cada cena escolhida com o cuidado do gancho; contraste com a vizinha (`viitu.contraste`);
   animação no trecho de mecanismo; `musica` pelo clima; `creditos_descricao`.
4. `python3 -m viitu.editar <p> --remotion` → `cd remotion && npm run render` →
   copiar `out/short_remotion.mp4` para `out/<p>.mp4`.

## 2. Regras de som (as que o dono já cobrou)
- Som de função (buzzer, acerto, ding, moeda) **só com gráfico correspondente na tela** e **na pausa**
  (o editor já empurra para o fim da frase). Nunca sobre a fala. Na dúvida, não use.
- Música audível: alvo **~12–14 dB abaixo da voz** sob a fala, sobe nas pausas (medido na auditoria).
- Foley em 2 camadas (Sonniss) — conferir nomes novos em `assets/sonniss/escolhas.json`.
- Boom só na virada (1–2 por vídeo).

## 3. Verificações obrigatórias (nesta ordem, corrigir antes de seguir)
1. `python3 -m viitu.revisar <p>` → abrir `saida/revisao.jpg`.
2. `python3 -m viitu.auditoria <p> remotion/out/<p>.mp4` → loudness −14, música vs voz, efeitos sobre a fala,
   cenas escuras, ritmo, loop.
3. `python3 -m viitu.direitos <p>` → sem ❌.
4. Prancha 1 quadro/s (`ffmpeg -vf fps=1,scale=180:-1,tile=10x6`) → olhar tudo (logo do TikTok, cena que não
   combina com a frase, repetição, escuro).
5. Só então: commit + enviar ao dono com o resumo do que mudou e o que ele deve olhar.
