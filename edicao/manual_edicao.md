# 🎬 Manual de edição profissional — Viitu Shorts

Memória de edição do canal. Toda edição segue este manual. Cada técnica tem: **o que é → quando usar →
como está no nosso editor** (✅ automático · 🔧 manual no cenas.json · ⏳ ainda não implementado).
Objetivo único de toda técnica: **imersão** (o espectador esquece que está vendo um vídeo) e **retenção**
(o cérebro não tem tempo de se acostumar).

---

## 1. Princípios (valem para tudo)
1. **Toda escolha serve à história.** Efeito sem motivo é ruído. Pergunta-teste: "o que isso faz o espectador
   sentir ou entender?". Sem resposta, corta.
2. **Contraste o tempo todo.** O cérebro desliga o que é constante: alterna escala, energia, direção, volume, cor.
3. **Ver e ouvir a mesma coisa.** O que aparece na tela tem que ter som; o que se fala tem que aparecer.
4. **Antecipar.** Som e movimento chegam um instante antes da imagem/palavra: o espectador sente que o vídeo
   "puxa" ele para a frente.
5. **Menos é mais nos picos.** Os momentos fortes (gancho, virada, revelação) ganham o maior efeito; o resto fica
   mais limpo para os picos se destacarem.

---

## 2. SOM — as 6 camadas do sound design profissional
Um editor profissional pensa o som em camadas, cada uma com seu volume e função.

| Camada | O que é | Volume relativo | No editor |
|---|---|---|---|
| 1. Voz | narração (Otto, ElevenLabs v4) | referência (0 dB) | ✅ |
| 2. Trilha | música que dá a emoção do vídeo | −20 dB sob a voz, sobe nas pausas (*ducking*) | ✅ biblioteca própria |
| 3. Ambiência (*room tone / bed*) | o "ar" do lugar: vento, floresta, cidade, grilos | baixa e contínua, nunca some de repente | ✅ foley de ambiência |
| 4. Foley | o som do que acontece na tela (fogo, passos, água, motor) | médio, logo abaixo da voz | ✅ CLIP escolhe por cena |
| 5. Efeitos pontuais (*hard FX / spot*) | som sincronizado com uma AÇÃO (chama explode, objeto cai, splash) | alto e curto | ⏳ |
| 6. Efeitos de edição (*sweeteners*) | woosh, pop, ding, riser, boom — marcam a EDIÇÃO, não o mundo | curto, nunca cobre a palavra | ✅ |

### Técnicas de som (imersão)
- **Corte em J (*pre-lap*)** — o som da próxima cena entra ~0,25 s ANTES do corte da imagem. O ouvido chega
  antes do olho e a transição fica "puxada". ✅ (`PRE_LAP = 8` quadros em `viitu/foley.py`)
- **Corte em L** — o som da cena anterior se arrasta um pouco depois do corte e some em crossfade. Evita o
  "buraco" de som no corte. ✅ (`CAUDA = 6` quadros)
- **Pan estéreo** — o som sai do lado onde a coisa está (fogo à esquerda → som mais na esquerda). Com fone de
  ouvido (maioria no Shorts) isso coloca o espectador DENTRO da cena. ✅ (pela posição `alvo`; espelhar inverte)
- **Ducking** — a trilha abaixa quando a voz fala e sobe nas pausas, sem o espectador perceber. ✅ (0,11 / 0,20)
- **Vácuo sonoro antes do impacto** — tudo some (trilha, foley, ambiência) por ~0,3 s logo antes da revelação;
  depois entra o boom e a trilha volta MAIS forte. O silêncio é o efeito mais forte que existe. ✅ (`impacto_em`)
- **Riser / drone de tensão** — som que sobe antes da revelação e prepara o susto. ✅ (tensao.mp3, 1,7 s antes)
- **Ambiência contínua** — cenas vizinhas no mesmo lugar mantêm o mesmo "ar"; trocar de ambiência = trocar de
  lugar. ✅ (faixas iguais se fundem)
- **Perspectiva/distância** — plano aberto = som mais abafado e baixo; close = som mais presente e brilhante. ⏳
- **Efeito pontual na ação** — o pico de movimento da cena (pico de fluxo óptico) recebe um som de impacto do
  tipo certo (chama, água, metal). ⏳ (próximo passo: biblioteca `assets/spot/`)
- **Música editada na batida** — cortes importantes caem no tempo forte da trilha. ⏳
- **Loudness final** — −14 LUFS integrados, pico ≤ −1 dBTP (padrão YouTube). ✅ medido na auditoria

**Regras de volume:** voz sempre ≥ 15 dB acima da trilha; foley nunca mascara consoantes da voz (sob a fala
o foley cai 15%); efeito de edição nunca em cima de palavra-gatilho (exceto o boom do impacto).

---

## 3. IMAGEM — corte, câmera e ritmo
- **Ritmo:** 1,7–2,9 s por cena (máx. 2,8 s no editor). ✅ Cena só muda quando muda a ideia OU a cada ~2,5 s
  com um estímulo (zoom, círculo, corte).
- **Corte na ação (*cut on action*)** — cortar NO MEIO de um movimento (a mão descendo, a chama subindo):
  o movimento esconde o corte. ⏳ (alinhar corte ao pico de fluxo óptico)
- **Contraste entre cenas** — escala (close ↔ aberto), quantidade, direção (`espelhar`), energia. ✅ `viitu.contraste`
- **Continuidade de direção** — se o objeto sai pela direita, entra pela esquerda na próxima cena. 🔧 `espelhar`
- **Câmera virtual** — zoom lento (Ken Burns) em imagem parada, punch 4,5% na palavra-chave, tremida no
  impacto. ✅
- **Speed ramp** — câmera lenta no momento satisfatório, acelera no resto. 🔧 `velocidade` ⏳ rampa automática
- **Match cut** — corte entre duas imagens com a mesma forma/movimento (círculo → círculo). 🔧 escolha de cena
- **Enquadramento** — sujeito no terço, nunca cortado, olhar com espaço na direção que olha. ✅ auto_enquadrar/OWLv2
- **Frame 0** — a imagem mais forte, em tela cheia, com seta vermelha. ✅

## 4. COR e acabamento (unifica clipes de fontes diferentes)
- **Correção** — clarear cena escura (gamma), igualar exposição. ✅ `_escura`
- **Grade (look)** — contraste +7%, saturação +12%: todas as fontes ficam com cara de "um filme só". ✅
- **Vinheta** — bordas levemente escuras puxam o olho para o centro. ✅
- **Grão fino** — 7%, mascara diferenças de qualidade entre clipes (576p do TikTok vs 4K do Pixabay). ✅
- **Look por clima (futuro)** — perigo: mais frio/contraste; curiosidade leve: mais quente. ⏳

## 5. Gráficos e texto
- Legenda 1 palavra, Anton, branca/amarela com contorno, centro-inferior (y 1180) ou topo se o sujeito estiver
  embaixo; nunca abaixo de 1400. ✅
- Círculo vermelho que se desenha e segue o objeto (+ pop); seta vermelha no frame 0. ✅
- Texto na tela só com o que a voz NÃO diz (número, pergunta do gancho). 🔧
- CTA: botão INSCREVA-SE → ✓ INSCRITO (+ pop + clique). ✅

## 6. Transições (biblioteca e quando usar)
| Momento | Visual | Som |
|---|---|---|
| Frame 0 | flash branco→amarelo 0,2 s | ding |
| Corte comum | glitch RGB de 3 quadros | woosh/whip alternados |
| Mesma cena, outro ângulo | corte seco (sem efeito) | só o corte em J do foley |
| Virada/revelação (`impacto_em`) | zoom blur + RGB + flash + tremida | vácuo → boom |
| Mudança de lugar/tempo | corte com troca de ambiência | nova ambiência entra antes (J) |
Nunca transição "de PowerPoint" (dissolve longo, wipe, estrela). Excesso de efeito em todo corte = amador.

## 7. Estrutura de emoção (curva do vídeo)
gancho (pico 1) → explicação (respira, som mais limpo) → virada "Mas..." (pico 2, vácuo + boom) →
resolução satisfatória (trilha sobe) → loop (frase suspensa, som contínuo para emendar no início).
O som segue a curva: trilha mais baixa na explicação, cheia na virada e no final.

## 8. Checklist do editor profissional (antes de entregar)
- [ ] Toda cena tem som do que mostra (foley/ambiência) e nenhuma ambiência some no seco
- [ ] Som entra antes do corte (J) e o pan acompanha o sujeito
- [ ] Vácuo + boom na virada; nenhum efeito cobre a palavra-gatilho
- [ ] Voz ≥ 15 dB acima da trilha; −14 LUFS
- [ ] Cor unificada (nenhum clipe destoa); nenhuma cena escura sem motivo
- [ ] Ritmo 1,7–2,9 s; contraste entre cenas vizinhas; frame 0 forte com seta
- [ ] Revisão, auditoria e direitos aprovados

## 9. Próximas técnicas a implementar (ordem de impacto)
1. Efeitos pontuais na ação (biblioteca `assets/spot/` + pico de movimento) ⏳
2. Perspectiva de som por plano (aberto abafado / close presente) ⏳
3. Corte na ação (ajustar a borda do corte para o pico de movimento) ⏳
4. Cortes na batida da trilha ⏳
5. Look de cor por clima do tema ⏳
