# Viitu Shorts — instruções para o Claude

Canal de YouTube Shorts de curiosidades em PT-BR (@viitushorts). O dono opera **pelo celular**, nesta
sessão cloud. Fale sempre em **português do Brasil**, simples e direto.

## Como trabalhar
- **Tutorial:** um passo por vez, sem dar várias opções. Decida e explique o porquê em uma linha.
- Passos manuais do dono: numerados, curtos, com links diretos.
- Antes de entregar qualquer coisa, confira você mesmo (prancha, revisão). Nunca entregue sem olhar.
- **Toda etapa segue `edicao/formato.md` (a planta) e começa por `edicao/reclamacoes.md`** (o que o dono já reprovou). As travas `viitu.montagem` (antes do
  render) e `viitu.entrega` (antes de mandar) são obrigatórias em TODO vídeo.
- Técnica nova aprendida (referência, pedido do dono) vai para o lugar certo do mapa abaixo, não para cá.

## Regras que nunca quebram
1. **Números:** nunca inventar views/inscritos. Só YouTube Data API ou print do dono.
2. **Trava de números:** todo vídeo citado ao dono passa por
   `python3 -m viitu.provar <link> --papel validacao|bruto|referencia` NA MESMA RESPOSTA e aparece com o
   rótulo do papel + link exato. Validação e bruto só com ≥ 1M de views.
3. **Chaves:** nunca pedir chave/senha no chat. Ficam no `.env` (fora do git) ou nos secrets do ambiente.
4. **Direitos e monetização:** roteiro próprio que EXPLICA, edição substancial, fatos com fonte. Áudio
   original de terceiro desligado; crédito dos @ na descrição; trilhas/sons só das bibliotecas liberadas
   (`edicao/biblioteca_sons.md`). `viitu.direitos` sem ❌ antes de entregar.
5. **Dados pessoais do dono** nunca vão para serviços externos.

## Fluxo de produção (cada etapa é uma skill)
1. `/tema <dia>` → 3 temas validados com números reais e lacuna em PT-BR
2. `/roteiro` → texto HISA + marcações de edição
3. `/clipes` (+ `/brutos` se o dono enviar arquivos) → cenas reais escolhidas e triadas
4. `/animacao` → o trecho explicativo em 3D (o que não existe em vídeo, é difícil de achar ou impossível de filmar)
5. `/editar` → voz, montagem, som, Remotion e **`python3 -m viitu.entrega <p>` LIBERADA** (sem isso não se entrega)
6. `/publicar` → título, descrição, créditos, horário; o dono agenda no app do YouTube Studio
- `/analisar <link>`: todo vídeo/canal que o dono mandar vira conhecimento (Hall da Fama).

## O formato do canal: HISA 2.0 do dono (público adulto 25+, 100% faceless)
- **Só 2 formatos:** **Tiro Curto** 12–15 s (30–38 palavras; curiosidade rápida, física bizarra, susto, gambiarra;
  **re-hook aos 6 s**) ou **Bastidor** 20–28 s (50–65 palavras; engenharia, processo industrial, máquina, trabalho
  manual: risco/problema → macete técnico → "momento eureka").
- **Estrutura:** gancho ≤ 3 s quebrando a expectativa → **ouro parcelado** (a explicação vem aos poucos enquanto a ação
  acontece) → eureka/virada → CTA-elogio (se couber) → **loop**: nunca termina em ponto final; fecha com conjunção
  suspensa ("...vendo que", "...porque quando") que emenda na 1ª palavra.
- **Áudio:** "ding" no 00:00; voz do Otto no máximo com silêncios cortados (auto-cut); som original de clipe LIVRE
  sobe no clímax (de terceiro fica desligado: Content ID).
- **Visual:** zero fisheye; legenda 1 palavra, amarelo ouro #FFD700, contorno preto forte, terço superior; 3D no
  trecho explicativo; clipe real no gancho e como prova.
- **Tom:** curiosidade técnica narrada com maturidade; duplo sentido ("lá ele") só pontual, quando a cena entregar.
- **Temas que funcionam:** motivo oculto de objeto > recorde/"mais caro" > perigo/erro (`/tema`).
- Comparar no Studio os vídeos de 45 s (vd005, vd006) com os do formato do dono antes de mudar qualquer regra.

## Mapa do conhecimento (onde cada coisa mora)
| Assunto | Arquivo |
|---|---|
| **O FORMATO (planta: roteiro + B-roll + 3D + som, batida por batida)** | `edicao/formato.md` |
| **Reclamações recorrentes do dono → regras + trava da montagem** | `edicao/reclamacoes.md` · `viitu/montagem.py` |
| Volumes de som e regras visuais (valores fixos) | `edicao/especificacao.json` |
| Qual efeito em qual momento/cena, engenharia reversa dos canais | `edicao/logica_editor.md` |
| Técnicas de edição (som em camadas, corte J/L, 3D, cor) | `edicao/manual_edicao.md` |
| Sons e trilhas: de onde vêm, para que servem | `edicao/biblioteca_sons.md` |
| Lógica de temas (625 vídeos de 3 canais BR) | `hall_da_fama/logica_temas.md` |
| Vídeos/canais de referência analisados | `hall_da_fama/` e `pesquisa/reverso/` |
| Projetos de vídeo (roteiro, cenas, saída) | `projetos/<vdNNN_nome>/` |
| Código | `viitu/` (Python) e `remotion/src/` (acabamento e animações) |

## Limpeza (sempre)
- Depois de publicar um vídeo: apagar `projetos/<p>/clipes`, `saida/cenas` e vozes antigas (`voz_v*.mp3`); manter
  roteiro, cenas.json, créditos e o mp4 final em `remotion/out/` só até o dono confirmar que postou.
- Cache Sonniss: manter só os sons de `assets/sonniss/escolhas.json`. Versões antigas de arquivos não ficam no repositório.

## Ambiente
- **Começo de toda sessão:** `python3 -m viitu.saude` + `vidiq_balance`. Se algo falhar, seguir a reserva em `dados/plano_b.md`
  (o processo nunca para por uma cota ou serviço fora do ar).
- Nuvem não baixa do YouTube/Reddit: o dono envia clipes no chat ou na pasta Drive `brutos` (`/brutos`).
  **X (Twitter) baixa direto:** `yt-dlp <link do post>` (vd007: vídeo 4K oficial da SpaceX). Peça o link do post.
- **Gemini é opcional** (dono 18/11: "não dependa tanto do Gemini"): nenhuma trava nem etapa de produção depende dele.
  Classificar temas e julgar roteiro/cenas = o próprio Claude; som e imagem = medições próprias. Gemini só com `--gemini`
  (ex.: dissecar vídeo de referência no /analisar, onde é o único que assiste YouTube pelo link).
- Sem GPU: 3D renderiza em software (mais lento, funciona). Veo/IA de vídeo pela API é paga.
