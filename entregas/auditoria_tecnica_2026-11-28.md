# Auditoria técnica completa — Viitu Shorts (28/11/2026)

## 1. Código e ferramentas
| Item | Estado |
|---|---|
| 43 módulos Python (`viitu/`) | ✅ todos compilam |
| Gemini, ElevenLabs, Pixabay, Internet Archive, Sketchfab, yt-dlp (TikTok/X/Instagram) | ✅ funcionando |
| API do YouTube | ❌ sem permissão (chave ausente) → números só por print do dono |
| Pexels | ❌ chave recusada → apagar o "Network secret" api.pexels.com nas configurações (a variável basta) |
| Wikimedia Commons | ❌ bloqueio temporário (excesso de pedidos) → TikTok/X/Archive |
| Modelos "pro" do Gemini e Gemma | ❌ sem cota na chave grátis → conselho usa os "flash" |
| Ambiente (instalação automática) | ✅ CORRIGIDO: agora reinstala torch, librosa, Remotion e o ouvido (earshot) em toda sessão nova (antes, só ffmpeg/yt-dlp) — vale a partir da próxima sessão nova |

## 2. Travas automáticas × reclamações do dono
As 34 reclamações agora apontam para uma trava ou um passo conferido:
| Trava | Pega o quê | Reclamação |
|---|---|---|
| R0 | CTA/resumo no fim, partes do roteiro | 7, 19 |
| R1 / R10 | clipe repetido, imagens parecidas | 1, 21 |
| R2 / R17 | 3D picotado; vídeo SEM 3D do mecanismo | 3, 33 |
| R3 / R5 | gancho com foto/3D/baixa resolução | 4, 11 |
| R4 / R12 / R13 / R15 | desfocado, preto e branco, faixa preta, câmera lenta que engasga | 2, 23, 27, 31 |
| R6 | loop | 19 |
| R8 | ambiência, foley (agora BARRA se menos da metade das cenas tem som do que aparece), virada sonora, som na ação | 8, 12, 15, 26, 28 |
| R9 | ritmo: cena comum ≤ 3 s, ação ≤ 4,5 s, média 1,5–2,5 s | 30, decisão 28/11 |
| R11 | voz lenta | 21 |
| R14 | cena atravessando corte interno | 13 |
| R16 | sem ponto de mira, câmera parada, alvo na área que o YouTube cobre | 33, 34 |
| **R18 (nova)** | música ausente, fora da biblioteca de jogo antigo, ou igual à do vídeo anterior | 18, 31 |
| Ouvido (earshot) | efeito que não soa como o pedido | 12, 17, 20 |
| SOM MEDIDO | música audível, efeito por cima da voz, impacto, ding | 8c–8e, 25, 29 |
Ficam no OLHO (sem trava possível, conferidos nas pranchas): cena casa com a frase, gancho com urgência de verdade,
clímax no instante, entonação da voz (ouvido do dono).
Teste: o vd022 passa em tudo; o vd021 seria barrado hoje (sem ponto de mira e sem 3D — feito antes dessas regras).

## 3. Regras escritas (contradições)
- Faxina do conselho: 10 contradições; 8 eram texto velho → marcados como superados (BÍBLIA com autorização do dono);
  2 eram erro do conselho (legenda de baixo, que evita cobrir o sujeito; e o tempo de cena, que virou decisão do dono).
- Também marcados como superados: tabela de trilhas antiga (`biblioteca_sons.md`), valores de mixagem de 18/11
  (`logica_editor.md`), música pela tabela antiga (skill /roteiro), foley só Sonniss (skill /editar).
- Em conflito, vale: `edicao/especificacao.json` (números) → CLAUDE.md → BÍBLIA (com os "superado" apontando a regra atual).

## 4. Automático
- `python3 -m viitu.pipeline previa <p>`: triagem → montagem R0–R18 → decupagem + ouvido → editor → partes → som final +
  SOM MEDIDO → faixa preta; para no 1º ❌. Testado no vd022: passou em tudo.
- `python3 -m viitu.pipeline final <p> "TÍTULO"`: render → entrega → capa → cópia do vídeo.
- `/conselho`: decisão nova do dono passa por 5 conselheiros com base (canal + YouTube + nicho) antes de virar regra.
- Fica com o dono: escolher gancho, aprovar roteiro e storyboard, ouvir/assistir e publicar.

## 5. Pendências do dono (não bloqueiam)
1. Apagar o "Network secret" do Pexels nas configurações do ambiente.
2. (Opcional) chave da API do YouTube, para números automáticos.
3. Ouvir a amostra das músicas de jogo antigo e dizer se algum clima está errado.
