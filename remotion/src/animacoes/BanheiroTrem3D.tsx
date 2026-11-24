import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing, random} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd016 — corte lateral de um vagão: o banheiro antigo (cano reto → trilhos que passam) × o novo (vácuo suga pelo
// cano para um tanque embaixo do vagão). Wikipedia "Passenger train toilet"; India Water Portal (vácuo ~2 L/descarga).
// Eventos (quadros desde o início): novo ("copiaram"), vacuo ("vácuo"), agua ("litros"), tanque ("tanque").
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const MARROM = '#7a4a22';

export const BanheiroTrem3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tNovo = eventos.novo ?? 40, tVacuo = Math.max(eventos.vacuo ?? 70, tNovo + 8), tAgua = Math.max(eventos.agua ?? 110, tVacuo + 8);
  const tTanque = Math.max(eventos.tanque ?? 140, tAgua + 8);

  const perto = fase === 'perto';                                            // 2ª vista: o sistema novo já instalado
  const novo = perto ? 1 : interpolate(f, [tNovo - 6, tNovo + 12], [0, 1], suave);         // o cano reto vira cano + tanque
  const suga = perto ? 1 : interpolate(f, [tVacuo - 2, tVacuo + 6], [0, 1], cl);
  const enche = perto ? interpolate(f, [0, tTanque + 20], [0.3, 0.8], cl) : interpolate(f, [tVacuo, dur], [0.05, 0.3], cl);
  const gota = interpolate(f, [tAgua - 4, tAgua + 4, tAgua + 24], [0, 1, 0], cl);
  const brilhoTanque = interpolate(f, [tTanque - 4, tTanque + 4, tTanque + 30], [0, 1, 0.3], cl);
  const trilhoX = -(f * 0.22) % 1.2;                                         // dormentes passando (trem andando)

  const k = interpolate(f, [0, dur], [0, 1], suave);
  // vistas (fase): troca de câmera a cada ≤ 3,5 s dentro do bloco 3D (montagem R9) — "lado" = corte inteiro,
  // "perto" = vaso → cano → tanque de perto (a água e o tanque enchendo)
  const cam: [number, number, number] = perto ? [interpolate(k, [0, 1], [-0.2, 1.4]), 0.5, interpolate(k, [0, 1], [5.2, 4.6])]
    : [0.7, 0.4, interpolate(k, [0, 1], [10.6, 10.0])];
  const alvo: [number, number, number] = perto ? [interpolate(k, [0, 1], [-0.3, 1.5]), 0.1, 0] : [0.7, 0.0, 0];

  const bolinhas = useMemo(() => Array.from({length: 40}, (_, i) => ({fase: random(`b${i}`), dx: (random(`x${i}`) - 0.5) * 0.4})), []);

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 100}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.7} />
      <color attach="background" args={['#cfd8e3']} />
      <hemisphereLight args={['#ffffff', '#333333', 0.8]} />
      <directionalLight position={[3, 5, 6]} intensity={1.6} />

      {/* vagão em corte: paredes, piso */}
      <mesh position={[0, 2.2, -0.6]}><boxGeometry args={[6, 3.4, 0.1]} /><meshStandardMaterial color="#e9e4da" roughness={0.9} /></mesh>
      <mesh position={[0, 0.45, 0]}><boxGeometry args={[6, 0.18, 1.4]} /><meshStandardMaterial color="#5d646b" metalness={0.5} roughness={0.5} /></mesh>
      {/* vaso sanitário */}
      <group position={[-0.6, 1.0, 0]}>
        <mesh position={[0, 0.15, 0]}><cylinderGeometry args={[0.42, 0.28, 0.75, 32]} /><meshStandardMaterial color="#f4f4f2" roughness={0.3} /></mesh>
        <mesh position={[0, 0.55, 0]} rotation={[-Math.PI / 2, 0, 0]}><torusGeometry args={[0.38, 0.06, 12, 32]} /><meshStandardMaterial color="#ffffff" roughness={0.3} /></mesh>
      </group>
      {/* CANO ANTIGO: reto pro chão (some quando entra o novo) */}
      {novo < 0.99 && (
        <mesh position={[-0.6, 0.0, 0]} scale={[1, 1, 1 - novo]}><cylinderGeometry args={[0.12, 0.12, 1.1, 16]} /><meshStandardMaterial color="#8a8f95" metalness={0.7} roughness={0.3} transparent opacity={1 - novo} /></mesh>
      )}
      {/* CANO NOVO + TANQUE embaixo do vagão */}
      {novo > 0.01 && (
        <group>
          <mesh position={[-0.6, 0.15, 0]}><cylinderGeometry args={[0.1, 0.1, 0.4, 16]} /><meshStandardMaterial color="#b9c0c8" metalness={0.8} roughness={0.2} transparent opacity={novo} /></mesh>
          <mesh position={[0.35, -0.05, 0]} rotation={[0, 0, Math.PI / 2]} scale={[1, novo, 1]}><cylinderGeometry args={[0.1, 0.1, 1.9, 16]} /><meshStandardMaterial color="#b9c0c8" metalness={0.8} roughness={0.2} /></mesh>
          <mesh position={[1.75, -0.35, 0]} scale={[novo, novo, novo]}><boxGeometry args={[1.3, 0.75, 1.0]} />
            <meshStandardMaterial color="#9fb4c6" transparent opacity={0.45} roughness={0.2} emissive="#3fa8ff" emissiveIntensity={brilhoTanque * 0.5} depthWrite={false} /></mesh>
          {/* conteúdo do tanque */}
          <mesh position={[1.75, -0.72 + 0.37 * enche, 0]} scale={[novo, novo, novo]}><boxGeometry args={[1.22, 0.74 * enche, 0.92]} /><meshStandardMaterial color={MARROM} roughness={0.9} /></mesh>
        </group>
      )}
      {/* gota de água (os "2 litros") */}
      {gota > 0.02 && (
        <mesh position={[-0.6, 1.55 - gota * 0.3, 0]} scale={0.12 * gota}><sphereGeometry args={[1, 16, 12]} /><meshStandardMaterial color="#4fb3ff" emissive="#4fb3ff" emissiveIntensity={0.6} /></mesh>
      )}
      {/* trilhos e dormentes passando */}
      <mesh position={[0, -1.15, 0.25]}><boxGeometry args={[12, 0.08, 0.08]} /><meshStandardMaterial color="#6d6d6d" metalness={0.8} /></mesh>
      <mesh position={[0, -1.15, -0.25]}><boxGeometry args={[12, 0.08, 0.08]} /><meshStandardMaterial color="#6d6d6d" metalness={0.8} /></mesh>
      {Array.from({length: 12}, (_, i) => (
        <mesh key={i} position={[-6 + i * 1.2 + trilhoX + 0.6, -1.25, 0]}><boxGeometry args={[0.25, 0.08, 0.9]} /><meshStandardMaterial color="#5a4632" /></mesh>
      ))}
      <mesh position={[0, -1.4, 0]}><boxGeometry args={[12, 0.2, 2.5]} /><meshStandardMaterial color="#8c8378" roughness={1} /></mesh>
      {/* sujeira: antes cai nos trilhos; depois é sugada pelo cano até o tanque */}
      {bolinhas.map((b, i) => {
        const ciclo = 30;
        const u = ((f + b.fase * ciclo) % ciclo) / ciclo;
        let pos: [number, number, number];
        if (novo < 0.5) {
          pos = [-0.6 + b.dx * 0.3 - u * u * 1.2, 0.5 - u * 1.65, b.dx];       // cai e fica pra trás (trem andando)
        } else if (suga > 0.5) {
          const t = u;
          pos = t < 0.2 ? [-0.6, 0.6 - t * 3, 0] : [-0.6 + (t - 0.2) / 0.8 * 2.3, -0.05, 0];   // desce e corre no cano até o tanque
        } else {
          return null;
        }
        return <mesh key={i} position={pos} scale={0.06}><sphereGeometry args={[1, 8, 6]} /><meshStandardMaterial color={MARROM} /></mesh>;
      })}
    </ThreeCanvas>
  );
};
