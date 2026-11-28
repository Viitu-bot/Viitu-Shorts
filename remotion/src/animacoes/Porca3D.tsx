import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Camera} from './comum3d';

// vd023 — Hard Lock (nippon.com / ficha MISUMI): porca de BAIXO com ressalto cônico EXCÊNTRICO (cunha fina de um lado,
// grossa do outro), porca de CIMA com rebaixo cônico centrado. Apertar a de cima força o ressalto torto para o centro:
// a porca de baixo é EMPURRADA DE LADO contra a rosca = cunha martelada. Corte em "raio-x" (meio transparente).
// Eventos (quadros desde o início do bloco): torta, aperta, empurrada, martelada.
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};

const hex = (r: number, h: number) => new THREE.CylinderGeometry(r, r, h, 6, 1);

export const Porca3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const tTorta = eventos.torta ?? 20, tAperta = eventos.aperta ?? 40, tEmp = eventos.empurrada ?? 80, tMart = eventos.martelada ?? 130;

  const destaca = interpolate(f, [tTorta - 6, tTorta + 6, tAperta + 6], [0, 1, 0.4], cl);        // brilho no ressalto torto
  const desce = interpolate(f, [tAperta - 4, tEmp + 2], [0, 1], suave);                            // porca de cima descendo/girando
  const yCima = interpolate(desce, [0, 1], [1.55, 0.62]);
  const giro = desce * Math.PI * 3;
  const empurra = interpolate(f, [tEmp - 2, tEmp + 10], [0, 1], suave);                            // porca de baixo vai de lado
  const xBaixo = 0.2 * empurra;
  const martela = interpolate(f, [tMart - 2, tMart + 2, tMart + 14], [0, 1, 0.25], cl);           // impacto da cunha
  const tremer = f > tMart + 16 ? Math.sin(f * 2.4) * 0.03 : 0;                                    // vibração no fim: nada solta
  const seta = interpolate(f, [tEmp - 2, tEmp + 6, tMart + 20], [0, 1, 0.6], cl);

  const k = interpolate(f, [0, dur], [0, 1], suave);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [1.7, 1.2]), interpolate(k, [0, 1], [2.0, 1.5]), interpolate(k, [0, 1], [5.6, 4.6])];
  const alvo: [number, number, number] = [0.22, 0.55, 0];

  const gNut = useMemo(() => hex(0.62, 0.42), []);
  const metal = (cor: string, op = 0.55) => <meshStandardMaterial color={cor} metalness={0.35} roughness={0.35} transparent opacity={op} depthWrite={false} />;

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 38, position: cam, near: 0.05, far: 100}}>
      <Camera pos={cam} alvo={alvo} />
      <color attach="background" args={['#1d232b']} />
      <hemisphereLight args={['#ffffff', '#3a3f48', 1.0]} />
      <directionalLight position={[3, 4, 4]} intensity={2.2} />
      <pointLight position={[-2, 1.5, 2]} intensity={0.8} color="#9cc8ff" />

      <group position={[tremer, 0, 0]}>
        {/* placa e parafuso */}
        <mesh position={[0, -0.2, 0]}><boxGeometry args={[3.2, 0.25, 2.0]} /><meshStandardMaterial color="#5b636e" metalness={0.3} roughness={0.6} /></mesh>
        <mesh position={[0, 0.9, 0]}><cylinderGeometry args={[0.26, 0.26, 2.4, 32]} /><meshStandardMaterial color="#b8bec6" metalness={0.5} roughness={0.3} /></mesh>
        {Array.from({length: 18}, (_, i) => (
          <mesh key={i} position={[0, -0.05 + i * 0.12, 0]} rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[0.265, 0.012, 6, 32]} /><meshStandardMaterial color="#8d949c" /></mesh>
        ))}

        <mesh position={[0, 0.9, 0.62]}><boxGeometry args={[0.02, 2.2, 0.02]} /><meshBasicMaterial color="#ff3b3b" transparent opacity={destaca} /></mesh>
        <mesh position={[0.17 + xBaixo, 0.55, 0.62]}><boxGeometry args={[0.02, 0.5, 0.02]} /><meshBasicMaterial color="#ffb000" transparent opacity={destaca} /></mesh>
        {/* porca de BAIXO (azul) com ressalto cônico TORTO (laranja) */}
        <group position={[xBaixo, 0.21, 0]}>
          <mesh geometry={gNut}>{metal('#3d7bd6')}</mesh>
          <mesh position={[0.17, 0.32, 0]}>
            <cylinderGeometry args={[0.36, 0.52, 0.22, 32, 1, true]} />
            <meshStandardMaterial color="#ff8a1f" emissive="#ff6a00" emissiveIntensity={0.3 + destaca * 0.9 + martela} side={THREE.DoubleSide} transparent opacity={0.85} />
          </mesh>
        </group>

        {/* porca de CIMA (cinza) descendo e girando */}
        <group position={[0, yCima, 0]} rotation={[0, giro, 0]}>
          <mesh geometry={gNut}>{metal('#cfd5dc', 0.45)}</mesh>
        </group>

        {/* seta: empurrão lateral */}
        {seta > 0.02 && (
          <group position={[-0.95 + 0.2 * empurra, 0.22, 0.2]} scale={1.3}>
            <mesh rotation={[0, 0, -Math.PI / 2]}><coneGeometry args={[0.1, 0.24, 20]} /><meshBasicMaterial color="#ffd23a" transparent opacity={seta} /></mesh>
            <mesh position={[-0.28, 0, 0]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.035, 0.035, 0.4, 12]} /><meshBasicMaterial color="#ffd23a" transparent opacity={seta} /></mesh>
          </group>
        )}
        {/* clarão da cunha martelada no lado grosso */}
        {martela > 0.02 && (
          <mesh position={[0.6 + xBaixo, 0.42, 0.3]} scale={0.08 + 0.18 * martela}>
            <sphereGeometry args={[1, 16, 12]} /><meshBasicMaterial color="#fff2b0" transparent opacity={martela * 0.8} />
          </mesh>
        )}
      </group>
    </ThreeCanvas>
  );
};
