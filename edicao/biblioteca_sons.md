# 🔊 Biblioteca de sons — para que serve cada um e quando usar

## De onde vêm (todos liberados para YouTube monetizado)
| Fonte | O que tem | Licença |
|---|---|---|
| **Sonniss GDC 2015–2026** (`assets/sonniss/catalogo.json`, 7.319 sons) | gravações profissionais de campo e estúdio: fogo, vento, água, natureza, veículos, impactos, whooshes, ambiências do mundo inteiro | royalty-free, uso comercial e **YouTube monetizado**, sem crédito obrigatório. Proibido: revender os sons soltos e usar para treinar IA |
| **Próprios ElevenLabs** (`assets/sfx`, `assets/foley`, `assets/musica`) | identidade do canal (ding, pop, woosh, boom), foley de reserva, 5 trilhas | nossos (plano pago) |
Nunca: sons de "sites sem direitos" aleatórios, áudio original de TikTok/Reels, sons meme (vine boom etc.).

## Quando a Sonniss não tem o som
Gere no ElevenLabs (sound-generation, "..., no music"), salve em `assets/sfx/<nome>.mp3` e use no sfx do 3D com
`"arquivo": "assets/sfx/<nome>.mp3"` (ex.: `pneu_lama.mp3`, criado para o vd006).

## Como buscar
`python3 -m viitu.sons buscar "close up campfire crackling" --exigir "fire|campfire" --min 4`
Descrição em inglês e concreta (o que, onde, distância). O sistema acha 12 candidatos pelo nome e o modelo
CLAP **escuta** cada um e escolhe o que soa como a descrição. Escolhas ficam em `assets/sonniss/escolhas.json`.
No editor é automático: cada cena recebe **2 camadas** (tabela `CAMADAS` em `viitu/foley.py`).

## As camadas e quando usar cada uma
| Camada | Para que serve (o que o espectador sente) | Quando usar | Volume | Exemplo de busca |
|---|---|---|---|---|
| **Ambiência / fundo** | "estou lá": dá o lugar e o clima; sem ela o vídeo soa vazio, de estúdio | SEMPRE, em toda cena; contínua entre cenas do mesmo lugar | baixo, constante | `large wildfire roaring`, `night forest crickets`, `city traffic distant` |
| **Detalhe de perto (ASMR)** | textura que arrepia: estalo, chiado, raspagem; prende a atenção e dá "realidade" | cena em close ou com a ação principal (fogo, comida, máquina, água) | médio, logo abaixo da voz | `close up campfire crackling`, `oil sizzling close`, `gravel footsteps close` |
| **Efeito pontual (hard FX)** | sincroniza o olho com o ouvido no momento da ação: o cérebro "acredita" | quando algo acontece na tela: cai, bate, explode, acende | alto e curto | `match strike ignite`, `tree falling crash`, `water splash big` |
| **Whoosh / transição** | marca a EDIÇÃO e dá velocidade | corte com movimento, entrada de texto/gráfico; alternar tipos; nunca em todo corte | médio | `fast whoosh short`, `air swish` |
| **Riser / drone de tensão** | prepara o susto; o espectador sente que vem algo | 1–2 s antes da revelação ("Mas...") | sobe até o impacto | `tension riser`, `low drone dark` |
| **Impacto / boom** | ponto de exclamação sonoro | só na virada/revelação (1–2 por vídeo) | alto | `cinematic boom deep`, `sub drop` |
| **UI / pop / ding** | chama o olho para um elemento gráfico | círculo, seta, número na tela, CTA | curto | próprios: pop, ding, clique |
| **Silêncio (vácuo)** | o efeito mais forte: o mundo prende a respiração | 0,3 s antes do impacto | — | automático em `impacto_em` |

## Mixagem em 2 grupos (desde 18/11 — dono: "parece que só tem clipe e narração")
- **Leito** (música, foley contínuo, ambiente): 10 dB abaixo da voz durante a fala (`plano.duck`, gravado nos `*_d.m4a`).
- **Efeitos curtos** (whoosh, som de ação, riser/boom, pop, ding): só 4 dB abaixo, piso 0,3 (`plano.duck_fx`); whoosh −8 dB. Efeito
  enterrado = vídeo "sem edição". `sfx_cena` entre −2 e −6 dB; 3D entre −2 e −6 dB.
- Música CRESCE 2,5 s depois do boom da virada (dinâmica). O OUVIDO (`viitu.ouvido`, Gemini) dá a nota final (≥ 8).

## Regras de ouro
1. Toda cena tem som do que mostra; ambiência nunca corta no seco (corte em J/L automático).
2. Ver e ouvir a mesma coisa: fogo pequeno = estalo; incêndio = rugido grave. Escala do som = escala da imagem.
3. Plano aberto = mais ambiência; close = mais detalhe ASMR.
4. Voz sempre na frente (≥ 15 dB acima da trilha). Foley baixa 15% enquanto a voz fala.
5. Variar: o mesmo arquivo não toca do mesmo ponto em cenas diferentes (o editor muda o trecho).
6. Conferir as escolhas novas pelo nome em `escolhas.json` (o CLAP pode confundir: fogos de artifício ≠ fogo,
   estalo elétrico ≠ brasa). Corrigir a descrição/`EXIGIR` e apagar a entrada errada.

## Trilhas (biblioteca própria — `assets/musica/`)
| Arquivo | Clima | Quando usar |
|---|---|---|
| tensao_documentario | suspense, perigo | perigo/erro/segurança, desastres |
| descoberta_leve | curioso, leve | objeto do dia a dia, motivo oculto leve |
| epico_engenharia | grandioso | recorde, escala, "mais caro do mundo", engenharia |
| natureza_calma | orgânico | animais, natureza |
| curioso_documentario | neutro | geral |
Próximo: gerar mais trilhas (2 por clima) para não repetir a mesma em vídeos seguidos.

- vd007: a Sonniss não tem foguete. Gerados no ElevenLabs (`assets/sfx/`): foguete_motor, reentrada_plasma, braco_metal,
  motor_corte, hidraulico_grande, peca_solta. Endpoint `sound-generation`, header `xi-api-key: proxy-injected`.

> **[superado 27/11 → a trilha do arquivo vem da biblioteca de JOGO ANTIGO livre (`assets/musica/jogo_antigo/LEIA.md`); esta tabela fica só como referência do que os concorrentes usam]**

## Trilhas por categoria (pesquisa 18/11/2026: 43 Shorts de referência — A vida é uma maravilha, GeneralTV, KSO, Polaco, Andre, Zack D.)
Regras medidas: **100% dos vídeos têm trilha**; fica 12–18 dB abaixo da voz (nossa spec: −14 sob a fala, −6 nas pausas);
entra no frame 0 e quase sempre é **constante**; quando muda, é para **subir na revelação/virada** ou **subir no final
para o loop** (o editor já faz). Nenhum dos 43 usa música clássica. Todas as nossas são próprias (ElevenLabs Music).

| Categoria (nos 43) | Arquivo | Quando usar (gatilho do roteiro) | Referência |
|---|---|---|---|
| Suspense rítmico (~12) | `tensao_documentario.mp3` | perigo/erro, "nunca faça", acidente, risco | A vida "O CLT mais infernal", "Posso nadar aqui?" |
| Mistério (sem batida) | `misterio_sombrio.mp3` | segredo, "ninguém sabe por quê", fenômeno estranho | Andre "Posso nadar nessa piscina?" |
| Phonk / eletrônica (~11) | `phonk_processo.mp3` | processo satisfatório, máquina, invenção, esporte | A vida "bolas de handebol", "LUVA na Copa"; Polaco |
| Lo-fi hip hop (~9) | `lofi_curioso.mp3` | motivo oculto do dia a dia explicado com calma, truque | Zack D. "Water out of your ear"; KSO "edifício japonês" |
| Synthwave (aviação) | `synthwave_aviacao.mp3` | avião, aeronave, máquina de alta tecnologia | TikTok: freio de avião (3,3 mi), porca/parafuso (2,9 mi) — estilo "Blade Runner 2049" |
| Épica (~3) | `epico_engenharia.mp3` | escala gigante, recorde, engenharia monumental | A vida "ponte mais alta do mundo" |
| Brincalhona (~3) | `upbeat_brincalhao.mp3`, `curioso_documentario.mp3` | humor, bicho, comida, "olha isso" | KSO "chocolate", Andre "gato no aquário" |
| Emocional (~2) | `emocional_piano.mp3` | virada humana/emocional (história, luto, superação) | A vida "Bebês reborn" (sobe na virada emocional) |
| Calma/natureza | `natureza_calma.mp3`, `descoberta_leve.mp3` | natureza contemplativa, bicho calmo | — |
| Cultural (~2) | gerar na hora | lugar/tradição de outro país: instrumento típico | A vida "gelo antigo" (chinesa); KSO "portas" (africana) |

Gerar trilha nova: `POST https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128` com
`{"prompt": "...instrumental..., no vocals, loopable", "music_length_ms": 45000}` (header `xi-api-key: proxy-injected`),
UMA de cada vez (em paralelo dá 429). Conferir o estilo com o CLAP (rótulos sem "lo-fi", que vira balaio) antes de usar.

## Músicas CONHECIDAS do nicho (identificadas pelo Gemini em 33 Shorts dos canais de referência, 18/11/2026)
Só vídeos de curiosidade/engenharia (A vida é uma maravilha, GeneralTV, KSO, Polaco, Andre, Zack D.) + sons do TikTok
usados em vídeos de explicação/ciência (vidIQ). Repetição em 2+ canais = mais confiável (o Gemini pode errar 1 nome).
Dados: `pesquisa/musicas_nicho.json`.

| Música | Visto em | Clima → quando usar | Direitos / como usar |
|---|---|---|---|
| The Lost Soul Down — NBSPLV | **4** (A vida ×2, GeneralTV ×2) | eletrônica misteriosa → perigo, motivo oculto técnico | com direitos → **app** |
| The Next Episode (remix/instrumental) — Dr. Dre | **3** (Zack D., Polaco, KSO) | hip-hop marcante → invenção, gadget, processo | com direitos → **app** |
| Montagem - PR Funk — S3BZS | **2** (A vida) | phonk BR → máquina, esporte, processo satisfatório | com direitos → **app** |
| MTG - CHIHIRO — DJ Arana | 1 (A vida "CLT infernal") | phonk BR pesado → trabalho perigoso | com direitos → **app** |
| Nocturne Op. 9 nº 2 — Chopin | 1 (A vida "caneta do Da Vinci") | clássica elegante → história, arte, invenção antiga | obra livre; gravação livre do Commons (pendente: Commons 429) |
| The Lamp — The Deli | 1 (A vida "cobertor mais caro") | lo-fi → explicação calma, dinheiro/raro | com direitos → **app** |
| Je te laisserai des mots — Patrick Watson | 1 (Andre) | piano melancólico → virada emocional | com direitos → **app** |
| The Sound of Your Fear | 1 (Zack D. tubarão) | suspense pulsante → bicho perigoso | com direitos → **app** |
| The Gonk — Herbert Chappell | 1 (Zack D. tomadas) | orquestra cômica → objeto do dia a dia engraçado | biblioteca KPM (reclama) → **app** |
| Monkeys Spinning Monkeys — Kevin MacLeod | 1 (Andre hashis) | brincalhona → curiosidade leve, outro país | **livre com crédito** → `brincalhao_kevin_monkeys.mp3` |
| Happy — MBB | 1 (Zack D.) | violão alegre → final feliz, bicho | livre com crédito (artista royalty-free) |
| Blade Runner 2049 — Synthwave Goose (TikTok) | vídeos de freio de avião (3,3 mi) e porca/parafuso (2,9 mi) | synthwave → engenharia, aviação | com direitos → **app** |
| Mysterious and Sad — Beats by Lucky (TikTok) | radiotelescópio (3,8 mi), IA que projeta motor | mistério → tecnologia estranha | com direitos → **app** |

**Como usar a música com direitos sem levar reclamação:** no `cenas.json`, `"musica": "app:The Lost Soul Down - NBSPLV"` →
o editor gera o vídeo SEM trilha; na hora de enviar, o dono toca em **Adicionar som** no app do YouTube, escolhe a faixa
(é licenciada para Shorts) e baixa o volume dela para ~10–15% (o nosso sidechain não alcança a trilha do app).
Nunca embutir música com direitos no arquivo: o Content ID reivindica a receita ou bloqueia.

## Trilhas chiptune (dono 24/11 — combinam com a marca "sans."/8-bit)
| arquivo | clima | quando usar | licença |
|---|---|---|---|
| bit_shift_kevin_macleod | 8-bit rápido, sintetizador limpo | máquina, tecnologia, invenção, processo rápido | CC BY 4.0 — crédito na descrição (LICENCAS.txt) |
| itty_bitty_8bit_kevin_macleod | 8-bit leve e brincalhão | curiosidade leve, humor, "olha isso" (linha do "sans.") | CC BY 4.0 — crédito na descrição |
Pendentes (o dono baixa e sobe no Drive, a nuvem não acessa): YouTube Audio Library — "Destiny" (GalaxyTones),
"Nostalgia Neuralgia" (Joshua Moses), "Good Old Times" (HolFix); Pixabay Music — Reganati (Chill Chiptune Loop),
echoes_of_lumen (Pixel Art Game Soundtrack), NickPanek (Chiptune Sherlock Holmes Anthem). Kubbi "Ember" e ko0x
"Galaxy Guppy": licença não confirmada → não usar até conferir.
