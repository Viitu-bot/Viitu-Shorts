# Biblioteca de sons do Viitu (público adulto 25+) — organizada em 24/11
Os arquivos aqui são ATALHOS para `assets/` (o código continua lendo de lá; nada duplicado). Som novo baixado: salvar
na pasta certa daqui com nome em inglês descritivo (ex.: `sub_drop_short.mp3`) e conferir com
`earshot match <arquivo> "<o que deve soar>"` — só entra se der strong/plausible.

| pasta | para quê | quando | hoje |
|---|---|---|---|
| 01_gancho_impacto | riser curto, sub-drop, impacto cinematográfico sutil | SÓ nos 2 primeiros segundos ou na revelação | 5 |
| 02_transicoes_sutis | whoosh suave, corte de ar seco | troca de cena (no máx. 1 efeito a cada 3 s) | 4 |
| 03_foley_textura | sons reais e táteis (clique, câmera, relógio, máquina, água, motor) | o que aparece na tela | 52 |
| 04_trilhas_fundo | instrumental leve de curiosidade/investigação/tensão moderada, sem batida pesada | o vídeo todo, −22 a −26 dB | 6 |
| 05_ambiencia | SOM DO LUGAR em loop (oficina, fábrica, feira, rua, cozinha, escritório, obra, chuva, floresta, vento) — dono 27/11 | fundo de TODA cena (`"foley": "<nome do arquivo>"`), entra antes da biblioteca Sonniss | 10 |
| _proibidos | pop agudo, scratch de DJ, ukulele alegre, phonk/techno/lo-fi com batida, música infantil | nunca | 8 |

**Tempo do som (dono 26/11, vd018):** o som de algo que a narração NOMEIA (sirene, motor, tiro) entra NA palavra (ou
quando o objeto aparece), nunca antes — e nunca cobre a palavra anterior. Na dúvida, começar no ápice da imagem.

Regras: sem desenho animado, meme, boing, buzina, risada ou pop agudo · máx. 1 efeito a cada 3 s · efeitos −12 a −18 dB e
trilha −22 a −26 dB sob a voz (automático em `viitu/som_final.py`).

## LISTA DE GARIMPO (termos exatos em inglês — Freesound.org e Pixabay.com/sound-effects, licença CC0/Pixabay)
Faltam principalmente sons de gancho limpos e trilhas sem batida.
- **01_gancho_impacto:** `sub drop` · `cinematic sub boom` · `low impact hit cinematic` · `short riser 2 seconds` ·
  `reverse cymbal short` · `braam short` · `tension hit subtle` · `deep thud trailer`
- **02_transicoes_sutis:** `soft whoosh` · `subtle swish` · `air swipe short` · `transition whoosh soft` · `cloth swish` ·
  `paper swipe`
- **03_foley_textura:** `camera shutter dslr` · `metal click` · `mechanical switch click` · `clock ticking close` ·
  `page turn` · `paper rustle` · `keyboard typing mechanical` · `industrial machine hum` · `room tone office` ·
  `water drip close` · `zipper close` · `coin drop table`
- **04_trilhas_fundo:** `documentary curiosity ambient` · `investigation suspense underscore` · `mystery ambient pad` ·
  `light tension background no drums` · `minimal piano curious` · `science documentary background`
Filtro ao baixar: duração curta (efeito ≤ 2 s), sem voz, sem logo de marca d'água sonora.

## Sons CC0 (24/11) — `cc0_*`
45 sons CC0 do pacote do Barty-Bart/motion-graphics (Freesound/Kenney, CC0 = uso livre, sem crédito) em `assets/sfx/cc0/`;
só os 16 aprovados no ouvido (earshot "strong") entraram aqui com prefixo `cc0_`. Autor/fonte de cada um em
`assets/sfx/cc0/catalogo.json`. Licenças aceitas no canal: CC0 e Mixkit Free (nunca CC-BY-NC).
Timing (mesmo pacote): whoosh começa 2 quadros ANTES do corte; o riser TERMINA no impacto da revelação.

## Imersão (dono 27/11, vd021: "faltou atenção nos efeitos… o foley, a ambientação… toda aquela imersão")
Todo vídeo tem as 3 camadas, conferidas na decupagem:
1. **Ambiência** (05_ambiencia) em ≥ 70% das cenas — o lugar soa (oficina na serra, feira na demonstração…).
2. **Foley do que aparece** (03_foley_textura) — a coisa na tela faz barulho NA palavra/no ápice: motor da serra ligada
   (`serra_ligada`), a lâmina afundando (`lamina_afunda_mesa`), batida seca (`batida_seca_madeira`), freio (`freio_serra_clack`).
3. **Transição** (02_transicoes_sutis) em TODA troca: `whoosh_rapido` (cena de ação), `whoosh_grave` (antes da revelação),
   `swish_pano` (movimento de braço), `cc0_whoosh_fs830856` (suave padrão).
Sons novos de 27/11 gerados na ElevenLabs e aprovados no earshot (strong; `batida_seca_madeira` plausible). Recusados no
ouvido e NÃO usar: "whoosh suave" gerado (soou como pancada), "plateia espantada" (soou como aplauso/risada).
