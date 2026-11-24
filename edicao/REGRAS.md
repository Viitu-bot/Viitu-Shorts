# REGRAS DO VIITU SHORTS — manual único de retenção, imagem e som
> Substitui a BÍBLIA, formato.md, logica_editor.md, manual_edicao.md, biblioteca_sons.md, fontes_das_regras.md,
> formatos.md, identidade.md e reclamacoes.md (aposentados pelo dono em 24/11; histórico em `arquivo/edicao/`).
> **Números moram só em `edicao/inventario.json`** (o código lê de lá). Aqui fica o texto. Mudança de regra = o dono
> autoriza no chat → muda aqui (e o número no inventário). Base de cada regra: **D** = dono · **M** = medido.
> Em conflito com qualquer outro arquivo (skill, comentário de código), vale ESTE.

## 1. DNA do canal (inegociável) — D + M (12 vídeos editados pelo dono, medidos em 20–24/11)
- **Voz:** a do dono ("Minha voz", clone na ElevenLabs, `viitu/voz.py`), ritmo ≥ 3,0 palavras/s (alvo 3,15).
- **Humor:** malandro e adulto (25+), duplo sentido pontual quando a cena entrega; comparação pop exagerada
  ("falha na Matrix", "mini Godzilla", "dinossauro aposentado", "míssil teleguiado"). Nunca infantil.
- **Fala:** narrador que conversa ("Olha o nó que esse cara deu…", "Esquece…"); gírias leves (maluco, tiozinho,
  caboclo, paradão, a parada, todo santo dia); frases curtas; pergunta direta ao espectador.
- **Explicação de rua:** "o segredo é…", "isso aqui é atrito extremo".
- **Abertura:** flash branco→amarelo 0,2 s + DING em 2 toques com eco estéreo (`assets/sfx/abertura_viitu.wav`), no
  nível da voz. Seta vermelha no frame 0.
- **Legenda:** 1 palavra, Anton, amarela (#FFD700) ou branca, contorno preto forte, grande (30% assiste na TV);
  longe do sujeito, nunca abaixo de y 1400. Com número grande na tela, a legenda some.
- **Música "sans." (Toby Fox)** era a marca na fase do dono, mas tem dono: nunca dentro do arquivo (Content ID). Só
  como sugestão extra no `/publicar`.

## 2. Estrutura e retenção — padrão-ouro vd004 bombeiros (90,8% de retenção) — D + M
- **Duração 35–45 s**, ~100–130 palavras, ~1,8 s por cena (o vd004: 26 cenas em 45,7 s).
- Roteiro em partes rotuladas `[GANCHO]` `[INÍCIO]` `[MEIO]` `[FINAL]` (trava R0). Sem `[CTA]`.
- **Gancho (meta 78%+ continuam):** sem introdução; a 1ª frase abre o loop de curiosidade em 1,5–2 s, em cima do
  quadro mais forte do vídeo, nomeando o objeto. Nunca entrega a resposta. Sempre clipe real em movimento (R3).
- **Início:** desmistificação ("a maioria acha X, mas…"), fato com fonte, nada [INCERTO].
- **Meio:** ouro parcelado — 1 ideia por frase; aqui entram o 3D e o "mas tem um porém" (virada).
- **Final:** termina na última palavra da revelação ou emenda no gancho. PROIBIDO resumo, moral, "da próxima vez",
  CTA de inscrição/like (R0). Texto da voz fecha em conjunção suspensa ("…quando", "…vendo que"), nunca ponto final.
  O vídeo corta no último som da voz (margem `corte_final_s`).
- **Formatos** (presets e trava RF): `inventario.json → formatos`. Rodízio: não repetir o mesmo molde seguido.
- **Aleatoriedade 70/20/10:** `edicao/matriz_702010.md` (70% base provada, 20% variação do `/espiar`, 10% teste).
  Ganchos: `edicao/ganchos_gatilhos.md`. Nicho: `edicao/biblioteca_nicho.md`.

## 3. Imagem — ritmo e MOVIMENTO (zero estático)
- **Corte ≤ 3 s** (R9); troca quando a ideia/etapa muda; tomada que prende (processo hipnotizante) pode ficar até 3 s.
- **Cada fonte UMA vez**; vizinhas diferentes, perto/longe intercalado (R1, R10). ≥ 7 fontes reais por vídeo.
- **Nenhum take parado (dono 24/11):** todo take tem zoom contínuo de pelo menos 12% (`visual.zoom_min` = 1,12) e/ou
  deslocamento lateral (`visual.deriva_lateral`), inclusive clipe vertical, câmera virtual, foto, quadro inteiro e a
  cena do loop (que faz 1,12 → 1,0 e termina igual ao frame 0). Zoom manual no cenas.json abaixo do mínimo é corrigido
  para cima. O 3D nunca congela: a câmera se move o tempo todo, também entre os cortes internos.
  ⏳ No código: entra na unificação (`viitu/editar.py` `_filtro_cena` + `Short.tsx` `CorteCamera`).
- Punch-in de 4,5% nas palavras de destaque; tremida em todo som de impacto; zoom blur + flash na virada.
- **A ação acontece NA palavra:** "decola" → rodas saindo do chão nesse instante. Ajustar o `inicio` do clipe para
  isso (imagem e som caem juntos na palavra — ver §4).
- **Clipe:** colorido/HD do lugar real antes de arquivo P&B (arquivo só como prova); ≥ 720 px no lado menor, nítido,
  em movimento, sem logo/legenda/rosto de tiktoker/tela de app (R4, triagem); sujeito dentro do recorte 9:16;
  pessoa real quando a frase cita alguém. Fotos: no máximo 2, nunca no gancho, nunca seguidas (R5).
- **3D:** só para o invisível/por dentro/impossível de filmar; UM bloco contínuo de 6–10 s no meio (R2), vistas de
  ≤ 3,5 s; física certa; som próprio em cada evento. Nunca no gancho nem para tapar falta de clipe.
- **Loop:** a última cena é o mesmo clipe e segundo da primeira (R6).
- **Seta/círculo:** alvo MEDIDO no quadro; a ponta encosta na borda do alvo.
- Fontes de clipe (ordem): busca web TikTok/X/Instagram + `yt-dlp` → Pixabay/Pexels → Internet Archive (só prova) →
  vidIQ → link do dono.

## 4. Som — camadas fixas (níveis em `inventario.json → mix_db`, dB relativos à voz)
| Camada | Nível | Quando |
|---|---|---|
| Voz (tratamento leve "suave") | 0 | sempre na frente |
| Música (trilha própria licenciada, SEMPRE dentro do arquivo) | −16 sob a fala, sobe nas pausas, cresce na virada e no fim | o vídeo todo |
| **Ambiente contínuo** (vento/mar/bunker do lugar) | −30 | por baixo de TUDO, do 0 ao fim ⏳ |
| Som de lugar por cena (foley em 2 camadas, corte J/L) | −20 | cada cena |
| **Transição** | whoosh −14 · clique −11 | **TODA troca de cena**; clique no lugar do whoosh quando há outro efeito a < 1 s ⏳ |
| Efeito de ação | −10 a −5 | **na palavra-chave** (atirava, coice, avião…); pode haver mais de 1 a cada 3 s (dono 24/11) ⏳ |
| Riser → vácuo → boom | −7 / −4 | só na virada |
| Abertura (ding) | 0 | frame 0 |
- Só sons de `biblioteca_sfx/` e da Sonniss/ElevenLabs. PROIBIDO desenho, meme, boing, buzina, risada, pop agudo.
- Todo efeito passa no OUVIDO (`viitu.ouvir`, earshot): som que não soa como o pedido barra o render.
- O som apoia a história: nunca por cima de palavra (só o boom da virada), voz sempre inteligível.
- ⏳ = regra nova de 24/11 ainda não implementada no código; entra na unificação (um motor de som só, que gera a
  prévia por partes E o arquivo final — hoje são dois: `Short.tsx` na prévia e `som_final.py` no final).

## 5. Travas e conferência (nada vai ao dono sem isto)
- `viitu.montagem` (R0 roteiro · R1 repetição · R2 3D em bloco · R3 gancho · R4 qualidade · R5 fotos · R6 loop ·
  R7 cena longa · R8 som · R9 ritmo · R10 parecidas · R11 voz lenta · RF formato) → `viitu.decupagem` (folha + ouvido)
  → `viitu.partes` (parte por parte) → render → `viitu.entrega` LIBERADA → olhar a prancha.
- Encadear com falha que para: `set -o pipefail; montagem && editar && render && entrega`.
- **Conferência que a máquina não faz (prancha 1 quadro/s):** em 1 s dá para entender cada cena? a ação cai na
  palavra? a cena faz SENTIR (perigo, escala)? 3D com física certa e som? nenhum logo/tarja preta/marca d'água?
  sujeito dentro do recorte? algum take parado? alguma troca sem som?
- O dono é o ouvido e o olho final: se ele diz que não encaixa, não encaixa.

## 6. Regras que nunca quebram
1. Números só da YouTube Data API ou print do dono; vídeo citado passa por `python3 -m viitu.provar`.
2. Chaves nunca no chat; dados pessoais do dono nunca vão para fora.
3. Direitos: roteiro próprio, áudio de terceiro desligado, crédito dos @, `viitu.direitos` sem ❌.
4. Sem achismo: número novo só com base (D ou M) escrita aqui.
