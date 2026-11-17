---
name: clipes
description: Escolhe e baixa os VÍDEOS que representam cada frase do roteiro do Viitu Shorts, por função psicológica, analisando os clipes de verdade (nitidez, movimento, onde está o sujeito). Use quando o usuário digitar /clipes ou pedir cenas para o tema/roteiro.
---

# /clipes: escolher cenas como um editor

Regra de ouro: **vídeo, não foto.** Foto só para uma prova visual impossível em vídeo (ex.: macro
de pupila) ou para uma demonstração com efeito, no máximo 2 vezes por vídeo.
**Clipe-âncora primeiro:** se existir um vídeo real do fenômeno (Reddit/TikTok/Douyin, enviado
pelo usuário via link do Drive ou TikTok), ele é a espinha do vídeo e o stock só completa.

## 0. Regras (definidas com o dono)
- **Toda cena é escolhida com o cuidado do gancho:** representa exatamente a frase E tem apelo visual (o melhor
  trecho, assunto em destaque, enquadrado). Sem cena de enchimento. Decidir NA ESCOLHA, não consertar depois.
- **Contraste com a cena anterior:** mudar pelo menos 1 eixo — escala, quantidade, direção (`"espelhar": true`),
  energia. `python3 -m viitu.contraste <proj> --aplicar`. Nunca espelhar imagem com texto/logo (`"texto_na_imagem": true`).
- **Quando NÃO procurar clipe → `/animacao` (3D):** a cena explica um mecanismo que não existe em vídeo, é muito
  difícil de achar ou é impossível de filmar (dentro do corpo, forças invisíveis, antes/depois, "o que acontece se").
- **Triagem obrigatória** antes de escolher: `python3 -m viitu.triagem <proj>` (tela do app, preto, desfoque, corte
  interno, resolução). REPROVADO não entra; < 720p só sem alternativa.
- **De onde vêm as imagens:** comece pelo viral que validou o tema
  (`viitu.assistir perguntar <link> "cenas, origem, marcas d'água"`) e busque esses ORIGINAIS. Prefira: Reddit
  original, arquivo do criador com permissão, Pixabay/Commons, material gravado pelo dono. TikTok baixado vem em
  576p com logo e tela final (o editor corta a tela final; crédito do @ na descrição). Clipes de terceiros: só os
  que viralizaram. **Antes de baixar do Pixabay, confira as tags pela API: "ai generated" = descartar** (no vd005, 2 dos 5
  melhores clipes eram IA). Foto do Commons: confira se mostra mesmo o que a frase diz (um "birdstrike" era de trem).
- **Brutos longos:** só com ≥ 1M de views (`viitu.tema brutos` filtra). Antes de pedir ao dono, verifique com
  `python3 -m viitu.assistir achar <link> "<cenas>"` e passe o link + os minutos exatos de cada trecho.
- Clipe de terceiros entra como PROVA no meio, não no gancho (gancho com imagem livre sempre que possível).

## 1. Plano de cenas por GATILHO PSICOLÓGICO
Para cada frase do roteiro, defina a função da cena antes do objeto citado:

| Função | Quando usar | Cena típica |
|---|---|---|
| **Contato visual** | gancho, chamada para comentar | animal ou pessoa olhando para a câmera |
| **Ameaça se aproximando** | predador, perigo, "quem caça" | animal vindo em direção à câmera |
| **Arco de ação** (início-meio-fim) | explicação de comportamento | algo para, reage e age (ex.: cervo alerta → foge) |
| **Payoff** | a palavra que fecha a ideia ("bote", "explode") | o momento exato da ação |
| **Prova** | "não é redondo", "olha isso" | close/macro do detalhe + círculo vermelho |
| **Quebra de padrão** | "Mas tem um porém" | punch-in brusco + som de impacto |
| **Espelho** | "e você?", "a nossa..." | olho/rosto humano: o espectador se vê |
| **Loop** | última frase | o mesmo quadro do frame 0 |

Anote a função no `cenas.json` (campo `_funcao`).

**Emoção acima de representação.** A cena não basta ilustrar a frase: ela precisa fazer quem
assiste SENTIR a ideia. Defina `_emocao` para cada frase e busque a cena que provoca isso:
- "presa / perigo" → predador vindo NA DIREÇÃO da câmera (o espectador vira a presa)
- "fugir / escapar" → o momento do disparo (pico de movimento cai na palavra)
- "vigiar / alerta" → animal sentinela virando a cabeça
Use termos de ação na busca ("cheetah chase", "rabbit running", "meerkat") e ordene por
movimento. Evite clipes com tag "ai generated" (exigem aviso de conteúdo sintético no YouTube).

**Câmera virtual (padrão para vídeo):** sem `foco` manual, o editor rastreia o ponto de atenção
(sujeito; ou centro entre dois sujeitos em cena de ação; ou a parte descrita em `sujeito`) ~5x/s
e faz um pan suave com keyframes a cada 0,25 s. `"seguir": false` desliga.

## 1b. Procurar BRUTOS (vídeos longos do tema)
Um vídeo longo (documentário, processo de fábrica) rende início, meio e fim de verdade, e vários
Shorts. Liste candidatos com:
```
python3 -m viitu.tema brutos "<tema em inglês, ex.: vampire bat documentary>"
```
A nuvem não baixa do YouTube: o usuário baixa/grava a tela das cenas e envia no chat ou por Drive.
Material de terceiros entra com narração transformadora + crédito na descrição.

## 1c. Contraste entre cenas vizinhas (planejar ANTES de baixar)
Para cada cena, anote também o contraste com a anterior: escala, quantidade (1 ↔ muitos), direção
(← ↔ →) e energia (parado ↔ ação). Ex.: galo em close → um monte de galinhas → um galo inteiro.
Depois de montar o cenas.json: `python3 -m viitu.contraste <proj> --aplicar`.

## 2. Buscar e ANALISAR candidatos (nunca escolher por miniatura)
```
python3 -m viitu.visao candidatos "goat eating" "cat stalking" ... -n 6 --saida <scratchpad>/cand
```
- Termos curtos em inglês (2 palavras). Vários termos por função.
- A ferramenta baixa a versão leve, mede **nitidez**, **movimento** e **sujeito** (YOLO) em 8
  quadros ao longo do clipe e gera `prancha_<id>.jpg`.
- Empilhe as pranchas dos melhores (`ffmpeg -filter_complex vstack`) e **olhe** (Read).
- Prefira: rosto/olho visível, ação acontecendo, sujeito grande. Descarte: costas, corpo sem
  cabeça, desfocado, parado.
- Anote o **segundo exato** (`inicio`) do trecho bom de cada clipe.

## 2b. Inteligência visual (viitu/inteligencia.py)
- `semantica(clipes, {"chave": "descrição em inglês"})`: CLIP dá nota a cada 0,5 s de cada clipe
  para cada frase. Use como primeira triagem; confirme olhando a prancha.
- `pico_acao(clipe, t0, t1)`: segundo de maior movimento. Calcule `inicio` para o pico cair
  na palavra-gatilho ("bote", "fugir", "explode").
- `localizar(clipe, "the eye of a goat", t0, t1)`: OWLv2 acha a parte descrita. No cenas.json:
  `"sujeito": "the eye of a goat"` enquadra pela cabeça; `"marca_auto": {"texto": ...}` desenha o
  círculo animado que segue o objeto. Prefira partes pequenas (olho, nariz): "head" às vezes
  devolve o animal inteiro.
- Clipe horizontal importante (clipe-âncora): `"layout": "inteiro"` (clipe inteiro sobre fundo
  desfocado, nada cortado, créditos visíveis). `"velocidade": 0.5` = câmera lenta.
  `"manter": true` = não dividir a cena longa.

## 3. Baixar em HD os escolhidos
```
python3 -m viitu.clipes baixar <projeto> pixabay <id>
python3 -m viitu.clipes baixar <projeto> pixabay-foto <id>
```

## 4. cenas.json
- `"em"`: trecho da narração onde a cena começa · `"clipe"` · `"inicio"` (segundo no clipe)
- Sem `"foco"`: o editor **enquadra sozinho no sujeito** (YOLO). Se o detector pegar o corpo
  em vez da cabeça, defina `"foco": [x, 0.5]` (posição do recorte 9:16) e `"alvo": [x, y]`
  (para onde o zoom vai, dentro do recorte).
- `"marca": {"x":..,"y":..,"r":..}`: círculo vermelho sobre o detalhe (coordenadas 1080x1920).
- `"efeito": "girar" | "desgirar"` para demonstrações.

## 5. Depois
Montagem, verificações e prancha: `/editar`.

## Fontes
- Pixabay (principal, livre), Wikimedia Commons (reserva, instável na nuvem).
- Clipes do usuário: TikTok por link direto (tentar baixar), Reddit/YouTube via link do Drive.
- Nunca remover marca d'água de vídeo de terceiros; dar crédito na descrição.


## Trava de números
Antes de mostrar qualquer vídeo ao dono: `python3 -m viitu.provar <link> --papel validacao|bruto` e copiar a linha (rótulo + views conferidas + link).
