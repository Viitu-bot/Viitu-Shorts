import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, random, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
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

// corta tudo abaixo da barriga (pernas do trem de pouso que o modelo traz abaixadas); precisa estar DENTRO do canvas
const Recolher: React.FC<{obj: THREE.Group | null}> = ({obj}) => {
  const {gl} = useThree();
  useMemo(() => {
    if (!obj) return;
    obj.updateMatrixWorld(true);
    const r = new THREE.Raycaster(new THREE.Vector3(0, -60, -10), new THREE.Vector3(0, 1, 0));
    const h = r.intersectObject(obj, true)[0];
    if (!h) return;
    gl.localClippingEnabled = true;
    const plano = new THREE.Plane(new THREE.Vector3(0, 1, 0), -(h.point.y - 0.6));
    obj.traverse((o) => { const m = o as THREE.Mesh; if (m.isMesh) (m.material as THREE.Material).clippingPlanes = [plano]; });
  }, [obj]);
  return null;
};

export const Reabastece3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({fase, dur, eventos}) => {
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
    if (nome.includes('wheel')) m.visible = false;      // em voo o trem de pouso está recolhido (dono: física coerente)
    const manter = ['glass', 'window', 'wheel', 'dials', 'black'].some((k) => nome.includes(k));
    if (!manter) {                                       // tira TODA a pintura (inclusive a cauda da ANA)
      mat.map = null;
      mat.color = new THREE.Color(nome.includes('wing') ? '#cfd6dd' : '#eef3f8');
      mat.metalness = 0.35; mat.roughness = 0.35;
      mat.needsUpdate = true;
    }
  });
  const tanque = preparar(kc);

  const sem = fase === 'sem';
  // 'completo' (padrão desde 18/11): UMA tomada contínua para a explicação inteira — close no bocal → o avião-tanque
  // chega → a lança desce e encaixa no fim. Nada de clipe real no meio (trava R2 do viitu.montagem).
  const completo = fase === 'completo';
  const tTq = eventos.tanque ?? Math.round(dur * 0.4);
  const tLa = eventos.lanca ?? Math.round(dur * 0.65);
  const chega = completo ? interpolate(f, [tTq - 6, tLa], [0, 1], suave) : 1;         // tanque descendo até a posição
  const soBocal = fase === 'bocal' || (completo && f < tTq - 6);                     // close no bocal do teto (sem o tanque ainda)                           // "o avião novo vem SEM esse truque": tanque vai embora, bocal some (X)
  const tSem = eventos.sem ?? Math.round(dur * 0.55);
  const tEnc = eventos.encosta ?? Math.round(dur * 0.45);
  const tEnc2 = eventos.enche ?? Math.round(dur * 0.7);
  const desce = soBocal ? 0 : sem ? interpolate(f, [0, 18], [0.6, 0], suave)
    : completo ? interpolate(f, [tLa, dur - 4], [0, 1], suave) : interpolate(f, [0, tEnc], [0, 1], suave);   // lança baixando até o bocal
  const encaixe = sem || soBocal ? 0 : completo ? interpolate(f, [dur - 6, dur - 2], [0, 1], cl) : interpolate(f, [tEnc - 2, tEnc + 4], [0, 1], cl);
  const fluxo = sem || completo ? 0 : interpolate(f, [tEnc2 - 4, tEnc2 + 6], [0, 1], cl);
  const foge = sem ? interpolate(f, [0, dur], [0, 1], suave) : 0;           // tanque sobe e vai embora
  const xVermelho = sem ? interpolate(f, [tSem - 3, tSem + 3], [0, 1], cl) : 0;
  const balanco = Math.sin(f * 0.07) * 0.25;

  // posições: 747 embaixo; KC-135 à frente e acima; o bocal fica no teto do 747 logo atrás da cabine
  const P747: [number, number, number] = [0, balanco * 0.4, 0];
  // bocal EM CIMA DO NARIZ (receptáculo dos 747 presidenciais): altura tirada da superfície real do modelo
  const ZB = completo ? -29 : -23;
  const topo = useMemo(() => {
    if (!af1) return 0.9;
    af1.updateMatrixWorld(true);
    const r = new THREE.Raycaster(new THREE.Vector3(0, 60, ZB), new THREE.Vector3(0, -1, 0));
    const h = r.intersectObject(af1, true)[0];
    return h ? h.point.y + 0.05 : 0.9;
  }, [af1]);
  const BOCAL: [number, number, number] = [0, topo + balanco * 0.4, ZB];
  const PKC: [number, number, number] = soBocal ? [0, 400, -900]
    : [0, 16.6 + balanco + foge * 40 + (1 - chega) * 45, ZB - 25 - foge * 120];
  const raiz: [number, number, number] = [0, PKC[1] - 4.2, PKC[2] + 18];   // embaixo da cauda do tanque
  const ponta: [number, number, number] = [0, interpolate(desce, [0, 1], [raiz[1] - 4, BOCAL[1] + 0.4]) + balanco * (1 - desce * 0.6), interpolate(desce, [0, 1], [raiz[2] + 3, BOCAL[2]])];
  const lanca = new THREE.Vector3(...ponta).sub(new THREE.Vector3(...raiz));
  const compr = lanca.length();
  const meio = new THREE.Vector3(...raiz).add(lanca.clone().multiplyScalar(0.5));
  const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), lanca.clone().normalize());

  const k = sem ? 1 : completo ? interpolate(f, [tTq - 6, dur], [0, 1], suave) : interpolate(f, [0, dur], [0, 1], suave);
  const kb = completo ? interpolate(f, [0, tTq - 6], [0, 1], suave) : interpolate(f, [0, dur], [0, 1], suave);   // câmera desliza do nariz até o bocal
  const dz = ZB + 23;                                         // desloca câmeras quando o bocal vai para o nariz
  const camBocal: [number, number, number] = [interpolate(kb, [0, 1], [14, 6]), interpolate(kb, [0, 1], [6, 4.5]) + topo - 0.9, interpolate(kb, [0, 1], [-48, -17]) + dz];
  // completo: do close no bocal abre para um plano 3/4 que mostra o tanque em cima e a lança chegando ao nariz
  const cam: [number, number, number] = soBocal ? camBocal
    : completo ? [interpolate(k, [0, 1], [6, 34]), interpolate(k, [0, 1], [4.5 + topo - 0.9, 12]), interpolate(k, [0, 1], [-17 + dz, -8])]
    : [interpolate(k, [0, 1], [58, 20]), interpolate(k, [0, 1], [14, 9]), interpolate(k, [0, 1], [18, -12])];
  const alvo: [number, number, number] = soBocal
    ? [0, topo - 0.1, interpolate(kb, [0, 1], [-30, -23]) + dz]
    : completo ? [0, interpolate(k, [0, 1], [topo, 6]), interpolate(k, [0, 1], [ZB, ZB - 6])]
    : [0, interpolate(k, [0, 1], [7, 5]), interpolate(k, [0, 1], [-28, -25])];

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 40, position: cam, near: 0.5, far: 3000}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <Recolher obj={af1} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo />
      <hemisphereLight args={['#eaf2fb', '#9aa5b0', 0.7]} />
      <directionalLight position={[60, 120, 40]} intensity={2.4} color="#fff6e8" />
      <fog attach="fog" args={['#d8e6f2', 200, 1400]} />
      {!completo && <Nuvens f={f} />}{/* no close do 'completo' as nuvens soltas cruzavam o nariz; o céu HDRI já tem nuvens */}
      {af1 && <group position={P747} rotation={[0, 0, 0]}><primitive object={af1} /></group>}
      {tanque && <group position={PKC} rotation={[0, Math.PI, 0]}><primitive object={tanque} /></group>}
      {/* lança do tanque (tubo com aletas) */}
      <mesh visible={!soBocal} position={meio.toArray() as [number, number, number]} quaternion={quat}>
        <cylinderGeometry args={[0.35, 0.45, compr, 16]} />
        <meshStandardMaterial color="#9aa2aa" metalness={0.7} roughness={0.35} />
      </mesh>
      <group position={ponta} visible={!soBocal}>
        <mesh><cylinderGeometry args={[0.18, 0.25, 1.4, 12]} /><meshStandardMaterial color="#5d646b" metalness={0.8} /></mesh>
        <mesh position={[0, 0.9, 0]}><boxGeometry args={[3.2, 0.08, 0.8]} /><meshStandardMaterial color="#9aa2aa" metalness={0.6} /></mesh>
      </group>
      {/* bocal no teto do 747: luz verde quando encaixa */}
      {xVermelho > 0.01 && [1, -1].map((s) => (
        <mesh key={s} position={[BOCAL[0], BOCAL[1] + 0.5, BOCAL[2]]} rotation={[0, 0, s * Math.PI / 4]} scale={xVermelho}>
          <boxGeometry args={[4.2, 0.55, 0.3]} /><meshBasicMaterial color="#ff2a2a" />
        </mesh>
      ))}
      {/* moldura escura do receptáculo (porta aberta) */}
      <mesh position={[BOCAL[0], BOCAL[1] - 0.02, BOCAL[2]]} rotation={[Math.PI / 2, 0, 0]} visible={!sem || xVermelho < 0.5}>
        <torusGeometry args={[0.52, 0.09, 10, 28]} /><meshStandardMaterial color="#2a2f35" metalness={0.6} roughness={0.4} />
      </mesh>
      <mesh position={BOCAL} visible={!sem || xVermelho < 0.5}>
        <cylinderGeometry args={[0.42, 0.42, 0.05, 24]} />
        <meshStandardMaterial color={encaixe > 0.5 ? '#3dff6a' : '#ffd23d'} emissive={encaixe > 0.5 ? '#3dff6a' : '#ffaa00'} emissiveIntensity={soBocal ? 1 + Math.sin(f * 0.4) * 0.8 : 1.4} />
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
