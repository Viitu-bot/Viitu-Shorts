import React from 'react';
import {interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';

// Pássaros 3D SOBREPOSTOS a um clipe real (fundo transparente): gaivotas passando perto da asa,
// vistas da janela do avião. Uso: "animacao": {"nome": "passarosjanela", "eventos": {...}} numa cena com clipe real.

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Camera: React.FC = () => {
  const {camera} = useThree();
  camera.position.set(0, 0, 8);
  camera.lookAt(0, 0, 0);
  return null;
};

const Gaivota: React.FC<{pos: [number, number, number]; f: number; escala: number; rumo: number}> = ({pos, f, escala, rumo}) => {
  const asa = Math.sin(f * 0.28) * 0.35;
  return (
    <group position={pos} scale={escala} rotation={[0.75, rumo, 0.12]}>
      <mesh scale={[0.5, 0.16, 0.16]}>
        <sphereGeometry args={[1, 12, 8]} />
        <meshStandardMaterial color="#f4f4f2" flatShading />
      </mesh>
      <mesh position={[0.52, 0.04, 0]} scale={[0.14, 0.12, 0.12]}>
        <sphereGeometry args={[1, 8, 6]} />
        <meshStandardMaterial color="#f4f4f2" flatShading />
      </mesh>
      <mesh position={[0.68, 0.02, 0]} rotation={[0, 0, -Math.PI / 2]}>
        <coneGeometry args={[0.04, 0.14, 6]} />
        <meshStandardMaterial color="#f2b62c" />
      </mesh>
      {[-1, 1].map((l) => (
        // asa de gaivota em "M": parte interna sobe, parte externa desce, ponta preta
        <group key={l} rotation={[l * (asa + 0.3), 0, 0]}>
          <mesh position={[0, 0, l * 0.32]}>
            <boxGeometry args={[0.3, 0.025, 0.62]} />
            <meshStandardMaterial color="#eceeef" flatShading />
          </mesh>
          <group position={[0, 0, l * 0.62]} rotation={[l * -0.65, 0, 0]}>
            <mesh position={[-0.03, 0, l * 0.3]} scale={[0.75, 1, 1]}>
              <boxGeometry args={[0.3, 0.022, 0.6]} />
              <meshStandardMaterial color="#e2e5e7" flatShading />
            </mesh>
            <mesh position={[-0.06, 0, l * 0.62]} scale={[0.5, 1, 1]}>
              <boxGeometry args={[0.3, 0.023, 0.14]} />
              <meshStandardMaterial color="#1e1e1e" flatShading />
            </mesh>
          </group>
        </group>
      ))}
    </group>
  );
};

export const PassarosJanela3D: React.FC<{dur: number; eventos: Record<string, number>}> = ({dur}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  // 6 gaivotas atravessam da direita para a esquerda, em profundidades diferentes (perto = grande e rápida)
  const aves = Array.from({length: 9}, (_, i) => ({
    ini: Math.round((i / 9) * dur * 0.7),
    y: 0.4 + random(`gy${i}`) * 2.6,
    z: -1 + random(`gz${i}`) * 4.5,
    vel: 0.14 + random(`gv${i}`) * 0.08,
  }));
  return (
    <ThreeCanvas width={width} height={height} gl={{alpha: true}} style={{background: 'transparent'}}
      camera={{fov: 50, position: [0, 0, 8]}}>
      <Camera />
      <ambientLight intensity={1.0} />
      <directionalLight position={[3, 5, 6]} intensity={1.6} color="#fff1d6" />
      {aves.map((a, i) => {
        const t = f - a.ini;
        if (t < 0) return null;
        const prof = (a.z + 1) / 4.5;                         // 0 longe, 1 perto
        const x = -4.5 - prof * 2 + t * a.vel * (1 + prof);   // voam para a direita (para onde o bico aponta)
        const y = a.y + Math.sin(t * 0.08 + i) * 0.15;
        const op = interpolate(x, [4.5, 6], [1, 0], cl);
        return op > 0 ? <Gaivota key={i} pos={[x, y, a.z]} f={f + i * 7} escala={0.55 + prof * 0.6} rumo={0} /> : null;
      })}
    </ThreeCanvas>
  );
};
