import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, useCurrentFrame, useVideoConfig, Easing, random} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, useModelo, useTexturas} from './comum3d';

// vd010: por que o Abrams é "feito para explodir". Modelo pronto (Sketchfab, CC BY 4.0, MirzaArrafiERV_45).
// UMA tomada contínua (REGRAS.md): o casco fica translúcido (raio-X) → a munição aparece no compartimento atrás
// da torre → a porta blindada fecha (tripulação protegida, verde) → os painéis do teto pulsam ("fracos de
// propósito") → a munição explode → os painéis voam e o fogo sai reto para CIMA; a tripulação continua verde.
// Eventos (quadros desde o início da cena): porta, teto, explode. Frente do modelo = +z, traseira = −z.
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};

// perfil do teto: altura do topo em cada z (raycast de cima para baixo)
const usePerfil = (obj: THREE.Group | null) => useMemo(() => {
  if (!obj) return null;
  obj.updateMatrixWorld(true);
  const r = new THREE.Raycaster();
  const topo = (x: number, z: number) => {
    r.set(new THREE.Vector3(x, 30, z), new THREE.Vector3(0, -1, 0));
    const h = r.intersectObject(obj, true)[0];
    return h ? h.point.y : -99;
  };
  const zs = Array.from({length: 81}, (_, i) => -5 + i * 0.1);
  const ys = zs.map((z) => Math.max(topo(-0.3, z), topo(0.3, z)));
  const deck = [...ys].sort((a, b) => a - b)[Math.floor(ys.length * 0.35)];       // convés do casco
  const torre = zs.filter((_, i) => ys[i] > deck + 0.35);
  const z0 = Math.min(...torre);                                                 // fim traseiro da torre
  const teto = topo(0, z0 + 0.6);
  return {z0, teto, deck};
}, [obj]);

export const Abrams3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>; debug?: boolean}> = ({dur, eventos, debug}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri']);
  const base = useModelo('abrams.glb');
  const per = usePerfil(base);
  const tPorta = eventos.porta ?? 50, tTeto = eventos.teto ?? 86, tExp = eventos.explode ?? 168;

  const raiox = interpolate(f, [4, 18], [1, 0.2], suave);                    // casco fica translúcido
  const tanque = useMemo(() => {
    if (!base) return null;
    const c = base.clone(true);
    c.traverse((o) => { const m = o as THREE.Mesh; if (m.isMesh) m.material = (m.material as THREE.Material).clone(); });
    return c;
  }, [base]);
  if (tanque) tanque.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const mat = m.material as THREE.MeshStandardMaterial;
    const tr = raiox < 0.98 && !debug;
    mat.transparent = tr; mat.depthWrite = !tr; mat.opacity = tr ? raiox : 1;
  });

  // medidas do modelo (perfil dos vértices, 18/11): teto da torre ≈ 1,12 m; traseira da torre (bustle) z −3,0…−2,1
  void per;
  const teto = 1.13, zc = -2.55, yc = 0.86, zPorta = -1.98;
  const fecha = interpolate(f, [tPorta - 6, tPorta + 6], [0, 1], suave);          // porta desce e fecha
  const pulso = f >= tTeto - 2 && f < tExp ? 0.5 + 0.5 * Math.sin((f - tTeto) * 0.5) : 0;
  const boom = interpolate(f, [tExp, tExp + 5], [0, 1], cl);
  const tv = Math.max(0, f - tExp) / 30;                                         // segundos desde a explosão
  const flash = f >= tExp ? interpolate(f, [tExp, tExp + 3, tExp + 14], [0, 1, 0], cl) : 0;

  const k = interpolate(f, [0, dur], [0, 1], suave);
  const sobe = interpolate(f, [tExp - 4, dur], [0, 1], suave);
  const cam: [number, number, number] = debug ? [eventos.cx ?? 12, eventos.cy ?? 6, eventos.cz ?? 0]
    : [interpolate(k, [0, 1], [7.5, 5.2]) + sobe * 1.5, interpolate(k, [0, 1], [4.2, 3.4]) + sobe * 2.2, interpolate(k, [0, 1], [-6.5, -1.5])];
  const alvo: [number, number, number] = [0, yc + sobe * 1.8, zc + 0.6];

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 42, position: cam, near: 0.1, far: 500}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo />
      <hemisphereLight args={['#eaf2fb', '#6b5a45', 0.8]} />
      <directionalLight position={[8, 12, 6]} intensity={2.2} />
      <pointLight position={[0, yc, zc]} intensity={flash * 60 + (f >= tExp ? 8 : 0)} color="#ff8a2a" distance={14} />
      {debug && <axesHelper args={[5]} />}
      {/* chão de terra para dar lugar e escala */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.69, 0]}><planeGeometry args={[200, 200]} /><meshStandardMaterial color="#8a7458" roughness={1} /></mesh>
      {tanque && <primitive object={tanque} />}

      {/* munição: 2 fileiras de projéteis com a base virada para trás */}
      {Array.from({length: 12}, (_, i) => {
        const x = -0.5 + (i % 6) * 0.2, y = yc + (i < 6 ? 0.09 : -0.09);
        const vis = f < tExp + 2;
        return (
          <group key={i} position={[x, y, zc]} visible={vis}>
            <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.06, 0.06, 0.8, 14]} /><meshStandardMaterial color="#b8962e" metalness={0.8} roughness={0.3} emissive="#ff5a00" emissiveIntensity={pulso * 0.15} /></mesh>
            <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0.5]}><coneGeometry args={[0.065, 0.18, 14]} /><meshStandardMaterial color="#5a5f63" metalness={0.7} /></mesh>
          </group>
        );
      })}
      {/* porta blindada entre a munição e a tripulação: desce e fecha */}
      <mesh position={[1.5 * (1 - fecha), yc - 0.05, zPorta]} visible={fecha > 0.02}>
        <boxGeometry args={[1.45, 0.5, 0.06]} />
        <meshStandardMaterial color="#6f767c" metalness={0.85} roughness={0.25} emissive="#3dff6a" emissiveIntensity={fecha * 0.25} />
      </mesh>
      {/* tripulação (3 lugares) — verde = protegida */}
      {[-0.45, 0, 0.45].map((x, i) => (
        <mesh key={i} position={[x, yc - 0.15, zPorta + 0.6 + (i === 1 ? 0.3 : 0)]}>
          <capsuleGeometry args={[0.13, 0.32, 6, 12]} />
          <meshStandardMaterial color="#3dff6a" emissive="#3dff6a" emissiveIntensity={0.6 + fecha * 0.6} transparent opacity={0.85} />
        </mesh>
      ))}
      {/* painéis do teto: pulsam ("fracos de propósito") e voam na explosão */}
      {[-0.38, 0.38].map((x, i) => {
        const vy = 9 + i * 1.5, g = 9.8;
        const y = teto + 0.02 + (f >= tExp ? vy * tv - 0.5 * g * tv * tv : 0);
        return (
          <mesh key={i} position={[x * (1 + tv * 0.8), Math.max(y, teto - 4), zc + tv * (i ? -0.6 : 0.4)]}
            rotation={[tv * (i ? 7 : -6), tv * 2, tv * (i ? 3 : -4)]}>
            <boxGeometry args={[0.62, 0.05, 0.85]} />
            <meshStandardMaterial color={pulso > 0 ? '#ffd23d' : '#8b8f74'} emissive="#ffaa00" emissiveIntensity={pulso * 1.6} metalness={0.6} />
          </mesh>
        );
      })}
      {/* bola de fogo dentro do compartimento */}
      {flash > 0.01 && <mesh position={[0, yc, zc]} scale={0.15 + boom * 0.2}><sphereGeometry args={[1, 20, 16]} /><meshBasicMaterial color="#ff9a3a" transparent opacity={flash * 0.8} blending={THREE.AdditiveBlending} depthWrite={false} /></mesh>}
      {/* coluna de fogo saindo REto para cima pelo teto */}
      {f >= tExp && Array.from({length: 46}, (_, i) => {
        const fase = ((tv * 1.6 + random(`p${i}`)) % 1);
        const yy = teto + fase * 5 * Math.min(1, tv * 3);
        const s = 0.1 + fase * 0.45;
        const x = (random(`x${i}`) - 0.5) * (0.4 + fase * 0.7), z = zc + (random(`z${i}`) - 0.5) * (0.5 + fase * 0.6);
        const cor = fase < 0.2 ? '#ffc04d' : fase < 0.6 ? '#ff5a10' : '#2e2e2e';
        return (
          <mesh key={i} position={[x, yy, z]} scale={[s, s * 1.8, s]}>
            <sphereGeometry args={[1, 10, 8]} />
            <meshBasicMaterial color={cor} transparent opacity={(1 - fase) * 0.6} blending={fase < 0.7 ? THREE.AdditiveBlending : THREE.NormalBlending} depthWrite={false} />
          </mesh>
        );
      })}
    </ThreeCanvas>
  );
};
