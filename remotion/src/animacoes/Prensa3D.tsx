import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing, random} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd011 v4 — o processo REAL (dono 20/11: "o 3D ficou muito ficção"). Fonte: ITF "Balls – ball manufacture", Wilson
// Labs, Dunlop: as duas metades vão nos moldes de uma prensa hidráulica, a CÂMARA da prensa recebe ar comprimido, a
// prensa fecha e PRENDE esse ar entre as metades, e o calor vulcaniza a borda com cola numa peça só. Depois, a borracha
// deixa o gás atravessar a parede devagar (difusão).
// Eventos (quadros desde o início): ar ("cheia"), fecha ("preso"), calor ("calor"), peca ("peça"), vaza ("vazar").
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const R = 1;
const AZUL = '#6fe3ff';

const Concha: React.FC<{cima: boolean; calor: number; vidro: number; costura: number}> = ({cima, calor, vidro, costura}) => (
  <group rotation={[cima ? 0 : Math.PI, 0, 0]}>
    <mesh><sphereGeometry args={[R, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
      <meshStandardMaterial color="#3b3b3e" roughness={0.75} emissive="#ff5a1f" emissiveIntensity={calor * 0.25} side={THREE.DoubleSide}
        transparent opacity={1 - vidro * 0.65} depthWrite={vidro < 0.05} /></mesh>
    <mesh><sphereGeometry args={[R * 0.86, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
      <meshStandardMaterial color="#76726c" roughness={0.9} side={THREE.BackSide} transparent opacity={1 - vidro * 0.8} depthWrite={vidro < 0.05} /></mesh>
    {/* borda com COLA (amarelada); com o calor fica laranja e some quando vira peça só */}
    <mesh rotation={[Math.PI / 2, 0, 0]}><ringGeometry args={[R * 0.86, R, 64]} />
      <meshStandardMaterial color="#c9b26a" emissive="#ff7a1a" emissiveIntensity={calor * 2.4} roughness={0.6} side={THREE.DoubleSide}
        transparent opacity={costura} /></mesh>
  </group>
);

const Placa: React.FC<{y: number; calor: number}> = ({y, calor}) => (
  <mesh position={[0, y, 0]}>
    <boxGeometry args={[3.6, 1.1, 2.6]} />
    <meshStandardMaterial color="#8c949c" metalness={0.85} roughness={0.32} emissive="#ff3d0a" emissiveIntensity={calor * 0.18} />
  </mesh>
);

export const Prensa3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tAr = eventos.ar ?? 42, tFecha = eventos.fecha ?? 84, tCalor = eventos.calor ?? 122, tPeca = eventos.peca ?? 164, tVaza = eventos.vaza ?? 198;

  // abertura da prensa: aberta → fecha (prende o ar) → abre de novo e a bola sai inteira
  const gap = interpolate(f, [0, tFecha - 14, tFecha, tPeca - 6, tPeca + 14], [1.5, 1.5, 0, 0, 2.6], suave);
  const meioCima = f < tPeca - 6 ? gap : 0;                          // depois de fundir, a metade de cima fica na bola
  const enche = interpolate(f, [tAr - 6, tFecha - 16], [0, 1], cl);   // câmara enchendo de ar comprimido
  const calor = interpolate(f, [tCalor - 4, tCalor + 10, tPeca - 2, tPeca + 24], [0, 1, 1, 0], cl);
  const costura = interpolate(f, [tCalor + 8, tPeca + 4], [1, 0], cl);
  const sobe = interpolate(f, [tPeca + 4, tPeca + 30], [0, 0.9], suave);
  const gira = interpolate(f, [tPeca, dur], [0, 1.2], cl);
  const vidro = interpolate(f, [tPeca + 26, tPeca + 40], [0, 1], cl);   // casca fica translúcida: dá para ver o ar PRESO
  const camara = interpolate(f, [tFecha + 4, tFecha + 18], [1, 0], cl);   // vidro da câmara some depois de fechar
  const ponteiro = interpolate(enche, [0, 1], [-2.2, 0.5], cl);

  const k1 = interpolate(f, [tPeca, tPeca + 30], [0, 1], suave);
  const k2 = interpolate(f, [tPeca + 26, tPeca + 56], [0, 1], suave);
  const cam: [number, number, number] = [
    interpolate(k1, [0, 1], [3.6, 1.6]) + interpolate(k2, [0, 1], [0, -0.6]),
    interpolate(k1, [0, 1], [2.2, 1.5]) + interpolate(k2, [0, 1], [0, -0.4]),
    interpolate(k1, [0, 1], [11.5, 6.6]) + interpolate(k2, [0, 1], [0, -1.4]),
  ];
  const alvo: [number, number, number] = [0, interpolate(k1, [0, 1], [0.35, 0.9]), 0];

  // ar da câmara: entra pelo cano da esquerda e ocupa TODA a câmara; os que ficam entre as metades ficam presos
  const ar = useMemo(() => Array.from({length: 110}, (_, i) => ({
    x: (random(`x${i}`) - 0.5) * 3.2, y: random(`y${i}`), z: (random(`z${i}`) - 0.5) * 2.2, fase: random(`f${i}`),
    a: random(`a${i}`) * Math.PI * 2, b: Math.acos(2 * random(`b${i}`) - 1), r: 0.15 + random(`r${i}`) * 0.6, preso: i < 42,
    sai: random(`s${i}`),
  })), []);

  const baseY = -0.55 - 0.55;                 // placa de baixo: topo em y = -0.55 (a metade fica meio enterrada no molde)
  const topoY = (g: number) => g + 0.55 + 0.55;

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 200}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.7} />
      <color attach="background" args={['#121418']} />
      <fog attach="fog" args={['#121418', 9, 22]} />
      <hemisphereLight args={['#dfe8f5', '#202020', 0.55]} />
      <directionalLight position={[3, 6, 5]} intensity={2.2} />
      <pointLight position={[-3, 1.5, 2.5]} intensity={6} color={AZUL} distance={10} />
      <pointLight position={[0, 0.3, 1.8]} intensity={calor * 8} color="#ff6a1a" distance={6} />

      {/* PRENSA: coluna, placa de baixo (molde com a metade), placa de cima (molde com a outra metade) */}
      <mesh position={[-2.05, 1.2, -0.9]}><cylinderGeometry args={[0.16, 0.16, 6, 16]} /><meshStandardMaterial color="#5d646b" metalness={0.8} roughness={0.35} /></mesh>
      <mesh position={[2.05, 1.2, -0.9]}><cylinderGeometry args={[0.16, 0.16, 6, 16]} /><meshStandardMaterial color="#5d646b" metalness={0.8} roughness={0.35} /></mesh>
      <Placa y={baseY} calor={calor} />
      <Placa y={topoY(gap)} calor={calor} />
      {/* cano de ar comprimido + manômetro */}
      <mesh position={[-2.35, 0.25, 0.6]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.12, 0.12, 1.4, 16]} /><meshStandardMaterial color="#b8c0c8" metalness={0.9} roughness={0.2} /></mesh>
      <group position={[-2.15, 0.95, 0.6]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.36, 0.36, 0.08, 32]} /><meshStandardMaterial color="#e9e6dc" roughness={0.5} /></mesh>
        <mesh position={[0, 0, 0.05]} rotation={[0, 0, ponteiro]}><boxGeometry args={[0.035, 0.3, 0.02]} /><meshBasicMaterial color="#d22" /></mesh>
        <mesh position={[0, -0.5, 0]}><cylinderGeometry args={[0.05, 0.05, 0.6, 8]} /><meshStandardMaterial color="#b8c0c8" metalness={0.9} /></mesh>
      </group>
      {/* câmara (vidro) entre as placas */}
      {camara > 0.01 && (
        <mesh position={[0, (-0.55 + topoY(gap) - 0.55) / 2, 0]}>
          <boxGeometry args={[3.5, Math.max(topoY(gap) - 0.55 + 0.55, 0.05), 2.5]} />
          <meshStandardMaterial color="#9fd8ff" transparent opacity={0.09 * camara} roughness={0.1} depthWrite={false} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* a bola: metade de baixo fixa; de cima desce com a placa; depois de fundir sobe e gira */}
      <group position={[0, sobe, 0]} rotation={[0, gira, 0]}>
        <group position={[0, meioCima, 0]}><Concha cima calor={calor} vidro={vidro} costura={costura} /></group>
        <Concha cima={false} calor={calor} vidro={vidro} costura={costura} />
      </group>

      {/* AR */}
      {ar.map((p, i) => {
        const entrou = interpolate(enche, [p.fase * 0.75, p.fase * 0.75 + 0.25], [0, 1], cl);
        if (entrou <= 0) return null;
        const cano = new THREE.Vector3(-1.9, 0.25, 0);
        const alto = Math.max(topoY(gap) - 1.1, 0.05);
        const naCamara = new THREE.Vector3(p.x, -0.55 + p.y * (alto + 0.55), p.z);
        const tremor = Math.sin(f * 0.8 + i) * 0.03;
        if (!p.preso) {
          const some = interpolate(f, [tFecha - 6, tFecha + 6], [1, 0], cl);   // ar de fora da bola: a câmara esvazia
          if (some <= 0) return null;
          const pos = cano.clone().lerp(naCamara, entrou);
          return <mesh key={i} position={[pos.x, pos.y + tremor, pos.z]} scale={0.045}><sphereGeometry args={[1, 8, 6]} />
            <meshBasicMaterial color={AZUL} transparent opacity={0.85 * some} blending={THREE.AdditiveBlending} depthWrite={false} /></mesh>;
        }
        // presos: começam na câmara, entre as metades, e ficam DENTRO da bola quando ela fecha
        const dir = new THREE.Vector3(Math.sin(p.b) * Math.cos(p.a), Math.cos(p.b), Math.sin(p.b) * Math.sin(p.a));
        const dentro = dir.clone().multiplyScalar(p.r).add(new THREE.Vector3(0, meioCima / 2 + sobe, 0));
        const junta = interpolate(f, [tFecha - 14, tFecha], [0, 1], cl);
        const vaza = interpolate(f, [tVaza - 20 + p.sai * 70, tVaza + 20 + p.sai * 70], [0, 1], cl);   // atravessa a parede devagar
        const pos = cano.clone().lerp(naCamara, entrou).lerp(dentro, junta);
        if (p.sai < 0.35) pos.add(dir.clone().multiplyScalar(vaza * (R * 1.25 - p.r)));      // só alguns atravessam a parede, devagar
        return <mesh key={i} position={[pos.x, pos.y + tremor * (1 - junta * 0.5), pos.z]} scale={0.045}><sphereGeometry args={[1, 8, 6]} />
          <meshBasicMaterial color={AZUL} transparent opacity={0.9 * (1 - (p.sai < 0.35 ? vaza * 0.35 : 0))} blending={THREE.AdditiveBlending} depthWrite={false} /></mesh>;
      })}
    </ThreeCanvas>
  );
};
