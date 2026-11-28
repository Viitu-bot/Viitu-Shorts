import React from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Camera} from './comum3d';

// vd022 — por que a cadeira tranca a porta (dono 28/11: "faltou animação 3D"). Porta de sala com maçaneta de ALAVANCA:
// 1) a alavanca desce e a lingueta (em "raio-x", amarela) recua para dentro da porta → abre;
// 2) a cadeira entra virada de ponta-cabeça e o pé de FERRO encaixa logo embaixo da alavanca;
// 3) alguém tenta abaixar: a alavanca bate no ferro e para (anel vermelho) → a lingueta não recua, a porta não abre.
// Eventos (quadros desde o início do bloco): desce, vira, ferro, tenta.
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const LX = 0.62, LY = 0.0;            // pivô da alavanca na porta (perto da borda direita da folha)
const BORDA = 0.95;                    // borda direita da folha da porta

export const Porta3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const tDesce = eventos.desce ?? 30, tVira = eventos.vira ?? 70, tFerro = eventos.ferro ?? 95, tTenta = eventos.tenta ?? 130;

  // 1) alavanca desce e volta; lingueta recua junto
  const desce = interpolate(f, [tDesce - 10, tDesce + 2, tDesce + 8, tDesce + 15], [0, 1, 1, 0], suave);
  // 3) tentativa bloqueada: desce só um tiquinho e tranca (com tremida)
  const tenta = interpolate(f, [tTenta - 4, tTenta + 3], [0, 1], cl);
  const treme = f > tTenta && f < tTenta + 16 ? Math.sin((f - tTenta) * 2.2) * 0.025 * (1 - (f - tTenta) / 16) : 0;
  const angulo = 0.62 * desce + 0.09 * tenta + treme;   // positivo = ponta da alavanca para BAIXO
  const lingueta = 0.17 * desce;                       // quanto a lingueta recua para dentro da porta
  const choque = interpolate(f, [tTenta + 1, tTenta + 5, tTenta + 26], [0, 1, 0], cl);

  // 2) cadeira: entra de baixo/direita girando de ponta-cabeça; o pé (barra) termina logo abaixo da alavanca
  const entra = interpolate(f, [tVira - 6, tFerro], [0, 1], suave);
  const chX = interpolate(entra, [0, 1], [2.6, 0.32]), chY = interpolate(entra, [0, 1], [-2.6, -0.39]);
  const chRot = interpolate(entra, [0, 1], [0, Math.PI]);
  const encaixa = interpolate(f, [tFerro - 3, tFerro + 4, tFerro + 14], [0, 1, 0.35], cl);

  // câmera: perto da maçaneta → recua para ver a cadeira chegar → aproxima na tentativa
  const k1 = interpolate(f, [tVira - 10, tVira + 8], [0, 1], suave);
  const k2 = interpolate(f, [tTenta - 18, tTenta - 2], [0, 1], suave);
  const cam: [number, number, number] = [
    interpolate(k2, [0, 1], [interpolate(k1, [0, 1], [0.95, 1.25]), 1.0]),
    interpolate(k2, [0, 1], [interpolate(k1, [0, 1], [0.25, -0.35]), 0.15]),
    interpolate(k2, [0, 1], [interpolate(k1, [0, 1], [1.9, 3.6]), 1.7]) + interpolate(f, [0, dur], [0.15, 0], cl),
  ];
  const alvo: [number, number, number] = [
    interpolate(k1, [0, 1], [LX - 0.1, 0.5]) * (1 - k2) + (LX - 0.05) * k2,
    interpolate(k1, [0, 1], [LY, -0.45]) * (1 - k2) + (LY - 0.05) * k2,
    0,
  ];

  const metal = <meshStandardMaterial color="#c9ccd1" metalness={0.35} roughness={0.3} />;
  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 100}}>
      <Camera pos={cam} alvo={alvo} />
      <color attach="background" args={['#cfc4ae']} />
      <hemisphereLight args={['#fff6e6', '#5a4a3a', 1.0]} />
      <directionalLight position={[2.5, 3, 4]} intensity={2.0} />
      <pointLight position={[LX, 0.4, 1.2]} intensity={0.6} />

      {/* parede e batente */}
      <mesh position={[0, 0, -0.08]}><boxGeometry args={[8, 8, 0.05]} /><meshStandardMaterial color="#e3d9c4" roughness={0.9} /></mesh>
      <mesh position={[BORDA + 0.12, 0, -0.02]}><boxGeometry args={[0.18, 6, 0.16]} /><meshStandardMaterial color="#8a6a48" roughness={0.6} /></mesh>
      {/* folha da porta (madeira), meio transparente perto da fechadura para ver a lingueta */}
      <mesh position={[-0.55, 0, 0]}><boxGeometry args={[3.0, 6, 0.09]} /><meshStandardMaterial color="#a8763f" roughness={0.55} transparent opacity={0.72} depthWrite={false} /></mesh>
      {/* lingueta (raio-x): sai da borda da porta e entra no batente */}
      <mesh position={[BORDA + 0.07 - lingueta, -0.18, 0]}>
        <boxGeometry args={[0.26, 0.1, 0.12]} /><meshBasicMaterial color="#ffd23a" />
      </mesh>
      {/* espelho da maçaneta */}
      <mesh position={[LX, LY - 0.12, 0.06]}><boxGeometry args={[0.14, 0.5, 0.03]} />{metal}</mesh>
      {/* ALAVANCA: gira em torno do pivô (z), apontando para dentro da porta (−x) */}
      <group position={[LX, LY, 0.12]} rotation={[0, 0, angulo]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.045, 0.045, 0.12, 20]} />{metal}</mesh>
        <mesh position={[-0.24, 0, 0.06]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.035, 0.035, 0.5, 20]} />{metal}</mesh>
      </group>
      {/* anel vermelho no choque alavanca × ferro */}
      {choque > 0.02 && (
        <mesh position={[LX - 0.36, LY - 0.09, 0.22]} scale={0.08 + 0.12 * choque}>
          <torusGeometry args={[1, 0.12, 12, 40]} /><meshBasicMaterial color="#ff2a2a" transparent opacity={choque} />
        </mesh>
      )}

      {/* CADEIRA ESCOLAR (assento azul, pés de ferro); de ponta-cabeça o pé de trás vira a barra sob a alavanca */}
      <group position={[chX, chY, 0.51]} rotation={[0, 0, chRot]}>
        <mesh position={[0, 0.5, 0]}><boxGeometry args={[0.9, 0.07, 0.75]} /><meshStandardMaterial color="#2b3f8f" roughness={0.5} /></mesh>
        <mesh position={[0, 0.95, -0.36]} rotation={[0.15, 0, 0]}><boxGeometry args={[0.9, 0.55, 0.06]} /><meshStandardMaterial color="#2b3f8f" roughness={0.5} /></mesh>
        {[[-0.4, 0.33], [0.4, 0.33], [-0.4, -0.33], [0.4, -0.33]].map(([x, z], i) => (
          <mesh key={i} position={[x, 0.07, z]}><cylinderGeometry args={[0.03, 0.03, 0.9, 12]} />{metal}</mesh>
        ))}
        {/* travessa de ferro entre os pés de trás: é ela que fica sob a alavanca */}
        <mesh position={[0, -0.3, -0.33]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.03, 0.03, 0.82, 12]} />
          <meshStandardMaterial color="#c9ccd1" metalness={0.35} roughness={0.3} emissive="#ffd23a" emissiveIntensity={encaixa * 0.8} /></mesh>
      </group>
    </ThreeCanvas>
  );
};
