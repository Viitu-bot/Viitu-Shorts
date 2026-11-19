# A PLANTA DO VÍDEO VIITU (formato técnico — obedece a edicao/BIBLIA.md)
Um arquivo só que diz, batida por batida, o que o ROTEIRO fala, o que a IMAGEM mostra (B-roll ou 3D) e o que o SOM faz.
Todas as skills seguem esta planta; as travas `viitu.montagem` e `viitu.entrega` cobram o que dá para medir.
Base: HISA 2.0 do dono + engenharia reversa de A vida é uma maravilha, Zack D. Films, KSO, GeneralTV (logica_editor.md)
+ todas as reclamações do dono (reclamacoes.md).

## 1. Bastidor (20–28 s, 50–70 palavras) — engenharia, máquina, processo, "motivo oculto"
| Batida | Tempo | Palavras | ROTEIRO (o que fala) | IMAGEM | SOM |
|---|---|---|---|---|---|
| **1. GANCHO** | 0–3 s | ~8 | afirmação impossível / pergunta que o espectador faria / hipótese derrubada. Nomeia o objeto. Nunca entrega a resposta | **clipe real** do sujeito EM MOVIMENTO, 1 sujeito só, a ação cai na palavra; seta no frame 0; ≥ 720p | ding + flash no 0,0 s; som de ação do sujeito ALTO (−2 a −4 dB); música entra junto |
| **2. CONTEXTO / RISCO** | 3–9 s | ~15 | por que isso importa: o problema, o perigo, quem depende disso | **2–3 clipes reais de fontes NOVAS**; quando a frase fala de alguém → a PESSOA real (presidente, piloto, operário) | som de ação em cada cena (`sfx_cena`); whoosh nos cortes |
| **3. EXPLICAÇÃO (ouro parcelado)** | 9–17 s (25–60% do vídeo) | ~20 | o mecanismo em passos curtos e visuais: 1 frase = 1 passo que dá para desenhar | **3D em UM bloco contínuo de 6–10 s** se for invisível/por dentro/impossível de filmar (ver §3); senão, clipe real do processo | whoosh na entrada do 3D + 1 som por EVENTO do 3D (encaixe, motor, líquido); música estável |
| **4. PROVA** | logo após o 3D, 1–3 s | ~6 | "e é assim de verdade": a mesma coisa do 3D acontecendo | **clipe real** do mecanismo explicado (fonte nova) | som de ação forte e sincronizado (clique, clunk, jato) |
| **5. VIRADA / EUREKA** | ~75% do vídeo | ~12 | "Só que…" / "Mas…": o detalhe que ninguém sabe, a consequência, o novo fato | **clipe real impactante**; zoom blur + flash | riser → vácuo 0,3 s → boom; a MÚSICA CRESCE 2,5 s depois |
| **6. LOOP** | últimos 1–2 s | ~5 | frase suspensa que emenda na 1ª palavra ("…e ninguém percebeu que" → "o antigo avião…") | **o mesmo quadro do frame 0** | música sobe para o loop; sem silêncio no fim |
**CTA INTERATIVO é OBRIGATÓRIO** (BÍBLIA §1): antes do loop, ligado a um acontecimento do vídeo, frase nunca repetida; botão SE INSCREVE na tela (`"cta": {"em": "se inscreve"}`).

## 2. Tiro Curto (12–15 s, 30–38 palavras) — curiosidade rápida, física bizarra, susto, gambiarra
| Batida | Tempo | ROTEIRO | IMAGEM | SOM |
|---|---|---|---|---|
| 1. GANCHO | 0–3 s | quebra de expectativa | clipe real em movimento | ding + flash + ação alta |
| 2. AÇÃO | 3–6 s | o que está acontecendo | clipe real (fonte nova) | som de ação |
| 3. RE-HOOK | ~6 s | nova pergunta/virada rápida | corte brusco + punch-in | hit curto |
| 4. PAYOFF | 6–12 s | a resposta | 3D de 3–5 s se for invisível; senão real | som por evento |
| 5. LOOP | fim | frase suspensa | frame 0 | música sobe |

## 3. Quando usar 3D (decida nesta ordem)
1. **Existe vídeo real que MOSTRA o mecanismo com clareza?** → use o real (3D é para o que a câmera não alcança).
2. **É invisível, por dentro, uma força, um "e se", antes/depois, raro ou impossível de filmar?** → 3D.
3. **Nunca 3D:** no gancho, na prova, para mostrar pessoas, para tapar falta de clipe (falta de clipe = buscar mais fontes).
- **Um bloco só**, contínuo (várias fases = cenas 3D seguidas, a câmera continua); nenhum clipe real no meio.
- 6–10 s no Bastidor, 3–5 s no Tiro Curto, máximo 45% do vídeo, começa entre 25% e 60% do vídeo.
- Qualidade: modelo pronto (Sketchfab/Poly Haven), céu HDRI, física certa (nariz para onde anda, trem recolhido em
  voo, o que queimou não volta), sem marca de empresa no modelo.
- Som do 3D: entrada + 1 som por evento (trava R8).

## 4. Regras do B-roll (clipe real)
- **Função antes do objeto:** cada cena tem um papel (contato visual, ameaça, arco de ação, payoff, prova, pessoa).
  A cena faz SENTIR (perigo, escala, peso), não só ilustra. A ação acontece NA palavra.
- **≥ 7 fontes diferentes**; cada arquivo em no máximo 2 cenas; ≥ 60% das cenas reais de fontes diferentes (R1).
- **Qualidade:** ≥ 600 px úteis na vertical (horizontal 720p recortado não serve, só com justificativa), nítido, em
  movimento, sem logo/legenda/rosto de tiktoker (recortar ou descartar), sem tela de app (R4, triagem).
- **Pessoas reais** quando a frase cita alguém: contas oficiais (Casa Branca, Forças Armadas, NASA, fabricantes).
- **Fontes, em ordem:** busca web TikTok/X/Instagram + yt-dlp → Pixabay/Pexels → Internet Archive (só prova) →
  vidIQ (crédito mensal) → link do dono.
- Clipe horizontal: conferir na prancha se a PESSOA/sujeito ficou dentro do recorte (`foco` + `seguir: false`).

## 5. Som (camadas fixas — biblioteca_sons.md)
| Camada | Nível sob a voz | Quando |
|---|---|---|
| Música da categoria (tabela da pesquisa: aviação = `synthwave_aviacao`, perigo = tensão, processo = phonk…) | −10 a −12 dB na fala (audível no celular), sobe nas pausas, cresce na virada e no fim | o vídeo todo, desde o frame 0 |
| Foley/ambiência contínua (o lugar) | −10 dB | toda cena, emenda em J/L |
| Som de ação (`sfx_cena`) | −2 a −6 dB | o que aparece na tela, na palavra |
| Whoosh | quase na voz | na MAIORIA dos cortes (29/30 nos canais) |
| Riser → vácuo → boom | alto | só na virada (1–2 por vídeo) |
| Ding + flash | DING no nível da voz, fora do abaixamento | frame 0 (identidade; medido na entrega) |
Mixagem em 2 grupos (leito −10 dB / efeitos −3 dB). Nota do OUVIDO (Gemini) ≥ 8 na trava de entrega.

## 6. Ordem de produção (cada etapa confere a planta)
`/tema` (tem imagem? fato vale hoje?) → `/roteiro` (batidas e palavras da §1/§2) → `/clipes` (≥ 7 fontes, §4) →
`/animacao` (§3) → `/editar` (§5; `viitu.montagem` barra) → render → `viitu.entrega` (ouvido + prancha) → enviar.
