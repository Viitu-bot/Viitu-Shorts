---
name: clipes
description: Escolhe e baixa os VÍDEOS que representam cada frase do roteiro do Viitu Shorts, por função psicológica, analisando os clipes de verdade (nitidez, movimento, onde está o sujeito). Use quando o usuário digitar /clipes ou pedir cenas para o tema/roteiro.
---

# /clipes: escolher cenas como um editor

Regra de ouro: **vídeo, não foto.** Foto só para uma prova visual impossível em vídeo (ex.: macro
de pupila) ou para uma demonstração com efeito, no máximo 2 vezes por vídeo.
**Clipe-âncora primeiro:** se existir um vídeo real do fenômeno (Reddit/TikTok/Douyin, enviado
pelo usuário via link do Drive ou TikTok), ele é a espinha do vídeo e o stock só completa.

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

## 5. Revisão obrigatória
Depois do render, extraia ~25 quadros (um por cena) numa prancha e olhe. Corrija
enquadramento e cenas ruins **antes** de mandar ao usuário.

## Fontes
- Pixabay (principal, livre), Wikimedia Commons (reserva, instável na nuvem).
- Clipes do usuário: TikTok por link direto (tentar baixar), Reddit/YouTube via link do Drive.
- Nunca remover marca d'água de vídeo de terceiros; dar crédito na descrição.
