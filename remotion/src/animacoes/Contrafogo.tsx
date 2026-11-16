import React from 'react';
import {AbsoluteFill, interpolate, random, useCurrentFrame} from 'remotion';

// Mapa visto de cima: mata, incêndio descendo, faixa queimada (contrafogo) e casas protegidas.
// fase "faixa": a linha se desenha (lápis) e a faixa queima da esquerda para a direita enquanto o incêndio avança.
// fase "apaga": o incêndio chega na faixa, não tem o que queimar e morre (vira fumaça).
// Tudo é função do quadro (determinístico). eventos = quadros (relativos à cena) das palavras-gatilho.

const W = 1080;
const H = 1920;
const FAIXA_Y0 = 830;
const FAIXA_Y1 = 990;

type Props = {fase: 'faixa' | 'apaga'; dur: number; eventos: Record<string, number>};

const ARVORES = Array.from({length: 300}, (_, i) => ({
  x: random(`ax${i}`) * (W + 80) - 40,
  y: random(`ay${i}`) * (H + 80) - 40,
  r: 30 + random(`ar${i}`) * 26,
  c: ['#1f5a2a', '#24672f', '#1a4d24', '#2c7537'][Math.floor(random(`ac${i}`) * 4)],
}));

const CASAS = [140, 340, 540, 740, 940].map((x, i) => ({x, y: 1620 + (i % 2) * 70}));

const borda = (x: number, yF: number, f: number) =>
  yF + Math.sin(x / 60 + f * 0.35) * 16 + Math.sin(x / 23 - f * 0.6) * 7;

export const Contrafogo: React.FC<Props> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

  // posição da frente do incêndio
  const yF = fase === 'faixa'
    ? interpolate(f, [0, dur], [260, 600], cl)
    : interpolate(f, [0, Math.max((eventos.apaga ?? 14) - 2, 6)], [640, FAIXA_Y0 + 6], cl);
  // altura das chamas (some na fase apaga)
  const tApaga = eventos.apaga ?? Math.round(dur * 0.4);
  const chama = fase === 'apaga' ? interpolate(f, [tApaga, tApaga + 16], [1, 0], cl) : 1;

  // faixa: linha a lápis + queima da esquerda para a direita
  const tLinha = eventos.linha ?? 6;
  const tQueima = eventos.queima ?? tLinha + 12;
  const linha = fase === 'faixa' ? interpolate(f, [tLinha, tLinha + 10], [0, 1], cl) : 1;
  const queimaX = fase === 'faixa' ? interpolate(f, [tQueima, tQueima + 20], [0, W + 40], cl) : W + 40;

  const pts: string[] = [];
  for (let x = -20; x <= W + 20; x += 20) pts.push(`${x},${borda(x, yF, f).toFixed(1)}`);
  const queimado = `M-20,-20 L${pts.join(' L')} L${W + 20},-20 Z`;
  const linhaBorda = `M${pts.join(' L')}`;

  const zoom = interpolate(f, [0, dur], [1.0, 1.06], cl);
  const per = 2 * W;

  return (
    <AbsoluteFill style={{backgroundColor: '#2d5a26', transform: `scale(${zoom})`}}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <defs>
          <linearGradient id="chama" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ff3d00" />
            <stop offset="0.6" stopColor="#ff9100" />
            <stop offset="1" stopColor="#ffe066" />
          </linearGradient>
          <filter id="brilho" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="14" /></filter>
          <filter id="fumaca" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22" /></filter>
        </defs>

        {/* chão e árvores (as da faixa somem quando ela queima) */}
        <rect width={W} height={H} fill="#3a6b2e" />
        {ARVORES.map((a, i) => {
          const naFaixa = a.y > FAIXA_Y0 - 20 && a.y < FAIXA_Y1 + 20;
          if (naFaixa && a.x < queimaX - 30) return null;
          return (
            <g key={i}>
              <circle cx={a.x + 6} cy={a.y + 8} r={a.r} fill="rgba(0,0,0,0.25)" />
              <circle cx={a.x} cy={a.y} r={a.r} fill={a.c} />
              <circle cx={a.x - a.r * 0.3} cy={a.y - a.r * 0.3} r={a.r * 0.45} fill="rgba(255,255,255,0.08)" />
            </g>
          );
        })}

        {/* faixa queimada (terra escura) */}
        <rect x={0} y={FAIXA_Y0} width={Math.min(queimaX, W)} height={FAIXA_Y1 - FAIXA_Y0} fill="#2b2118" />
        {fase === 'faixa' && queimaX > 0 && queimaX < W + 40 && (
          <g>
            <rect x={queimaX - 40} y={FAIXA_Y0} width={60} height={FAIXA_Y1 - FAIXA_Y0} fill="url(#chama)" filter="url(#brilho)" />
            <rect x={queimaX - 20} y={FAIXA_Y0} width={22} height={FAIXA_Y1 - FAIXA_Y0} fill="#ffb300" />
          </g>
        )}
        {/* linhas a lápis marcando a faixa */}
        {[FAIXA_Y0, FAIXA_Y1].map((y) => (
          <line key={y} x1={0} y1={y} x2={W} y2={y} stroke="#FFD400" strokeWidth={9} strokeLinecap="round"
            strokeDasharray={per} strokeDashoffset={per * (1 - linha) + per / 2} opacity={0.95} />
        ))}

        {/* área já queimada pelo incêndio + brasas */}
        <path d={queimado} fill="#1c1611" />
        {Array.from({length: 60}, (_, i) => {
          const cx = random(`cx${i}`) * W;
          const cy = random(`cy${i}`) * (yF - 30);
          return cy > 0 ? <circle key={`c${i}`} cx={cx} cy={cy} r={18 + random(`cr${i}`) * 30} fill="#3a332c" opacity={0.5} /> : null;
        })}
        {Array.from({length: 40}, (_, i) => {
          const bx = random(`bx${i}`) * W;
          const by = random(`by${i}`) * (yF - 40);
          const o = 0.3 + 0.7 * Math.abs(Math.sin(f * 0.3 + i));
          return by > 0 ? <circle key={i} cx={bx} cy={by} r={4} fill="#ff6d00" opacity={o * 0.6} /> : null;
        })}

        {/* frente do incêndio: brilho + língua de fogo tremulando */}
        {chama > 0.01 && (
          <g opacity={chama}>
            <path d={linhaBorda} stroke="#ff5a00" strokeWidth={120 * chama} fill="none" filter="url(#brilho)" />
            <path d={linhaBorda} stroke="url(#chama)" strokeWidth={46 * chama} fill="none" strokeLinejoin="round" />
            {Array.from({length: 27}, (_, i) => {
              const x = i * 41 + 10;
              const y = borda(x, yF, f);
              const h = (60 + 45 * Math.abs(Math.sin(f * 0.5 + i * 1.7))) * chama;
              return <path key={i} d={`M${x - 16},${y} Q${x},${y + h * 1.4} ${x + 16},${y} Z`} fill="#ffcc33" opacity={0.9} />;
            })}
          </g>
        )}

        {/* fumaça subindo da frente (fica mais forte quando o fogo morre) */}
        <g filter="url(#fumaca)">
          {Array.from({length: 9}, (_, i) => {
            const sx = (i * 137 + f * 2.2) % (W + 200) - 100;
            const sy = yF - 60 - ((f * 3 + i * 50) % 260);
            const op = fase === 'apaga' ? 0.25 + 0.35 * (1 - chama) : 0.3;
            return <circle key={i} cx={sx} cy={sy} r={70 + (i % 3) * 25} fill="#9a9a9a" opacity={op} />;
          })}
        </g>

        {/* casas que a faixa protege */}
        {CASAS.map((c, i) => (
          <g key={i} transform={`translate(${c.x},${c.y})`}>
            <rect x={-46} y={-30} width={92} height={70} fill="#e9dcc3" stroke="#3b2a1a" strokeWidth={5} />
            <path d="M-58,-28 L0,-78 L58,-28 Z" fill="#b5442c" stroke="#3b2a1a" strokeWidth={5} strokeLinejoin="round" />
            <rect x={-14} y={2} width={28} height={22} fill="#ffd54a" />
          </g>
        ))}
      </svg>
    </AbsoluteFill>
  );
};
