# DE ONDE VEM CADA REGRA (auditoria "sem achismo" — dono, 19/11/2026)
Toda regra/número do projeto tem uma base. **D** = regra do Dono (BÍBLIA) · **M** = Medido (fonte + amostra) ·
**H** = Hipótese do Claude (sem base ainda). **H nunca bloqueia vídeo**: vira aviso e entra no plano de teste abaixo.
Número novo só entra no projeto com a base escrita aqui.

## Roteiro e estrutura
| Regra | Valor | Base | Fonte |
|---|---|---|---|
| 5 partes + CTA interativo + loop suspenso | — | D | protocolo HISA do dono; BÍBLIA §1 |
| Tiro Curto / Bastidor | 12–15 s / 20–28 s | D | HISA 2.0 do dono |
| Gancho ≤ 3 s, desmistificação, "mas tem um porém" | — | D + M | dono; 11 raio-X do Hall (funções: explicação 18, gancho 11, virada 10, desmistificação 8) |
| Fato com fonte, nada [INCERTO] | — | D | protocolo do dono |

## Imagem
| Regra | Valor | Base | Fonte |
|---|---|---|---|
| Troca de cena | quando a ideia/etapa muda; tomada que prende FICA | D + M | dono 19/11 ("aquilo dali já é o que está prendendo"); a média de 1,5 s/cena dos 35 Shorts é descrição, não obrigação |
| Não picotar a mesma ação em cortes do mesmo clipe | — | D | dono 19/11 |
| Clipe em ≤ 2 cenas (exceto bruto cronológico em ordem) | 2 | D | reclamações de repetição (6x) |
| Fontes diferentes ≥ 60% das cenas | 60% | **H** | aviso; testar |
| Seta no frame 0 | — | M | 80% dos 35 Shorts |
| Punch-in na palavra-chave | — | M | 91% dos 35 |
| Câmera lenta no momento satisfatório | — | M | 49% dos 35 |
| Resolução útil ≥ 600 px | 600 | M (técnico) | 1080p horizontal recortado = 607 px; abaixo disso a imagem amolece no celular |
| Nitidez mínima | 40 | M (calibrado) | clipes reais: 8 e 23–34 = borrados vistos na prancha; 62+ = nítidos |
| 3D em UM bloco, só no trecho explicativo | — | D | dono (vd009: "3D cortado no meio da explicação") |
| 3D ≤ 45% do vídeo / começa entre 25% e 60% | — | **H** | aviso; 40% dos 35 Shorts têm animação, mas a duração não foi medida |
| Sem logo/legenda/rosto de terceiro | — | D | reclamações do dono |

## Som
| Regra | Valor | Base | Fonte |
|---|---|---|---|
| Ding + flash no frame 0, audível | ding no nível da voz | D | identidade do dono |
| Música = faixa conhecida do nicho, pelo app | por formato | M + D | 33 Shorts (pesquisa/musicas_nicho.json): The Lost Soul Down ×4, The Next Episode ×3, Montagem PR Funk ×2; dono 19/11 |
| Trilha própria (exceção) sob a fala / nas pausas | −18 / −6 dB | M | 35 Shorts (resumo_edicao.json) — ajuste do ouvido do dono 17/11: −14/−6 |
| Whoosh | −3 dB, na maioria dos cortes | M | 35 Shorts (34/35 corte seco + whoosh; 29/30 na maioria dos cortes) |
| Pop | −5 dB | M | 35 Shorts |
| Boom da virada | 0 dB (1–2 por vídeo) | M | 35 Shorts |
| Riser | −6 dB | M | 35 Shorts |
| Som de ação (hit) | −6 dB, só quando o som certo existe | M + D | 35 Shorts (foley em 93%); BÍBLIA §4 |
| Ambiência só escolhida (nunca adivinhada) | — | D | vd011: adivinhação pôs galo numa fábrica |
| Som certo: nome do arquivo tem a palavra do pedido | — | M | auditoria: 24/78 escolhas automáticas estavam erradas |
| Som de ação no instante da ação NA IMAGEM (`no_clipe`), não na palavra | — | D | dono 19/11, vd011: "os efeitos não encaixam" |
| Ação descrita na frase aparece inteira (sem pular o meio) | — | D | dono 19/11, vd011: feltro em 8 |
| Montagem parte por parte, conferida antes da próxima | — | D | dono 20/11 |
| Efeito precisa SOAR como o pedido (earshot strong/plausible) | — | M | earshot (CLAP+AST): teste 20/11, som certo em 1º em 5/6 pedidos e 'galo' = nenhum; autor: 'strong' certo 98% em teste separado |
| Leito ≥ 10 dB abaixo da voz | 10 dB | M | pesquisa de 43 Shorts: trilha 12–18 dB abaixo da voz |
| Efeitos curtos até 4 dB da voz | 4 dB | M (derivado) | whoosh medido a −3 dB |
| Música cresce depois da virada (×2) | ×2 | **H** | M diz que sobe na virada, mas a quantidade não foi medida |

## Temas
| Regra | Valor | Base | Fonte |
|---|---|---|---|
| Validação ≥ 1M views + lacuna PT em 3 buscas | — | D | regra do dono |
| Categoria: motivo oculto > recorde > perigo | — | M | 625 vídeos de 3 canais BR (logica_temas.md) |
| Processo de bruto cronológico é prioridade | — | D | dono 19/11 |
| Pesos do radar (frescor 25, força 25, categoria 20, lacuna 20, canal 10) | — | **H** | aviso; testar contra as views reais dos nossos vídeos |
| Rodízio semanal de formatos | — | **H** | testar |
| Mínimo de fontes por formato (7, 5, 4…) | — | **H** | aviso |

## Ferramenta de medição (20/11)
`rea-video decompose` (github.com/JuneYaooo/rea-video, Apache-2.0) mede tomadas, cortes, BPM, voz e instante dos
efeitos de um vídeo de referência sem IA paga. Validado no vd013: 10/10 cortes exatos; efeitos 7/10 no instante (o
rótulo do tipo erra). Medição de referência feita com ela pode virar regra **M** (escrever a amostra aqui).

## Plano de teste das hipóteses (com dados do SEU canal, não de opinião)
1. Depois de cada vídeo postado: views em 48 h, % que não deslizou, retenção média (print do Studio ou vidIQ
   channel analytics) → `dados/desempenho.md`, junto com formato, duração, % de 3D e nota do radar.
2. Com 3 vídeos por formato: comparar. O formato que performa sobe no rodízio; os pesos do radar são recalibrados
   pelo que de fato viralizou.
3. Só então uma **H** vira **M** (com a amostra escrita aqui) ou sai do projeto.
