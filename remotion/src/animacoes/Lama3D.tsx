import React, {useEffect, useMemo, useState} from 'react';
import * as THREE from 'three';
import {continueRender, delayRender, interpolate, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';

// Caminhonete atolada (vd006). Texturas reais CC0 do Poly Haven (public/tex/*).
// Antes de "bloqueio": roda esquerda patina no atoleiro (jatos de lama com gravidade, tremor, fumaça do escape),
// roda direita parada no seco. No "bloqueio": anel trava, as duas giram, a caminhonete dá um tranco e sai.

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
type Tex = Record<string, THREE.Texture>;

const useTexturas = (nomes: string[]): {tex: Tex; erro: string; pronto: boolean; h: number} => {
  // texturas criadas JÁ na montagem (o material nasce com o mapa); o quadro só é liberado quando todas carregam
  const [erro, setErro] = useState('');
  const [ok, setOk] = useState(false);
  const [h] = useState(() => delayRender('texturas'));
  const tex = useMemo(() => {
    const loader = new THREE.TextureLoader();
    let faltam = nomes.length;
    const o: Tex = {};
    const pronto = () => { faltam -= 1; if (faltam === 0) setOk(true); };
    nomes.forEach((n) => {
      const t = loader.load(staticFile(`tex/${n}.jpg`), pronto, undefined, (e) => { setErro(`${n}: ${String(e)}`); pronto(); });
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      if (n.endsWith('_diff')) t.colorSpace = THREE.SRGBColorSpace;
      o[n] = t;
    });
    return o;
  }, []);
  return {tex, erro, pronto: ok, h};
};

// dentro do canvas: quando as texturas chegam, força 2 redesenhos (sobe a textura) e só então libera o quadro
const Liberar: React.FC<{pronto: boolean; h: number}> = ({pronto, h}) => {
  const {advance, invalidate} = useThree();
  useEffect(() => {
    if (!pronto) return;
    invalidate();
    advance(performance.now());
    const t = setTimeout(() => { advance(performance.now()); continueRender(h); }, 300);
    return () => clearTimeout(t);
  }, [pronto]);
  return null;
};

const rep = (t: THREE.Texture | undefined, x: number, y: number) => {
  if (!t) return undefined;
  t.repeat.set(x, y);                // cada textura é usada por um único chão: ajusta a repetição nela mesma
  return t;
};

const Camera: React.FC<{pos: [number, number, number]; alvo: [number, number, number]}> = ({pos, alvo}) => {
  const {camera} = useThree();
  camera.position.set(...pos);
  camera.lookAt(...alvo);
  return null;
};

// pneu de cravo: borracha + blocos de cravo + aro
const Pneu: React.FC<{ang: number; pos: [number, number, number]; sujo: number}> = ({ang, pos, sujo}) => (
  <group position={pos} rotation={[ang, 0, 0]}>
    <mesh rotation={[0, 0, Math.PI / 2]}>
      <cylinderGeometry args={[0.48, 0.48, 0.38, 36]} />
      <meshStandardMaterial color={sujo > 0.5 ? '#3a2c1e' : '#1b1c1e'} roughness={0.95} />
    </mesh>
    {Array.from({length: 22}, (_, i) => {
      const a = (i / 22) * Math.PI * 2;
      return (
        <mesh key={i} position={[(i % 2 ? 0.08 : -0.08), Math.cos(a) * 0.5, Math.sin(a) * 0.5]} rotation={[a, 0, 0]}>
          <boxGeometry args={[0.16, 0.06, 0.1]} />
          <meshStandardMaterial color={sujo > 0.5 ? '#4a3726' : '#222326'} roughness={0.9} />
        </mesh>
      );
    })}
    <mesh rotation={[0, 0, Math.PI / 2]} position={[Math.sign(pos[0]) * 0.2, 0, 0]}>
      <cylinderGeometry args={[0.28, 0.28, 0.04, 24]} />
      <meshStandardMaterial color="#c3c8ce" metalness={0.85} roughness={0.25} />
    </mesh>
    {[0, 1, 2, 3, 4, 5].map((k) => (
      <mesh key={k} position={[Math.sign(pos[0]) * 0.22, 0, 0]} rotation={[(k / 6) * Math.PI * 2, 0, 0]}>
        <boxGeometry args={[0.02, 0.42, 0.06]} />
        <meshStandardMaterial color="#9aa1a8" metalness={0.8} />
      </mesh>
    ))}
  </group>
);

const Caminhonete: React.FC<{esq: number; dir: number; trava: number; pitch: number; tremor: number; sujo: number}> = ({esq, dir, trava, pitch, tremor, sujo}) => (
  <group rotation={[pitch, 0, tremor]} position={[0, 0.48, 0]}>
    {/* chassi + caçamba + cabine */}
    <mesh position={[0, 0.55, 0.9]}>
      <boxGeometry args={[1.75, 0.55, 4.4]} />
      <meshStandardMaterial color="#b3261e" metalness={0.35} roughness={0.45} />
    </mesh>
    <mesh position={[0, 1.15, 1.75]}>
      <boxGeometry args={[1.65, 0.75, 1.6]} />
      <meshStandardMaterial color="#b3261e" metalness={0.35} roughness={0.45} />
    </mesh>
    <mesh position={[0, 1.2, 0.94]}>
      <boxGeometry args={[1.5, 0.5, 0.05]} />
      <meshStandardMaterial color="#1d2a36" metalness={0.6} roughness={0.15} />
    </mesh>
    {/* paredes da caçamba */}
    {[-0.85, 0.85].map((x) => (
      <mesh key={x} position={[x, 1.0, -0.3]}>
        <boxGeometry args={[0.06, 0.4, 2.0]} />
        <meshStandardMaterial color="#a3221b" metalness={0.35} roughness={0.45} />
      </mesh>
    ))}
    <mesh position={[0, 1.0, -1.3]}>
      <boxGeometry args={[1.75, 0.4, 0.06]} />
      <meshStandardMaterial color="#a3221b" metalness={0.35} roughness={0.45} />
    </mesh>
    {/* lanternas + para-choque */}
    {[-0.8, 0.8].map((x) => (
      <mesh key={x} position={[x, 0.85, -1.34]}>
        <boxGeometry args={[0.16, 0.32, 0.03]} />
        <meshStandardMaterial color="#ff2b1a" emissive="#ff2b1a" emissiveIntensity={1.4} />
      </mesh>
    ))}
    <mesh position={[0, 0.3, -1.38]}>
      <boxGeometry args={[1.9, 0.14, 0.12]} />
      <meshStandardMaterial color="#d7dbe0" metalness={0.9} roughness={0.2} />
    </mesh>
    {/* lama na lataria do lado atolado */}
    {sujo > 0.05 && Array.from({length: 14}, (_, i) => (
      <mesh key={i} position={[-0.88, 0.35 + random(`ls${i}`) * 0.45, -0.9 + random(`lz${i}`) * 1.4]} scale={[0.02, 0.05 + random(`lh${i}`) * 0.08, 0.06 + random(`lw${i}`) * 0.1]}>
        <sphereGeometry args={[1, 6, 5]} />
        <meshStandardMaterial color="#3e2c1b" roughness={0.4} transparent opacity={Math.min(sujo * 1.5, 1)} />
      </mesh>
    ))}
    {/* eixo traseiro, diferencial e anel de bloqueio */}
    <mesh rotation={[0, 0, Math.PI / 2]} position={[0, 0, -0.75]}>
      <cylinderGeometry args={[0.06, 0.06, 1.8, 12]} />
      <meshStandardMaterial color="#6f767d" metalness={0.8} />
    </mesh>
    <mesh position={[0, 0, -0.75]}>
      <sphereGeometry args={[0.24, 20, 14]} />
      <meshStandardMaterial color="#4f565d" metalness={0.75} roughness={0.35} />
    </mesh>
    <mesh position={[0.24 + (1 - trava) * 0.45, 0, -0.75]} rotation={[0, 0, Math.PI / 2]}>
      <torusGeometry args={[0.16, 0.05, 10, 24]} />
      <meshStandardMaterial color="#ff2a2a" emissive="#ff2a2a" emissiveIntensity={0.25 + trava * 1.2} />
    </mesh>
    <Pneu ang={esq} pos={[-0.98, 0, -0.75]} sujo={sujo} />
    <Pneu ang={dir} pos={[0.98, 0, -0.75]} sujo={0} />
    <Pneu ang={dir} pos={[-0.98, 0, 2.3]} sujo={0} />
    <Pneu ang={dir} pos={[0.98, 0, 2.3]} sujo={0} />
  </group>
);

// jatos de lama: pedaços irregulares lançados para trás em arco, com gravidade
const JatosLama: React.FC<{origem: [number, number, number]; f: number; forca: number; semente: string}> = ({origem, f, forca, semente}) => (
  <group>
    {forca > 0.02 && Array.from({length: 90}, (_, i) => {
      const vida = 22;
      const t0 = Math.floor(random(`${semente}t${i}`) * vida);
      const t = ((f + t0) % vida) / 30;                 // segundos desde o lançamento
      const vx = (random(`${semente}x${i}`) - 0.6) * 1.4;
      const vy = 2.2 + random(`${semente}y${i}`) * 2.6;
      const vz = -(2.0 + random(`${semente}z${i}`) * 3.2);
      const y = origem[1] + vy * t - 4.9 * t * t;
      if (y < -0.05) return null;
      const tam = (0.012 + random(`${semente}s${i}`) * 0.035) * forca;
      const estica = 1 + Math.min(Math.hypot(vy - 9.8 * t, vz) * 0.25, 2.2);   // respingo esticado na direção do voo
      return (
        <mesh key={i} position={[origem[0] + vx * t, y, origem[2] + vz * t]} rotation={[Math.atan2(vy - 9.8 * t, -vz), 0, 0]} scale={[tam, tam, tam * estica]}>
          <sphereGeometry args={[1, 7, 5]} />
          <meshStandardMaterial color={i % 3 ? '#3b2a19' : '#4d3721'} roughness={0.12} metalness={0.1} />
        </mesh>
      );
    })}
  </group>
);

const Fumaca: React.FC<{origem: [number, number, number]; f: number; forca: number}> = ({origem, f, forca}) => (
  <group>
    {Array.from({length: 10}, (_, i) => {
      const c = (f * 0.03 + i / 10) % 1;
      return (
        <mesh key={i} position={[origem[0] - c * 0.4, origem[1] + c * 1.2, origem[2] - c * 1.4]} scale={0.08 + c * 0.45}>
          <sphereGeometry args={[1, 8, 6]} />
          <meshStandardMaterial color="#bfbfbf" transparent opacity={(1 - c) * 0.35 * forca} depthWrite={false} />
        </mesh>
      );
    })}
  </group>
);

export const Lama3D: React.FC<{dur: number; eventos: Record<string, number>}> = ({dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, erro, pronto, h} = useTexturas(['brown_mud_02_diff', 'dirt_floor_diff', 'grass_path_2_diff']);
  const tTrava = eventos.bloqueio ?? Math.round(dur * 0.7);

  let esq = 0, dir = 0, z = 0;
  for (let k = 0; k < f; k++) {
    if (k < tTrava) esq += 0.55;
    else { const v = interpolate(k, [tTrava, tTrava + 8], [0.05, 0.16], cl); esq += v; dir += v; z += v * 0.48; }
  }
  const trava = interpolate(f, [tTrava - 8, tTrava], [0, 1], cl);
  const afunda = f < tTrava ? interpolate(f, [0, tTrava], [0, -0.12], cl) : interpolate(f, [tTrava, tTrava + 25], [-0.12, 0], cl);
  const tremor = f < tTrava ? Math.sin(f * 2.1) * 0.012 : 0;
  const pitch = f >= tTrava ? interpolate(f, [tTrava, tTrava + 6, tTrava + 22], [0, -0.08, 0], cl) : Math.sin(f * 1.7) * 0.006;
  const lama = f < tTrava ? 1 : interpolate(f, [tTrava, tTrava + 6, tTrava + 30], [1.6, 1.2, 0], cl);
  const sujo = interpolate(f, [0, 40], [0.2, 1], cl);

  // atoleiro com relevo (vértices deslocados = lama mexida)
  const geoLama = useMemo(() => {
    const g = new THREE.PlaneGeometry(3.4, 4.2, 48, 48);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), y = p.getY(i);
      const borda = Math.max(0, 1 - Math.hypot(x / 1.7, y / 2.1));
      // dentro da oval: lama mexida; fora dela: afunda abaixo do chão (some) → poça com borda natural e irregular
      const irreg = 1 + Math.sin(Math.atan2(y, x) * 5) * 0.08;
      const dentro = Math.hypot(x / (1.7 * irreg), y / (2.1 * irreg)) < 1;
      p.setZ(i, dentro ? 0.02 + Math.sin(x * 7 + y * 5) * 0.012 * borda + (random(`v${i}`) - 0.5) * 0.018 * borda : -0.05);
    }
    g.computeVertexNormals();
    return g;
  }, []);

  const cam: [number, number, number] = [-3.6, interpolate(f, [0, dur], [2.0, 1.7], cl), -5.6 + z * 0.85];
  const alvo: [number, number, number] = [0.3, 0.4, 0.9 + z];
  const corte = f >= tTrava - 2 && f < tTrava + 14;                         // close no anel travando
  const camF: [number, number, number] = corte ? [1.5, 0.45, -2.9 + z] : cam;   // close pelo lado direito (longe dos jatos de lama)
  const alvoF: [number, number, number] = corte ? [0.1, 0.45 + afunda, -0.75 + z] : alvo;

  return (
    <>
    <ThreeCanvas width={width} height={height} style={{backgroundColor: '#a9c3d6'}} camera={{fov: 50, position: camF, near: 0.05, far: 120}}>
      <Camera pos={camF} alvo={alvoF} />
      <Liberar pronto={pronto} h={h} />
      <fog attach="fog" args={['#a9c3d6', 14, 40]} />
      <hemisphereLight args={['#dfeaf5', '#5a4a36', 0.8]} />
      <directionalLight position={[-6, 9, -4]} intensity={2.2} color="#fff1dc" />
      {(
        <>
          {/* grama dos lados, estrada de terra e o atoleiro */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 6]}>
            <planeGeometry args={[40, 60]} />
            <meshStandardMaterial map={rep(tex.grass_path_2_diff, 14, 20)} roughness={1} color="#ffffff" />
          </mesh>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 6]}>
            <planeGeometry args={[4.6, 60]} />
            <meshStandardMaterial map={rep(tex.dirt_floor_diff, 2, 24)} roughness={0.95} color="#ffffff" />
          </mesh>
          <mesh geometry={geoLama} rotation={[-Math.PI / 2, 0, 0]} position={[-0.95, 0.015, -0.6]}>
            <meshStandardMaterial map={rep(tex.brown_mud_02_diff, 2, 2.5)} roughness={0.32} metalness={0} color="#d8b890" side={THREE.DoubleSide} />
          </mesh>
        </>
      )}
      <group position={[0, afunda, z]}>
        <Caminhonete esq={esq} dir={dir} trava={trava} pitch={pitch} tremor={tremor} sujo={sujo} />
      </group>
      <JatosLama origem={[-0.98, 0.15, -1.1 + z]} f={f} forca={lama} semente="j1" />
      <Fumaca origem={[0.6, 0.55, -1.45 + z]} f={f} forca={f < tTrava ? 1 : 0.6} />
    </ThreeCanvas>
    {erro && <div style={{position: 'absolute', top: 40, left: 20, color: 'red', fontSize: 30, background: 'white'}}>{erro}</div>}
    </>
  );
};
