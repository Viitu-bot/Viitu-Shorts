# Viitu Shorts — instruções para o Claude

Canal de YouTube Shorts de curiosidades em PT-BR (@viitushorts). O dono opera **pelo celular**, nesta
sessão cloud. Fale sempre em **português do Brasil**, simples e direto.

## Como trabalhar
- **Tutorial:** um passo por vez, sem dar várias opções. Decida e explique o porquê em uma linha.
- Passos manuais do dono: numerados, curtos, com links diretos.
- Antes de entregar qualquer coisa, confira você mesmo (prancha, revisão). Nunca entregue sem olhar.
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
5. `/editar` → voz, montagem, som, Remotion e TODAS as verificações
6. `/publicar` → título, descrição, créditos, horário; o dono agenda no app do YouTube Studio
- `/analisar <link>`: todo vídeo/canal que o dono mandar vira conhecimento (Hall da Fama).

## O formato do canal (resumo; detalhes nas skills)
- **Duração:** LONGO 45–60 s (padrão) ou CURTO 25–35 s. Nada entre 36 e 44 s. Encher linguiça derruba a retenção.
- **Estrutura:** gancho (0–3 s, manda olhar + lacuna) → mito/motivo real → mecanismo em **3D** → virada
  ("Mas tem um porém…") → loop (frase suspensa que emenda no começo).
- **Imagens:** clipe real no gancho e como prova; **3D no trecho explicativo**; Pixabay como apoio.
- **Edição:** segue a especificação fixa tirada de 35 Shorts do nicho (volumes, ritmo de 1,5 s/cena, corte seco
  + whoosh, seta vermelha no frame 0, legenda com destaque amarelo).
- **Temas que funcionam:** motivo oculto de objeto > recorde/"mais caro" > perigo/erro (`/tema`).

## Mapa do conhecimento (onde cada coisa mora)
| Assunto | Arquivo |
|---|---|
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
- Nuvem não baixa do YouTube/Reddit: o dono envia clipes no chat ou na pasta Drive `brutos` (`/brutos`).
- Gemini (análise de vídeo) tem cota grátis diária; se acabar, pular a crítica e seguir.
- Sem GPU: 3D renderiza em software (mais lento, funciona). Veo/IA de vídeo pela API é paga.
