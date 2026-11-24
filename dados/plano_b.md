# Plano B do Viitu — o processo NUNCA para (revisão de 18/11/2026)

Regra do dono: "se uma cota acabar, não pode parar o processo". Toda etapa tem fonte principal → reservas, na ordem.
Começo de sessão: `python3 -m viitu.saude` (testa tudo em ~1 min) + `vidiq_balance` (créditos do dia).

## Falhas que JÁ aconteceram (e a correção)
| Quando | O que falhou | Efeito | Correção aplicada |
|---|---|---|---|
| 18/11 madrugada | Cota de BUSCA da API do YouTube (10 mil/dia) | radar parou | radar pelo vidIQ (skill /tema); radar não trava mais (segue com o que coletou); views continuam (videos.list é outra cota) |
| 18/11 tarde | Créditos do vidIQ gastos — e eles são **150 por MÊS** (renova dia 17), não por dia | busca automática de clipe parou | busca de clipe agora é pela busca web (TikTok/X/Instagram) + yt-dlp, sem cota; vidIQ só para tema/título |
| 18/11 o dia todo | Wikimedia Commons 429 (bloqueio do nosso IP) | sem fotos/vídeos do Commons | Internet Archive, TikTok/Instagram/X via yt-dlp; não ficar esperando o Commons |
| 18/11 | Chave do Pexels salva com "Bearer" (401) | Pexels inútil | dono cola a chave PURA nas configurações do ambiente (o formulário sempre põe Bearer) |
| 18/11 | "ElevenLabs fora" era falso alarme: só a consulta de assinatura trava | saúde acusava falha | teste da saúde passou a usar /v1/models; a voz gera normal |
| 18/11 | Reinício da sessão matou render em segundo plano | vídeo não saiu | render SEMPRE com `run_in_background` da ferramenta (não `&` no shell); conferir o log ao voltar |
| 18/11 | ElevenLabs Music 429 em pedidos paralelos | trilhas falharam | gerar UMA de cada vez |
| 18/11 | Música famosa com direitos | risco de Content ID | modo `"musica": "app:<faixa>"` (dono adiciona no app) |
| 17–18/11 | Sound design cobrindo a voz | reclamação do dono | sidechain universal (`viitu/mixagem.py`) + regra de margem 10 dB |
| 18/11 noite | Render travou no áudio ("Missing ')'" no ffmpeg) | vd009 não saiu | duck gravado dentro da música/foley/ambiente (`mixagem.assar_duck` → `*_d.m4a`); volumes em degraus de 1,5 dB no Short.tsx |
| 18/11 | Vídeo montado com foto parada / 3D demais por falta de fonte | dono reprovou o vd009 v1 | regra no /clipes: se a fonte falhar, trocar de fonte ou pedir links — nunca foto parada no gancho |

## Cadeia de reservas por etapa
| Etapa | 1ª | 2ª | 3ª | 4ª |
|---|---|---|---|---|
| Tema (radar) | `viitu.radar` (API YouTube; o Claude classifica, coleta em cache) | vidIQ trending/outliers + youtube_search | `viitu.quente` (Google Trends) | Hall da Fama / `dados/pesquisas` antigas |
| Lacuna PT-BR | `viitu.tema lacuna` (API) | `vidiq_youtube_search` regionCode BR | — | — |
| Views (trava) | `viitu.provar` (videos.list, quase nunca acaba) | print do dono | — | — |
| Clipes reais | busca web TikTok/X/IG + yt-dlp | Pixabay / Pexels | Internet Archive / NASA (480p: só prova) | vidIQ (se houver crédito) → dono manda link |
| 3D | modelos Sketchfab / Poly Haven | modelo em código | — | — |
| Voz | ElevenLabs ("Minha voz", clone do dono) | esperar e repetir | — | — |
| Música | biblioteca própria (`assets/musica`) | `app:` música do app do YouTube | Kevin MacLeod (CC BY) | — |
| Efeitos | Sonniss (cache) | Mixkit kit | ElevenLabs sound-generation | — |
| Análise de vídeo | medições próprias + o Claude olha a prancha | Gemini só com --gemini (2ª opinião) | — | — |

## Orçamento diário (para não acabar no meio)
- **API do YouTube (busca, 10 mil):** radar ~5,5 mil (1x por dia, logo cedo) + lacunas extras ≤ 20 (2 mil). Resto: reserva.
- **vidIQ (150 créditos POR MÊS, renova dia 17):** ~35 por semana. Tema ≤ 20/semana · títulos ≤ 10 · clipes: não depende mais dele.
- **Gemini:** grátis com limite diário; análises em lote de canal só fora do dia de produção.
- **ElevenLabs:** voz ~400 caracteres por vídeo; sons/trilhas novas só quando faltar na biblioteca.

## Fluxo que evita engasgo no fim
1. Saúde + créditos → 2. tema → 3. roteiro → 4. **voz já** (se o ElevenLabs cair, ainda há tempo) →
5. **clipes antes do 3D** (se faltar imagem real, resolve antes de gastar render) → 6. 3D → 7. editar + verificações → 8. render.
