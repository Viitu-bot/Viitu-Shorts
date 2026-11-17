# 🧠 Lógica do editor — qual efeito, em que momento, em qual cena

Pesquisa de nov/2026 (fontes no fim). Complementa `manual_edicao.md` (técnicas) e `biblioteca_sons.md` (sons).


## 00. ESPECIFICAÇÃO FIXA (regra, não medição) — `edicao/especificacao.json`
Tirada da engenharia reversa completa de 35 Shorts do nicho (6 canais + vídeos enviados pelo dono;
`pesquisa/reverso/resumo_edicao.json`). Valores = mediana dos vídeos de maior sucesso. O editor obedece direto.

**Mixagem (dB em relação à voz; todo som é normalizado à referência da voz antes — `viitu/mix.py`):**
| Camada | Nível | Leitura |
|---|---|---|
| Voz | 0 | referência (−14 LUFS) |
| Música sob a fala | **−18** | baixa enquanto fala… |
| Música nas pausas | **−6** | …e SOBE forte nas pausas (o "respiro" que dá ritmo) |
| Whoosh | −3 | quase o volume da voz, curto |
| Pop (seta/círculo) | −5 | |
| Boom (revelação) | **0** | tão alto quanto a voz, 1–2 por vídeo |
| Riser | −6 | |
| Ambiência (foley de fundo) | −12 | |
| Detalhe ASMR (foley de perto) | −5 | alto: é o som que "dá realidade" |
| Som original do clipe | −16 | quase sempre desligado |

**Imagem:** 1,5 s por cena (máx. 2,0) · corte SECO + whoosh (34/35; sem glitch no corte) · punch-in na
palavra-chave (91%) · zoom lento (69%) · câmera lenta no momento satisfatório (49%) · tremida só no impacto (6%) ·
cor saturada (69%) · seta vermelha no frame 0 (80%) · legenda branca com destaque amarelo, contorno, centro-
inferior, animação pop · CTA explícito ausente na maioria (19/35) → loop no lugar · marca d'água visível em 57%
(comum, mas preferimos sem) · animação 2D/3D em 40%.
Para mudar um valor: editar `especificacao.json` (nunca número solto no código).

## 0. ENGENHARIA REVERSA — 30 Shorts do nicho (nov/2026, `pesquisa/reverso/`)
Amostra: A vida é uma maravilha, GeneralTV, KSO Descobre, Polaco sem Polônia, Andre Shorts Br, Zack D. Films —
os 4 maiores sucessos do último ano de cada um + 1 vídeo mediano. Questionário respondido pelo Gemini (o que
aparece na maioria vira regra; listagem som-a-som do Gemini se mostrou não confiável e foi descartada).
| O que fazem | Resultado | Nossa regra |
|---|---|---|
| Música de fundo | **100%** dos vídeos | níveis na seção 00 ✅ |
| Whoosh nos cortes | na **maioria** dos cortes em 29/30 | kit `whoosh_corte` em quase todo corte ✅ |
| Pop quando aparece seta/círculo | **90%** | ✅ |
| Foley/ASMR do que aparece | **93%** (som original do clipe desligado em 22/30, baixo em 8) | 2 camadas Sonniss ✅ |
| Riser antes da revelação | 47% | só quando há revelação forte |
| Boom/impacto | mediana **2 por vídeo** (gancho/revelação/ação de força) | 1–2 ✅ |
| Ding/notificação | mediana **0** | raro; só com número na tela |
| Buzzer/acerto/sons de função | **não aparecem** | desligados por padrão (o dono também reprovou) |
| Som em cada palavra da legenda | **0%** | nunca |
| Sons de meme | **0%** em 30 vídeos | nunca |
| Vácuo/silêncio dramático | 13% | só na virada principal |
| Animação 2D/3D | **53%** dos vídeos (GeneralTV 80%, A vida 60%, Andre 40%, KSO/Polaco 20%, Zack 100%) — inserções de **1–10 s** no meio explicando mecanismo/anatomia; Zack: vídeo todo em 3D | animação curta no trecho do mecanismo ✅ |
| Assinatura sonora própria | nenhum canal tem — a identidade vem da CONSISTÊNCIA (mesmos whooshes, mesmo estilo visual) | nosso ding+flash é diferencial; manter o kit fixo |
Conclusão: o padrão do nicho é **limpo e consistente** (música constante + whoosh nos cortes + pop nas marcas +
foley + 2 booms + animação curta). Efeito "engraçadinho" ou de função não faz parte da linguagem desses canais.

## 1. Identidade sonora do Viitu (o que faz reconhecer o canal sem ler o nome)
Canal grande se reconhece pelo **conjunto pequeno e fixo** de sons que se repete em todo vídeo, sempre na
mesma função. Regra: poucos sons, sempre os mesmos papéis, alternando 3 variações de cada.
| Papel | Som | Fonte |
|---|---|---|
| **Logo sonoro** (frame 0) | ding próprio + flash branco→amarelo | ElevenLabs (nosso, exclusivo) |
| Corte | whoosh de ar curto (3 variações) | kit `whoosh_corte` (Mixkit) |
| Detalhe marcado | pop limpo | kit `pop_marca` |
| Revelação | riser → vácuo → boom cinematográfico | kit `riser_tensao` + `impacto_revelacao` |
| Fato/número (só com número animado na tela) | ding de notificação | kit `ding_fato` (raro) |
| Final | botão inscrever + clique | próprio |
O kit fica em `assets/kit/kit.json` (`python3 -m viitu.kit listar`). Mudar o kit = mudar a identidade: só com o dono.

## 2. Bom × ultrapassado (o que a maioria dos canais bons usa hoje)
**Usar (padrão atual):** whoosh de ar curto e suave · boom cinematográfico grave (com sub) · riser/swell antes da
revelação · pop limpo/bolha · ding de notificação · obturador de câmera · glitch digital curto · teclado · tique-taque ·
batida de coração cinematográfica · moeda/caixa registradora · buzzer de erro · rewind de fita · foley/ASMR real.
**Evitar (datado, cansado ou com direito incerto):** vine boom, "bruh", air horn/MLG, "oh no", Taco Bell bong,
trombone triste, risada de plateia, "fart", sons de videogame 8-bit, risada de desenho, scratch em todo vídeo,
qualquer trecho de música/filme/meme famoso (Content ID). Boom só 1–2 por vídeo (mais que isso vira meme).

## 3. Mapa de decisão: MOMENTO do roteiro → efeito
| Momento (detectar no roteiro) | Visual | Som | Regra |
|---|---|---|---|
| Frame 0 / gancho | flash identidade + seta vermelha | ding próprio + foley alto da cena | voz em 0,0 s |
| "A maioria acha…" (mito) | legenda riscada / X vermelho | `errado_mito` | 1 por vídeo |
| "…mas o motivo real é" | punch-in + legenda amarela | `certo_resposta` ou ding | |
| Número / dado | número grande animado (contador) | `ding_fato` | auto: dígitos, mil, milhões |
| Dinheiro / preço | contador + R$ | `dinheiro` | auto: reais, dólares, caro |
| Tempo / urgência | relógio/contagem | `relogio_tempo` (baixo) | |
| Perigo / medo | tremida leve, vinheta forte | `coracao_tensao` sob a voz | |
| Virada "Mas tem um porém" | zoom blur + RGB + flash + tremida | riser → vácuo 0,3 s → boom | `impacto_em` |
| Detalhe a observar | círculo que se desenha | `pop_marca` | |
| Explicação de mecanismo | **animação (2D/3D)** | whoosh na entrada + foley da animação | o "porquê" desenhado |
| Mudança de lugar | corte com nova ambiência | ambiência nova entra antes (J) | |
| Ação na tela (cai, bate, acende) | corte NA ação | efeito pontual sincronizado | |
| CTA (padrão do canal) | "SE INSCREVE" na tela + rosto/joinha | pop | CTA-elogio ligado ao tema + loop (`/roteiro`, item 6) |
| Loop (última frase) | volta à 1ª imagem | som contínuo emenda no início | sem silêncio no fim |

## 4. Mapa de decisão: TIPO DE CENA → tratamento
| Cena | Câmera | Som | Cuidado |
|---|---|---|---|
| Close / detalhe | zoom lento in, círculo | detalhe ASMR alto | legenda longe do detalhe |
| Plano aberto / escala | Ken Burns lento out | ambiência alta, detalhe baixo | seta no sujeito |
| Ação rápida | sem zoom extra, corte na ação | efeito pontual | não cortar antes do clímax |
| Parado / foto | Ken Burns + parallax | ambiência + shutter na entrada | máx. 2 s |
| Animação 2D/3D | movimento de câmera dentro da animação | whoosh entrada + foley | 1 ideia por animação |
| Clipe de terceiro (prova) | sem zoom (marca d'água) | foley próprio, áudio original OFF | crédito |

## 5. Orçamento de estímulos (densidade)
- Um estímulo visual a cada 2–3 s (corte, zoom, marca, animação). Nunca 2 efeitos grandes a menos de 1 s.
- Por vídeo de 45–60 s: logo sonoro 1 · boom 1–2 · riser 1–2 · errado/certo 1 cada · dings ≤ 4 · whoosh em
  ~metade dos cortes (corte seco dentro do mesmo lugar) · pops = nº de marcas.
- Picos só no gancho e na virada; o meio respira (som mais limpo) para os picos se destacarem.
- O meio do vídeo (35–65% do tempo) é onde a retenção cai: é ali que entra a ANIMAÇÃO e/ou a cena mais forte guardada.

## 6. Animação 3D no meio do vídeo — vale a pena? (medido em 16/11/2026, YouTube Data API)
- Canais 3D de "como funciona/o que acontece por dentro": Zack D. Films (29,7 mi inscritos) mediana **7,6 mi**
  views nos últimos 50 Shorts; Professor Of How (16,2 mi) mediana **5,9 mi**.
- Em espanhol/português: "Por Dentro De Todo" 12,3 mi; "Desmontando o Mundo" (PT) 4,3 mi; "E Se? 3D" (PT) 338 mil.
- Leitura: o formato 3D casa com a nossa categoria nº 1 (motivo oculto / processo revelado) e ainda há poucos
  canais em PT-BR. **Compensa** como **seção explicativa no meio** (8–15 s), mantendo gancho e prova com
  imagens reais — híbrido. Não migrar o canal inteiro para 3D (exige qualidade de estúdio que ainda não temos).
- Como fazer de graça: Three.js dentro do Remotion (`@remotion/three`) + modelos/texturas CC0 do Poly Haven.

## 7. Clipes de IA (Veo etc.) — de graça?
- Veo pela API não tem plano grátis (~US$ 0,05–0,40/s). Grátis só no app/Flow e no Kling, com **marca d'água**
  ("Made with Veo"/Kling) e cota diária: troca um logo pelo outro. Modelos abertos (Wan, LTX) precisam de GPU;
  esta máquina não tem.
- Decisão: o meio do vídeo usa **animação própria (2D/3D) + Pixabay + foley Sonniss** (grátis, sem marca d'água).
  IA paga só se o dono decidir investir (~US$ 2/vídeo). Conteúdo realista de IA exige marcar "conteúdo alterado".

## 8. O que ainda falta na nossa edição (prioridade)
1. ⏳ Seção 3D no meio (`@remotion/three` + Poly Haven)
2. ⏳ Sons de função automáticos (número→ding, dinheiro→moeda, mito→buzzer) — `sfx_em` no cenas.json + auto
3. ⏳ Contador animado de números (kinetic typography)
4. ⏳ "Texto atrás do sujeito" (recorte do objeto com rembg, grátis em CPU) — efeito em alta
5. ⏳ Parallax 2.5D em fotos (profundidade)
6. ⏳ Speed ramp automático no momento satisfatório
7. ⏳ Comparação lado a lado (split screen) para "X vs Y"
8. ⏳ Mapa animado (skill remotion-maps) para temas de lugar

## Fontes
YouTube Data API (medições acima); Sonniss (licença); Mixkit Sound Effects Free License; guias de SFX para Shorts
(Soundstripe, CreatorSFX); preços Veo (BenchLM, Puter); limites grátis de IA (fast.io, aivideobootcamp).

## Histórico (vindo do CLAUDE.md antigo, para referência)
- Análise de 12 vídeos do próprio canal (~20k views, nov/2026): os que funcionaram tinham UM clipe-âncora real,
  vertical, com início-meio-fim; clipe horizontal cortado para 9:16 fica ruim; stock só como complemento.
- Primeiro raio-X de 9 virais (`hall_da_fama/README.md`, `pesquisa/raiox/`): seta no frame 0 em 77%, ~2,5 s por cena,
  legenda de 1 palavra. A especificação atual (seção 00) substitui esses números onde houver conflito.
