import React from 'react';
import {
  AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Video} from '@remotion/media';
import {zoomBlur} from '@remotion/effects/zoom-blur';
import {chromaticAberration} from '@remotion/effects/chromatic-aberration';
import {Contrafogo} from './animacoes/Contrafogo';
import {Contrafogo3D} from './animacoes/Contrafogo3D';
import {Turbina3D} from './animacoes/Turbina3D';
import {PassarosJanela3D} from './animacoes/PassarosJanela3D';
import {Diferencial3D} from './animacoes/Diferencial3D';
import {Lama3D} from './animacoes/Lama3D';
import {Starship3D, FaseStarship} from './animacoes/Starship3D';
import {Tanque3D, FaseTanque} from './animacoes/Tanque3D';

// fonte local (o navegador do render não baixa do Google Fonts atrás do proxy)
const fontFamily = 'Anton';
loadFont({family: fontFamily, url: staticFile('Anton-Regular.ttf')});

export type Palavra = {texto: string; f0: number; f1: number; destaque: boolean; y: number};
export type Marca = {f0: number; f1: number; cena_f0: number; pos: [number, number, number][]; tipo?: 'circulo' | 'seta'};
export type Plano = {
  fps: number; duracao_frames: number; palavras: Palavra[]; marcas: Marca[];
  cortes: number[]; impactos: number[]; foley?: {f0: number; f1: number; som: string; vol: number}[]; foley_mix?: boolean;
  kit?: Record<string, string[]>; mix?: Record<string, number>; visual?: Record<string, number | boolean>; sfx?: {f: number; som: string; vol?: number; dur?: number}[];
  animacoes?: {nome: string; fase: string; f0: number; f1: number; eventos: Record<string, number>}[]; cta: {f0: number; texto: string} | null;
};

const AMARELO = '#FFD400';

// ---------- identidade: flash branco → amarelo nos primeiros 0,2 s ----------
const FlashIdentidade: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame > 7) return null;
  const branco = interpolate(frame, [0, 2, 4], [1, 0.85, 0], {extrapolateRight: 'clamp'});
  const amarelo = interpolate(frame, [1, 3, 7], [0, 0.75, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <>
      <AbsoluteFill style={{backgroundColor: AMARELO, opacity: amarelo, mixBlendMode: 'screen'}} />
      <AbsoluteFill style={{backgroundColor: 'white', opacity: branco}} />
    </>
  );
};

// ---------- círculo perfeito que se desenha e acompanha o objeto ----------
const CirculoMarca: React.FC<{marca: Marca}> = ({marca}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - marca.f0;
  if (local < 0 || frame >= marca.f1) return null;
  const i = Math.min(Math.max(frame - marca.cena_f0, 0), marca.pos.length - 1);
  const [x, y, r] = marca.pos[i];
  const traco = spring({frame: local, fps, config: {damping: 200}, durationInFrames: 11});
  const pop = spring({frame: local, fps, config: {damping: 10, stiffness: 200, mass: 0.6}});
  const escala = interpolate(pop, [0, 1], [0.6, 1]);
  const saida = interpolate(frame, [marca.f1 - 5, marca.f1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const circ = 2 * Math.PI * r;
  const anel = (cor: string, largura: number, dx = 0, dy = 0) => (
    <circle cx={dx} cy={dy} r={r} fill="none" stroke={cor} strokeWidth={largura} strokeLinecap="round"
      strokeDasharray={circ} strokeDashoffset={circ * (1 - traco)} transform="rotate(-90)" />
  );
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, overflow: 'visible', opacity: saida}}>
      <g transform={`translate(${x},${y}) scale(${escala})`}>
        {anel('rgba(0,0,0,0.5)', 22, 3, 5)}
        {anel('#FF2020', 13)}
        {anel('rgba(255,255,255,0.35)', 3)}
      </g>
    </svg>
  );
};

// ---------- seta vermelha que entra deslizando e "cutuca" o alvo (padrão dos canais grandes) ----------
const SetaMarca: React.FC<{marca: Marca}> = ({marca}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - marca.f0;
  if (local < 0 || frame >= marca.f1) return null;
  const i = Math.min(Math.max(frame - marca.cena_f0, 0), marca.pos.length - 1);
  const [x, y, r] = marca.pos[i];
  // a seta vem da diagonal de cima/esquerda (ou direita, se o alvo estiver à esquerda)
  const lado = x < 420 ? 1 : -1;
  const ang = lado === -1 ? 225 : 315;                   // graus: aponta para baixo, na direção do alvo
  const entra = spring({frame: local, fps, config: {damping: 13, stiffness: 160}});
  const cutuca = local > 10 ? Math.sin(((local - 10) / fps) * Math.PI * 4) * 12 : 0;
  const dist = r * 0.6 + 30 + interpolate(entra, [0, 1], [260, 0]) + cutuca;
  const rad = (ang * Math.PI) / 180;
  const px = x - Math.cos(rad) * dist;
  const py = y + Math.sin(rad) * dist;
  const saida = interpolate(frame, [marca.f1 - 5, marca.f1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const forma = 'M0,-20 L130,-20 L130,-52 L210,0 L130,52 L130,20 L0,20 Z';   // seta apontando para +x
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, overflow: 'visible', opacity: saida * entra}}>
      <g transform={`translate(${px},${py}) rotate(${-ang}) scale(1.45) translate(-210,0)`}>
        <path d={forma} fill="rgba(0,0,0,0.45)" transform="translate(4,6)" />
        <path d={forma} fill="#FF1E1E" stroke="white" strokeWidth={8} strokeLinejoin="round" />
      </g>
    </svg>
  );
};

// ---------- impacto: flash curto + tremida de câmera ----------
const useTremida = (impactos: number[]) => {
  const frame = useCurrentFrame();
  for (const f of impactos) {
    const k = frame - f;
    if (k >= 0 && k < 9) {
      const a = (1 - k / 9) * 14;
      return {x: Math.sin(k * 2.7) * a, y: Math.cos(k * 3.3) * a};
    }
  }
  return {x: 0, y: 0};
};

const FlashImpacto: React.FC<{f: number}> = ({f}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame - f, [0, 1, 4], [0, 0.6, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: 'white', opacity: o}} />;
};

// ---------- legenda: uma palavra por vez, com mola ----------
const PalavraNaTela: React.FC<{p: Palavra}> = ({p}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 11, stiffness: 220, mass: 0.5}});
  const escala = interpolate(s, [0, 1], [0.55, 1]);
  const subida = interpolate(s, [0, 1], [24, 0]);
  return (
    <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', paddingTop: p.y - 80}}>
      <div style={{
        fontFamily, fontSize: p.destaque ? 138 : 124, letterSpacing: 2,
        color: '#FFD700',                       // formato do dono: toda palavra em amarelo ouro
        WebkitTextStroke: '14px black', paintOrder: 'stroke fill',
        textShadow: '0 8px 18px rgba(0,0,0,0.55)',
        transform: `translateY(${subida}px) scale(${escala}) rotate(${p.destaque ? -2 : 0}deg)`,
      }}>{p.texto}</div>
    </AbsoluteFill>
  );
};

// ---------- chamada para se inscrever (final) ----------
const BotaoInscrever: React.FC<{texto: string}> = ({texto}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entra = spring({frame, fps, config: {damping: 11, stiffness: 180}});
  const clique = frame >= 14 && frame < 20 ? 0.92 : 1;
  const inscrito = frame >= 17;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', paddingTop: 1330}}>
      <div style={{
        transform: `scale(${interpolate(entra, [0, 1], [0.3, 1]) * clique})`, opacity: entra,
        backgroundColor: texto === 'INSCREVA-SE' && inscrito ? '#3d3d3d' : '#FF0000', color: 'white', fontFamily, fontSize: 84,
        letterSpacing: 2, padding: '18px 44px', borderRadius: 999, boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
      }}>{texto === 'INSCREVA-SE' ? (inscrito ? '✓ INSCRITO' : '🔔 INSCREVA-SE') : texto}</div>
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

const WOOSHES = ['woosh.mp3', 'whip.mp3', 'woosh2.mp3', 'woosh3.mp3'];
// kit de identidade (assets/kit): alterna as 3 variações de cada função; cai no som próprio se faltar
// MIXAGEM POR REGRA: ganho de cada camada vem do plano (edicao/especificacao.json); reserva = valores antigos
const RESERVA: Record<string, number> = {voz: 1, musica_fala: 0.11, musica_pausa: 0.2, som_original: 0.35, whoosh: 0.32,
  pop: 0.55, boom: 0.8, riser: 0.32, ding: 0.85, clique: 0.6};
const M = (plano: Plano, camada: string) => plano.mix?.[camada] ?? RESERVA[camada] ?? 0.5;
const kitSom = (plano: Plano, funcao: string, i: number, reserva: string) => {
  const l = plano.kit?.[funcao];
  return l && l.length ? l[i % l.length] : reserva;
};

const FundoComEfeitos: React.FC<{plano: Plano}> = ({plano}) => {
  const frame = useCurrentFrame();
  let zb = 0;
  let ca = 0;
  for (const f of plano.impactos) {
    const k = frame - f;
    if (k >= 0 && k < 10) {
      zb = Math.max(zb, interpolate(k, [0, 1, 10], [0, 70, 0]));
      ca = Math.max(ca, interpolate(k, [0, 1, 10], [0, 22, 0]));
    }
  }
  if (plano.visual?.glitch_no_corte !== false) {          // canais usam corte SECO; glitch só se a especificação pedir
    for (const c of plano.cortes) {
      const k = frame - c;
      if (k >= 0 && k < 4) ca = Math.max(ca, interpolate(k, [0, 1, 4], [0, 9, 0]));
    }
  }
  return (
    <Video src={staticFile('fundo.mp4')} muted
      effects={[
        zoomBlur({amount: zb, disabled: zb < 0.5}),
        chromaticAberration({amount: ca, angle: 0, disabled: ca < 0.5}),
      ]} />
  );
};

// ---------- acabamento de imagem: cor unificada + vinheta + grão (clipes de fontes diferentes viram "um filme") ----------
const Acabamento: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 75% 60% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.42) 100%)'}} />
      <AbsoluteFill style={{opacity: 0.07, mixBlendMode: 'overlay'}}>
        <svg width={1080} height={1920}>
          <filter id="grao"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={frame % 12} /></filter>
          <rect width="100%" height="100%" filter="url(#grao)" />
        </svg>
      </AbsoluteFill>
    </>
  );
};

export const Short: React.FC<{plano: Plano}> = ({plano}) => {
  const {durationInFrames} = useVideoConfig();
  const z = usePunch(plano.palavras);
  const t = useTremida(plano.impactos);
  const falando = (f: number) => plano.palavras.some((p) => f >= p.f0 - 2 && f <= p.f1 + 2);
  // VÁCUO SONORO: o mundo "prende a respiração" 10 quadros antes do impacto e volta com mais força depois
  const vacuo = (f: number) => {
    let v = 1;
    for (const i of plano.impactos) {
      if (f >= i - 10 && f < i) v = Math.min(v, interpolate(f, [i - 10, i - 6], [1, 0.05], {extrapolateRight: 'clamp'}));
      if (f >= i && f < i + 36) v = Math.max(v, interpolate(f, [i, i + 4, i + 36], [0.05, 1.35, 1], {extrapolateRight: 'clamp'}));
    }
    return v;
  };
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      <AbsoluteFill style={{transform: `translate(${t.x}px, ${t.y}px) scale(${z * (t.x ? 1.03 : 1)})`,
        filter: `contrast(${plano.visual?.contraste ?? 1.07}) saturate(${plano.visual?.saturacao ?? 1.12})`}}>
        <FundoComEfeitos plano={plano} />
      </AbsoluteFill>
      {/* animações explicativas próprias (motion graphics) cobrem a cena inteira */}
      {(plano.animacoes ?? []).map((a, k) => (
        <Sequence key={`an${k}`} from={a.f0} durationInFrames={Math.max(a.f1 - a.f0, 1)}>
          {a.nome === 'contrafogo' && <Contrafogo fase={a.fase as 'faixa' | 'apaga'} dur={a.f1 - a.f0} eventos={a.eventos} />}
          {a.nome === 'diferencial3d' && a.fase === 'lama' && <Lama3D dur={a.f1 - a.f0} eventos={a.eventos} />}
          {a.nome === 'diferencial3d' && a.fase !== 'lama' && <Diferencial3D fase={a.fase as 'dentro' | 'lama'} dur={a.f1 - a.f0} eventos={a.eventos} />}
          {a.nome === 'passarosjanela' && <PassarosJanela3D dur={a.f1 - a.f0} eventos={a.eventos} />}
          {a.nome === 'turbina3d' && <Turbina3D fase={a.fase as 'ar' | 'quebra' | 'teste' | 'bando'} dur={a.f1 - a.f0} eventos={a.eventos} />}
          {a.nome === 'tanque3d' && <Tanque3D fase={a.fase as FaseTanque} dur={a.f1 - a.f0} eventos={a.eventos} />}
          {a.nome === 'starship3d' && <Starship3D fase={a.fase as FaseStarship} dur={a.f1 - a.f0} eventos={a.eventos} />}
          {a.nome === 'contrafogo3d' && <Contrafogo3D fase={a.fase as 'ar' | 'encontro'} dur={a.f1 - a.f0} eventos={a.eventos} />}
        </Sequence>
      ))}
      <Acabamento />

      {plano.marcas.map((m, k) => (
        <React.Fragment key={k}>
          {m.tipo === 'seta' ? <SetaMarca marca={m} /> : <CirculoMarca marca={m} />}
          <Sequence from={m.f0} durationInFrames={30}><Audio src={staticFile(kitSom(plano, 'pop_marca', k, 'pop.mp3'))} volume={M(plano,'pop')} /></Sequence>
        </React.Fragment>
      ))}

      {plano.palavras.filter((p) => p.texto).map((p, k) => (
        <Sequence key={k} from={p.f0} durationInFrames={Math.max(p.f1 - p.f0, 1)}>
          <PalavraNaTela p={p} />
        </Sequence>
      ))}

      {plano.impactos.map((f, k) => (
        <React.Fragment key={k}>
          <FlashImpacto f={f} />
          <Sequence from={Math.max(f - 50, 0)} durationInFrames={52}><Audio src={staticFile(kitSom(plano, 'riser_tensao', k, 'tensao.mp3'))} volume={M(plano,'riser')} /></Sequence>
          <Sequence from={f} durationInFrames={60}><Audio src={staticFile(kitSom(plano, 'impacto_revelacao', k, 'boom.mp3'))} volume={M(plano,'boom')} /></Sequence>
        </React.Fragment>
      ))}

      {plano.cta && (
        <Sequence from={plano.cta.f0} durationInFrames={75}>
          <BotaoInscrever texto={plano.cta.texto} />
          <Audio src={staticFile('pop.mp3')} volume={M(plano,'pop')} />
          <Sequence from={14} durationInFrames={20}><Audio src={staticFile('clique.mp3')} volume={M(plano,'clique')} /></Sequence>
        </Sequence>
      )}

      {/* efeitos sonoros: woosh variado em cada corte (começa um pouco antes) */}
      {plano.cortes.filter((c) => !plano.impactos.includes(c)).map((c, k) => (
        <Sequence key={k} from={Math.max(c - 4, 0)} durationInFrames={24}>
          <Audio src={staticFile(plano.kit?.whoosh_corte ? plano.kit.whoosh_corte[k % plano.kit.whoosh_corte.length] : WOOSHES[k % WOOSHES.length])} volume={M(plano,'whoosh')} />
        </Sequence>
      ))}

      {/* sons de FUNÇÃO (número → ding, dinheiro → moeda, mito → buzzer...) */}
      {(plano.sfx ?? []).map((e, k) => (
        <Sequence key={`sx${k}`} from={e.f} durationInFrames={e.dur ?? 60}><Audio src={staticFile(e.som)} volume={e.vol ?? M(plano,'ding')} /></Sequence>
      ))}

      <FlashIdentidade />
      <Sequence from={0} durationInFrames={30}><Audio src={staticFile('ding.mp3')} volume={M(plano,'ding')} /></Sequence>

      {/* FOLEY já mixado em Python: corte em J/L (entra antes do corte) + pan estéreo pelo lado do sujeito */}
      {plano.foley_mix ? (
        <Audio src={staticFile('foley.m4a')}
          volume={(f) => vacuo(f) * (falando(f) ? 0.85 : 1)} />
      ) : (plano.foley ?? []).map((f, k) => (
        <Sequence key={`fo${k}`} from={f.f0} durationInFrames={Math.max(f.f1 - f.f0, 1)}>
          <Audio src={staticFile(f.som)} loop
            volume={(x) => f.vol * interpolate(x, [0, 6, f.f1 - f.f0 - 6, f.f1 - f.f0], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})} />
        </Sequence>
      ))}

      {/* trilha com DUCKING (abaixa sob a voz) + VÁCUO antes do impacto (silêncio → boom → trilha volta mais forte) */}
      <Audio src={staticFile('musica.mp3')} loop
        volume={(f) => {
          // LOOP: a trilha SOBE nos últimos 1,5 s (padrão dos canais grandes) e não some — o fim emenda no começo
          const sobe = interpolate(f, [durationInFrames - 45, durationInFrames - 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          const base = falando(f) ? M(plano,'musica_fala') : M(plano,'musica_pausa');
          return (base + (M(plano,'musica_pausa') * 1.3 - base) * sobe) * vacuo(f);
        }} />
      {/* som original dos clipes por baixo da voz (padrão dos virais: chiado, raspagem, bicho) */}
      <Audio src={staticFile('ambiente.m4a')} volume={(f) => M(plano,'som_original') * vacuo(f)} />
      <Audio src={staticFile('audio.m4a')} volume={M(plano,'voz')} />
    </AbsoluteFill>
  );
};
