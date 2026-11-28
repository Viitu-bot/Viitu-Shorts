# Faxina das regras — 28/11/2026 16:25

[respondido por gemini-3.6-flash, reserva]
Aqui está a lista única e unificada com todas as contradições encontradas nas regras do canal, consolidando as duas auditorias sem repetições.

---

### 1. Duração Alvo do Vídeo
* **Contradições nos arquivos:**
  * `edicao/BIBLIA.md` → §0 (24/11/2026): *"duração 35–45 s"*
  * `edicao/BIBLIA.md` → §0b (26/11/2026): *"Duração: 25–30 s NO MÁXIMO."*
  * `edicao/BIBLIA.md` → §0c (26/11/2026): *"Duração ágil: alvo 12–18 s. O teto de 30 s (0b) só quando o tema realmente exige"*
  * `CLAUDE.md` → DNA: *"alvo 12–18 s, teto 30 s só se o tema exigir (dono 26/11)"*
  * `edicao/especificacao.json` → `_formato_dono_17_11`: *"Tiro Curto 12–15 s ... e Bastidor 20–28 s"*
* **Regra vigente:** `edicao/BIBLIA.md` (§0c de 26/11/2026) e `CLAUDE.md`. Alvo de **12–18 segundos**, com teto máximo de 30 segundos.
* **Recomendação:** Apagar os trechos antigos que citam "35–45 s" (`BIBLIA.md` §0) e "25–30 s" (`BIBLIA.md` §0b / `reclamacoes.md` item 30), atualizando `especificacao.json` para o alvo de 12–18 s (teto 30 s).
* **Precisa de decisão do dono?** **NÃO** (decisão tomada pelo dono em 26/11 registrada no §0c e no `CLAUDE.md`).

---

### 2. Trilha Sonora (Embutida no Arquivo vs. Adicionada pelo App)
* **Contradições nos arquivos:**
  * `edicao/BIBLIA.md` → §4: *"Música conhecida do nicho (com direitos) = adicionada pelo dono no app do YouTube; nesse caso o arquivo vai sem trilha..."*
  * `edicao/reclamacoes.md` → Item 18 (20/11/2026): *"A música SEMPRE vai dentro do arquivo (trilha própria licenciada)..."*
  * `CLAUDE.md` → Som: *"Música 'sans.' (Toby Fox) em 7/12 (só pelo app). No arquivo: biblioteca de música de JOGO ANTIGO livre"*
  * `assets/musica/jogo_antigo/LEIA.md` (27/11/2026): *"Trilha no arquivo sempre (−16 na mixagem)... Trilha ORIGINAL de jogo ... essa só pelo app"*
* **Regra vigente:** `assets/musica/jogo_antigo/LEIA.md` (27/11/2026) e `CLAUDE.md` (07/12/2026). A edição sai com a trilha livre de jogo antigo **embutida no arquivo**. Músicas de terceiros (como "sans.") são inseridas opcionalmente pelo dono via app.
* **Recomendação:** Remover do §4 da `edicao/BIBLIA.md` a instrução antiga de exportar o vídeo "sem trilha".
* **Precisa de decisão do dono?** **NÃO** (padrão fixado em 27/11 no `LEIA.md` e 07/12 no `CLAUDE.md`).

---

### 3. Volume da Trilha Sonora na Mixagem (dB)
* **Contradições nos arquivos:**
  * `CLAUDE.md` → Som: *"música −16 na mixagem (audível sob a voz contínua)"*
  * `edicao/BIBLIA.md` → §0 (24/11/2026): *"música −16 na mixagem"*
  * `edicao/BIBLIA.md` → §4: *"−10 a −12 dB sob a voz (no celular, −17 some)"*
  * `edicao/reclamacoes.md` → Item 20 (24/11/2026): *"trilha −22 a −26"* e Item 25: *"música −20"*
  * `edicao/especificacao.json` → `mix_db`: `"musica_fala": -16`
  * `biblioteca_sfx/LEIA.md`: *"trilha −22 a −26 dB sob a voz"*
* **Regra vigente:** `edicao/especificacao.json` (`_mix_24_11d`), `CLAUDE.md` e `edicao/BIBLIA.md` (§0). Volume fixado em **−16 dB na mixagem**.
* **Recomendação:** Corrigir `biblioteca_sfx/LEIA.md` (que mantém −22 a −26 dB) e o §4 da `BIBLIA.md` (que cita −10 a −12 dB), alinhando todos em −16 dB.
* **Precisa de decisão do dono?** **NÃO** (resolvido na atualização `_mix_24_11d` de 24/11/2026 após o relato no vd017).

---

### 4. Volume dos Efeitos Sonoros / SFX (dB)
* **Contradições nos arquivos:**
  * `CLAUDE.md` → Som: *"efeitos −10 a −5 dB"*
  * `edicao/BIBLIA.md` → §0 (24/11/2026): *"efeitos −10 a −5 dB"*
  * `edicao/reclamacoes.md` → Item 20 (*"efeitos −12/−18"*) e Item 21 (*"efeitos −8/−3"*)
  * `biblioteca_sfx/LEIA.md`: *"efeitos −12 a −18 dB"*
  * `edicao/especificacao.json` → `mix_db`: `"sfx_min": -10, "sfx_max": -5`
* **Regra vigente:** `edicao/especificacao.json` e `CLAUDE.md` (24/11/2026). Faixa geral de **−10 a −5 dB**.
* **Recomendação:** Corrigir `biblioteca_sfx/LEIA.md` (que cita a faixa antiga de −12 a −18 dB) para −10 a −5 dB.
* **Precisa de decisão do dono?** **NÃO** (definido no `especificacao.json` e no `CLAUDE.md` em 24/11/2026).

---

### 5. Estrutura e Presença de CTA (Call to Action) no Final
* **Contradições nos arquivos:**
  * `edicao/BIBLIA.md` → §1 (Tabela): *"5. CTA INTERATIVO ... OBRIGATÓRIO; nunca a mesma frase de outro vídeo"*
  * `edicao/BIBLIA.md` → §0 (24/11/2026): *"O CTA de inscrição/like no fim sai (substitui o 'CTA obrigatório' do §1); proibido resumo/moral."*
  * `CLAUDE.md` → Final: *"PROIBIDO resumo, moral, 'da próxima vez…', CTA de inscrição/like no fim"*
  * `edicao/reclamacoes.md` → Item 7/19: *"sem CTA por padrão; quando houver, elogio contextual..."*
  * `edicao/especificacao.json` → `visual`: `"cta": "nenhum explícito na maioria (19/35); loop no lugar"`
* **Regra vigente:** `edicao/BIBLIA.md` (§0 de 24/11/2026) e `CLAUDE.md`. **PROIBIDO CTA no final**.
* **Recomendação:** Alterar a linha 5 da tabela no §1 da `BIBLIA.md` para remover o termo "OBRIGATÓRIO".
* **Precisa de decisão do dono?** **NÃO** (regra de remoção fixada no §0 da `BIBLIA.md` em 24/11/2026).

---

### 6. Frequência de Efeitos Sonoros e Whooshes
* **Contradições nos arquivos:**
  * `edicao/BIBLIA.md` → §0 (24/11/2026): *"máx. 1 efeito de AÇÃO a cada 3 s + whoosh suave em toda troca"*
  * `biblioteca_sfx/LEIA.md`: *"no máx. 1 efeito a cada 3 s"*
  * `edicao/reclamacoes.md` → Item 28: *"whoosh suave em toda troca (≥ 1 s de outro efeito, ≥ 1,4 s entre whooshes...)"*
  * `edicao/especificacao.json` → `_whoosh_27_11`: *"whoosh em TODA troca ... só pula se um efeito cair a menos de 0,3 s do corte. Efeito de AÇÃO continua 1 a cada 3 s."*
  * `CLAUDE.md` → Som: *"Máx. 1 efeito de AÇÃO a cada 3 s; whoosh (−14) em TODA troca..."*
* **Regra vigente:** `CLAUDE.md` e `edicao/especificacao.json` (`_whoosh_27_11` de 27/11/2026). Whoosh entra em **toda troca** (só pula se houver efeito a menos de 0,3 s); o limite de 3 s aplica-se **apenas a efeitos de AÇÃO**.
* **Recomendação:** Limpar do `biblioteca_sfx/LEIA.md` e do `reclamacoes.md` (item 28) as limitações antigas de "≥ 1 s" e "≥ 1,4 s".
* **Precisa de decisão do dono?** **NÃO** (decidido pelo dono no chat em 27/11/2026).

---

### 7. Voz da Narração
* **Contradições nos arquivos:**
  * `CLAUDE.md` → Voz: *"OTTO na ElevenLabs (viitu/voz.py, padrão de novo desde 28/11 — dono: o clone 'Minha voz' tinha eco...)"*
  * `edicao/reclamacoes.md` → Item 32 (28/11/2026): *"voz padrão volta ao Otto"*
  * `edicao/identidade.md` → §0: Cita análises da voz do dono ("Minha edição").
* **Regra vigente:** `CLAUDE.md` e `edicao/reclamacoes.md` (item 32 de 28/11/2026). Voz oficial **OTTO** (ElevenLabs).
* **Recomendação:** Atualizar a nota em `edicao/identidade.md` garantindo a indicação explícita de que a narração usa a voz OTTO.
* **Precisa de decisão do dono?** **NÃO** (retorno à voz OTTO decidido pelo dono em 28/11/2026 devido a eco no clone).

---

### 8. Ritmo da Fala (Palavras por Segundo)
* **Contradições nos arquivos:**
  * `edicao/BIBLIA.md` → §0 (24/11/2026): *"voz ≥ 3,0 palavras/s"*
  * `edicao/BIBLIA.md` → §0b (26/11/2026): *"~75–90 palavras a ~3,0 palavras/s"*
  * `edicao/fontes_das_regras.md` → Atualização 24/11: *"2,85 palavras/s (medido no vd004)"* e *"≥ 3,0 pal/s (alvo 3,15)"*
  * `CLAUDE.md` → Padrão-ouro: *"130 palavras (2,85/s)"* e em Som: *"voz ≥ 3,0 palavras/s"*
* **Regra vigente:** `edicao/BIBLIA.md` (§0 e §0b) e `fontes_das_regras.md`. Mínimo de **≥ 3,0 palavras/s** (alvo 3,15/s).
* **Recomendação:** Esclarecer no `CLAUDE.md` que 2,85/s é apenas um dado histórico de medição do vídeo vd004, mantendo a regra oficial em ≥ 3,0 pal/s.
* **Precisa de decisão do dono?** **NÃO** (regra estabelecida em 24/11/2026 após reclamação do vd016).

---

### 9. Posicionamento Vertical (Y) e Cor da Legenda
* **Contradições nos arquivos:**
  * `edicao/BIBLIA.md` → §2: *"Legenda 1 palavra, amarelo ouro #FFD700, contorno preto forte, terço superior."*
  * `CLAUDE.md`: *"legenda de 1 palavra... terço superior"*
  * `edicao/especificacao.json` → `visual`: `"legenda_y": 560, "legenda_y_alternativa": 1250`
  * `edicao/identidade.md` → §0: *"legenda 1 palavra amarela/branca, contorno preto, centro-baixo"*
  * `edicao/reclamacoes.md` → Item 34: reclamação no vd022 sobre a posição inferior (y=1250) ser tampada pela interface do YouTube.
* **Regra vigente:** `edicao/BIBLIA.md` (§2) e `CLAUDE.md`. Legenda no **terço superior** (Y=560).
* **Recomendação:** Remover `"legenda_y_alternativa": 1250` do `especificacao.json` e atualizar `identidade.md`, deixando apenas o terço superior.
* **Precisa de decisão do dono?** **NÃO** (o problema de interface coberta no rodapé expôs a necessidade do terço superior Y=560).

---

### 10. Tempo por Cena e Ritmo de Corte
* **Contradições nos arquivos:**
  * `CLAUDE.md`: *"corte a cada 2–3 s"*
  * `edicao/BIBLIA.md` → §0 (24/11/2026): *"ritmo de ~1,8 s por cena... corte ≤ 3 s"* (trava R9)
  * `edicao/especificacao.json`: `"seg_por_cena_alvo": 1.5, "max_cena": 2.0`
  * `edicao/retencao_storyboard.md` (26/11/2026): *"quebra de padrão a cada 1,5–2 s"* e *"cortes de 1–2,5 s"*
* **Regra vigente:** `edicao/retencao_storyboard.md` e `edicao/BIBLIA.md` (§0, trava R9).
* **Recomendação:** Alterar `"max_cena": 2.0` para `3.0` no `edicao/especificacao.json` para eliminar o conflito com a trava R9 da `BIBLIA.md`, padronizando o ritmo de cortes em **1,5 a 3,0 s**.
* **Precisa de decisão do dono?** **NÃO** (trava teto de corte ≤ 3 s já estabelecida na R9 da `BIBLIA.md` de 24/11/2026).

---
## Auditoria 1
[respondido por gemini-3.6-flash, reserva]
Aqui está a **Faxina das Regras**, com todas as contradições e duplicações encontradas nos arquivos do canal, ordenadas da que mais afeta a produção do vídeo para a que menos afeta.

---

### 1. ASSUNTO: Duração Alvo do Vídeo
* **`edicao/BIBLIA.md` → §0 (24/11/2026):** *"duração 35–45 s"*
* **`edicao/BIBLIA.md` → §0b (26/11/2026):** *"Duração: 25–30 s NO MÁXIMO."*
* **`edicao/BIBLIA.md` → §0c (26/11/2026, 2ª):** *"Duração ágil: alvo 12–18 s. O teto de 30 s (0b) só quando o tema realmente exige"*
* **`CLAUDE.md` → DNA:** *"alvo 12–18 s, teto 30 s só se o tema exigir (dono 26/11)"*
* **`edicao/especificacao.json` → `_formato_dono_17_11`:** *"Tiro Curto 12–15 s ... e Bastidor 20–28 s"*
* **Vigente:** **`edicao/BIBLIA.md` (§0c de 26/11/2026)** e **`CLAUDE.md`**. Alvo **12–18 segundos**, teto máximo de 30 segundos.
* **O que fazer:** Apagar a referência de "35–45 s" do §0 da BÍBLIA e uniformizar os arquivos secundários (`especificacao.json`) para a faixa 12–18 s (teto 30 s).

---

### 2. ASSUNTO: Trilha Sonora (Embutida no Arquivo vs. Adicionada pelo App)
* **`edicao/BIBLIA.md` → §4:** *"Música conhecida do nicho (com direitos) = adicionada pelo dono no app do YouTube; nesse caso o arquivo vai sem trilha..."*
* **`edicao/reclamacoes.md` → Item 18 (20/11/2026):** *"A música SEMPRE vai dentro do arquivo (trilha própria licenciada)... Música conhecida ('sans.') ... fica só como sugestão EXTRA no /publicar, nunca no lugar da trilha"*
* **`CLAUDE.md` → Som:** *"Música 'sans.' (Toby Fox) em 7/12 (só pelo app). No arquivo: biblioteca de música de JOGO ANTIGO livre"*
* **`assets/musica/jogo_antigo/LEIA.md`:** *"Trilha no arquivo sempre (−16 na mixagem)... Trilha ORIGINAL de jogo ... essa só pelo app"*
* **Vigente:** **`assets/musica/jogo_antigo/LEIA.md` (27/11/2026)** e **`CLAUDE.md` (07/12/2026)**. Toda edição sai com trilha de jogo antigo livre **embutida no arquivo**. Músicas protegidas/famosas (como "sans.") só são indicadas no `/publicar` para inserção opcional via app.
* **O que fazer:** Remover o trecho antigo do §4 da BÍBLIA que manda exportar o arquivo "sem trilha".

---

### 3. ASSUNTO: Volume da Música na Mixagem (dB)
* **`CLAUDE.md` → Som:** *"música −16 na mixagem (audível sob a voz contínua)"*
* **`edicao/BIBLIA.md` → §0 (24/11/2026):** *"música −16 na mixagem"*
* **`edicao/BIBLIA.md` → §4:** *"−10 a −12 dB sob a voz (no celular, −17 some)"*
* **`edicao/reclamacoes.md` → Item 20 (24/11/2026):** *"trilha −22 a −26"*
* **`edicao/reclamacoes.md` → Item 25 (24/11/2026):** *"música −20"*
* **`edicao/especificacao.json` → `mix_db` & `_mix_24_11d`:** `"musica_fala": -16` e *`"música −16 na mixagem, abaixamento 2,5"`*
* **`biblioteca_sfx/LEIA.md`:** *"trilha −22 a −26 dB sob a voz"*
* **Vigente:** **`edicao/especificacao.json` (`_mix_24_11d` de 24/11/2026)**, **`CLAUDE.md`** e **`assets/musica/jogo_antigo/LEIA.md`**. Volume fixado em **−16 dB na mixagem** sob a voz contínua.
* **O que fazer:** Atualizar `biblioteca_sfx/LEIA.md` (que ainda cita −22 a −26 dB) e ajustar o §4 da BÍBLIA (que cita −10 a −12 dB).

---

### 4. ASSUNTO: Volume dos Efeitos Sonoros / SFX (dB)
* **`CLAUDE.md` → Som:** *"efeitos −10 a −5 dB"*
* **`edicao/BIBLIA.md` → §0 (24/11/2026):** *"efeitos −10 a −5 dB"*
* **`edicao/reclamacoes.md` → Item 20 (24/11/2026):** *"efeitos −12/−18"*
* **`edicao/reclamacoes.md` → Item 21 (24/11/2026):** *"efeitos −8/−3"*
* **`biblioteca_sfx/LEIA.md`:** *"efeitos −12 a −18 dB"*
* **`edicao/especificacao.json` → `mix_db`:** `"sfx_min": -10, "sfx_max": -5` (com whoosh a −14, pop a −11, boom a −1, hit a −7)
* **Vigente:** **`edicao/especificacao.json`** e **`CLAUDE.md` (24/11/2026)**. A faixa geral é **−10 a −5 dB**, valendo a tabela específica do JSON para cada tipo de som.
* **O que fazer:** Corrigir a instrução em `biblioteca_sfx/LEIA.md` (que ainda traz a faixa antiga de −12 a −18 dB) e remover os relatos de testes do `reclamacoes.md` da busca de regras.

---

### 5. ASSUNTO: Presença e Estrutura de CTA (Call to Action)
* **`edicao/BIBLIA.md` → §1 (Tabela de Roteiro):** *"5. CTA INTERATIVO ... OBRIGATÓRIO; nunca a mesma frase de outro vídeo"*
* **`edicao/BIBLIA.md` → §0 (24/11/2026):** *"O CTA de inscrição/like no fim sai (substitui o 'CTA obrigatório' do §1); proibido resumo/moral."*
* **`CLAUDE.md` → Final:** *"PROIBIDO resumo, moral, 'da próxima vez…', CTA de inscrição/like no fim"*
* **`edicao/reclamacoes.md` → Item 7:** *"sem CTA por padrão; quando houver, elogio contextual..."*
* **`edicao/especificacao.json` → `visual`:** `"cta": "nenhum explícito na maioria (19/35); loop no lugar"`
* **Vigente:** **`edicao/BIBLIA.md` (§0 de 24/11/2026)** e **`CLAUDE.md`**. **PROIBIDO CTA de inscrição/like no final**. O vídeo encerra direto na revelação ou emenda no loop.
* **O que fazer:** Alterar a linha 5 da tabela da BÍBLIA (§1) para marcar "CTA no final" como PROIBIDO/Removido, evitando que o modelo leia a tabela antiga e insira CTA.

---

### 6. ASSUNTO: Frequência de Efeitos Sonoros e Whooshes
* **`edicao/BIBLIA.md` → §0 (24/11/2026):** *"máx. 1 efeito de AÇÃO a cada 3 s + whoosh suave em toda troca"*
* **`biblioteca_sfx/LEIA.md`:** *"no máx. 1 efeito a cada 3 s"* (aplica a regra a transições na tabela)
* **`edicao/especificacao.json` → `_whoosh_27_11`:** *"whoosh em TODA troca ... só pula se um efeito cair a menos de 0,3 s do corte. Efeito de AÇÃO continua 1 a cada 3 s."*
* **`CLAUDE.md` → Som:** *"Máx. 1 efeito de AÇÃO a cada 3 s; whoosh (−14) em TODA troca..."*
* **Vigente:** **`CLAUDE.md`** e **`edicao/especificacao.json` (`_whoosh_27_11` de 27/11/2026)**. Whoosh entra em **toda troca de cena**; a trava de "1 a cada 3 s" aplica-se **apenas a efeitos de AÇÃO/impacto**.
* **O que fazer:** Corrigir a tabela do `biblioteca_sfx/LEIA.md` para não limitar transições/whooshes a 3 segundos.

---

### 7. ASSUNTO: Voz da Narração
* **`CLAUDE.md` → Voz:** *"OTTO na ElevenLabs (viitu/voz.py, padrão de novo desde 28/11 — dono: o clone 'Minha voz' tinha eco...)"*
* **`edicao/reclamacoes.md` → Item 32 (28/11/2026):** *"voz padrão volta ao Otto"*
* **`edicao/identidade.md` → §0:** Cita transcrições e análises da voz do dono ("Minha edição").
* **Vigente:** **`CLAUDE.md`** e **`edicao/reclamacoes.md` (28/11/2026)**. A voz oficial do canal é a voz **OTTO** (ElevenLabs).
* **O que fazer:** Manter a nota no `identidade.md` apenas como histórico do estilo de fala/gírias, deixando explícito que a geração técnica usa a voz OTTO.

---

### 8. ASSUNTO: Ritmo da Fala / Palavras por Segundo
* **`edicao/BIBLIA.md` → §0 (24/11/2026):** *"≥ 3,0 palavras/s"*
* **`edicao/BIBLIA.md` → §0b (26/11/2026):** *"~75–90 palavras a ~3,0 palavras/s"*
* **`edicao/fontes_das_regras.md` → Atualização 24/11:** *"2,85 palavras/s (medido no vd004)"* e *"≥ 3,0 pal/s (alvo 3,15)"*
* **`CLAUDE.md` → Padrão-ouro:** *"130 palavras (2,85/s)"* e em **Som:** *"voz ≥ 3,0 palavras/s"*
* **Vigente:** **`edicao/BIBLIA.md` (§0 e §0b)** e **`CLAUDE.md` (Som)**. O valor do vd004 (2,85 pal/s) é dado histórico; a regra ativa para vídeos novos é **≥ 3,0 palavras/segundo** (alvo 3,0 a 3,15).
* **O que fazer:** Clarificar no `CLAUDE.md` que 2,85/s foi a medição do vídeo antigo (vd004), mas a regra oficial atual é ≥ 3,0/s.

---

### 9. ASSUNTO: Posição Vertical (Y) e Cor da Legenda
* **`edicao/BIBLIA.md` → §2:** *"Legenda 1 palavra, amarelo ouro #FFD700, contorno preto forte, terço superior."*
* **`edicao/especificacao.json` → `visual`:** `"legenda_y": 560, "legenda_y_alternativa": 1250`
* **`edicao/identidade.md` → §0:** *"legenda 1 palavra amarela/branca, contorno preto, centro-baixo"*
* **Vigente:** **`edicao/BIBLIA.md` (24/11/2026)** e **`edicao/especificacao.json`**. Legenda no **terço superior** (Y=560), 1 palavra por vez, amarela `#FFD700`. O trecho de `identidade.md` refere-se ao histórico antigo do dono no CapCut.
* **O que fazer:** Atualizar o texto em `edicao/identidade.md` para evitar confusão entre o histórico anterior e a regra atual de posicionamento no terço superior.

## Auditoria 2
[respondido por gemini-3.6-flash, reserva]
Aqui está a **faxina das regras do canal**, ordenada do impacto **MAIOR** (estrutura, som e entrega que mudam diretamente a edição) para o **MENOR** (parâmetros secundários de ritmo/layout).

---

### 1. DURAÇÃO DO VÍDEO
* **arquivo A:** `edicao/BIBLIA.md` (§0, 24/11/2026) → *"duração 35–45 s"*
* **arquivo B:** `edicao/BIBLIA.md` (§0b, 26/11/2026) → *"Duração: 25–30 s NO MÁXIMO."*
* **arquivo C:** `edicao/BIBLIA.md` (§0c, 26/11/2026, 2ª) → *"Duração ágil: alvo 12–18 s. O teto de 30 s (0b) só quando o tema realmente exige"*
* **arquivo D:** `CLAUDE.md` → *"alvo 12–18 s, teto 30 s só se o tema exigir"*
* **Qual parece mais recente/vigente:** `edicao/BIBLIA.md` (§0c, 26/11/2026) e `CLAUDE.md`. A base é o dado real do Studio do dono: os 4 vídeos com mais de 20 mil views tinham menos de 16 s e retenção acima de 105% (`edicao/BIBLIA.md` §0c).
* **O que fazer:** Atualizar o texto antigo da `edicao/BIBLIA.md` (§0 e §0b) e da `edicao/reclamacoes.md` (item 30), removendo as menções a 35–45 s e 25–30 s como padrão, fixando o **alvo em 12–18 s (teto 30 s)**.

---

### 2. MÚSICA EMBUTIDA NO VÍDEO VS. MÚSICA PELO APP DO YOUTUBE
* **arquivo A:** `edicao/BIBLIA.md` (§4) → *"Música = a que os canais do nicho usam... adicionada pelo dono no app do YouTube ao postar... O arquivo sai sem trilha"*
* **arquivo B:** `edicao/reclamacoes.md` (item 18, 20/11/2026) → *"A música SEMPRE vai dentro do arquivo (trilha própria licenciada...)"*
* **arquivo C:** `assets/musica/jogo_antigo/LEIA.md` (27/11/2026) → *"Trilha no arquivo sempre (−16 na mixagem, audível sob a voz)... Trilha ORIGINAL de jogo (sans...) tem dono e dá Content ID — essa só pelo app"*
* **Qual parece mais recente/vigente:** `assets/musica/jogo_antigo/LEIA.md` (27/11/2026) e `edicao/reclamacoes.md` (item 18).
* **O que fazer:** Corrigir a `edicao/BIBLIA.md` (§4), removendo a instrução de enviar vídeo sem trilha. O vídeo **SEMPRE sai com a trilha 8-bit própria embutida no render**; se o dono quiser usar música famosa ("sans."), ele troca no app por conta própria.

---

### 3. VOLUMES DE ÁUDIO (MIXAGEM DA TRILHA E EFEITOS EM dB)
* **arquivo A:** `biblioteca_sfx/LEIA.md` (24/11/2026) → *"efeitos −12 a −18 dB e trilha −22 a −26 dB sob a voz"*
* **arquivo B:** `edicao/BIBLIA.md` (§0, 24/11/2026) → *"efeitos −10 a −5 dB e música −16 na mixagem"*
* **arquivo C:** `CLAUDE.md` → *"música −16 na mixagem... efeitos −10 a −5 dB"*
* **arquivo D:** `edicao/especificacao.json` → `"musica_fala": -16`, `"sfx_min": -10`, `"sfx_max": -5` (com notas históricas em `_ajuste_24_11` citando −22 a −26 dB)
* **Qual parece mais recente/vigente:** `CLAUDE.md`, `edicao/BIBLIA.md` (§0) e `edicao/especificacao.json` (`_mix_24_11d`). A base é a reclamação do dono no vd017: *"a música não deu nem pra ouvir"*.
* **O que fazer:** Atualizar o arquivo `biblioteca_sfx/LEIA.md` e apagar os textos antigos de `edicao/especificacao.json`, unificando a regra: **música em −16 dB e efeitos entre −10 dB e −5 dB**.

---

### 4. CTA (CHAMADA PRA AÇÃO) NO FINAL DO VÍDEO
* **arquivo A:** `edicao/BIBLIA.md` (§1 - tabela) → *"5. CTA INTERATIVO ... OBRIGATÓRIO"*
* **arquivo B:** `edicao/BIBLIA.md` (§0, 24/11/2026) → *"O CTA de inscrição/like no fim sai (substitui o 'CTA obrigatório' do §1); proibido resumo/moral."*
* **arquivo C:** `edicao/reclamacoes.md` (item 7 e 19) → *"sem CTA por padrão... final na revelação ou emendando no gancho"*
* **Qual parece mais recente/vigente:** `edicao/BIBLIA.md` (§0, 24/11/2026) e `CLAUDE.md`.
* **O que fazer:** Alterar a tabela do §1 em `edicao/BIBLIA.md` para remover a palavra "OBRIGATÓRIO" da linha 5, garantindo que a regra reflita que o vídeo corta direto na última palavra da revelação ou no loop narrativo, sem CTA no final.

---

### 5. POSIÇÃO VERTICAL DA LEGENDA
* **arquivo A:** `edicao/BIBLIA.md` (§2) → *"legenda 1 palavra... terço superior."*
* **arquivo B:** `CLAUDE.md` → *"legenda de 1 palavra... terço superior"*
* **arquivo C:** `edicao/identidade.md` → *"legenda 1 palavra... centro-baixo"*
* **arquivo D:** `edicao/especificacao.json` → `"legenda_y": 560`, `"legenda_y_alternativa": 1250`
* **Qual parece mais recente/vigente:** `edicao/BIBLIA.md` (§2) e `CLAUDE.md` (terço superior). A base é a reclamação do vd022 (`edicao/reclamacoes.md` item 34): o rodapé (y=1250) fica tampado pela interface do YouTube (nome/descrição).
* **O que fazer:** Corrigir `edicao/identidade.md` e remover `"legenda_y_alternativa": 1250` do `edicao/especificacao.json`, padronizando **apenas o terço superior**.

---

### 6. FREQUÊNCIA E INTERVALO DOS WHOOSHES E EFEITOS
* **arquivo A:** `edicao/reclamacoes.md` (item 28) → *"whoosh suave em toda troca (≥ 1 s de outro efeito, ≥ 1,4 s entre whooshes...)"*
* **arquivo B:** `CLAUDE.md` → *"whoosh (−14) em TODA troca... só pula se um efeito cair a < 0,3 s do corte"*
* **arquivo C:** `edicao/especificacao.json` → `"whoosh_longe_de_efeito_s": 0.3`, `"whoosh_intervalo_s": 0.0`
* **Qual parece mais recente/vigente:** `CLAUDE.md` e `edicao/especificacao.json` (`_whoosh_27_11`, decisão do dono no chat em 27/11/2026).
* **O que fazer:** Atualizar a `edicao/reclamacoes.md` (item 28), apagando as limitações antigas de "≥ 1 s" e "≥ 1,4 s" e mantendo a trava atual de 0,3 s.

---

### 7. RITMO DA VOZ (PALAVRAS POR SEGUNDO)
* **arquivo A:** `CLAUDE.md` → *"vd004 bombeiros ... 130 palavras (2,85/s)"*
* **arquivo B:** `edicao/BIBLIA.md` (§0, 24/11/2026) → *"voz ≥ 3,0 palavras/s"*
* **arquivo C:** `edicao/fontes_das_regras.md` → *"Ritmo da voz: ≥ 3,0 pal/s (alvo 3,15)"*
* **Qual parece mais recente/vigente:** `edicao/BIBLIA.md` (§0, 24/11/2026) e `edicao/fontes_das_regras.md`. A base é a reclamação do dono no vd016 (`edicao/reclamacoes.md` item 21): *"ficou lento"*.
* **O que fazer:** Manter a citação do vd004 (2,85/s) apenas como registro histórico de medição e padronizar o requisito em todos os arquivos como **mínimo de 3,0 pal/s (alvo 3,15/s)**.

---

### 8. TEMPO MÁXIMO E ALVO POR CENA (RITMO DE CORTE)
* **arquivo A:** `CLAUDE.md` → *"corte a cada 2–3 s"*
* **arquivo B:** `edicao/BIBLIA.md` (§0, 24/11/2026) → *"ritmo de ~1,8 s por cena... corte ≤ 3 s"*
* **arquivo C:** `edicao/especificacao.json` → `"seg_por_cena_alvo": 1.5`, `"max_cena": 2.0`
* **arquivo D:** `edicao/retencao_storyboard.md` (26/11/2026) → *"quebra de padrão a cada 1,5–2 s" / "cortes de 1–2,5 s"*
* **Qual parece mais recente/vigente:** `edicao/retencao_storyboard.md` (26/11/2026) e `edicao/BIBLIA.md` (trava R9: corte ≤ 3 s).
* **O que fazer:** Atualizar `edicao/especificacao.json` alterando `"max_cena": 2.0` para `3.0` (para não conflitar com a trava R9 da BÍBLIA), padronizando a recomendação de ritmo em **1,5 a 3,0 s por cena**.