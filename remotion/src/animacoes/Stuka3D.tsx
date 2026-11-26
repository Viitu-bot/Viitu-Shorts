import React, {useEffect, useMemo, useState} from 'react';
import * as THREE from 'three';
import {continueRender, delayRender, interpolate, random, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {useThree} from '@react-three/fiber';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, rep, useModelo, useTexturas} from './comum3d';

// vd018 — Ju 87 Stuka em mergulho (modelo "Junkers Ju 87", helijah, Sketchfab CC BY 4.0).
// O modelo vem com hélice e bomba fundidas na fuselagem: aqui elas são RECORTADAS (triângulos na frente do nariz e
// embaixo da barriga) e refeitas em código para animar: hélice de 3 pás girando, bomba de 250 kg no GARFO em U
// (berço que balança a bomba para fora do disco da hélice), sirene nas pernas do trem de pouso.
// Eixos depois do useModelo: nariz para -x, para cima +y, envergadura em z. 1 unidade = 1 m.
// Fases (uma por cena do storyboard): helice · despenca · sirene · erro · garfo · arremessa · puxao · sozinho.
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};

const NARIZ_X = -5.0;               // tudo à frente disto é a hélice original (sai)
const HELICE_X = -5.25, HELICE_R = 1.7;
const PIVO: [number, number] = [0.4, -0.85];       // pino do garfo na barriga (x, y)
const BRACO: [number, number] = [-1.0, -0.3];      // do pino até o centro da bomba, garfo recolhido

type Info = {limpo: THREE.Group; rodas: THREE.Vector3[]; eixoY: number};

let DEBUG_COR = false;
const limpar = (cena: THREE.Group | null): Info | null => {
  if (!cena) return null;
  const c = cena.clone(true);
  c.updateMatrixWorld(true);
  const v = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3(), d = new THREE.Vector3();
  const baixos: THREE.Vector3[] = [];
  let somaY = 0, nY = 0, cont = 0;
  c.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.material = (m.material as THREE.Material).clone();
    if (((m.material as THREE.Material).name || '').includes('metal')) { m.visible = false; return; }   // suporte original da bomba (sai: o garfo é refeito)
    const g = m.geometry.clone();
    m.geometry = g;
    const pos = g.getAttribute('position') as THREE.BufferAttribute;
    const idx = g.index ? Array.from(g.index.array as ArrayLike<number>) : Array.from({length: pos.count}, (_, i) => i);
    const mw = m.matrixWorld;
    const fica: number[] = [];
    // amostra da pintura (para achar os tanques extras bege embaixo das asas e tirar)
    const uv = g.getAttribute('uv') as THREE.BufferAttribute | undefined;
    const img = ((m.material as THREE.MeshStandardMaterial).map?.image) as (HTMLImageElement | ImageBitmap | undefined);
    let px: Uint8ClampedArray | null = null, W = 0, H = 0;
    if (uv && img && (img as any).width) {
      W = (img as any).width; H = (img as any).height;
      const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
      const cx = cv.getContext('2d');
      if (cx) { cx.drawImage(img as any, 0, 0); px = cx.getImageData(0, 0, W, H).data; }
    }
    const bege = (i0: number, i1: number, i2: number) => {
      if (!px || !uv) return false;
      const u = (uv.getX(i0) + uv.getX(i1) + uv.getX(i2)) / 3, w = (uv.getY(i0) + uv.getY(i1) + uv.getY(i2)) / 3;
      const X = Math.min(W - 1, Math.max(0, Math.floor((((u % 1) + 1) % 1) * W)));
      const Y = Math.min(H - 1, Math.max(0, Math.floor((((w % 1) + 1) % 1) * H)));
      const o = (Y * W + X) * 4;
      const r = px[o], gg = px[o + 1], bb = px[o + 2];
      return r > gg + 12 && r > bb + 35 && r > 110;
    };
    for (let i = 0; i < idx.length; i += 3) {
      a.fromBufferAttribute(pos, idx[i]).applyMatrix4(mw);
      b.fromBufferAttribute(pos, idx[i + 1]).applyMatrix4(mw);
      d.fromBufferAttribute(pos, idx[i + 2]).applyMatrix4(mw);
      v.copy(a).add(b).add(d).multiplyScalar(1 / 3);
      // hélice original: qualquer vértice à frente do nariz e longe do eixo (as pás são triângulos longos)
      const raio = (q: THREE.Vector3) => Math.hypot(q.y - 0.1, q.z);
      const helice = v.x < NARIZ_X || [a, b, d].some((q) => q.x < NARIZ_X && raio(q) > 0.62);
      const bomba = v.x > -2.4 && v.x < 1.7 && Math.abs(v.z) < 0.5 && v.y < -0.8;
      const tanque = v.y < -0.45 && Math.abs(v.z) > 1.0 && Math.abs(v.z) < 3.2 && bege(idx[i], idx[i + 1], idx[i + 2]);
      // suportes dos tanques (varas finas e compridas embaixo das asas, |envergadura| ~1,6–2,1)
      const ext = (k: 'x' | 'y' | 'z') => Math.max(a[k], b[k], d[k]) - Math.min(a[k], b[k], d[k]);
      const vara = Math.abs(v.z) > 1.45 && Math.abs(v.z) < 2.2 && ((ext('x') > 1.0 && ext('y') < 0.25 && ext('z') < 0.25 && v.y < -0.05) || (ext('x') > 0.3 && ext('y') < 0.2 && ext('z') < 0.2 && v.y < -0.55));
      if (helice || bomba || tanque || vara) continue;
      fica.push(idx[i], idx[i + 1], idx[i + 2]);
      if (v.y < -1.55) baixos.push(v.clone());
      if (v.x < NARIZ_X + 0.4 && v.x > NARIZ_X - 0.1) { somaY += v.y; nY += 1; }
    }
    g.setIndex(fica);
    if (DEBUG_COR) { const mm = m.material as THREE.MeshStandardMaterial; mm.map = null; mm.color = new THREE.Color().setHSL((cont++ * 0.137) % 1, 0.9, 0.5); console.log('MALHA', cont - 1, mm.name, fica.length / 3); }
  });
  // rodas: média dos pontos mais baixos de cada lado
  const lado = (s: number) => {
    const p = baixos.filter((q) => Math.sign(q.z) === s);
    const m = new THREE.Vector3();
    p.forEach((q) => m.add(q));
    return p.length ? m.multiplyScalar(1 / p.length) : new THREE.Vector3(-1.8, -1.8, s * 1.6);
  };
  return {limpo: c, rodas: [lado(1), lado(-1)], eixoY: nY ? somaY / nY : 0.1};
};

// segura o quadro até o avião (já recortado) estar desenhado — sem isso a 1ª imagem de cada cena saía só com céu
const LiberarAviao: React.FC<{ok: boolean; h: number}> = ({ok, h}) => {
  const {advance, invalidate} = useThree();
  useEffect(() => {
    if (!ok) return;
    invalidate();
    advance(performance.now());
    const t = setTimeout(() => { advance(performance.now()); continueRender(h); }, 400);
    return () => clearTimeout(t);
  }, [ok]);
  return null;
};

const Helice: React.FC<{y: number; ang: number; borrao: number}> = ({y, ang, borrao}) => (
  <group position={[HELICE_X, y, 0]}>
    <mesh position={[-0.25, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
      <coneGeometry args={[0.32, 0.7, 24]} /><meshStandardMaterial color="#2d3a2a" metalness={0.4} roughness={0.5} />
    </mesh>
    <group rotation={[ang, 0, 0]}>
      {[0, 1, 2].map((i) => (
        <mesh key={i} rotation={[(i * 2 * Math.PI) / 3, 0, 0]}>
          <boxGeometry args={[0.08, HELICE_R * 2 * 0.98, 0.26]} />
          <meshStandardMaterial color="#1d211c" roughness={0.6} transparent opacity={1 - borrao * 0.75} />
        </mesh>
      ))}
    </group>
    {/* disco borrado da hélice girando (como numa câmera de verdade) */}
    <mesh rotation={[0, Math.PI / 2, 0]}>
      <circleGeometry args={[HELICE_R, 48]} />
      <meshStandardMaterial color="#d8dccf" transparent opacity={0.16 * borrao} side={THREE.DoubleSide} depthWrite={false} />
    </mesh>
  </group>
);

const Bomba: React.FC = () => (
  <group>
    <mesh rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.185, 0.185, 1.15, 24]} /><meshStandardMaterial color="#4a5040" metalness={0.5} roughness={0.45} /></mesh>
    <mesh position={[-0.75, 0, 0]} rotation={[0, 0, Math.PI / 2]}><coneGeometry args={[0.185, 0.36, 24]} /><meshStandardMaterial color="#4a5040" metalness={0.5} roughness={0.45} /></mesh>
    <mesh position={[0.62, 0, 0]} rotation={[0, 0, -Math.PI / 2]}><coneGeometry args={[0.185, 0.2, 24]} /><meshStandardMaterial color="#4a5040" metalness={0.5} roughness={0.45} /></mesh>
    {[0, 1, 2, 3].map((i) => (
      <mesh key={i} position={[0.85, 0, 0]} rotation={[(i * Math.PI) / 2, 0, 0]}>
        <boxGeometry args={[0.36, 0.3, 0.02]} /><meshStandardMaterial color="#3c4234" />
      </mesh>
    ))}
    <mesh position={[-0.35, 0, 0]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.19, 0.19, 0.06, 24]} /><meshStandardMaterial color="#c9a227" /></mesh>
  </group>
);

// garfo em U: dois braços do pino até os lados da bomba
const Garfo: React.FC<{theta: number; brilho: number}> = ({theta, brilho}) => {
  const L = Math.hypot(...BRACO);
  const base = Math.atan2(BRACO[1], BRACO[0]);
  return (
    <group position={[PIVO[0], PIVO[1], 0]} rotation={[0, 0, theta]}>
      {[-0.24, 0.24].map((z) => (
        <mesh key={z} position={[BRACO[0] / 2, BRACO[1] / 2, z]} rotation={[0, 0, base]}>
          <boxGeometry args={[L, 0.07, 0.05]} />
          <meshStandardMaterial color="#5a5f55" metalness={0.7} roughness={0.35} emissive="#ffcc00" emissiveIntensity={brilho} />
        </mesh>
      ))}
      <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.06, 0.06, 0.6, 12]} /><meshStandardMaterial color="#3a3d36" metalness={0.8} /></mesh>
    </group>
  );
};

const Sirene: React.FC<{p: THREE.Vector3; ang: number; grande?: boolean}> = ({p, ang, grande}) => (
  <group position={[p.x - 0.55, p.y + 0.55, p.z + (grande ? 0.25 : 0)]} scale={grande ? 1.8 : 1}>
    <mesh rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.09, 0.11, 0.28, 16]} /><meshStandardMaterial color="#2d3a2a" metalness={0.5} roughness={0.4} /></mesh>
    <group position={[-0.17, 0, 0]} rotation={[ang, 0, 0]}>
      {[0, 1, 2, 3].map((i) => (
        <mesh key={i} rotation={[(i * Math.PI) / 2, 0, 0]} position={[0, 0, 0]}>
          <boxGeometry args={[0.02, 0.36, 0.07]} /><meshStandardMaterial color="#b8b8b0" metalness={0.6} roughness={0.3} />
        </mesh>
      ))}
    </group>
  </group>
);

// linhas de vento passando rente ao avião (sensação de velocidade), finas e transparentes
const Vento: React.FC<{f: number; vel: number}> = ({f, vel}) => (
  <group>
    {Array.from({length: 40}, (_, c) => {
      const x = (random(`vx${c}`) - 0.5) * 22, z = (random(`vz${c}`) - 0.5) * 14;
      const y = (((random(`vy${c}`) * 60 + f * vel) % 60) + 60) % 60 - 30;
      return (
        <mesh key={c} position={[x, y, z]}>
          <boxGeometry args={[0.025, 2.5 + random(`vl${c}`) * 3, 0.025]} />
          <meshBasicMaterial color="#ffffff" transparent opacity={0.35} depthWrite={false} />
        </mesh>
      );
    })}
  </group>
);

export const Stuka3D: React.FC<{fase: string; dur: number; eventos: Record<string, number>}> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, pronto, h} = useTexturas(['ceu_nuvens_hdri', 'grass_path_2_diff']);
  const modelo = useModelo('stuka.glb');
  DEBUG_COR = fase === 'vercor';
  const info = useMemo(() => limpar(modelo), [modelo]);
  const [hAviao] = useState(() => delayRender('stuka pronto'));
  const k = interpolate(f, [0, dur], [0, 1], cl);

  // atitude do avião: ângulo de mergulho (rad, + = nariz para baixo)
  let mergulho = 1.48;
  if (fase === 'despenca') mergulho = interpolate(k, [0, 1], [1.1, 1.5], suave);
  if (fase === 'puxao') mergulho = interpolate(k, [0.1, 0.95], [1.45, -0.25], {...cl, easing: Easing.out(Easing.cubic)});
  if (fase === 'sozinho') mergulho = -0.35;
  if (fase.startsWith('ver')) mergulho = 0;
  if (fase === 'vercor') mergulho = 1.48;
  const rolagem = fase === 'despenca' ? interpolate(k, [0, 1], [0.6, 0], suave) : 0;

  // garfo e bomba
  const tSolta = eventos.solta ?? Math.round(dur * 0.15);
  let theta = 0, bombaLivre = 0, desliza = 0;
  if (fase === 'helice') theta = 0.12 + Math.sin(f * 0.35) * 0.1;               // a bomba balançando perto das pás
  if (fase === 'erro') desliza = interpolate(f, [tSolta, dur - 8], [0, 1], {...cl, easing: Easing.in(Easing.quad)});   // solta reto → vai na hélice
  if (fase === 'arremessa') {
    theta = interpolate(f, [2, dur * 0.45], [0, 1.3], {...cl, easing: Easing.out(Easing.cubic)});
    bombaLivre = interpolate(f, [dur * 0.45, dur], [0, 1], cl);
  }
  const brilhoGarfo = fase === 'garfo' ? interpolate(f, [0, 8, dur], [0, 0.9, 0.5], cl) : 0;

  const L = Math.hypot(...BRACO), base = Math.atan2(BRACO[1], BRACO[0]);
  const bx = PIVO[0] + Math.cos(base + theta) * L, by = PIVO[1] + Math.sin(base + theta) * L;
  // bomba solta: segue para a frente (para onde o nariz aponta) e se afasta
  const bombaPos: [number, number, number] = fase === 'erro'
    ? [bx + desliza * (HELICE_X + 0.95 - bx), by, 0]
    : fase === 'arremessa' && bombaLivre > 0
      ? [bx - bombaLivre * 9, by - bombaLivre * 1.2, 0]
      : [bx, by, 0];
  const mostraBomba = !['puxao', 'sozinho'].includes(fase) && !fase.startsWith('ver');
  const giro = f * (fase === 'erro' ? 0.18 : 0.9);                          // câmera lenta no erro
  const borrao = fase === 'erro' ? 0.25 : 1;
  const sireneAng = f * interpolate(k, [0, 1], [0.3, 1.6], cl) * (fase === 'sirene' ? 1 : 1.6);

  // CÂMERA por fase (coordenadas do mundo; avião no centro, girado pelo mergulho)
  const tremor = fase === 'puxao' ? (random(`t${f}`) - 0.5) * 0.25 * (1 - k) : 0;
  const cams: Record<string, [[number, number, number], [number, number, number], number]> = {
    helice: [[3.4 - k * 0.4, 1.6 - k * 0.5, 3.2], [0.0, -6.8, 0], 55],
    despenca: [[Math.sin(k * 1.6 + 0.4) * 19, 3 - k * 2, Math.cos(k * 1.6 + 0.4) * 19], [0, -1, 0], 40],
    sirene: [[2.6 - k * 0.3, -3.5, 3.6], [0.67, -4.3, 1.6], 40],
    erro: [[3.4, -8.8, 6.8 - k * 0.8], [0.7, -4.0, 0], 45],
    garfo: [[1.9, -0.6, 3.2 - k * 0.5], [0.85, -0.2, 0], 42],
    arremessa: [[0.8, -3.0, 10.5], [0.8, -3.0, 0], 45],
    puxao: [[9 + tremor, 2 + tremor, 11], [0, 0, 0], 45],
    sozinho: [[5.5 - k * 1.5, 2.6, 4.5], [-2, 0.8, 0], 45],
    ver: [[0, -0.3, 22], [0, -0.3, 0], 45],
    verbaixo: [[0, -14, 0.01], [0, 0, 0], 45],
    vercor: [[3.5, -3.0, 9.0], [0.5, -3.0, 0], 45],
  };
  // câmeras presas a peças (sirene na roda do lado da câmera)
  const mundo = (x: number, y: number, z: number): [number, number, number] =>
    [x * Math.cos(mergulho) - y * Math.sin(mergulho), x * Math.sin(mergulho) + y * Math.cos(mergulho), z];
  if (info && fase === 'sirene') {
    const r = info.rodas.reduce((m, q) => (q.z > m.z ? q : m), info.rodas[0]);
    const s = mundo(r.x - 0.55, r.y + 0.55, r.z + 0.25);
    cams.sirene = [[s[0] + 1.6, s[1] - 2.2 + k * 0.4, s[2] + 2.6 - k * 0.4], s, 38];
  }
  if (fase === 'helice') {
    const bw = mundo(bombaPos[0], bombaPos[1], 0), hw = mundo(HELICE_X, info ? info.eixoY : 0.1, 0);
    cams.helice = [[bw[0] + 1.1 - k * 0.2, bw[1] + 1.6 - k * 0.3, 1.5], [hw[0] * 0.5 + bw[0] * 0.5, hw[1] - 1.5, 0], 62];
  }
  const [cam, alvo, fov] = cams[fase] ?? cams.despenca;
  const chao = rep(tex.grass_path_2_diff, 60, 60);
  const altura = fase === 'helice' ? interpolate(k, [0, 1], [-260, -150]) : -260;   // chão crescendo no gancho
  const velNuvem = ['puxao', 'sozinho'].includes(fase) ? -1.2 : fase === 'erro' ? 0.4 : 2.2;

  return (
    <ThreeCanvas width={width} height={height} camera={{fov, position: cam, near: 0.05, far: 2000}}>
      <Camera pos={cam} alvo={alvo} />
      <Liberar pronto={pronto} h={h} />
      <LiberarAviao ok={!!info && pronto} h={hAviao} />
      <Ambiente tex={tex.ceu_nuvens_hdri} fundo forca={0.9} />
      <hemisphereLight args={['#ffffff', '#55604a', 0.8]} />
      <directionalLight position={[30, 60, 40]} intensity={2.0} />
      <fog attach="fog" args={['#b9c9d8', 120, 900]} />
      {!fase.startsWith('ver') && <Vento f={f} vel={velNuvem} />}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, altura, 0]}>
        <planeGeometry args={[3000, 3000]} />
        <meshStandardMaterial map={chao} color="#8fa070" roughness={1} />
      </mesh>
      {info && (
        <group rotation={[rolagem, 0, mergulho]}>
          <primitive object={info.limpo} />
          {!fase.startsWith('ver') && <Helice y={info.eixoY} ang={giro} borrao={borrao} />}
          {!fase.startsWith('ver') && info.rodas.map((r, i) => <Sirene key={i} p={r} ang={sireneAng} grande={fase === 'sirene'} />)}
          {mostraBomba && fase !== 'erro' && <Garfo theta={theta} brilho={brilhoGarfo} />}
          {mostraBomba && <group position={bombaPos}><Bomba /></group>}
        </group>
      )}
    </ThreeCanvas>
  );
};
