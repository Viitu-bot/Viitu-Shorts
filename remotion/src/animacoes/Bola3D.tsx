import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing, random} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd011: o segredo da bola de tênis em UMA tomada (formatos.md, formato processo — 3D só no que a câmera não mostra):
// duas conchas de borracha separadas → ar entra sob pressão (partículas azuis) → as conchas fecham (costura brilha) →
// setas de pressão empurram para fora → a bola cai e QUICA (amassa e volta) → o ar escapa aos poucos pela borracha.
// Eventos (quadros desde o início): ar ("enfia"), quica ("quicar"), escapa ("escapa").
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const R = 1;                                   // raio da bola (1 = 3,3 cm na vida real; tudo é relativo)

const Concha: React.FC<{lado: 1 | -1; brilho: number; vidro: number}> = ({lado, brilho, vidro}) => (
  <group rotation={[lado === 1 ? 0 : Math.PI, 0, 0]}>
    {/* casca externa e interna (borracha grossa); "vidro" deixa ver o ar preso lá dentro */}
    <mesh><sphereGeometry args={[R, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} /><meshStandardMaterial color="#3a3a3d" roughness={0.7} metalness={0.05} side={THREE.DoubleSide} transparent opacity={1 - vidro * 0.6} depthWrite={vidro < 0.05} /></mesh>
    <mesh><sphereGeometry args={[R * 0.86, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} /><meshStandardMaterial color="#77736d" roughness={0.9} side={THREE.BackSide} transparent opacity={1 - vidro * 0.75} depthWrite={vidro < 0.05} /></mesh>
    {/* borda (aro) onde as metades se colam */}
    <mesh rotation={[Math.PI / 2, 0, 0]}><ringGeometry args={[R * 0.86, R, 64]} /><meshStandardMaterial color="#8a8780" emissive="#ffcf3a" emissiveIntensity={brilho} roughness={0.8} side={THREE.DoubleSide} /></mesh>
  </group>
);

export const Bola3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tAr = eventos.ar ?? 40, tQuica = eventos.quica ?? 100, tEsc = eventos.escapa ?? 126;
  const tFecha = Math.min(tAr + 28, tQuica - 14);

  const abre = interpolate(f, [0, tFecha - 12, tFecha], [1.05, 1.05, 0], suave);          // distância das metades (vertical)
  const vidro = interpolate(f, [tFecha + 4, tFecha + 14], [0, 1], cl);                      // casca translúcida: ver o ar dentro
  const costura = interpolate(f, [tFecha - 2, tFecha + 4, tFecha + 20], [0, 2.2, 0.15], cl);
  const enche = interpolate(f, [tAr - 4, tFecha], [0, 1], cl);                              // ar entrando
  const pressao = f >= tFecha ? interpolate(f, [tFecha, tFecha + 8], [0, 1], cl) * interpolate(f, [tEsc, dur], [1, 0.35], cl) : 0;

  // queda e quique (amassa no chão)
  const chao = -2.2;
  const t = (f - tQuica + 10) / 30;
  let y = 0, amassa = 1;
  if (f >= tQuica - 10) {
    const g = 18, h0 = 0, vy0 = 0;
    const tc = Math.sqrt((2 * (h0 - (chao + R))) / g);                                       // tempo até tocar
    if (t < tc) y = h0 - 0.5 * g * t * t;
    else {
      const tb = t - tc, v = g * tc * 0.62;                                                   // volta com 62% da velocidade
      y = Math.max(chao + R, chao + R + v * tb - 0.5 * g * tb * tb);
      amassa = 1 - 0.32 * Math.exp(-tb * 40);
    }
    void vy0;
  }

  const k = interpolate(f, [0, dur], [0, 1], suave);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [1.4, 1.8]), interpolate(k, [0, 1], [0.8, 0.3]), interpolate(k, [0, 1], [6.4, 7.6])];
  const alvo: [number, number, number] = [0, interpolate(k, [0, 1], [0, -0.7]), 0];

  const particulas = useMemo(() => Array.from({length: 70}, (_, i) => ({
    a: random(`a${i}`) * Math.PI * 2, b: Math.acos(2 * random(`b${i}`) - 1), r: 0.2 + random(`r${i}`) * 0.55, fase: random(`f${i}`),
  })), []);

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 200}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.8} />
      <color attach="background" args={['#14161a']} />
      <fog attach="fog" args={['#14161a', 8, 20]} />
      <hemisphereLight args={['#dfe8f5', '#202020', 0.6]} />
      <directionalLight position={[3, 5, 4]} intensity={2.2} />
      <pointLight position={[-3, 1, 2]} intensity={8} color="#5fd0ff" distance={10} />
      {/* chão de quadra (saibro escuro) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, chao, 0]}><planeGeometry args={[40, 40]} /><meshStandardMaterial color="#8a4b2c" roughness={1} /></mesh>

      <group position={[0, y, 0]} scale={[1 + (1 - amassa) * 0.6, amassa, 1 + (1 - amassa) * 0.6]}>
        <group position={[0, abre, 0]}><Concha lado={1} brilho={costura} vidro={vidro} /></group>
        <group position={[0, -abre, 0]}><Concha lado={-1} brilho={costura} vidro={vidro} /></group>
        {/* bico da máquina soprando ar (some quando fecha) */}
        {abre > 0.05 && (
          <mesh position={[1.75, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.09, 0.14, 1.2, 16]} /><meshStandardMaterial color="#9aa2aa" metalness={0.85} roughness={0.25} />
          </mesh>
        )}
        {/* ar: entra pelo bico e fica preso lá dentro; depois escapa pela borracha */}
        {particulas.map((p, i) => {
          const entrou = interpolate(enche, [p.fase * 0.7, p.fase * 0.7 + 0.3], [0, 1], cl);
          const fuga = f >= tEsc ? interpolate(f, [tEsc + p.fase * (dur - tEsc) * 0.7, tEsc + p.fase * (dur - tEsc) * 0.7 + 20], [0, 1], cl) : 0;
          if (entrou <= 0) return null;
          const tremor = Math.sin(f * 0.9 + i) * 0.03 * pressao;
          const dentro = new THREE.Vector3(Math.sin(p.b) * Math.cos(p.a), Math.cos(p.b), Math.sin(p.b) * Math.sin(p.a)).multiplyScalar(p.r + tremor);
          const pos = new THREE.Vector3(1.75, 0, 0).lerp(dentro, entrou).add(dentro.clone().normalize().multiplyScalar(fuga * 1.6));
          return (
            <mesh key={i} position={pos.toArray() as [number, number, number]} scale={0.045}>
              <sphereGeometry args={[1, 8, 6]} />
              <meshBasicMaterial color="#6fe3ff" transparent opacity={0.9 * (1 - fuga * 0.9)} blending={THREE.AdditiveBlending} depthWrite={false} />
            </mesh>
          );
        })}
        {/* setas de pressão empurrando a borracha para fora */}
        {pressao > 0.01 && Array.from({length: 8}, (_, i) => {
          const a = (i / 8) * Math.PI * 2;
          const d = new THREE.Vector3(Math.cos(a), Math.sin(a) * 0.9, Math.sin(a) * 0.45).normalize();
          const p = d.clone().multiplyScalar(R * 0.55);
          const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d);
          return (
            <mesh key={i} position={p.toArray() as [number, number, number]} quaternion={q} scale={0.6 + 0.4 * pressao}>
              <coneGeometry args={[0.08, 0.26, 12]} /><meshBasicMaterial color="#6fe3ff" transparent opacity={pressao} depthTest={false} />
            </mesh>
          );
        })}
      </group>
    </ThreeCanvas>
  );
};
