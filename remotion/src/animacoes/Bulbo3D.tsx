import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd013 — o bulbo de proa visto de lado (Wikipedia "Bulbous bow": o vale da onda do bulbo coincide com a crista da onda
// da proa e as duas se cancelam — interferência destrutiva). Casco + bulbo debaixo d'água; a linha VERMELHA é a onda que
// o casco empurra; a AZUL é a onda do bulbo, logo antes; vale encaixa na crista; a superfície fica LISA.
// Eventos (quadros desde o início): onda2 ("outra"), vale ("vale"), crista ("crista"), apagam ("apagam").
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const X0 = -5.5, X1 = 3.4, N = 160;
const K = 2.4, A = 0.42, CRISTA = 0.35;          // número de onda, amplitude, posição da crista da onda do casco
const env = (x: number) => Math.exp(-(((x - CRISTA + 0.8) / 2.0) ** 2));
const casco = (x: number) => A * Math.cos(K * (x - CRISTA)) * env(x);   // crista em x = CRISTA (logo à frente da proa)

const linha = (fn: (x: number) => number, dy: number) => {
  const pts = Array.from({length: N}, (_, i) => {
    const x = X0 + (i / (N - 1)) * (X1 - X0);
    return new THREE.Vector3(x, fn(x) + dy, 0.62);
  });
  return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 160, 0.035, 8, false);
};

export const Bulbo3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tOnda2 = eventos.onda2 ?? 25, tVale = eventos.vale ?? 76, tCrista = eventos.crista ?? 108, tApaga = eventos.apagam ?? 158;

  const onda2 = interpolate(f, [tOnda2 - 4, tOnda2 + 14], [0, 1], suave);       // a onda do bulbo aparece
  const separa = interpolate(f, [tOnda2, tOnda2 + 14, tApaga - 10, tApaga + 6], [0, 1, 1, 0], suave);   // linhas guia acima da água
  const apaga = interpolate(f, [tApaga - 6, tApaga + 12], [0, 1], suave);       // a soma: superfície lisa
  const brilhoVale = interpolate(f, [tVale - 4, tVale + 4, tCrista + 20], [0, 1, 0.3], cl);
  const brilhoCrista = interpolate(f, [tCrista - 4, tCrista + 4, tApaga], [0, 1, 0.3], cl);
  const ondula = Math.sin(f * 0.25) * 0.03;

  const bulbo = (x: number) => -casco(x) * onda2;                                 // mesma onda, fase oposta
  const superficie = (x: number) => casco(x) * (1 - apaga) + (casco(x) + bulbo(x)) * apaga + ondula * (1 - apaga);

  // água: forma 2D com a superfície em cima (recalculada a cada quadro)
  const agua = useMemo(() => {
    const s = new THREE.Shape();
    s.moveTo(X0, -7);
    for (let i = 0; i < N; i++) { const x = X0 + (i / (N - 1)) * (X1 - X0); s.lineTo(x, superficie(x)); }
    s.lineTo(X1, -7);
    return new THREE.ShapeGeometry(s);
  }, [f]); // eslint-disable-line react-hooks/exhaustive-deps
  const gCasco = useMemo(() => linha(casco, 0), []);
  const gBulbo = useMemo(() => linha((x) => -casco(x), 0), []);
  const gSup = useMemo(() => linha(superficie, 0), [f]); // eslint-disable-line react-hooks/exhaustive-deps

  const xVale = CRISTA;                         // o vale da onda do bulbo cai exatamente na crista da onda do casco
  const k = interpolate(f, [0, dur], [0, 1], suave);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [0.0, 0.2]), interpolate(k, [0, 1], [1.7, 1.6]), interpolate(k, [0, 1], [9.8, 9.3])];
  const alvo: [number, number, number] = [0.1, 1.6, 0];

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 100}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.8} />
      <color attach="background" args={['#9cc6e8']} />
      <hemisphereLight args={['#ffffff', '#1d3550', 0.8]} />
      <directionalLight position={[3, 5, 6]} intensity={1.8} />

      {/* CASCO de lado: costado escuro, fundo vermelho (antiincrustante), proa e o BULBO debaixo d'água */}
      <group position={[0, 0, 0]}>
        <mesh position={[-2.9, 0.55, 0]}><boxGeometry args={[4.6, 1.5, 1.0]} /><meshStandardMaterial color="#20262e" roughness={0.6} /></mesh>
        <mesh position={[-2.9, -0.75, 0]}><boxGeometry args={[4.6, 1.1, 1.0]} /><meshStandardMaterial color="#9b2a22" roughness={0.7} /></mesh>
        <mesh position={[-0.35, 0.2, 0]} rotation={[0, 0, -0.22]}><boxGeometry args={[1.0, 2.6, 1.0]} /><meshStandardMaterial color="#20262e" roughness={0.6} /></mesh>
        <mesh position={[0.05, -1.05, 0]} rotation={[0, 0, Math.PI / 2]} scale={[1, 1.5, 1]}>
          <sphereGeometry args={[0.42, 32, 16]} /><meshStandardMaterial color="#b3332a" roughness={0.6} emissive="#ff4a3a" emissiveIntensity={onda2 * 0.25} />
        </mesh>
      </group>

      {/* ÁGUA (vidro azul na frente do casco) */}
      <mesh geometry={agua} position={[0, 0, 0.55]}>
        <meshStandardMaterial color="#1f6fae" transparent opacity={0.55} roughness={0.2} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={gSup}><meshBasicMaterial color="#ffffff" /></mesh>

      {/* linhas guia: onda do CASCO (vermelha) e do BULBO (azul), acima da água para comparar */}
      {separa > 0.01 && (
        <>
          <group position={[0, 1.15 * separa, 0]}><mesh geometry={gCasco}><meshBasicMaterial color="#ff4a3a" transparent opacity={separa} /></mesh></group>
          <group position={[0, 2.05 * separa, 0]}><mesh geometry={gBulbo}><meshBasicMaterial color="#2fb7ff" transparent opacity={separa * onda2} /></mesh></group>
          {/* vale (azul) e crista (vermelha) no MESMO ponto */}
          <mesh position={[xVale, 2.05 * separa - A * env(xVale), 0.65]} scale={0.11 + 0.05 * brilhoVale}><sphereGeometry args={[1, 16, 12]} />
            <meshBasicMaterial color="#9fe4ff" transparent opacity={brilhoVale} /></mesh>
          <mesh position={[xVale, 1.15 * separa + A * env(xVale), 0.65]} scale={0.11 + 0.05 * brilhoCrista}><sphereGeometry args={[1, 16, 12]} />
            <meshBasicMaterial color="#ffb0a6" transparent opacity={brilhoCrista} /></mesh>
          {brilhoCrista > 0.05 && (
            <mesh position={[xVale, 1.6 * separa, 0.64]}><boxGeometry args={[0.03, 0.9 * separa, 0.03]} /><meshBasicMaterial color="#ffffff" transparent opacity={brilhoCrista} /></mesh>
          )}
        </>
      )}
    </ThreeCanvas>
  );
};
