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
    {Array.from({length: 18}, (_, c) => {
      const cx = (random(`cx${c}`) - 0.5) * 1400, cz = ((random(`cz${c}`) - 0.5) * 1400 + f * 4) % 1400 - 700;
      return (
        <group key={c} position={[cx, -140 - random(`cy${c}`) * 40, cz]}>
          {Array.from({length: 7}, (_, i) => {
            const s = 25 + random(`s${c}${i}`) * 45;
            return (
              <mesh key={i} position={[(random(`x${c}${i}`) - 0.5) * 120, random(`y${c}${i}`) * 12, (random(`z${c}${i}`) - 0.5) * 80]} scale={[s, s * 0.45, s]}>
                <sphereGeometry args={[1, 16, 12]} />
                <meshStandardMaterial color="#ffffff" roughness={1} transparent opacity={0.55} depthWrite={false} />
              </mesh>
            );
          })}
        </group>
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
  // tira a pintura de companhia aérea do modelo: fuselagem/asas lisas (branco-azulado do Air Force One), sem marca
  const af1 = preparar(b747, (m) => {
    const mat = m.material as THREE.MeshStandardMaterial;
    const nome = (mat.name || '').toLowerCase();
    const manter = ['glass', 'window', 'wheel', 'dials', 'black'].some((k) => nome.includes(k));
    if (!manter) {                                       // tira TODA a pintura (inclusive a cauda da ANA)
      mat.map = null;
      mat.color = new THREE.Color(nome.includes('wing') ? '#cfd6dd' : '#eef3f8');
      mat.metalness = 0.35; mat.roughness = 0.35;
      mat.needsUpdate = true;
    }
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
  const BOCAL: [number, number, number] = [0, 0.9 + balanco * 0.4, -23];     // teto da cabine superior do 747
  const PKC: [number, number, number] = [0, 16.6 + balanco, -48];
  const raiz: [number, number, number] = [0, PKC[1] - 4.2, PKC[2] + 18];   // embaixo da cauda do tanque
  const ponta: [number, number, number] = [0, interpolate(desce, [0, 1], [raiz[1] - 4, BOCAL[1] + 0.4]) + balanco * (1 - desce * 0.6), interpolate(desce, [0, 1], [raiz[2] + 3, BOCAL[2]])];
  const lanca = new THREE.Vector3(...ponta).sub(new THREE.Vector3(...raiz));
  const compr = lanca.length();
  const meio = new THREE.Vector3(...raiz).add(lanca.clone().multiplyScalar(0.5));
  const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), lanca.clone().normalize());

  const k = interpolate(f, [0, dur], [0, 1], suave);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [58, 20]), interpolate(k, [0, 1], [14, 9]), interpolate(k, [0, 1], [18, -12])];
  const alvo: [number, number, number] = [0, interpolate(k, [0, 1], [7, 5]), interpolate(k, [0, 1], [-28, -25])];

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.5, far: 3000}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo />
      <hemisphereLight args={['#eaf2fb', '#9aa5b0', 0.7]} />
      <directionalLight position={[60, 120, 40]} intensity={2.4} color="#fff6e8" />
      <fog attach="fog" args={['#d8e6f2', 200, 1400]} />
      <Nuvens f={f} />
      {af1 && <group position={P747} rotation={[0, 0, 0]}><primitive object={af1} /></group>}
      {tanque && <group position={PKC} rotation={[0, Math.PI, 0]}><primitive object={tanque} /></group>}
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
