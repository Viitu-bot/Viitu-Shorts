import React, {useEffect, useMemo, useState} from 'react';
import {interpolate, useCurrentFrame, useVideoConfig, Easing, continueRender, delayRender, staticFile} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as THREE from 'three';
import {clone as clonarEsqueleto} from 'three/examples/jsm/utils/SkeletonUtils.js';
import {Camera, Liberar} from './comum3d';

// vd018 — por que o olho do rato "pula": o músculo que fecha a mandíbula (masseter) passa por trás do olho
// (PetMD "What Is Rat Boggling?"). Modelo: 'Black Rat' (Nestaeric, Sketchfab, CC BY 4.0), com ossos do olho e
// da mandíbula. Visão de raio-X: pele semitransparente, músculo vermelho, olho preto brilhante.
// Fases (cenas seguidas, câmera contínua):
//  'musculo' — rato inteiro de lado, a pele fica transparente e o músculo acende (evento "mandibula"),
//              a câmera fecha na cabeça (evento "atras": músculo encostado atrás do olho).
//  'olho'    — perfil fechado: a mandíbula range, o músculo incha e o olho sai e volta (evento "fora").
//  'motor'   — 3/4 de frente: o ritmo acelera (evento "motor") e os dois olhos vibram juntos.
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const VERMELHO = '#e8323c';

type Rig = {cena: THREE.Group; clipes: THREE.AnimationClip[]};
const cache: {rig?: Promise<Rig>} = {};
const carregar = () => {
  if (!cache.rig) cache.rig = new Promise((ok, erro) => new GLTFLoader().load(staticFile('modelos/rato_preto.glb'),
    (g) => ok({cena: g.scene as unknown as THREE.Group, clipes: g.animations}), undefined, erro));
  return cache.rig;
};

const useRato = () => {
  const [rig, setRig] = useState<Rig | null>(null);
  const [h] = useState(() => delayRender('rato3d', {timeoutInMilliseconds: 150000}));
  const [falhou, setFalhou] = useState(false);
  useEffect(() => { carregar().then((r) => setRig(r)).catch((e) => { console.error(e); setFalhou(true); continueRender(h); }); }, []);
  return {rig, h, falhou};
};

const achar = (raiz: THREE.Object3D, ...partes: string[]) => {
  let r: THREE.Object3D | undefined;
  raiz.traverse((o) => { if (!r && partes.every((p) => o.name.includes(p))) r = o; });
  return r;
};

// músculo = feixe de 5 fibras (cápsulas) entre dois pontos, inchando com "aperto" (0..1)
const Musculo: React.FC<{a: THREE.Vector3; b: THREE.Vector3; aperto: number; brilho: number; vis: number}> = ({a, b, aperto, brilho, vis}) => {
  const meio = a.clone().add(b).multiplyScalar(0.5);
  const dir = b.clone().sub(a);
  const L = dir.length();
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
  const r = L * (0.17 + 0.09 * aperto);
  return (
    <group position={meio} quaternion={q} scale={[1, 1 - 0.12 * aperto, 1]}>
      {[[0, 0], [0.55, 0.2], [-0.55, 0.2], [0.3, -0.5], [-0.3, -0.5]].map(([x, z], i) => (
        <mesh key={i} position={[x * r * 0.7, 0, z * r * 0.7]} scale={[r * (i === 0 ? 0.9 : 0.7), L * 0.58, r * (i === 0 ? 0.65 : 0.5)]}>
          <sphereGeometry args={[1, 18, 14]} />
          <meshStandardMaterial color={VERMELHO} emissive="#ff2a2a" emissiveIntensity={0.25 + brilho * 1.2}
            roughness={0.45} transparent opacity={vis} depthWrite={vis > 0.95} />
        </mesh>
      ))}
    </group>
  );
};

export const Rato3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>; debug?: boolean; dcam?: [number, number, number]; dalvo?: [number, number, number]}> = ({fase, dur, eventos, debug, dcam, dalvo}) => {
  const f = useCurrentFrame();
  const {width, height, fps} = useVideoConfig();
  const {rig, h} = useRato();

  // uma cópia própria do rato (com esqueleto) por fase
  const m = useMemo(() => {
    if (!rig) return null;
    const bruto = clonarEsqueleto(rig.cena) as THREE.Group;
    const cena = new THREE.Group();
    cena.add(bruto);
    bruto.updateMatrixWorld(true);
    const caixa = new THREE.Box3().setFromObject(bruto, true);
    const tam = caixa.getSize(new THREE.Vector3());
    const esc = 0.3 / Math.max(tam.x, tam.y, tam.z);
    const c0 = caixa.getCenter(new THREE.Vector3());
    bruto.scale.multiplyScalar(esc);
    bruto.position.set(-c0.x * esc, -caixa.min.y * esc, -c0.z * esc);
    console.log('RATO caixa', JSON.stringify({min: caixa.min, max: caixa.max, esc}));
    const mixer = new THREE.AnimationMixer(cena);
    const idle = rig.clipes.find((c) => c.name.includes('idle_A1')) ?? rig.clipes[0];
    if (idle) mixer.clipAction(idle).play();
    const mats: THREE.MeshStandardMaterial[] = [];
    cena.traverse((o: any) => {
      if (o.isMesh) {
        o.frustumCulled = false;
        const mat = (o.material as THREE.MeshStandardMaterial).clone();
        mat.userData.olho = mat.name.includes('eyes');
        mat.transparent = !mat.userData.olho;
        o.material = mat;
        o.renderOrder = mat.userData.olho ? 2 : 1;
        mats.push(mat);
      }
    });
    return {
      cena, mixer, mats,
      olhoL: achar(cena, 'Eyeball', 'L_0182') ?? achar(cena, 'EyeballL'),
      olhoR: achar(cena, 'Eyeball', 'R_0185') ?? achar(cena, 'EyeballR'),
      queixo: achar(cena, 'Mouth_Lower') ?? achar(cena, 'Jaw'),
      cabeca: achar(cena, 'Head_Head'),
    };
  }, [rig]);

  // ritmo do ranger: lento na fase olho (dá para ver o olho sair e voltar), rápido no motor
  const tFora = eventos.fora ?? Math.round(dur * 0.35);
  const tMotor = eventos.motor ?? Math.round(dur * 0.3);
  const tMand = eventos.mandibula ?? 15;
  const tAtras = eventos.atras ?? Math.round(dur * 0.6);
  let ciclo = 0;                                   // 0..1 (1 = dente apertado, músculo cheio, olho para fora)
  if (fase === 'olho' && f >= tFora) ciclo = (1 - Math.cos(((f - tFora) / 12) * Math.PI * 2)) / 2;
  if (fase === 'motor') {
    const hz = interpolate(f, [tMotor - 10, tMotor + 15], [1.6, 5], cl);
    let fase0 = 0; for (let i = 0; i < f; i++) fase0 += interpolate(i, [tMotor - 10, tMotor + 15], [1.6, 5], cl) / fps;
    ciclo = (1 - Math.cos(fase0 * Math.PI * 2)) / 2; void hz;
  }

  // transparência da pele e brilho do músculo
  const xray = fase === 'musculo' ? interpolate(f, [tMand - 12, tMand + 6], [0, 1], cl) : 1;
  const brilho = fase === 'musculo' ? interpolate(f, [tMand, tMand + 5, tMand + 25], [0, 1, 0.35], cl) + interpolate(f, [tAtras, tAtras + 5, tAtras + 25], [0, 0.8, 0.3], cl) : 0.3 + 0.5 * ciclo;

  // pose: animação de respiração do modelo + ossos do olho e da mandíbula
  let pos: {L?: THREE.Vector3; R?: THREE.Vector3; a?: THREE.Vector3; b?: THREE.Vector3; aR?: THREE.Vector3; bR?: THREE.Vector3; cab?: THREE.Vector3} = {};
  if (m) {
    m.mixer.setTime(f / fps);
    for (const mat of m.mats) {
      if (mat.userData.olho) continue;
      mat.opacity = interpolate(xray, [0, 1], [1, 0.22]);
      mat.depthWrite = xray < 0.5;
    }
    if (m.queixo) m.queixo.rotation.x += 0.22 * ciclo;            // mandíbula fecha/abre (range)
    m.cena.updateMatrixWorld(true);
    const centro = m.cabeca ? m.cabeca.getWorldPosition(new THREE.Vector3()) : new THREE.Vector3(0, 0.07, 0.07);
    const empurra = (o?: THREE.Object3D) => {
      if (!o || !o.parent) return undefined;
      const w = o.getWorldPosition(new THREE.Vector3());
      const sai = new THREE.Vector3(Math.sign(w.x - centro.x) || 1, 0.15, 0.1).normalize().multiplyScalar(0.003 * ciclo);   // olho sai para o lado
      const alvo = o.parent.worldToLocal(w.clone().add(sai));
      o.position.copy(alvo);
      o.scale.setScalar(1 + 0.14 * ciclo);
      o.updateMatrixWorld(true);
      return w;
    };
    const L = empurra(m.olhoL), R = empurra(m.olhoR);
    m.cena.updateMatrixWorld(true);
    const lado = (w?: THREE.Vector3) => {
      if (!w) return [undefined, undefined];
      const s = Math.sign(w.x) || 1;
      // músculo: de trás/baixo do olho (arco do zigomático) até o canto da mandíbula
      return [new THREE.Vector3(w.x * 0.9, w.y + 0.001, w.z - 0.005), new THREE.Vector3(w.x * 1.02 + s * 0.001, w.y - 0.017, w.z + 0.004)];
    };
    const [a, b] = lado(L); const [aR, bR] = lado(R);
    pos = {L, R, a, b, aR, bR, cab: centro};
    if (debug) console.log('RATO pos', JSON.stringify({L, R, centro, q: m.queixo?.name, cab: m.cabeca?.name, oL: m.olhoL?.name}));
  }

  // câmeras (o modelo tem ~30 cm; cabeça perto de y 0.07, z 0.09 — o focinho aponta para +z)
  const k = interpolate(f, [0, dur], [0, 1], cl);
  const olhoW = pos.L ?? new THREE.Vector3(0.012, 0.077, 0.099);
  let cam: [number, number, number]; let alvo: [number, number, number];
  const meioOlhos = pos.L && pos.R ? pos.L.clone().add(pos.R).multiplyScalar(0.5) : new THREE.Vector3(0, 0.08, 0.07);
  if (fase === 'musculo') {
    const e = Easing.inOut(Easing.cubic)(k);
    const c0 = [0.5, 0.1, 0.03], c1 = [olhoW.x + 0.12, olhoW.y + 0.012, olhoW.z + 0.015];
    const a0 = [0, 0.07, 0.05], a1 = [olhoW.x, olhoW.y - 0.008, olhoW.z - 0.004];
    cam = [0, 1, 2].map((i) => interpolate(e, [0, 1], [c0[i], c1[i]])) as [number, number, number];
    alvo = [0, 1, 2].map((i) => interpolate(e, [0, 1], [a0[i], a1[i]])) as [number, number, number];
  } else if (fase === 'olho') {
    cam = [olhoW.x + 0.075 - 0.01 * k, olhoW.y + 0.008, olhoW.z + 0.012];
    alvo = [olhoW.x, olhoW.y - 0.008, olhoW.z - 0.004];
  } else {
    const ang = interpolate(k, [0, 1], [0.25, 0.05]);
    const c = meioOlhos;
    cam = [c.x + Math.sin(ang) * 0.12, c.y + 0.035, c.z + Math.cos(ang) * 0.12];
    alvo = [c.x, c.y - 0.012, c.z];
  }
  if (dcam) { cam = dcam; alvo = dalvo ?? [0, 0.05, 0]; }
  const tremor = fase === 'motor' ? ciclo * 0.0006 : 0;

  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 34, position: cam, near: 0.005, far: 5}}>
      <Camera pos={[cam[0] + tremor, cam[1], cam[2]]} alvo={alvo} />
      <Liberar pronto={!!m} h={h} />
      <color attach="background" args={['#0e1420']} />
      <fog attach="fog" args={['#0e1420', 0.35, 1.2]} />
      <hemisphereLight args={['#cfe3ff', '#2a2020', 1.1]} />
      <directionalLight position={[0.6, 0.8, 0.9]} intensity={2.2} />
      <directionalLight position={[-0.8, 0.3, -0.6]} intensity={1.4} color="#7fb2ff" />
      <pointLight position={[olhoW.x + 0.05, olhoW.y + 0.03, olhoW.z + 0.05]} intensity={0.08} distance={0.4} />
      {m && <primitive object={m.cena} />}
      {pos.a && pos.b && <Musculo a={pos.a} b={pos.b} aperto={ciclo} brilho={brilho} vis={xray} />}
      {pos.aR && pos.bR && fase === 'motor' && <Musculo a={pos.aR} b={pos.bR} aperto={ciclo} brilho={brilho} vis={1} />}
      {debug && pos.L && <mesh position={pos.L} renderOrder={9}><sphereGeometry args={[0.006, 8, 8]} /><meshBasicMaterial color="lime" depthTest={false} /></mesh>}
      {debug && pos.cab && <mesh position={pos.cab} renderOrder={9}><sphereGeometry args={[0.006, 8, 8]} /><meshBasicMaterial color="yellow" depthTest={false} /></mesh>}
      {debug && <axesHelper args={[0.2]} />}
    </ThreeCanvas>
  );
};
