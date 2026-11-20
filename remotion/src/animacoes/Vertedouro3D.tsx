import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing, random} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useTexturas} from './comum3d';

// vd014 — vertedouro em salto de esqui, visto de lado (Wikipedia "Spillway"; J. S. Afr. Inst. Civ. Eng. v68n2: a rampa
// no fim lança o jato pelo ar, ele se desfaz em gotas, perde energia e cai longe da fundação, num poço).
// Fase 1 (sem rampa): a água desce e bate no pé da barragem → o chão afunda (buraco vermelho, "perigo").
// Fase 2 (com rampa): a rampa sobe, o jato vira um arco no ar que se espalha em gotas e cai longe, num poço.
// Eventos (quadros desde o início): buraco ("buraco"), rampa ("rampa"), jato ("ar"), gotas ("gotas"), cai ("longe").
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const AGUA = '#e8f7ff';

// perfil da calha: do topo (x=-3.2,y=2.6) descendo até o pé (x=0.2, y=-1.1)
const calha = (t: number): [number, number] => {
  const x = -3.2 + t * 3.4;
  const y = 2.6 - 3.7 * Math.pow(t, 1.6);
  return [x, y];
};

export const Vertedouro3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const tB0 = eventos.buraco ?? 30;
  const tRampa = Math.max(eventos.rampa ?? 75, tB0 + 20), tAr = eventos.jato ?? 95, tGotas = eventos.gotas ?? 115, tLonge = Math.max(eventos.cai ?? 150, tRampa + 20);
  const tBuraco = Math.min(tB0, tRampa - 20);   // eventos colados no tempo não quebram a animação

  const rampa = interpolate(f, [tRampa - 8, tRampa + 10], [0, 1], suave);        // a rampa "nasce" no fim da calha
  const buraco = interpolate(f, [tBuraco - 10, tBuraco + 8, tRampa, tRampa + 20], [0.6, 1, 1, 0.2], cl);
  const perigo = interpolate(f, [tBuraco - 4, tBuraco + 4, tRampa - 2, tRampa + 8], [0.5, 1, 1, 0], cl);
  const espalha = interpolate(f, [tGotas - 8, tGotas + 18], [0, 1], cl);
  const poco = interpolate(f, [tLonge - 10, tLonge + 6], [0, 1], cl);
  const k = interpolate(f, [tRampa, tLonge], [0, 1], suave);                    // 1º: barragem e buraco; 2º: segue o jato até o poço
  const cam: [number, number, number] = [interpolate(k, [0, 1], [-1.2, 3.0]), 1.0, interpolate(k, [0, 1], [13.5, 13.0])];
  const alvo: [number, number, number] = [interpolate(k, [0, 1], [-1.3, 2.9]), 0.3, 0];

  // gotas: partículas que correm a calha e, com a rampa, saem num arco balístico
  const gotas = useMemo(() => Array.from({length: 420}, (_, i) => ({fase: random(`g${i}`), dz: (random(`z${i}`) - 0.5) * 0.9, sp: random(`s${i}`)})), []);
  const geoCalha = useMemo(() => {
    const pts = Array.from({length: 40}, (_, i) => new THREE.Vector3(...calha(i / 39), 0));
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 80, 0.12, 8, false);
  }, []);

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.05, far: 200}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.8} />
      <color attach="background" args={['#a9cbe6']} />
      <hemisphereLight args={['#ffffff', '#3a3226', 0.8]} />
      <directionalLight position={[3, 6, 6]} intensity={1.8} />

      {/* barragem (bloco de concreto) e o reservatório atrás */}
      <mesh position={[-4.1, 1.0, 0]}><boxGeometry args={[1.8, 3.6, 2.2]} /><meshStandardMaterial color="#b9b4aa" roughness={0.9} /></mesh>
      <mesh position={[-6.6, 2.4, 0]}><boxGeometry args={[3.2, 0.12, 2.2]} /><meshStandardMaterial color="#3d8fc4" roughness={0.2} /></mesh>
      {/* calha de concreto (o vertedouro) */}
      <mesh geometry={geoCalha}><meshStandardMaterial color="#c9c3b6" roughness={0.85} /></mesh>
      {/* a RAMPA (salto de esqui) no fim da calha */}
      <mesh position={[0.45, -1.05 + 0.2 * rampa, 0]} rotation={[0, 0, 0.55 * rampa]} scale={[1, rampa, 1]}>
        <boxGeometry args={[0.7, 0.35, 1.0]} /><meshStandardMaterial color="#d8d1c2" roughness={0.85} emissive="#ffd23f" emissiveIntensity={interpolate(f, [tRampa, tRampa + 6, tRampa + 24], [0, 0.6, 0], cl)} />
      </mesh>
      {/* chão do rio, com o BURACO no pé da barragem (fase 1) e o POÇO lá longe (fase 2) */}
      <mesh position={[3.5, -1.55, 0]}><boxGeometry args={[12, 0.6, 2.4]} /><meshStandardMaterial color="#6b5a45" roughness={1} /></mesh>
      <mesh position={[0.6, -1.25 - 0.45 * buraco, 0]} scale={[1 + buraco * 0.4, 0.5 + buraco, 1]}>
        <sphereGeometry args={[0.55, 24, 12]} /><meshStandardMaterial color="#3b2a1d" roughness={1} emissive="#ff2a1a" emissiveIntensity={perigo * 0.8} />
      </mesh>
      <mesh position={[5.2, -1.22, 0]} rotation={[-Math.PI / 2, 0, 0]} scale={[1, 0.8, 1]}>
        <circleGeometry args={[1.3, 32]} /><meshStandardMaterial color="#2f7fb5" emissive="#5fc8ff" emissiveIntensity={poco * 0.6} transparent opacity={0.6 + poco * 0.4} roughness={0.2} />
      </mesh>

      {/* ÁGUA */}
      {gotas.map((g, i) => {
        const ciclo = 50;
        const u = ((f + g.fase * ciclo) % ciclo) / ciclo;                         // 0→1: viagem de cada gota
        let pos: [number, number, number];
        let tam = 0.13;
        let alpha = 0.95;
        if (u < 0.5 || rampa < 0.5) {
          const t = Math.min(u / 0.5, 1);
          const [x, y] = calha(t);
          pos = [x, y + 0.16 + (g.sp - 0.5) * 0.12, g.dz * 0.6];
          if (rampa < 0.5 && u >= 0.5) { pos = [0.3 + (g.sp - 0.5) * 0.6, -1.0 + (u - 0.5) * 0.6, g.dz]; alpha = 1 - (u - 0.5) * 2; }
        } else {
          const t = (u - 0.5) / 0.5;                                             // voo: arco balístico até o poço
          const x = 0.6 + t * 4.6;
          const y = -0.9 + 4.2 * t - 4.55 * t * t;
          const abre = espalha * t;
          pos = [x + (g.sp - 0.5) * abre * 1.6, y + (g.fase - 0.5) * abre * 1.3, g.dz * (0.6 + abre * 2.2)];
          tam = 0.13 * (1 - 0.35 * abre);
          alpha = 0.95 - 0.5 * abre * t;
        }
        return (
          <mesh key={i} position={pos} scale={tam}>
            <sphereGeometry args={[1, 8, 6]} />
            <meshStandardMaterial color={AGUA} emissive={'#9fdcff'} emissiveIntensity={0.5} transparent opacity={alpha} roughness={0.2} />
          </mesh>
        );
      })}
    </ThreeCanvas>
  );
};
