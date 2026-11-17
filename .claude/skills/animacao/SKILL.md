---
name: animacao
description: Cria a animação 3D explicativa do Short (Three.js no Remotion) para a cena que não existe em vídeo, é difícil de achar ou impossível de filmar — o "porquê" desenhado. Use quando o roteiro tiver um trecho de mecanismo/explicação, quando faltar clipe para uma cena, ou quando o usuário pedir animação/3D.
---

# /animacao: o mecanismo em 3D

**Regra do canal:** toda parte explicativa que não tem vídeo bom (mecanismo invisível, dentro de algo, forças,
"o que acontece se", algo raro ou impossível de filmar) vira 3D. Clipe real fica no gancho e como prova.
Base: 40–53% dos vídeos dos canais do nicho têm animação; inserções de 1–10 s (`edicao/logica_editor.md`).

## Padrão de uso
- Narrativa: clipe real → **3D explica** → clipe real como prova → **3D mostra o resultado**.
- 1 ideia por animação, 3 a 6 s por entrada; sincronizar eventos às palavras (`"eventos": {"puxa": "puxa o ar"}`).
- Estilo: maquete low-poly vista de cima, câmera inclinada que se aproxima e gira um pouco, cores fortes,
  setas para forças invisíveis (vento, calor, pressão). Formato vertical: TUDO que importa precisa caber no quadro.
- **Lógica física consistente:** o que o fogo/água/etc. já atingiu muda de estado e não volta; no encontro de
  duas frentes não sobra faixa intacta; nada some sem motivo.

## Como fazer
1. Copie o modelo `remotion/src/animacoes/Contrafogo3D.tsx` para `remotion/src/animacoes/<Tema>3D.tsx`.
   Ele mostra: `ThreeCanvas` do `@remotion/three`, câmera via `useThree`, objetos em código (árvores, chamas,
   casas, pessoas, setas), fumaça, tudo como função do quadro (`useCurrentFrame`; nada de relógio/aleatório
   sem semente — use `random("semente")`).
2. Registre no `remotion/src/Short.tsx` (bloco "animações explicativas": `a.nome === '<tema>3d'`).
3. No `cenas.json`, a cena: `"animacao": {"nome": "<tema>3d", "fase": "...", "eventos": {...}}`,
   `"manter": true`, `"revisao": "manual"`, `"foley"` do que se vê; o `"clipe"` fica escondido (qualquer Pixabay do projeto).
4. `python3 -m viitu.editar <p> --remotion` e confira 3–4 quadros soltos de cada fase
   (`npx remotion still ... --frame=N --scale=0.3`) ANTES do render completo. Ajuste câmera/legibilidade.
5. O 3D renderiza sem GPU (software): mais lento, funciona. Modelos/texturas extras: Poly Haven (CC0).
6. Técnica nova que der certo → `edicao/manual_edicao.md` (seção animação).
