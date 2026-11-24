import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd017 — canhão de desaparecimento em corte lateral (carreta Buffington-Crozier, Wikipedia "Disappearing gun"):
// muro de concreto na frente (mar à direita); o canhão na ponta de 2 braços que giram num pino; o contrapeso do outro
// lado do pino. Eventos (quadros desde o início): tiro (clarão + coice), baixo (o canhão desce atrás do muro),
// contrapeso (o contrapeso sobe e fica lá em cima, carregado).
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const CONCRETO = '#b9b2a6';
const ACO = '#4b5560';

export const Canhao3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tTiro = eventos.tiro ?? 10;
  const tBaixo = Math.max(eventos.baixo ?? 45, tTiro + 6);
  const tPeso = Math.max(eventos.contrapeso ?? 90, tBaixo + 6);

  // ângulo do braço: em cima (canhão acima do muro) → embaixo (escondido). O coice começa no tiro e termina em "baixo".
  const desce = interpolate(f, [tTiro + 1, tBaixo + 10], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  const ang = interpolate(desce, [0, 1], [1.25, 2.95]);            // rad: braço em pé (canhão acima do muro) → deitado para trás
  const flash = interpolate(f, [tTiro, tTiro + 2, tTiro + 9], [0, 1, 0], cl);
  const fumaca = interpolate(f, [tTiro, tTiro + 40], [0, 1], cl);
  const brilhoPeso = interpolate(f, [tPeso - 4, tPeso + 4, tPeso + 30], [0, 1, 0.25], cl);

  const L = 2.4;                                                    // braço: pino → munhão do canhão
  const px = -0.8, py = -0.2;                                        // pino da carreta
  const gx = px + Math.cos(ang) * L, gy = py + Math.sin(ang) * L;   // munhão (onde o canhão está preso)
  const cx = px - Math.cos(ang) * 1.0, cy = py - Math.sin(ang) * 1.0;   // contrapeso (lado oposto do pino)

  const k = interpolate(f, [0, dur], [0, 1], cl);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [-0.3, -0.5]), 0.6, interpolate(k, [0, 1], [14.5, 13.6])];
  const alvo: [number, number, number] = [-0.3, 0.5, 0];

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 42, position: cam, near: 0.05, far: 100}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.7} />
      <color attach="background" args={['#9fb7cc']} />
      <hemisphereLight args={['#ffffff', '#444444', 0.9]} />
      <directionalLight position={[4, 6, 6]} intensity={1.7} />

      {/* mar ao fundo, à direita */}
      <mesh position={[6.5, -0.65, -1]}><boxGeometry args={[9, 0.1, 6]} /><meshStandardMaterial color="#3d6f93" roughness={0.3} /></mesh>
      {/* terreno e fosso (o canhão se esconde aqui dentro) */}
      <mesh position={[-1.6, -1.6, 0]}><boxGeometry args={[6, 2.0, 2.4]} /><meshStandardMaterial color="#6b6457" roughness={1} /></mesh>
      {/* MURO de concreto na frente (lado do mar) */}
      <mesh position={[1.7, 0.2, 0]}><boxGeometry args={[1.2, 3.2, 2.4]} /><meshStandardMaterial color={CONCRETO} roughness={0.95} /></mesh>
      <mesh position={[2.55, 1.3, 0]} rotation={[0, 0, -0.6]}><boxGeometry args={[1.4, 0.3, 2.4]} /><meshStandardMaterial color={CONCRETO} roughness={0.95} /></mesh>

      {/* base giratória + pino */}
      <mesh position={[px, py - 0.4, 0]}><boxGeometry args={[1.2, 0.5, 1.4]} /><meshStandardMaterial color={ACO} metalness={0.6} roughness={0.4} /></mesh>
      <mesh position={[px, py, 0]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.18, 0.18, 1.5, 20]} /><meshStandardMaterial color="#2c3238" metalness={0.8} /></mesh>
      {/* 2 BRAÇOS (do contrapeso ao canhão, passando pelo pino) */}
      {[-0.55, 0.55].map((z) => (
        <mesh key={z} position={[(cx + gx) / 2, (cy + gy) / 2, z]} rotation={[0, 0, ang]}>
          <boxGeometry args={[L + 1.1, 0.22, 0.12]} /><meshStandardMaterial color="#5c6670" metalness={0.7} roughness={0.35} />
        </mesh>
      ))}
      {/* CONTRAPESO */}
      <mesh position={[cx, cy, 0]}><boxGeometry args={[0.9, 0.9, 1.3]} />
        <meshStandardMaterial color="#3a3f45" metalness={0.5} roughness={0.5} emissive="#ffb000" emissiveIntensity={brilhoPeso * 0.6} /></mesh>
      {/* CANHÃO (sempre na horizontal, apontando para o mar) */}
      <group position={[gx, gy, 0]}>
        <mesh position={[1.6, 0, 0]} rotation={[0, 0, -Math.PI / 2]}><cylinderGeometry args={[0.15, 0.26, 2.8, 24]} /><meshStandardMaterial color="#2f363d" metalness={0.75} roughness={0.3} /></mesh>
        <mesh position={[0.15, 0, 0]}><sphereGeometry args={[0.32, 20, 16]} /><meshStandardMaterial color="#2f363d" metalness={0.75} roughness={0.3} /></mesh>
        {/* clarão do tiro na boca */}
        {flash > 0.02 && (
          <mesh position={[3.15, 0, 0]} scale={0.25 + flash * 0.9}><sphereGeometry args={[1, 16, 12]} />
            <meshStandardMaterial color="#ffd27a" emissive="#ff9a00" emissiveIntensity={3 * flash} transparent opacity={flash} /></mesh>
        )}
      </group>
      {/* fumaça do tiro: fica no ar enquanto o canhão some */}
      {fumaca > 0.02 && fumaca < 0.99 && [0, 1, 2, 3].map((i) => (
        <mesh key={i} position={[px + Math.cos(1.25) * L + 3.4 + i * 0.5 * fumaca, py + Math.sin(1.25) * L + 0.2 + i * 0.25 * fumaca, 0]}
          scale={0.35 + fumaca * (0.6 + i * 0.2)}>
          <sphereGeometry args={[1, 12, 10]} /><meshStandardMaterial color="#e8e6e1" transparent opacity={0.55 * (1 - fumaca)} depthWrite={false} />
        </mesh>
      ))}
    </ThreeCanvas>
  );
};
