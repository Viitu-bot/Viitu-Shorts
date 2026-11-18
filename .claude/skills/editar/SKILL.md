---
name: editar
description: Edita o Short do Viitu do roteiro aprovado até o mp4 final (voz, cenas, animação, sound design, Remotion) e passa por TODAS as verificações antes de entregar ao dono. Use quando o usuário digitar /editar, pedir para gerar/renderizar/refazer o vídeo.
---

# /editar: do roteiro aprovado ao mp4 conferido

Valores fixos (volumes, ritmo, cor): `edicao/especificacao.json` — nunca número solto no código.
Quando usar cada efeito: `edicao/logica_editor.md`. Técnicas: `edicao/manual_edicao.md`. Sons: `edicao/biblioteca_sons.md`.

## 1. Montagem
1. Voz: `python3 -m viitu.voz <p>` (Otto, eleven_v4; lê o "TEXTO FINAL PARA A VOZ" do roteiro.md) →
   `voz.mp3` + `palavras.json`. Antes de refazer, guarde a anterior (`voz_vNN.mp3`).
2. Triagem dos clipes novos: `python3 -m viitu.triagem <p>`.
3. `cenas.json`: `"em"` (trecho onde a cena começa), `"clipe"`, `"inicio"`; animação 3D com
   `"animacao": {...}, "manter": true, "revisao": "manual"`; `"musica"` pelo clima; `"impacto_em"` (virada);
   `"destaques"`; `"creditos_descricao"`; `"permissoes"`.
4. `python3 -m viitu.editar <p> --remotion` → `cd remotion && npm run render` →
   `cp out/short_remotion.mp4 out/<p>.mp4`. Antes do render completo, confira quadros soltos de animações novas
   (`npx remotion still src/index.ts Short <arq>.png --frame=N --scale=0.3`).

## 2. Identidade e efeitos (o editor já faz; não reinventar)
| Momento | Visual | Som |
|---|---|---|
| Frame 0 | flash branco→amarelo 0,2 s + seta vermelha | ding próprio |
| Corte | corte SECO | kit `whoosh_corte` (alterna 3) |
| Virada (`impacto_em`) | zoom blur + RGB + flash + tremida | riser → vácuo → boom |
| Palavra-chave (`destaques`) | punch 4,5% + legenda amarela maior | — |
| Detalhe | círculo vermelho que se desenha e segue o objeto | pop |
- **Legenda:** 1 palavra, Anton, branca/amarela com contorno; longe do sujeito (y 1180 ou 420), nunca abaixo de 1400.
- **Som:** foley em 2 camadas (Sonniss: ambiência + ASMR de perto; conferir nomes novos em
  `assets/sonniss/escolhas.json`); áudio original de terceiro desligado; corte J/L e pan automáticos.
- **Som de função** (buzzer, acerto, ding, moeda) só com gráfico correspondente na tela e na pausa. Na dúvida, não.
- Sem CTA explícito por padrão (os canais usam o loop); sem sons de meme.

## 2b. Regras de montagem (cobradas pelo dono)
- **Loop perfeito:** a última cena é o MESMO quadro do frame 0 (copie a cena 1 com `"em": "<última palavra>"`,
  `"zoom": [1.0, 1.0]`). O flash do frame 0 esconde a emenda.
- **No máximo 2 cenas por clipe curto** (o revisor barra a 3ª). Faltou imagem? Busque outro clipe ou use 3D.
- **Clipe reaproveitado** (mesmo clipe em 2 cenas): na 2ª vez `"reverso": true` (toca ao contrário = continuação).
- **Cena longa que o editor divide** (> 2 s) com movimento cíclico (hélice, roda, água): `"bumerangue": true` — a 2ª
  parte começa no último quadro da 1ª e toca ao contrário (sem o pulo de "copiar e colar"). Não usar com gente andando.
- **Seta do gancho:** conferir no quadro 10 se ela aponta para o sujeito. Se o detector errar (pegou outro objeto,
  fora do quadro), use posição fixa `"seta": [x, y, r]` (pixels da tela 1080x1920).
- **Apontar detalhe em foto/cena sem rastreio:** `"seta": [x, y, r]` funciona em QUALQUER cena; `"marca"` fixa não
  aparece no Remotion e o `marca_auto` pode errar o objeto (vd007 pegou o corpo em vez da base) — conferir no quadro.
- **Palavra de ação = ação acontecendo nela:** "decolagem" → rodas saindo do chão NESSE instante; "pouso" → avião
  tocando a pista. Calcule o `inicio` para o momento da ação cair na palavra.
- Cena que não existe em vídeo mas tem cenário real (ex.: pássaros vistos da janela): clipe real + 3D sobreposto
  com fundo transparente (modelo `remotion/src/animacoes/PassarosJanela3D.tsx`).

## 2c. Sound design à prova de voz (desde 18/11 — dono: "efeito por cima da voz não pode acontecer")
- `viitu/mixagem.py` roda sozinho no fim do `editar --remotion`: simula a mixagem inteira, aplica SIDECHAIN em TODAS
  as camadas não-voz (`plano.duck`, o Short.tsx multiplica cada uma por `D(plano, f)`) para o fundo ficar ≥ 10 dB
  abaixo da voz, e recorta 2–4 kHz da música/foley/ambiente (espaço da inteligibilidade).
- Ler as 2 linhas que ele imprime: **DEPOIS** precisa de pior ≥ 0 dB e quase nada abaixo de 10 dB. Se a culpa for
  sempre a mesma camada, baixar o nível base dela em `edicao/especificacao.json` (não só confiar no ducking).
- Regras embutidas: boom termina antes da próxima palavra; sem whoosh na emenda do loop; música só sobe depois da
  última fala. Medir sem mudar nada: `python3 -m viitu.mixagem --medir`.

## 3. Verificações obrigatórias (nesta ordem; corrigir antes de seguir)
1. `python3 -m viitu.revisar <p>` → abrir `saida/revisao.jpg` (cena de animação é ignorada na repetição).
2. `python3 -m viitu.auditoria <p> remotion/out/<p>.mp4` (`--sem-gemini` se a cota acabou): loudness −14,
   efeitos sobre a fala, cenas escuras, ritmo, loop.
3. `python3 -m viitu.direitos <p>` → sem ❌.
4. Prancha 1 quadro/s: `ffmpeg -i <mp4> -vf "fps=1,scale=144:-1,tile=14x4" -frames:v 1 prancha.png` e OLHAR:
   cena que não combina com a frase, mesma imagem por muito tempo, escuro, logo, 3D com erro de lógica
   (ex.: mato verde onde o fogo já passou).
5. Commit + push, enviar ao dono com o que mudou e o que ele deve olhar.
