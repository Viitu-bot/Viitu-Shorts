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
| Épica (~3) | `epico_engenharia.mp3` | escala gigante, recorde, engenharia monumental | A vida "ponte mais alta do mundo" |
| Brincalhona (~3) | `upbeat_brincalhao.mp3`, `curioso_documentario.mp3` | humor, bicho, comida, "olha isso" | KSO "chocolate", Andre "gato no aquário" |
| Emocional (~2) | `emocional_piano.mp3` | virada humana/emocional (história, luto, superação) | A vida "Bebês reborn" (sobe na virada emocional) |
| Calma/natureza | `natureza_calma.mp3`, `descoberta_leve.mp3` | natureza contemplativa, bicho calmo | — |
| Cultural (~2) | gerar na hora | lugar/tradição de outro país: instrumento típico | A vida "gelo antigo" (chinesa); KSO "portas" (africana) |

Gerar trilha nova: `POST https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128` com
`{"prompt": "...instrumental..., no vocals, loopable", "music_length_ms": 45000}` (header `xi-api-key: proxy-injected`),
UMA de cada vez (em paralelo dá 429). Conferir o estilo com o CLAP (rótulos sem "lo-fi", que vira balaio) antes de usar.
