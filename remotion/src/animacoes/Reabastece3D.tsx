import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, random, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useModelo, useTexturas} from './comum3d';

// vd009: reabastecimento em voo do Air Force One. Modelos PRONTOS (Sketchfab, CC BY 4.0): Boeing 747-100
// (pintado nas cores do Air Force One) e KC-135R Stratotanker. A lança do tanque desce, encaixa no bocal do teto
// do 747 (atrás da cabine) e o combustível passa. Acima das nuvens, céu HDRI real.
// Eventos: "encosta" (lança encaixa), "enche" (combustível passa). 1 unidade = 1 m.

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};

// orienta o modelo: comprimento no eixo z (nariz para -z), em pé (y para cima)
const preparar = (cena: THREE.Group | null, pintar?: (m: THREE.Mesh) => void) => useMemo(() => {
  if (!cena) return null;
  const c = cena.clone(true);
  c.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.isMesh) {
      m.material = (m.material as THREE.Material).clone();
      if (pintar) pintar(m);
    }
  });
  return c;
}, [cena]);

const Nuvens: React.FC<{f: number}> = ({f}) => (
  <group>
    {Array.from({length: 26}, (_, i) => {
      const x = (random(`nx${i}`) - 0.5) * 900, z = ((random(`nz${i}`) - 0.5) * 900 + f * 3.5) % 900 - 450;
      const s = 40 + random(`ns${i}`) * 90;
      return (
        <mesh key={i} position={[x, -60 - random(`ny${i}`) * 30, z]} scale={[s, s * 0.25, s * 0.7]}>
          <sphereGeometry args={[1, 14, 10]} />
          <meshStandardMaterial color="#ffffff" roughness={1} transparent opacity={0.9} />
        </mesh>
      );
    })}
  </group>
);

export const Reabastece3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const b747 = useModelo('boeing747.glb');
  const kc = useModelo('kc135.glb');
  // Air Force One: azul-claro em cima, branco embaixo (pinta pelo lado do vértice? usa tom geral azul-claro + metal)
  const af1 = preparar(b747, (m) => {
    const mat = m.material as THREE.MeshStandardMaterial;
    if (mat.color) mat.color.lerp(new THREE.Color('#9fc3e6'), 0.35);
    mat.metalness = Math.min((mat.metalness ?? 0) + 0.2, 0.6);
  });
  const tanque = preparar(kc);

  const tEnc = eventos.encosta ?? Math.round(dur * 0.45);
  const tEnc2 = eventos.enche ?? Math.round(dur * 0.7);
  const desce = interpolate(f, [0, tEnc], [0, 1], suave);          // lança baixando até o bocal
  const encaixe = interpolate(f, [tEnc - 2, tEnc + 4], [0, 1], cl);
  const fluxo = interpolate(f, [tEnc2 - 4, tEnc2 + 6], [0, 1], cl);
  const balanco = Math.sin(f * 0.07) * 0.25;

  // posições: 747 embaixo; KC-135 à frente e acima; o bocal fica no teto do 747 logo atrás da cabine
  const P747: [number, number, number] = [0, balanco * 0.4, 0];
  const BOCAL: [number, number, number] = [0, 6.4 + balanco * 0.4, -22];
  const PKC: [number, number, number] = [0, 22 + balanco, -42];
  const ponta: [number, number, number] = [0, interpolate(desce, [0, 1], [16, BOCAL[1] + 0.3]) + balanco * (1 - desce * 0.6), interpolate(desce, [0, 1], [-30, BOCAL[2]])];
  const raiz: [number, number, number] = [0, PKC[1] - 2.5, PKC[2] + 18];
  const lanca = new THREE.Vector3(...ponta).sub(new THREE.Vector3(...raiz));
  const compr = lanca.length();
  const meio = new THREE.Vector3(...raiz).add(lanca.clone().multiplyScalar(0.5));
  const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), lanca.clone().normalize());

  const k = interpolate(f, [0, dur], [0, 1], suave);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [70, 22]), interpolate(k, [0, 1], [18, 12]), interpolate(k, [0, 1], [30, -6])];
  const alvo: [number, number, number] = [0, interpolate(k, [0, 1], [8, 7]), interpolate(k, [0, 1], [-20, -22])];

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.5, far: 3000}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo />
      <hemisphereLight args={['#eaf2fb', '#9aa5b0', 0.7]} />
      <directionalLight position={[60, 120, 40]} intensity={2.4} color="#fff6e8" />
      <fog attach="fog" args={['#d8e6f2', 200, 1400]} />
      <Nuvens f={f} />
      {af1 && <group position={P747}><primitive object={af1} /></group>}
      {tanque && <group position={PKC}><primitive object={tanque} /></group>}
      {/* lança do tanque (tubo com aletas) */}
      <mesh position={meio.toArray() as [number, number, number]} quaternion={quat}>
        <cylinderGeometry args={[0.35, 0.45, compr, 16]} />
        <meshStandardMaterial color="#9aa2aa" metalness={0.7} roughness={0.35} />
      </mesh>
      <group position={ponta}>
        <mesh><cylinderGeometry args={[0.18, 0.25, 1.4, 12]} /><meshStandardMaterial color="#5d646b" metalness={0.8} /></mesh>
        <mesh position={[0, 0.9, 0]}><boxGeometry args={[3.2, 0.08, 0.8]} /><meshStandardMaterial color="#9aa2aa" metalness={0.6} /></mesh>
      </group>
      {/* bocal no teto do 747: luz verde quando encaixa */}
      <mesh position={BOCAL}>
        <cylinderGeometry args={[0.6, 0.6, 0.15, 20]} />
        <meshStandardMaterial color={encaixe > 0.5 ? '#3dff6a' : '#ffd23d'} emissive={encaixe > 0.5 ? '#3dff6a' : '#ffaa00'} emissiveIntensity={1.4} />
      </mesh>
      {/* combustível passando pela lança: traços brilhantes descendo */}
      {fluxo > 0.01 && Array.from({length: 14}, (_, i) => {
        const t = ((f * 0.05 + i / 14) % 1);
        const p = new THREE.Vector3(...raiz).add(lanca.clone().multiplyScalar(t));
        return (
          <mesh key={i} position={p.toArray() as [number, number, number]} quaternion={quat}>
            <cylinderGeometry args={[0.42, 0.42, 0.9, 10]} />
            <meshBasicMaterial color="#ffb547" transparent opacity={0.85 * fluxo} blending={THREE.AdditiveBlending} depthWrite={false} />
          </mesh>
        );
      })}
    </ThreeCanvas>
  );
};
