import React from 'react';
import {
  AbsoluteFill, Audio, OffthreadVideo, Sequence, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/fonts';

// fonte local (o navegador do render não baixa do Google Fonts atrás do proxy)
const fontFamily = 'Anton';
loadFont({family: fontFamily, url: staticFile('Anton-Regular.ttf')});

export type Palavra = {texto: string; f0: number; f1: number; destaque: boolean};
export type Marca = {f0: number; f1: number; cena_f0: number; pos: [number, number, number][]};
export type Plano = {fps: number; duracao_frames: number; palavras: Palavra[]; marcas: Marca[]; cortes: number[]};

// ---------- círculo desenhado à mão (traço de caneta com mola) ----------
const caminhoCirculo = (r: number, voltas: number) => {
  const pts: string[] = [];
  const inicio = -Math.PI * 0.6;
  const passos = Math.max(2, Math.round(90 * voltas));
  let comprimento = 0;
  let ant: [number, number] | null = null;
  for (let k = 0; k <= passos; k++) {
    const a = inicio + 2 * Math.PI * voltas * (k / passos);
    const rr = r * (1 + 0.06 * Math.sin(3 * a) + 0.03 * Math.sin(7 * a));
    const p: [number, number] = [rr * 1.08 * Math.cos(a), rr * 0.92 * Math.sin(a)];
    if (ant) comprimento += Math.hypot(p[0] - ant[0], p[1] - ant[1]);
    ant = p;
    pts.push(`${k === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`);
  }
  return {d: pts.join(' '), comprimento};
};

const CirculoMarca: React.FC<{marca: Marca}> = ({marca}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const i = Math.min(Math.max(frame - marca.cena_f0, 0), marca.pos.length - 1);
  const [x, y, r] = marca.pos[i];
  const local = frame - marca.f0;
  if (local < 0 || frame >= marca.f1) return null;
  // traço: desenha em ~12 frames com desaceleração (mola sem quicar)
  const traco = spring({frame: local, fps, config: {damping: 200}, durationInFrames: 12});
  // "pop": escala com leve quique no fim
  const pop = spring({frame: local, fps, config: {damping: 9, stiffness: 180, mass: 0.6}});
  const escala = interpolate(pop, [0, 1], [0.7, 1]);
  const pulso = 1 + 0.025 * Math.sin((local / fps) * Math.PI * 3);
  const {d, comprimento} = caminhoCirculo(r, 1.12);
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
      <g transform={`translate(${x},${y}) scale(${escala * (local > 14 ? pulso : 1)})`}>
        <path d={d} fill="none" stroke="rgba(0,0,0,0.45)" strokeWidth={20} strokeLinecap="round"
          strokeDasharray={comprimento} strokeDashoffset={comprimento * (1 - traco)} transform="translate(3,4)" />
        <path d={d} fill="none" stroke="#FF2222" strokeWidth={12} strokeLinecap="round"
          strokeDasharray={comprimento} strokeDashoffset={comprimento * (1 - traco)} />
      </g>
    </svg>
  );
};

// ---------- legenda: uma palavra por vez, com "pop" de mola ----------
const PalavraNaTela: React.FC<{p: Palavra}> = ({p}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 11, stiffness: 220, mass: 0.5}});
  const escala = interpolate(s, [0, 1], [0.55, 1]);
  const subida = interpolate(s, [0, 1], [24, 0]);
  return (
    <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', paddingTop: 560}}>
      <div style={{
        fontFamily, fontSize: p.destaque ? 138 : 124, letterSpacing: 2,
        color: p.destaque ? '#FFD400' : '#FFFFFF',
        WebkitTextStroke: '12px black', paintOrder: 'stroke fill',
        textShadow: '0 8px 18px rgba(0,0,0,0.55)',
        transform: `translateY(${subida}px) scale(${escala}) rotate(${p.destaque ? -2 : 0}deg)`,
      }}>{p.texto}</div>
    </AbsoluteFill>
  );
};

// ---------- "punch" de câmera nas palavras de destaque ----------
const usePunch = (palavras: Palavra[]) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  let z = 1;
  for (const p of palavras) {
    if (!p.destaque || frame < p.f0 || frame > p.f0 + 20) continue;
    const s = spring({frame: frame - p.f0, fps, config: {damping: 12, stiffness: 200}});
    z = Math.max(z, 1 + 0.045 * Math.sin(Math.min(s, 1) * Math.PI));
  }
  return z;
};

export const Short: React.FC<{plano: Plano}> = ({plano}) => {
  const z = usePunch(plano.palavras);
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      <AbsoluteFill style={{transform: `scale(${z})`}}>
        <OffthreadVideo src={staticFile('fundo.mp4')} muted />
      </AbsoluteFill>
      {plano.marcas.map((m, k) => (
        <React.Fragment key={k}>
          <CirculoMarca marca={m} />
          <Sequence from={m.f0} durationInFrames={20}><Audio src={staticFile('tick.mp3')} volume={0.9} /></Sequence>
        </React.Fragment>
      ))}
      {plano.palavras.filter((p) => p.texto).map((p, k) => (
        <Sequence key={k} from={p.f0} durationInFrames={Math.max(p.f1 - p.f0, 1)}>
          <PalavraNaTela p={p} />
        </Sequence>
      ))}
      <Audio src={staticFile('audio.m4a')} />
    </AbsoluteFill>
  );
};
