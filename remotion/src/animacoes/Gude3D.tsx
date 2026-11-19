import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd012 — o que a câmera não mostra (Wikipedia "Marble (toy)": no "olho de gato", veios de vidro colorido são injetados
// no fluxo transparente; Grit/Marble King: a 2ª cor entra no vidro derretido). O filete de vidro em brasa desce; o
// vidro AMARELO (forno à parte, visto no bruto) entra como um FIO no meio; a lâmina corta uma gota; a gota abre ao meio
// e mostra a cor JÁ lá dentro.
// Eventos (quadros desde o início): fio ("fio"), meio ("transparente"), corta ("corta"), dentro ("gota").
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const BRASA = '#ff5a14';
const AMARELO = '#ffd21f';

export const Gude3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tFio = eventos.fio ?? 27, tMeio = eventos.meio ?? 66, tCorta = eventos.corta ?? 114, tDentro = eventos.dentro ?? 131;

  const fio = interpolate(f, [tFio - 6, tFio + 18], [0, 1], suave);            // o fio amarelo desce dentro do filete
  const vidro = interpolate(f, [tFio - 4, tFio + 14, tMeio - 6, tMeio + 6], [0.9, 0.55, 0.55, 0.3], cl);      // o filete fica translúcido: ver o fio no MEIO
  const lamina = interpolate(f, [tCorta - 6, tCorta + 2, tCorta + 10], [-2.6, 0, 2.6], cl);
  const cai = interpolate(f, [tCorta + 2, tDentro], [0, 1], suave);            // a gota cortada cai e arredonda
  const abre = interpolate(f, [tDentro, tDentro + 10], [0, 0.8], suave);      // a gota abre ao meio
  const gira = interpolate(f, [tCorta, tDentro], [0, 0.6], cl);
  const pulso = 1 + Math.sin(f * 0.35) * 0.03;

  const k = interpolate(f, [tCorta, tDentro + 8], [0, 1], suave);
  const cam: [number, number, number] = [interpolate(k, [0, 1], [1.8, 0.7]), interpolate(k, [0, 1], [1.2, -1.3]), interpolate(k, [0, 1], [9.0, 4.8])];
  const alvo: [number, number, number] = [-0.3 * (1 - k), interpolate(k, [0, 1], [0.9, -1.8]), 0];

  // veio do "olho de gato": fita curva amarela dentro da esfera
  const veio = useMemo(() => {
    const pts = Array.from({length: 24}, (_, i) => {
      const t = i / 23, a = t * Math.PI * 1.2 - 0.6;
      return new THREE.Vector3(Math.sin(a) * 0.32, (t - 0.5) * 0.9, Math.cos(a) * 0.12);
    });
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 48, 0.07, 10, false);
  }, []);

  const yGota = -1.15 - cai * 0.75;
  const esticada = interpolate(cai, [0, 1], [1.5, 1]);

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 100}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.6} />
      <color attach="background" args={['#120d0a']} />
      <hemisphereLight args={['#fff1e0', '#1a1410', 0.5]} />
      <directionalLight position={[2, 4, 5]} intensity={1.6} />
      <pointLight position={[0, 0.5, 2]} intensity={10} color={BRASA} distance={8} />

      {/* bico do forno grande (vidro transparente) e bico do forno à parte (amarelo) */}
      <mesh position={[0, 2.55, 0]}><cylinderGeometry args={[0.55, 0.32, 0.7, 32]} /><meshStandardMaterial color="#6b625a" metalness={0.6} roughness={0.5} /></mesh>
      <mesh position={[-1.25, 2.35, 0]} rotation={[0, 0, -1.0]}><cylinderGeometry args={[0.1, 0.1, 1.8, 16]} /><meshStandardMaterial color="#6b625a" metalness={0.6} roughness={0.5} emissive={AMARELO} emissiveIntensity={fio * 1.6} /></mesh>
      <mesh position={[-1.9, 2.75, 0]}><sphereGeometry args={[0.35, 24, 16]} /><meshStandardMaterial color="#7a6f64" metalness={0.4} roughness={0.6} emissive={AMARELO} emissiveIntensity={0.25} /></mesh>

      {/* FILETE de vidro em brasa (de cima até o corte) */}
      <mesh position={[0, 0.65, 0]}>
        <cylinderGeometry args={[0.26 * pulso, 0.26 * pulso, 3.2, 32, 1, true]} />
        <meshStandardMaterial color={BRASA} emissive={BRASA} emissiveIntensity={0.55} transparent opacity={vidro} roughness={0.15} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {/* o FIO amarelo no meio do filete, descendo */}
      {fio > 0.01 && (
        <mesh position={[0, 2.25 - fio * 1.6, 0]}>
          <cylinderGeometry args={[0.11, 0.11, fio * 3.2, 16]} />
          <meshStandardMaterial color={AMARELO} emissive={AMARELO} emissiveIntensity={2.2} />
        </mesh>
      )}
      {/* LÂMINA */}
      <mesh position={[lamina, -0.95, 0]}><boxGeometry args={[1.6, 0.05, 0.9]} /><meshStandardMaterial color="#c9ced4" metalness={0.95} roughness={0.15} /></mesh>

      {/* a GOTA: cai, arredonda e abre ao meio mostrando o veio */}
      {f >= tCorta - 2 && (
        <group position={[0, yGota, 0]} rotation={[0, gira, 0]} scale={[1, esticada, 1]}>
          {[1, -1].map((lado) => (
            <group key={lado} position={[lado * abre, 0, 0]} rotation={[0, -lado * abre * 1.1, 0]}>
              <mesh rotation={[0, 0, lado * Math.PI / 2]}>
                <sphereGeometry args={[0.5, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2]} />
                <meshStandardMaterial color={interpolate(cai, [0, 1], [0, 1]) > 0.5 ? '#9fe0c8' : BRASA} emissive={BRASA}
                  emissiveIntensity={interpolate(cai, [0, 1], [1.1, 0.15])} transparent opacity={0.4} roughness={0.05}
                  side={THREE.DoubleSide} depthWrite={false} />
              </mesh>
              {/* face do corte com o veio amarelo */}
              {abre > 0.02 && (
                <mesh rotation={[0, lado * Math.PI / 2, 0]}><circleGeometry args={[0.5, 40]} />
                  <meshStandardMaterial color="#cfeee2" transparent opacity={0.25} side={THREE.DoubleSide} depthWrite={false} /></mesh>
              )}
            </group>
          ))}
          <mesh geometry={veio} position={[0, 0, 0]}>
            <meshStandardMaterial color={AMARELO} emissive={AMARELO} emissiveIntensity={interpolate(cai, [0, 1], [1.2, 0.5])} />
          </mesh>
        </group>
      )}
    </ThreeCanvas>
  );
};
