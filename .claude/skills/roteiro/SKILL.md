---
name: roteiro
description: Escreve o roteiro do Viitu Shorts (protocolo HISA) a partir do tema validado, com fatos verificados, gancho, virada e loop, já marcando onde entram animação, sons de função e impacto. Use quando o usuário digitar /roteiro ou pedir o texto/roteiro de um tema.
---

## REGRAS DO DONO 24/11 (valem sobre qualquer instrução abaixo que conflite)
- **Padrão-ouro vd004 bombeiros:** 35–45 s, ~100–130 palavras (2,85/s), narração adulta, DNA do `CLAUDE.md` (humor
  malandro, comparação pop, gíria leve, pergunta direta ao espectador).
- **Gancho:** 1ª frase abre o loop de curiosidade em 1,5–2 s, sem introdução/contexto, casada com o quadro mais estranho.
  Modelos: "Piscou o olho, perdeu…", "Como sumir do mapa…", "Por que esses…", "Olha o que esse cara…". Escolher 1 dos 10
  gatilhos de `edicao/ganchos_gatilhos.md` e escrever qual no roteiro.md (variar entre vídeos).
- **Final:** termina na última palavra da revelação ou emenda no gancho (loop). PROIBIDO: CTA de inscrição/like no fim,
  resumo, moral, "da próxima vez…". Partes no roteiro.md: [GANCHO] [INÍCIO] [MEIO] [FINAL] (sem [CTA]).
- Pergunta ao espectador, se houver, vai no MEIO/FINAL como parte da história, nunca como encerramento.
- Antes de escrever: escolher a faixa da matriz 70/20/10 (`edicao/matriz_702010.md`) sem repetir o molde do vídeo anterior.

# /roteiro: roteiro HISA que já nasce editável

> **Regras:** `edicao/REGRAS.md` (manual único; manda em tudo) · formatos: `edicao/inventario.json → formatos`.
> Marque no roteiro.md: `Formato: <chave>`.

Pré-requisito: tema validado por `/tema` (prova ≥ 1M, lacuna PT-BR, categoria/gatilho fortes).

## 0. Antes de escrever (`edicao/REGRAS.md` §2)
- **Explicação que dá para entender:** 1 ideia por frase; o trecho do mecanismo precisa caber num bloco 3D de 6–10 s
  Ler em voz alta: se a explicação "acaba antes de começar", cortar informação, não acelerar.
- **Fato vivo:** o que o roteiro afirma no presente ainda é verdade HOJE? Buscar notícia recente do assunto
  (vd009: o avião "atual" já tinha sido trocado em julho; o texto teve de virar "o antigo avião conseguia").
- **Cada frase pede uma imagem que existe:** quem é citado (presidente, piloto, operário) aparece de verdade;
  marque `[PESSOA: ...]` para o /clipes buscar.
- **Sem CTA no fim** (dono 24/11): nada de inscrição/like, resumo ou moral; termina na revelação ou emenda no gancho.
- **Roteiro marcado por partes:** `[GANCHO]`, `[INÍCIO]`, `[MEIO]`, `[FINAL]` no roteiro.md (a trava R0 confere; `[CTA]` reprova).

## 1. Formato (escolha pelo bruto/tema — `inventario.json → formatos`)
- **Padrão: 35–45 s = 100–130 palavras** (vd004). Risco/problema → macete técnico real → virada → emenda no gancho.
- **tiro_curto 12–15 s = 30–38 palavras** só na faixa de teste (10%): re-hook cravado aos ~6 s.
- Voz: palavras ÷ 3,15 ≈ segundos ("Minha voz", clone do dono; trava R11 ≥ 3,0 pal/s). Contar antes de entregar.
- Tom adulto (25+), sem linguagem infantil; duplo sentido só se a cena entregar a oportunidade.

## 2. Estrutura (HISA)
1. **Gancho (≤ 3 s):** quebra de expectativa, objeto nomeado em ≤ 8 palavras + lacuna. Voz em 0,0 s. Nunca entrega a resposta.
   **Ouro parcelado:** depois do gancho, a explicação vem em pedaços enquanto a ação acontece (nunca tudo de uma vez).
2. **Desmistificação:** "A maioria acha X, mas…" → motivo real.
3. **Mecanismo:** o "porquê" que vira ANIMAÇÃO 3D (`/animacao`) no meio do vídeo — escreva frases curtas e visuais
   (cada frase = um passo que dá para desenhar).
4. **Virada:** "Mas tem um porém…" ou o re-hook → `impacto_em`.
5. **Conexão/consequência** (Brasil, vida de quem assiste) — opcional, só se for forte.
6. **Loop (sem CTA):** a última frase fica suspensa ("…quando", "…vendo que") e emenda na 1ª palavra do gancho.

## 2b. Fórmulas que funcionam (Hall da Fama — conferidas em 2+ vídeos de canais grandes)
**Gancho (escolha 1):**
- **A pergunta que o espectador faria:** "Por que não colocam tela no motor do avião?" / "Por que tampa tem anel que arrebenta?"
- **Alerta/proibição:** "Nunca faça isso…", "Não cometa o erro de…" + ação física já acontecendo (tartaruga, van do Japão).
- **Afirmação impossível:** "carne crua fora da geladeira por meses", "massa viva há 90 anos", "doce sem açúcar".
- **Hipótese comum derrubada:** "Você acha que é X… mas" (terremoto no Japão → espelho falso).
- **Ação estranha no frame 0** (alguém fazendo algo desconfortável/sem sentido) e a narração explica.
**Meio:**
- **Analogia do dia a dia** para o conceito difícil ("é queratina, igual sua unha"; "válvula de mão única").
- **Duas camadas de motivo** (ex.: clima + segurança) para sustentar até o fim; a 2ª camada é a virada.
- **História concreta > conceito** (o pão feito com a mesma massa desde 1932, não "fermentação").
- Narração SEM pausa longa: cada segundo traz informação nova (o auto-cut ajuda; o texto também).
**Fim:**
- **Guardar a cena mais satisfatória/reveladora para o terço final** ("lado de dentro" do espelho, o fatiamento,
  o resultado limpo) — é o que segura até o loop.
- Prova real (teste, câmera oficial) depois da explicação.

## 3. Evidências
Todo fato com [CONFIRMADO] + fonte ou [INCERTO]. Nada [INCERTO] no texto final.

## 4. Marcações para a edição (entregar junto)
- `impacto_em`: a frase da virada (1, no máx. 2).
- `destaques`: 6–10 palavras-chave (punch + legenda amarela).
- `animacao`: quais frases viram animação e o que ela mostra (1 ideia por animação).
- `sfx_em`: só onde houver um GRÁFICO correspondente na tela (X no mito, ✓ na resposta, contador no número).
  Sem gráfico, não marque (som de função sem imagem soa aleatório e atropela a narração).
- `musica`: escolher pela tabela "Trilhas por categoria" (`edicao/biblioteca_sons.md`) a partir do GATILHO do roteiro
  (perigo → suspense rítmico; segredo → mistério; processo/máquina → phonk; dia a dia calmo → lo-fi; escala → épica;
  humor/bicho → brincalhona; virada humana → emocional; outro país → cultural gerada na hora).
- Título e descrição: ver `/publicar`.

## 5. Entregar ao dono
Texto final para a voz (em `projetos/<p>/roteiro.md`, seção "✅ TEXTO FINAL PARA A VOZ") + marcações +
duração estimada. Esperar "ok".
