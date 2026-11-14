---
name: clipes
description: Encontra e baixa vídeos/fotos para representar o tema escolhido do Viitu Shorts (Pixabay, Wikimedia Commons, clipes do usuário via Google Drive). Use quando o usuário digitar /clipes ou pedir vídeos/cenas para o tema.
---

# /clipes

Objetivo: montar a **paleta visual** do vídeo: uma cena forte para cada ideia/palavra-gatilho do roteiro.

## Passos

1. **Lista de cenas:** a partir do tema (e do roteiro, se já existir), liste de 8 a 15 cenas.
   Cada cena = o que a tela precisa mostrar (ex.: "close da pupila horizontal da cabra").
   A cena do **frame 0** (gancho) é a mais importante: tem que ser a imagem mais impressionante.

2. **Buscar no Pixabay** (fonte principal, vídeo livre e sem crédito obrigatório):
   ```
   python3 -m viitu.clipes buscar "<termo curto em inglês>" -n 4 --miniaturas <scratchpad>/mini/<cena>
   ```
   - Use **termos curtos** (2 palavras: "goat eye", "gecko eye"). Termos longos trazem lixo.
   - Monte uma prancha das miniaturas com ffmpeg (`tile=4xN`) e **olhe** (Read) para escolher.
   - Evite vídeos marcados "ai generated" quando houver opção real.

3. **Reserva: Wikimedia Commons** (fotos de alta qualidade, licença livre; instável na nuvem, erro 429):
   `--fontes commons`. Foto entra no vídeo com zoom lento.

4. **Clipes do usuário** (Reddit/TikTok/Douyin): o usuário baixa no celular, sobe no Google Drive
   e manda o link compartilhado. YouTube e Reddit bloqueiam downloads a partir da nuvem.

5. **Baixar os escolhidos:**
   ```
   python3 -m viitu.clipes baixar <projeto> pixabay <id>
   ```
   Projeto = `vdNNN_<slug>` (ex.: `vd002_pupilas`). Os créditos vão para `projetos/<projeto>/creditos.txt`.

6. **Responder curto:** cenas encontradas (✅), cenas faltando (❌) e o que o usuário precisa
   mandar pelo Drive, se for o caso. Mídia não vai para o git (`.gitignore`).

## Fontes descartadas
- Pexels: a chave salva no cofre recebe prefixo "Bearer" e o Pexels recusa (401).
- YouTube Creative Commons: resultados irrelevantes.
