import React, {useMemo} from 'react';
import * as THREE from 'three';
import {interpolate, random, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Ambiente, Camera, Liberar, rep, useTexturas} from './comum3d';

// vd008: caminhão-tanque meio cheio, em corte (metade da frente do tanque removida).
// Fases: onda (freada: o líquido corre, bate na frente e empurra o caminhão) · paredes (as paredes furadas
// aparecem por dentro; close nos furos) · ondinhas (nova freada: cada compartimento faz só uma onda pequena).
// 1 unidade ≈ 1 m. Tanque ao longo de x (cabine em +x), raio 1,1 m, 7 m de comprimento.

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
const R = 1.1, L = 7, X0 = -3.5;           // raio, comprimento, início do tanque
const PAREDES = [-1.75, 0, 1.75];          // posições das paredes internas (x)
const N = 56;                              // fatias do líquido

// seção circular abaixo da altura y (de -R a +R), como forma 2D no plano (z, y)
const segmento = (y: number) => {
  const s = new THREE.Shape();
  const yy = Math.max(-R + 0.01, Math.min(R - 0.01, y));
  const a = Math.asin(yy / R);
  s.absarc(0, 0, R * 0.985, a, Math.PI - a, true);   // do lado direito por baixo até o esquerdo
  s.lineTo(Math.cos(a) * R * 0.985, yy);
  return s;
};

const Liquido: React.FC<{altura: (x: number) => number}> = ({altura}) => {
  const fatias = useMemo(() => Array.from({length: N}, (_, i) => X0 + (i + 0.5) * (L / N)), []);
  return (
    <group>
      {fatias.map((x, i) => {
        const g = new THREE.ExtrudeGeometry(segmento(altura(x)), {depth: L / N + 0.002, bevelEnabled: false, curveSegments: 18});
        return (
          <mesh key={i} geometry={g} position={[x - L / N / 2, 0, 0]} rotation={[0, Math.PI / 2, 0]}>
            <meshPhysicalMaterial color="#d9a21a" roughness={0.08} metalness={0} transmission={0} clearcoat={1} clearcoatRoughness={0.05}
              emissive="#5a3a00" emissiveIntensity={0.25} />
          </mesh>
        );
      })}
    </group>
  );
};

// parede interna com 3 furos (forma com buracos)
const Parede: React.FC<{x: number; op: number; sobe: number}> = ({x, op, sobe}) => {
  const g = useMemo(() => {
    const s = new THREE.Shape();
    s.absarc(0, 0, R * 0.98, 0, Math.PI * 2, false);
    [[0, -0.45, 0.22], [-0.5, 0.25, 0.16], [0.5, 0.25, 0.16]].forEach(([cx, cy, r]) => {
      const h = new THREE.Path();
      h.absarc(cx, cy, r, 0, Math.PI * 2, true);
      s.holes.push(h);
    });
    return new THREE.ExtrudeGeometry(s, {depth: 0.05, bevelEnabled: false, curveSegments: 28});
  }, []);
  if (op <= 0.01) return null;
  return (
    <mesh geometry={g} position={[x, (1 - sobe) * 2.8, 0]} rotation={[0, Math.PI / 2, 0]}>
      <meshStandardMaterial color="#c9ced3" metalness={0.85} roughness={0.25} transparent opacity={op} side={THREE.DoubleSide} />
    </mesh>
  );
};

const Roda: React.FC<{x: number; z: number; ang: number}> = ({x, z, ang}) => (
  <group position={[x, -1.75, z]} rotation={[0, 0, -ang]}>
    <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.5, 0.5, 0.35, 28]} /><meshStandardMaterial color="#1c1c1e" roughness={0.9} /></mesh>
    <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, z > 0 ? 0.18 : -0.18]}><cylinderGeometry args={[0.28, 0.28, 0.02, 20]} /><meshStandardMaterial color="#b9bec4" metalness={0.9} roughness={0.2} /></mesh>
    {[0, 1, 2, 3, 4].map((k) => (
      <mesh key={k} position={[0, 0, z > 0 ? 0.19 : -0.19]} rotation={[0, 0, (k / 5) * Math.PI * 2]}>
        <boxGeometry args={[0.06, 0.5, 0.01]} /><meshStandardMaterial color="#7d848b" metalness={0.8} />
      </mesh>
    ))}
  </group>
);

const Respingos: React.FC<{f: number; t0: number; x: number; forca: number}> = ({f, t0, x, forca}) => {
  const t = (f - t0) / 30;
  if (t < 0 || t > 1.1 || forca < 0.05) return null;
  return (
    <group>
      {Array.from({length: 46}, (_, i) => {
        const vx = -(0.6 + random(`rx${i}`) * 2.0), vy = 1.6 + random(`ry${i}`) * 2.4, vz = (random(`rz${i}`) - 0.5) * 1.4;
        const y = 0.4 + vy * t - 4.9 * t * t;
        if (y < -0.9) return null;
        const s = (0.03 + random(`rs${i}`) * 0.05) * forca;
        return (
          <mesh key={i} position={[x + vx * t, y, vz * t]} scale={[s, s * (1 + Math.abs(vy - 9.8 * t) * 0.3), s]}>
            <sphereGeometry args={[1, 8, 6]} /><meshPhysicalMaterial color="#e2ae2a" roughness={0.05} clearcoat={1} />
          </mesh>
        );
      })}
    </group>
  );
};

export type FaseTanque = 'onda' | 'paredes' | 'ondinhas';

export const Tanque3D: React.FC<{fase: FaseTanque; dur: number; eventos: Record<string, number>}> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, erro, pronto, h} = useTexturas(['asphalt_02_diff', 'grass_path_2_diff', 'ceu_nuvens_hdri']);

  // ----- movimento do caminhão e inclinação do líquido por fase -----
  let vel = 0, inclina = 0, onda = 0, empurra = 0, pitch = 0, paredesOp = 0, paredesSobe = 0, respingo = -999;
  let cam: [number, number, number] = [5.8, 2.6, 8.2];
  let alvo: [number, number, number] = [0.2, 0.2, 0];
  if (fase === 'onda') {
    const tBate = eventos.bate ?? Math.round(dur * 0.55);
    const tEmp = eventos.empurra ?? Math.round(dur * 0.75);
    vel = interpolate(f, [0, 10, tBate], [1, 1, 0], cl);
    inclina = interpolate(f, [8, tBate - 6, tBate + 4, tBate + 30], [0, 0.85, 0.95, 0.2], suave);   // sobe na frente
    onda = interpolate(f, [tBate - 12, tBate, tBate + 20], [0, 1, 0.2], cl);
    empurra = interpolate(f, [tEmp - 4, tEmp + 6, tEmp + 24], [0, 0.35, 0.3], cl);
    pitch = interpolate(f, [12, tBate - 10, tBate, tBate + 10, tBate + 30], [0, 0.02, 0.045, -0.015, 0], cl);
    respingo = tBate;
    cam = [interpolate(f, [0, dur], [11.5, 10.2], cl), interpolate(f, [0, dur], [4.6, 4.0], cl), interpolate(f, [0, dur], [5.2, 4.6], cl)];
    alvo = [1.1, -0.5, 0];
  } else if (fase === 'paredes') {
    const tPar = eventos.paredes ?? Math.round(dur * 0.3);
    const tFur = eventos.furadas ?? Math.round(dur * 0.75);
    paredesSobe = interpolate(f, [tPar - 6, tPar + 10], [0, 1], suave);
    paredesOp = interpolate(f, [tPar - 6, tPar], [0, 1], cl);
    const close = interpolate(f, [tFur - 10, tFur + 4], [0, 1], suave);
    cam = [interpolate(close, [0, 1], [10.8, 1.6]), interpolate(close, [0, 1], [4.4, 0.35]), interpolate(close, [0, 1], [4.8, 2.6])];
    alvo = [interpolate(close, [0, 1], [0.4, 0.0]), interpolate(close, [0, 1], [-0.4, -0.05]), 0];
  } else {
    paredesOp = 1; paredesSobe = 1;
    vel = interpolate(f, [0, 8, 40], [1, 1, 0], cl);
    inclina = interpolate(f, [6, 34, 70], [0, 0.16, 0.03], suave);     // por compartimento: só uma ondinha
    pitch = interpolate(f, [8, 30, 45, 70], [0, 0.015, -0.005, 0], cl);
    cam = [interpolate(f, [0, dur], [10.6, 9.6], cl), 4.2, interpolate(f, [0, dur], [5.0, 4.4], cl)];
    alvo = [1.0, -0.5, 0];
  }

  // estrada andando (o caminhão fica no quadro): soma da velocidade quadro a quadro
  let pista = 0;
  for (let k = 0; k < f; k++) pista += (fase === 'paredes' ? 0 : (k < 10 ? 1 : vel)) * 0.012;

  // altura do líquido em x: plano inclinado (sobe na frente = +x) + onda; com paredes, cada compartimento inclina sozinho
  const altura = (x: number) => {
    const h0 = -0.05;                                      // meio cheio
    if (paredesOp > 0.5) {
      const bordas = [X0, ...PAREDES, X0 + L];
      let i = 0; while (i < bordas.length - 2 && x > bordas[i + 1]) i++;
      const c = (bordas[i] + bordas[i + 1]) / 2;
      const w = Math.sin(f * 0.35 + i) * 0.015;
      return h0 + inclina * (x - c) * 0.9 + w;
    }
    const frente = Math.exp(-((x - (X0 + L - 0.5)) ** 2) / 1.0) * onda * 0.7;   // crista batendo na frente
    return h0 + inclina * (x / (L / 2)) * 0.9 + frente + Math.sin(x * 2.2 - f * 0.25) * 0.02;
  };

  return (
    <>
      <ThreeCanvas width={width} height={height} camera={{fov: 45, position: cam, near: 0.05, far: 300}}>
        <Camera pos={cam} alvo={alvo} />
        <Liberar pronto={pronto} h={h} />
        <Ambiente tex={tex.ceu_nuvens_hdri} fundo />
        <hemisphereLight args={['#e8f1fa', '#6a5a46', 0.6]} />
        <directionalLight position={[6, 10, 7]} intensity={2.2} color="#fff4e4" />
        <fog attach="fog" args={['#c9dbe9', 30, 120]} />
        {/* estrada e acostamento (textura corre para trás) */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.26, 0]}>
          <planeGeometry args={[200, 9]} />
          <meshStandardMaterial map={rep(tex.asphalt_02_diff, 40, 2, pista)} roughness={0.9} color="#ffffff" />
        </mesh>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.27, 0]}>
          <planeGeometry args={[200, 80]} />
          <meshStandardMaterial map={rep(tex.grass_path_2_diff, 60, 24, pista * 1.5)} roughness={1} color="#ffffff" />
        </mesh>
        {[-1, 1].map((s) => (
          <mesh key={s} rotation={[-Math.PI / 2, 0, 0]} position={[((-pista * 200 / 40) % 6) + s * 3, -2.25, 2.0]}>
            <planeGeometry args={[2.2, 0.15]} /><meshBasicMaterial color="#f2f2f2" />
          </mesh>
        ))}
        {/* caminhão: inclina para a frente na freada e é empurrado pelo líquido */}
        <group position={[empurra, 0, 0]} rotation={[0, 0, -pitch]}>
          {/* tanque em corte: metade de trás (aço por fora, interior visível), tampas nas pontas */}
          <mesh rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[R, R, L, 48, 1, true, Math.PI / 2, Math.PI]} />
            <meshStandardMaterial color="#d7dce1" metalness={0.85} roughness={0.22} side={THREE.DoubleSide} />
          </mesh>
          <mesh rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[R + 0.004, R + 0.004, L, 48, 1, true, -Math.PI / 2, Math.PI]} />
            <meshStandardMaterial color="#d7dce1" metalness={0.85} roughness={0.22} transparent opacity={0.12} side={THREE.DoubleSide} depthWrite={false} />
          </mesh>
          {[X0, X0 + L].map((x) => (
            <mesh key={x} position={[x, 0, 0]} rotation={[0, Math.PI / 2, 0]}>
              <circleGeometry args={[R, 48, -Math.PI / 2, Math.PI]} /><meshStandardMaterial color="#b8bec4" metalness={0.8} roughness={0.3} side={THREE.DoubleSide} />
            </mesh>
          ))}
          {/* borda do corte (anel vermelho) para ler como "corte" */}
          {[-1, 1].map((s) => (
            <mesh key={s} position={[0, s * R, 0]}><boxGeometry args={[L, 0.03, 0.03]} /><meshBasicMaterial color="#e23b2e" /></mesh>
          ))}
          <Liquido altura={altura} />
          {PAREDES.map((x) => <Parede key={x} x={x - 0.025} op={paredesOp} sobe={paredesSobe} />)}
          {/* chassi, cabine e rodas */}
          <mesh position={[0.6, -1.3, 0]}><boxGeometry args={[9.6, 0.25, 1.0]} /><meshStandardMaterial color="#2b2d30" roughness={0.6} /></mesh>
          <group position={[4.65, -0.35, 0]}>
            <mesh><boxGeometry args={[1.9, 2.1, 2.3]} /><meshStandardMaterial color="#c8281f" metalness={0.4} roughness={0.35} /></mesh>
            <mesh position={[0.96, 0.35, 0]}><boxGeometry args={[0.02, 0.8, 2.0]} /><meshStandardMaterial color="#1b2836" metalness={0.7} roughness={0.08} /></mesh>
            <mesh position={[0.97, -0.75, 0]}><boxGeometry args={[0.04, 0.35, 2.3]} /><meshStandardMaterial color="#d8dde2" metalness={0.9} roughness={0.2} /></mesh>
          </group>
          {[[-2.6, 1], [-1.5, 1], [4.4, 1], [-2.6, -1], [-1.5, -1], [4.4, -1]].map(([x, z], k) => (
            <Roda key={k} x={x} z={z * 1.05} ang={pista * 40} />
          ))}
          {/* luz de freio */}
          <mesh position={[X0 - 0.75, -1.35, 0]}><boxGeometry args={[0.05, 0.2, 1.4]} /><meshBasicMaterial color={vel < 0.99 && fase !== 'paredes' ? '#ff2a1a' : '#5a1a14'} /></mesh>
          <Respingos f={f} t0={respingo} x={X0 + L - 0.3} forca={1} />
        </group>
      </ThreeCanvas>
      {erro && <div style={{position: 'absolute', top: 40, left: 20, color: 'red', fontSize: 30, background: 'white'}}>{erro}</div>}
    </>
  );
};
