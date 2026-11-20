import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd015 — por que a estrada em Guizhou vai "voando": corte lateral de um relevo de morros e cânions.
// 1) a estrada antiga (vermelha) desce e sobe cada vale — o carro vermelho anda devagar, sobe e desce;
// 2) a estrada nova (amarela) segue RETA: pontes sobre os vales e túneis pelos morros — o carro amarelo chega antes.
// Eventos (quadros desde o início): desce ("descer"), sobe ("subir"), reta ("reta"), pontes ("pontes"), tuneis ("túneis").
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const X0 = -6, X1 = 6, N = 240;
// relevo: morros e cânions (altura em função de x)
const terreno = (x: number) => 0.2 + 1.5 * Math.exp(-(((x + 2.6) / 0.9) ** 2)) + 1.7 * Math.exp(-(((x - 3.4) / 1.0) ** 2))
  + 0.5 * Math.sin(x * 2.1) - 2.4 * Math.exp(-(((x - 0.6) / 0.75) ** 2)) - 0.6;
const ALTURA = 1.25;                            // cota da estrada nova (reta, acima dos vales)

export const Estrada3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tDesce = eventos.desce ?? 10, tSobe = eventos.sobe ?? 25, tReta = Math.max(eventos.reta ?? 50, tSobe + 10);
  const tPontes = Math.max(eventos.pontes ?? 70, tReta + 6), tTuneis = Math.max(eventos.tuneis ?? 95, tPontes + 6);

  const geoTerra = useMemo(() => {
    const s = new THREE.Shape();
    s.moveTo(X0, -4);
    for (let i = 0; i < N; i++) { const x = X0 + (i / (N - 1)) * (X1 - X0); s.lineTo(x, terreno(x)); }
    s.lineTo(X1, -4);
    return new THREE.ExtrudeGeometry(s, {depth: 1.6, bevelEnabled: false});
  }, []);
  const linha = (fn: (x: number) => number, r: number, ate: number) => {
    const n = Math.max(2, Math.round(N * ate));
    const pts = Array.from({length: n}, (_, i) => { const x = X0 + (i / (N - 1)) * (X1 - X0); return new THREE.Vector3(x, fn(x) + 0.06, 0.85); });
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), n * 2, r, 6, false);
  };
  const velha = interpolate(f, [tDesce - 6, tSobe + 14], [0.02, 1], cl);           // a estrada antiga se desenha seguindo o relevo
  const nova = interpolate(f, [tReta - 4, tReta + 22], [0.02, 1], suave);           // a nova, reta
  const geoVelha = useMemo(() => linha(terreno, 0.07, velha), [velha]);           // eslint-disable-line react-hooks/exhaustive-deps
  const geoNova = useMemo(() => linha(() => ALTURA, 0.09, nova), [nova]);          // eslint-disable-line react-hooks/exhaustive-deps
  const pontes = interpolate(f, [tPontes - 4, tPontes + 10], [0, 1], cl);
  const tuneis = interpolate(f, [tTuneis - 4, tTuneis + 10], [0, 1], cl);

  // pilares das pontes: onde o terreno fica abaixo da estrada; túneis: onde o morro passa da estrada
  const pilares = useMemo(() => Array.from({length: 24}, (_, i) => X0 + 0.25 + i * 0.5).filter((x) => terreno(x) < ALTURA - 0.3), []);
  const tuneisX = useMemo(() => {
    const r: [number, number][] = []; let a: number | null = null;
    for (let i = 0; i <= 300; i++) { const x = X0 + (i / 300) * (X1 - X0); const dentro = terreno(x) > ALTURA - 0.05;
      if (dentro && a === null) a = x; if (!dentro && a !== null) { r.push([a, x]); a = null; } }
    if (a !== null) r.push([a, X1]); return r;
  }, []);

  // carros: vermelho segue o relevo (lento); amarelo vai reto (rápido)
  const tCarro = (f - tReta) / Math.max(dur - tReta, 1);
  const xa = X0 + Math.min(Math.max(tCarro, 0), 1) * (X1 - X0);
  const xv = X0 + Math.min(Math.max(tCarro, 0), 1) * (X1 - X0) * 0.42;
  const carro = (x: number, y: number, cor: string, vis: number) => vis > 0.01 && (
    <mesh position={[x, y + 0.2, 0.85]}><boxGeometry args={[0.6, 0.3, 0.3]} /><meshStandardMaterial color={cor} emissive={cor} emissiveIntensity={0.5} transparent opacity={vis} /></mesh>
  );
  const visCarro = interpolate(f, [tReta + 10, tReta + 20], [0, 1], cl);

  const k = interpolate(f, [0, dur], [0, 1], suave);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [-0.4, 0.4]), 0.6, interpolate(k, [0, 1], [17.0, 17.5])];
  const alvo: [number, number, number] = [interpolate(k, [0, 1], [-0.4, 0.4]), 0.0, 0];

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 200}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.8} />
      <color attach="background" args={['#b8d6ee']} />
      <fog attach="fog" args={['#b8d6ee', 14, 30]} />
      <hemisphereLight args={['#ffffff', '#2c3a22', 0.85]} />
      <directionalLight position={[3, 6, 6]} intensity={1.7} />
      {/* relevo verde (morros e cânions) */}
      <mesh geometry={geoTerra} position={[0, 0, -0.8]}><meshStandardMaterial color="#4f7a3a" roughness={1} /></mesh>
      {/* rio no fundo dos cânions */}
      <mesh position={[0.6, -2.55, 0.2]}><boxGeometry args={[1.2, 0.08, 1.4]} /><meshStandardMaterial color="#3a8fbf" roughness={0.3} /></mesh>
      {/* estrada antiga (desce e sobe) */}
      {velha > 0.03 && <mesh geometry={geoVelha}><meshStandardMaterial color="#e2483a" emissive="#e2483a" emissiveIntensity={0.25} /></mesh>}
      {/* estrada nova (reta) */}
      {nova > 0.03 && <mesh geometry={geoNova}><meshStandardMaterial color="#ffd23f" emissive="#ffb800" emissiveIntensity={0.45} /></mesh>}
      {/* PONTES: pilares que sobem do vale até a estrada */}
      {pilares.map((x, i) => {
        const base = terreno(x), alt = (ALTURA - base) * pontes;
        return alt > 0.02 && (
          <mesh key={i} position={[x, base + alt / 2, 0.85]}><boxGeometry args={[0.1, alt, 0.12]} /><meshStandardMaterial color="#d7d2c8" roughness={0.7} /></mesh>
        );
      })}
      {/* TÚNEIS: boca escura onde a estrada atravessa o morro */}
      {tuneisX.map(([a, b], i) => (
        <mesh key={i} position={[(a + b) / 2, ALTURA + 0.06, 0.9]} scale={[1, tuneis, 1]}>
          <boxGeometry args={[b - a, 0.34, 0.3]} /><meshStandardMaterial color="#1a1a1a" transparent opacity={0.85 * tuneis} />
        </mesh>
      ))}
      {carro(xv, terreno(xv) + 0.06, '#e2483a', visCarro)}
      {carro(xa, ALTURA + 0.06, '#ffd23f', visCarro)}
    </ThreeCanvas>
  );
};
