---
name: animacao
description: Cria a animação 3D explicativa do Short (Three.js no Remotion) para a cena que não existe em vídeo, é difícil de achar ou impossível de filmar — o "porquê" desenhado. Use quando o roteiro tiver um trecho de mecanismo/explicação, quando faltar clipe para uma cena, ou quando o usuário pedir animação/3D.
---

# /animacao: o mecanismo em 3D

> **Planta oficial:** `edicao/formato.md` (batidas, tempos, B-roll, quando usar 3D, som). Siga-a.

**Regra do canal:** toda parte explicativa que não tem vídeo bom (mecanismo invisível, dentro de algo, forças,
"o que acontece se", algo raro ou impossível de filmar) vira 3D. Clipe real fica no gancho e como prova.
Base: 40–53% dos vídeos dos canais do nicho têm animação; inserções de 1–10 s (`edicao/logica_editor.md`).

**Sempre 3D, nunca 2D** (dono: a animação 2D do mapa ficou simples; o 3D é o padrão do canal).

## Padrão de uso
- Narrativa: clipe real (gancho/contexto) → **3D explica em UM bloco contínuo** → clipe real como prova/virada.
  NUNCA intercalar clipe real dentro da explicação (dono, vd009 18/11: "o 3D foi cortado pelas imagens reais no meio
  da explicação, não faz sentido"). Várias fases do mecanismo = várias cenas 3D SEGUIDAS (a câmera continua).
- Bloco de 6–10 s no Bastidor (3–5 s no Tiro Curto), máximo 45% do vídeo; eventos nas palavras
  (`"eventos": {"puxa": "puxa o ar"}`). Trava: `viitu.montagem` regra R2.
- Estilo: maquete low-poly vista de cima, câmera inclinada que se aproxima e gira um pouco, cores fortes,
  setas para forças invisíveis (vento, calor, pressão). Formato vertical: TUDO que importa precisa caber no quadro.
- **Direção e física do movimento:** todo veículo/bicho anda para onde o nariz/cabeça aponta (no vd005 o avião
  voava de ré); inclinação coerente (sobe de nariz para cima, plana de nariz um pouco abaixo, arredonda antes de
  tocar); câmera nunca dentro de objeto (prédio, chão) nem cortando o sujeito. Conferir em quadros soltos.
- **Lógica física consistente:** o que o fogo/água/etc. já atingiu muda de estado e não volta; no encontro de
  duas frentes não sobra faixa intacta; nada some sem motivo.

## Nível de qualidade do 3D (dono, 17/11: "o 3D tá básico, a gaivota saiu sem bico")
- **3D só no trecho explicativo** (um bloco contínuo): o mecanismo impossível de filmar. O resto é clipe real.
- **Iluminação HDRI sempre:** céu 360° real do Poly Haven (CC0) como `scene.environment` (+ fundo quando for ao ar livre);
  aço com metalness 0.85 / roughness 0.22. Modelo: componente `Ambiente` em `Starship3D.tsx`; arquivo `assets/texturas/*_hdri.jpg`.
- **Modelos prontos em vez de caixas** (bicho, veículo, máquina): GLB carregado com `GLTFLoader`, animação do modelo
  sincronizada ao quadro. Fontes: Poly Haven models (CC0, objetos realistas), Quaternius (CC0, bichos animados),
  Sketchfab (CC-BY, milhões, precisa de token da conta grátis), NASA 3D Resources (domínio público, naves).
  Crédito do autor na descrição quando CC-BY.
- Próximo nível a testar: Blender 4.0 (disponível no apt) renderizando a inserção em Cycles/CPU.

## Visual vivo (padrão desde o vd006)
- **Cenário completo**, não objeto solto no vazio: chão, estrada, grama, céu com neblina. Texturas reais CC0 do
  Poly Haven em `assets/texturas/` (baixar `Diffuse` 1k pela API `api.polyhaven.com/files/<nome>`; o editor copia
  para `public/tex`). Modelo: `remotion/src/animacoes/Lama3D.tsx`.
- Carregar texturas com o padrão do Lama3D (`useTexturas` + `<Liberar>`: o quadro só sai depois de um redesenho
  com a textura). Sem isso o chão sai PRETO em quadros aleatórios.
- `useTexturas` no topo do componente = TODO `ThreeCanvas` de TODAS as fases precisa do `<Liberar>` (fase sem ele
  trava o render por timeout — vd007).
- Componente com várias fases (modelo `remotion/src/animacoes/Starship3D.tsx`): 1 arquivo, câmera e cenário por fase,
  objetos reaproveitados (nave, torre). Confira se o lado certo do objeto encara a câmera (escudo preto ≠ aço).
- NÃO usar normal map nem sombras (`shadows`) — no render sem GPU escurecem/pretejam o chão.
- Efeitos com física: pedaços com gravidade e respingos esticados na direção do voo (lama, água, faísca),
  tremor/afundar do objeto, fumaça. Nada de "bolinhas" paradas.
- Superfície irregular (poça, terreno): plano com vértices deslocados e borda irregular; borda baixa (sem "parede").

## 3D sobreposto a clipe real
`ThreeCanvas` com `gl={{alpha: true}}` e fundo transparente por cima do clipe (ex.: gaivotas passando pela asa
vista da janela). Bichos: forma característica (gaivota = asa em "M" com ponta preta), voando de FRENTE para onde
se movem, batida de asa lenta, tamanho que não domina a tela.

## Como fazer
1. Copie o modelo `remotion/src/animacoes/Contrafogo3D.tsx` para `remotion/src/animacoes/<Tema>3D.tsx`.
   Ele mostra: `ThreeCanvas` do `@remotion/three`, câmera via `useThree`, objetos em código (árvores, chamas,
   casas, pessoas, setas), fumaça, tudo como função do quadro (`useCurrentFrame`; nada de relógio/aleatório
   sem semente — use `random("semente")`).
2. Registre no `remotion/src/Short.tsx` (bloco "animações explicativas": `a.nome === '<tema>3d'`).
3. No `cenas.json`, a cena: `"animacao": {"nome": "<tema>3d", "fase": "...", "eventos": {...}}`,
   `"manter": true`, `"revisao": "manual"`, `"foley"` do que se vê; o `"clipe"` fica escondido (qualquer Pixabay do projeto).
4. **Sound design do 3D (obrigatório — dono: "o 3D sem som acabou com a imersão")**:
   - `"foley"` da cena = ambiência do LUGAR da animação (ex.: `turbina`, `hangar`, `voo`; tipos em `CAMADAS`, `viitu/foley.py`).
   - `"sfx"` na animação = um som para CADA ação que acontece na tela, amarrado ao evento:
     `{"evento": "batesse", "busca": "heavy body impact thud", "exigir": "impact|thud", "db": -3, "desloc": 0, "dur": 1.5}`.
     Toda batida, quebra, disparo, explosão, splash, motor ligando/desligando ganha som.
   - Conferir os nomes escolhidos em `assets/sonniss/escolhas.json` (o CLAP confunde: "ligando" ≠ "desligando",
     sci-fi, turbina eólica ≠ jato) e trocar `busca`/`exigir` do que não combinar.
5. `python3 -m viitu.editar <p> --remotion` e confira 3–4 quadros soltos de cada fase
   (`npx remotion still ... --frame=N --scale=0.3`) ANTES do render completo. Ajuste câmera/legibilidade.
6. O 3D renderiza sem GPU (software): mais lento, funciona. Modelos/texturas extras: Poly Haven (CC0).
7. Técnica nova que der certo → `edicao/manual_edicao.md` (seção animação).
