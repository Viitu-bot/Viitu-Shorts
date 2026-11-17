import React, {useEffect, useMemo, useState} from 'react';
import * as THREE from 'three';
import {continueRender, delayRender, interpolate, random, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';

// vd007: Starship pega pela torre (Flight 15, 14/11/2026). 1 unidade = 10 m.
// Fases: reentrada (barriga em brasa, vira em pé) · captura (braços fecham na nave) · pernas (perna = peso morto,
// solta, a carga entra) · rampa (pouso no chão; a torre gira e põe a nave no booster) · genial (fim de tarde, órbita).
// Texturas CC0 do Poly Haven (public/tex), sem normal map e sem sombras (render sem GPU).

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = {...cl, easing: Easing.inOut(Easing.cubic)};
type Tex = Record<string, THREE.Texture>;

const useTexturas = (nomes: string[]) => {
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
      t.colorSpace = THREE.SRGBColorSpace;
      if (n.endsWith('_hdri')) t.mapping = THREE.EquirectangularReflectionMapping;   // céu 360° real
      o[n] = t;
    });
    return o;
  }, []);
  return {tex, erro, pronto: ok, h};
};

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

const Camera: React.FC<{pos: [number, number, number]; alvo: [number, number, number]}> = ({pos, alvo}) => {
  const {camera} = useThree();
  camera.position.set(...pos);
  camera.lookAt(...alvo);
  return null;
};

const rep = (t: THREE.Texture | undefined, x: number, y: number) => { if (t) t.repeat.set(x, y); return t; };

// HDRI: foto 360° de céu real (Poly Haven, CC0) ilumina a cena e aparece refletida no aço — aspecto de render de verdade
const Ambiente: React.FC<{tex?: THREE.Texture; fundo: boolean; forca?: number}> = ({tex, fundo, forca = 1}) => {
  const {scene} = useThree();
  useEffect(() => {
    if (!tex) return;
    scene.environment = tex;
    (scene as any).environmentIntensity = forca;
    if (fundo) { scene.background = tex; (scene as any).backgroundIntensity = 1; }
  }, [tex, fundo, forca]);
  return null;
};

const ACO = '#e4e8ec';
const PRETO = '#17181a';

// ---------- a nave (origem = centro da base) ----------
const perfilNariz = Array.from({length: 14}, (_, i) => {
  const y = i / 13;
  return new THREE.Vector2(0.45 * Math.pow(Math.cos((y * Math.PI) / 2), 0.75) + 0.0001, y * 1.0);
});

const Chama: React.FC<{f: number; forca: number; x: number; z: number; s: number}> = ({f, forca, x, z, s}) => {
  if (forca <= 0.01) return null;
  const L = (0.9 + Math.sin(f * 1.9 + x * 7) * 0.08 + random(`c${f % 7}${x}`) * 0.06) * forca * s;
  return (
    <group position={[x, -0.3, z]}>
      <mesh position={[0, -L / 2, 0]}>
        <cylinderGeometry args={[0.07 * s, 0.015, L, 12, 1, true]} />
        <meshBasicMaterial color="#e8f1ff" transparent opacity={0.9} blending={THREE.AdditiveBlending} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, -L * 0.62, 0]}>
        <cylinderGeometry args={[0.12 * s, 0.03, L * 1.3, 12, 1, true]} />
        <meshBasicMaterial color="#ff8a2a" transparent opacity={0.55} blending={THREE.AdditiveBlending} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
};

type NaveProps = {f: number; chama?: number; plasma?: number; pernas?: number; pernasCai?: number; alerta?: number; corte?: number; carga?: number};
const Nave: React.FC<NaveProps> = ({f, chama = 0, plasma = 0, pernas = 0, pernasCai = 0, alerta = 0, corte = 0, carga = 0}) => {
  const vidro = corte > 0.01;
  return (
    <group>
      {/* corpo: parte de baixo (opaca) e de cima (abre em corte para mostrar a carga) */}
      <mesh position={[0, 1.2, 0]}>
        <cylinderGeometry args={[0.45, 0.45, 2.4, 40, 1, true]} />
        <meshStandardMaterial color={ACO} metalness={0.85} roughness={0.22} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, 3.2, 0]}>
        <cylinderGeometry args={[0.45, 0.45, 1.6, 40, 1, true]} />
        <meshStandardMaterial color={ACO} metalness={0.85} roughness={0.22} transparent={vidro} opacity={1 - corte * 0.8} depthWrite={!vidro} side={THREE.DoubleSide} />
      </mesh>
      {/* anéis de solda */}
      {[0.5, 1.1, 1.7, 2.3, 2.9, 3.5].map((y) => (
        <mesh key={y} position={[0, y, 0]}>
          <torusGeometry args={[0.452, 0.006, 4, 40]} />
          <meshStandardMaterial color="#8e959c" metalness={0.6} roughness={0.4} transparent={vidro && y > 2.4} opacity={y > 2.4 ? 1 - corte * 0.8 : 1} />
        </mesh>
      ))}
      {/* escudo térmico (barriga, lado -z) */}
      <mesh position={[0, 2.0, 0]}>
        <cylinderGeometry args={[0.458, 0.458, 4.0, 40, 1, true, Math.PI / 2, Math.PI]} />
        <meshStandardMaterial color={PRETO} roughness={0.85} side={THREE.DoubleSide} transparent={vidro} opacity={1 - corte * 0.6} />
      </mesh>
      {/* nariz */}
      <group position={[0, 4.0, 0]}>
        <mesh>
          <latheGeometry args={[perfilNariz, 40]} />
          <meshStandardMaterial color={ACO} metalness={0.85} roughness={0.22} side={THREE.DoubleSide} />
        </mesh>
        <mesh scale={[1.015, 1.0, 1.015]}>
          <latheGeometry args={[perfilNariz, 40, Math.PI / 2, Math.PI]} />
          <meshStandardMaterial color={PRETO} roughness={0.85} side={THREE.DoubleSide} />
        </mesh>
      </group>
      {/* flaps (dianteiros pequenos, traseiros grandes), puxados para a barriga */}
      {[-1, 1].map((s) => (
        <group key={s}>
          <mesh position={[s * 0.52, 4.35, -0.12]} rotation={[0, 0, s * -0.08]}>
            <boxGeometry args={[0.18, 0.75, 0.05]} />
            <meshStandardMaterial color={PRETO} roughness={0.8} />
          </mesh>
          <mesh position={[s * 0.6, 0.65, -0.12]} rotation={[0, 0, s * -0.05]}>
            <boxGeometry args={[0.32, 1.2, 0.06]} />
            <meshStandardMaterial color={PRETO} roughness={0.8} />
          </mesh>
          {/* pinos de captura (onde os braços seguram) */}
          <mesh position={[s * 0.55, 4.05, 0.1]}>
            <boxGeometry args={[0.14, 0.08, 0.12]} />
            <meshStandardMaterial color="#5c6268" metalness={0.7} roughness={0.35} />
          </mesh>
        </group>
      ))}
      {/* motores: 3 centrais + 3 de vácuo (maiores) */}
      {[0, 1, 2].map((k) => {
        const a = (k / 3) * Math.PI * 2;
        const b = a + Math.PI / 3;
        return (
          <group key={k}>
            <mesh position={[Math.cos(a) * 0.12, -0.12, Math.sin(a) * 0.12]}>
              <cylinderGeometry args={[0.035, 0.08, 0.24, 16, 1, true]} />
              <meshStandardMaterial color="#3d3a37" metalness={0.7} roughness={0.45} side={THREE.DoubleSide} />
            </mesh>
            <mesh position={[Math.cos(b) * 0.3, -0.16, Math.sin(b) * 0.3]}>
              <cylinderGeometry args={[0.05, 0.13, 0.32, 16, 1, true]} />
              <meshStandardMaterial color="#4a4541" metalness={0.7} roughness={0.45} side={THREE.DoubleSide} />
            </mesh>
            <Chama f={f} forca={chama} x={Math.cos(a) * 0.12} z={Math.sin(a) * 0.12} s={1} />
          </group>
        );
      })}
      <mesh position={[0, 0.0, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.45, 40]} />
        <meshStandardMaterial color="#2c2a28" roughness={0.9} />
      </mesh>
      {/* plasma da reentrada: casca brilhante na barriga */}
      {plasma > 0.01 && (
        <>
          <mesh position={[0, 2.3, -0.05]}>
            <cylinderGeometry args={[0.6, 0.6, 5.0, 32, 1, true, Math.PI / 2, Math.PI]} />
            <meshBasicMaterial color="#ff6a2a" transparent opacity={0.35 * plasma} blending={THREE.AdditiveBlending} depthWrite={false} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[0, 2.3, -0.1]}>
            <cylinderGeometry args={[0.85, 0.85, 5.6, 32, 1, true, Math.PI / 2, Math.PI]} />
            <meshBasicMaterial color="#ff3d7a" transparent opacity={0.16 * plasma} blending={THREE.AdditiveBlending} depthWrite={false} side={THREE.DoubleSide} />
          </mesh>
        </>
      )}
      {/* pernas de pouso (só na explicação): vermelhas, pulsando = peso */}
      {pernas > 0.01 && [0, 1, 2, 3].map((k) => {
        const a = (k / 4) * Math.PI * 2 + Math.PI / 4;
        const cai = pernasCai;
        return (
          <group key={k} position={[Math.cos(a) * (0.42 + cai * 0.5), 0.35 - cai * cai * 1.25, Math.sin(a) * (0.42 + cai * 0.5)]} rotation={[0, -a, cai * 1.2]}>
            <mesh position={[0.32, -0.35, 0]} rotation={[0, 0, 0.75]}>
              <boxGeometry args={[0.07, 1.0, 0.07]} />
              <meshStandardMaterial color="#d8342b" emissive="#ff2a1a" emissiveIntensity={0.25 + alerta * (0.6 + 0.5 * Math.sin(f * 0.5))} metalness={0.4} roughness={0.5} transparent opacity={pernas} />
            </mesh>
            <mesh position={[0.66, -0.72, 0]}>
              <cylinderGeometry args={[0.12, 0.14, 0.05, 16]} />
              <meshStandardMaterial color="#b52a22" transparent opacity={pernas} />
            </mesh>
          </group>
        );
      })}
      {/* carga: pilha de satélites chatos dentro do porão */}
      {carga > 0.01 && Array.from({length: 18}, (_, i) => {
        const entra = interpolate(carga * 18, [i, i + 1], [0, 1], cl);
        if (entra <= 0) return null;
        return (
          <mesh key={i} position={[0, 2.55 + i * 0.075, (1 - entra) * 1.6]}>
            <boxGeometry args={[0.6, 0.045, 0.34]} />
            <meshStandardMaterial color={i % 2 ? '#2e5a8c' : '#d9dde2'} metalness={0.5} roughness={0.4} emissive="#1b3d66" emissiveIntensity={0.25} />
          </mesh>
        );
      })}
    </group>
  );
};

// ---------- booster (origem = base) ----------
const Booster: React.FC = () => (
  <group>
    <mesh position={[0, 3.5, 0]}>
      <cylinderGeometry args={[0.45, 0.45, 7.0, 40]} />
      <meshStandardMaterial color={ACO} metalness={0.85} roughness={0.25} />
    </mesh>
    {[1, 2, 3, 4, 5, 6].map((y) => (
      <mesh key={y} position={[0, y, 0]}><torusGeometry args={[0.452, 0.006, 4, 40]} /><meshStandardMaterial color="#8e959c" /></mesh>
    ))}
    {[0, 1, 2, 3].map((k) => {
      const a = (k / 4) * Math.PI * 2;
      return (
        <mesh key={k} position={[Math.cos(a) * 0.55, 6.6, Math.sin(a) * 0.55]} rotation={[0, -a, 0]}>
          <boxGeometry args={[0.2, 0.4, 0.35]} />
          <meshStandardMaterial color="#3b3f44" metalness={0.6} roughness={0.5} />
        </mesh>
      );
    })}
  </group>
);

// ---------- torre "Mechazilla" (origem = pé da torre) ----------
const ALT_TORRE = 14.5;
const Torre: React.FC = () => {
  const niveis = Math.floor(ALT_TORRE / 0.8);
  const cor = '#3a3f45';
  return (
    <group>
      {[-1, 1].flatMap((sx) => [-1, 1].map((sz) => (
        <mesh key={`${sx}${sz}`} position={[sx * 0.6, ALT_TORRE / 2, sz * 0.6]}>
          <boxGeometry args={[0.13, ALT_TORRE, 0.13]} />
          <meshStandardMaterial color={cor} metalness={0.5} roughness={0.55} />
        </mesh>
      )))}
      {Array.from({length: niveis}, (_, i) => {
        const y = 0.4 + i * 0.8;
        return (
          <group key={i}>
            {[0, 1, 2, 3].map((k) => (
              <group key={k} rotation={[0, (k * Math.PI) / 2, 0]}>
                <mesh position={[0, y, 0.6]}><boxGeometry args={[1.2, 0.06, 0.06]} /><meshStandardMaterial color={cor} metalness={0.5} roughness={0.55} /></mesh>
                <mesh position={[0, y + 0.4, 0.6]} rotation={[0, 0, (i % 2 ? 1 : -1) * 0.59]}><boxGeometry args={[1.4, 0.045, 0.045]} /><meshStandardMaterial color={cor} metalness={0.5} roughness={0.55} /></mesh>
              </group>
            ))}
          </group>
        );
      })}
      {/* topo: guindaste */}
      <mesh position={[0, ALT_TORRE + 0.25, 0]}><boxGeometry args={[1.4, 0.5, 1.4]} /><meshStandardMaterial color="#2c3035" /></mesh>
      <mesh position={[0, ALT_TORRE + 0.7, 0.4]} rotation={[0.25, 0, 0]}><boxGeometry args={[0.15, 0.15, 2.6]} /><meshStandardMaterial color="#2c3035" /></mesh>
      {/* luz de topo */}
      <mesh position={[0, ALT_TORRE + 0.55, 0]}><sphereGeometry args={[0.07, 8, 6]} /><meshBasicMaterial color="#ff2a2a" /></mesh>
    </group>
  );
};

// braços: carro na torre (altura y) + 2 braços que abrem (abre 0..1); giro em volta da torre
const BRACO_Z = 0.7;
const Bracos: React.FC<{y: number; abre: number; tranco: number}> = ({y, abre, tranco}) => (
  <group position={[0, y, 0]}>
    <mesh position={[0, 0.2, 0]}><boxGeometry args={[1.5, 1.0, 1.5]} /><meshStandardMaterial color="#2f3439" metalness={0.5} roughness={0.5} /></mesh>
    {[-1, 1].map((s) => (
      <group key={s} position={[s * 0.68, -tranco, BRACO_Z]} rotation={[0, s * abre * 0.62, 0]}>
        {/* treliça do braço */}
        <mesh position={[0, 0.0, 1.7]}><boxGeometry args={[0.22, 0.06, 3.4]} /><meshStandardMaterial color="#d8dde2" metalness={0.5} roughness={0.4} /></mesh>
        <mesh position={[0, -0.42, 1.7]}><boxGeometry args={[0.22, 0.06, 3.4]} /><meshStandardMaterial color="#d8dde2" metalness={0.5} roughness={0.4} /></mesh>
        {Array.from({length: 9}, (_, i) => (
          <mesh key={i} position={[0, -0.21, 0.2 + i * 0.38]} rotation={[i % 2 ? 0.75 : -0.75, 0, 0]}>
            <boxGeometry args={[0.2, 0.55, 0.04]} />
            <meshStandardMaterial color="#c7ccd1" metalness={0.5} roughness={0.45} />
          </mesh>
        ))}
        {/* trilho amortecedor onde o pino apoia */}
        <mesh position={[-s * 0.1, 0.05, 1.7]}><boxGeometry args={[0.06, 0.06, 1.6]} /><meshStandardMaterial color="#f2c230" /></mesh>
      </group>
    ))}
  </group>
);

const BaseLancamento: React.FC = () => (
  <group>
    {Array.from({length: 6}, (_, k) => {
      const a = (k / 6) * Math.PI * 2;
      return <mesh key={k} position={[Math.cos(a) * 0.75, 1.0, Math.sin(a) * 0.75]}><boxGeometry args={[0.18, 2.0, 0.18]} /><meshStandardMaterial color="#5f6469" roughness={0.7} /></mesh>;
    })}
    <mesh position={[0, 2.0, 0]}><cylinderGeometry args={[0.95, 0.95, 0.3, 32, 1, false]} /><meshStandardMaterial color="#6b7075" metalness={0.4} roughness={0.6} /></mesh>
  </group>
);

const Vapor: React.FC<{f: number; pos: [number, number, number]; forca: number; semente: string}> = ({f, pos, forca, semente}) => (
  <group position={pos}>
    {forca > 0.01 && Array.from({length: 14}, (_, i) => {
      const c = (f * 0.025 + i / 14) % 1;
      return (
        <mesh key={i} position={[(random(`${semente}x${i}`) - 0.5) * 0.6 * (1 + c * 3), c * 0.9, (random(`${semente}z${i}`) - 0.5) * 0.6 * (1 + c * 3)]} scale={0.1 + c * 0.55}>
          <sphereGeometry args={[1, 8, 6]} />
          <meshStandardMaterial color="#e9edf0" transparent opacity={(1 - c) * 0.4 * forca} depthWrite={false} />
        </mesh>
      );
    })}
  </group>
);

const Seta: React.FC<{pos: [number, number, number]; cor: string; baixo: boolean; f: number; op: number}> = ({pos, cor, baixo, f, op}) => (
  op > 0.01 ? (
    <group position={[pos[0], pos[1] + Math.sin(f * 0.3) * 0.08 * (baixo ? -1 : 1), pos[2]]} rotation={[baixo ? Math.PI : 0, 0, 0]}>
      <mesh position={[0, 0, 0]}><cylinderGeometry args={[0.05, 0.05, 0.5, 10]} /><meshBasicMaterial color={cor} transparent opacity={op} /></mesh>
      <mesh position={[0, 0.35, 0]}><coneGeometry args={[0.13, 0.25, 12]} /><meshBasicMaterial color={cor} transparent opacity={op} /></mesh>
    </group>
  ) : null
);

// ---------- cenário de Starbase ----------
const Cenario: React.FC<{tex: Tex; cor?: string}> = ({tex}) => (
  <>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
      <planeGeometry args={[220, 220]} />
      <meshStandardMaterial map={rep(tex.coast_sand_01_diff, 40, 40)} color="#e8dcc4" roughness={1} />
    </mesh>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[1.2, 0.0, 1.2]}>
      <planeGeometry args={[9, 9]} />
      <meshStandardMaterial map={rep(tex.concrete_floor_02_diff, 3, 3)} color="#ffffff" roughness={0.95} />
    </mesh>
    {/* mar ao fundo */}
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, -95]}>
      <planeGeometry args={[400, 120]} />
      <meshStandardMaterial color="#3d7ea6" metalness={0.3} roughness={0.25} />
    </mesh>
  </>
);

export type FaseStarship = 'reentrada' | 'captura' | 'pernas' | 'rampa' | 'genial';
const MOUNT: [number, number, number] = [BRACO_Z + 1.7 - 0.05, 0, 0];   // a 90° da posição de captura
const Y_BRACO = 13.2;          // altura dos braços → base da nave a 9.0 (= topo do booster na base)
const NAVE_Z = BRACO_Z + 1.65; // nave entre os braços

export const Starship3D: React.FC<{fase: FaseStarship; dur: number; eventos: Record<string, number>}> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const {tex, erro, pronto, h} = useTexturas(['coast_sand_01_diff', 'concrete_floor_02_diff', 'ceu_nuvens_hdri']);

  if (fase === 'reentrada') {
    // nave de barriga, em brasa, caindo; perto do fim vira em pé e acende os motores
    const vira = interpolate(f, [dur * 0.62, dur], [0, 1], suave);
    const pitch = interpolate(vira, [0, 1], [-Math.PI / 2 + 0.8, 0]);
    const plasma = interpolate(f, [0, dur * 0.62, dur * 0.85], [1, 1, 0.15], cl);
    const cam: [number, number, number] = [interpolate(f, [0, dur], [11.5, 10], cl), interpolate(f, [0, dur], [-0.4, 0.2], cl), 0.3];
    return (
      <ThreeCanvas width={width} height={height} style={{background: 'linear-gradient(#020510 0%, #0b1838 45%, #2b4f8a 75%, #e07a3f 100%)'}} gl={{alpha: true}} camera={{fov: 50, position: cam, near: 0.05, far: 400}}>
        <Camera pos={cam} alvo={[0, 0, 0]} />
        <Liberar pronto={pronto} h={h} />
        <Ambiente tex={tex.ceu_nuvens_hdri} fundo={false} forca={0.5} />
        <ambientLight intensity={0.35} />
        <directionalLight position={[5, 3, 4]} intensity={2.0} color="#fff3e2" />
        <pointLight position={[0, -2.2, 0]} intensity={18 * plasma} distance={8} color="#ff7a33" />
        {/* Terra lá embaixo */}
        <mesh position={[0, -88, -30]}><sphereGeometry args={[80, 64, 32]} /><meshStandardMaterial color="#2a5d9a" emissive="#10305a" emissiveIntensity={0.5} roughness={0.8} /></mesh>
        <mesh position={[0, -88, -30]}><sphereGeometry args={[81.5, 64, 32]} /><meshBasicMaterial color="#6fb6ff" transparent opacity={0.18} side={THREE.BackSide} blending={THREE.AdditiveBlending} depthWrite={false} /></mesh>
        <group position={[0, Math.sin(f * 0.9) * 0.02, 0]} rotation={[pitch, 0, Math.sin(f * 0.37) * 0.03]}>
          <group position={[0, -2.5, 0]}>
            <Nave f={f} plasma={plasma} chama={interpolate(f, [dur * 0.82, dur * 0.95], [0, 1], cl)} />
          </group>
        </group>
        {/* rastro de plasma: faíscas esticadas subindo (o ar vem de baixo) */}
        {Array.from({length: 110}, (_, i) => {
          const vida = 18;
          const t = ((f + Math.floor(random(`p${i}`) * vida)) % vida) / vida;
          const ao = (random(`pz${i}`) - 0.5) * 4.6;
          const x = (random(`px${i}`) - 0.5) * 1.3;
          const y = -0.7 + t * 5.5;
          const op = (1 - t) * plasma;
          if (op < 0.02) return null;
          return (
            <mesh key={i} position={[x, y, ao * Math.cos(pitch + Math.PI / 2) * 0.9]} scale={[0.025, 0.25 + t * 0.9, 0.025]}>
              <boxGeometry args={[1, 1, 1]} />
              <meshBasicMaterial color={i % 3 ? '#ff8a3a' : '#ff4f8b'} transparent opacity={op} blending={THREE.AdditiveBlending} depthWrite={false} />
            </mesh>
          );
        })}
      </ThreeCanvas>
    );
  }

  // --- fases em Starbase ---
  const tPegou = eventos.pegou ?? Math.round(dur * 0.6);
  let naveY = 9.0, abre = 0, tranco = 0, chama = 0, vapor = 0, giro = 0;
  let cam: [number, number, number] = [6, 10, 8];
  let alvo: [number, number, number] = [0, 11.3, NAVE_Z];
  let mostrarNaveTorre = true;
  let ceu = '#9fc3e0';
  let sol = {pos: [-8, 12, 6] as [number, number, number], cor: '#fff4e6', i: 2.2};

  if (fase === 'captura') {
    naveY = interpolate(f, [0, tPegou], [12.8, 9.0], {...cl, easing: Easing.out(Easing.quad)});
    abre = interpolate(f, [tPegou - 9, tPegou], [1, 0.02], suave);
    tranco = interpolate(f, [tPegou, tPegou + 4, tPegou + 12], [0, 0.07, 0], cl);
    naveY -= tranco;
    chama = f < tPegou + 3 ? 0.8 : 0;
    vapor = interpolate(f, [tPegou, tPegou + 3, tPegou + 40], [0, 1, 0.3], cl);
    cam = [interpolate(f, [0, dur], [8.2, 7.2], cl), interpolate(f, [0, dur], [14.6, 14.0], cl), interpolate(f, [0, dur], [5.2, 4.6], cl)];
    alvo = [0, interpolate(f, [0, dur], [13.0, 12.0], cl), NAVE_Z - 0.5];
  } else if (fase === 'rampa') {
    const tChao = eventos.chao ?? Math.round(dur * 0.3);
    const tVolta = eventos.volta ?? Math.round(dur * 0.75);
    giro = interpolate(f, [tVolta - 6, tVolta + 22], [0, Math.PI / 2], suave);
    // olhar desce da nave até o pé da torre ("no chão"), depois abre o plano para o giro
    const desce = interpolate(f, [0, tChao], [0, 1], suave);
    const abrePlano = interpolate(f, [tChao + 6, tVolta - 8], [0, 1], suave);
    cam = [interpolate(abrePlano, [0, 1], [8.5, 13.5]), interpolate(desce, [0, 1], [11.5, 3.0]) + abrePlano * 4.0, interpolate(abrePlano, [0, 1], [9.5, 15.5])];
    alvo = [interpolate(abrePlano, [0, 1], [0.3, 1.3]), interpolate(desce, [0, 1], [11.5, 1.2]) + abrePlano * 7.3, interpolate(abrePlano, [0, 1], [1.4, 1.0])];
  } else if (fase === 'genial') {
    giro = Math.PI / 2;
    const ang = interpolate(f, [0, dur], [0.15, 0.75], cl);
    cam = [MOUNT[0] + Math.sin(ang) * 23, 3.0 + f * 0.01, Math.cos(ang) * 23];
    alvo = [MOUNT[0] * 0.6, 8.0, 0];
    ceu = '#f0a26a';
    sol = {pos: [14, 3.5, -10], cor: '#ffb070', i: 2.6};
  } else if (fase === 'pernas') {
    mostrarNaveTorre = false;
  }

  if (fase === 'pernas') {
    const tMenos = eventos.menos ?? Math.round(dur * 0.6);
    const tCarga = eventos.carga ?? Math.round(dur * 0.75);
    const cai = interpolate(f, [tMenos, tMenos + 16], [0, 1], cl);
    const pernasOp = interpolate(f, [tMenos + 10, tMenos + 22], [1, 0], cl);
    const corte = interpolate(f, [tCarga - 10, tCarga], [0, 1], suave);
    const carga = interpolate(f, [tCarga - 4, tCarga + 26], [0, 1], cl);
    const sobe = interpolate(f, [tMenos + 4, tMenos + 30], [0, 0.35], suave);
    const y = 1.1 + sobe + Math.sin(f * 0.12) * 0.03;
    const camP: [number, number, number] = [interpolate(f, [0, dur], [4.8, 3.9], cl), 3.2, interpolate(f, [0, dur], [6.2, 5.2], cl)];
    return (
      <>
        <ThreeCanvas width={width} height={height} style={{backgroundColor: ceu}} camera={{fov: 50, position: camP, near: 0.05, far: 400}}>
          <Camera pos={camP} alvo={[0, 2.6, 0]} />
          <Liberar pronto={pronto} h={h} />
          <Ambiente tex={tex.ceu_nuvens_hdri} fundo />
          <fog attach="fog" args={[ceu, 25, 120]} />
          <hemisphereLight args={['#e6f0fa', '#8a7a62', 0.85]} />
          <directionalLight position={sol.pos} intensity={sol.i} color={sol.cor} />
          <Cenario tex={tex} />
          <group position={[0, y, 0]}>
            <Nave f={f} chama={0.35} pernas={pernasOp} pernasCai={cai} alerta={1 - cai} corte={corte} carga={carga} />
          </group>
          {/* pernas caídas no chão */}
          {[-1, 1].map((sx) => (
            <Seta key={sx} pos={[sx * 1.15, 0.9 + y * 0.2, 0.4]} cor="#ff2a1a" baixo f={f} op={interpolate(f, [0, 6, tMenos, tMenos + 6], [0, 1, 1, 0], cl)} />
          ))}
          <Seta pos={[0.95, 3.4 + y, 0.5]} cor="#22d36b" baixo={false} f={f} op={interpolate(f, [tCarga, tCarga + 8], [0, 1], cl)} />
          <Vapor f={f} pos={[0, 0.05, 0]} forca={0.6} semente="pv" />
        </ThreeCanvas>
        {erro && <div style={{position: 'absolute', top: 40, left: 20, color: 'red', fontSize: 30, background: 'white'}}>{erro}</div>}
      </>
    );
  }

  return (
    <>
      <ThreeCanvas width={width} height={height} style={{backgroundColor: ceu}} camera={{fov: 50, position: cam, near: 0.05, far: 500}}>
        <Camera pos={cam} alvo={alvo} />
        <Liberar pronto={pronto} h={h} />
        <Ambiente tex={tex.ceu_nuvens_hdri} fundo={fase !== 'genial'} />
        <fog attach="fog" args={[ceu, 30, 160]} />
        <hemisphereLight args={[fase === 'genial' ? '#ffd2a8' : '#e6f0fa', '#7a6a52', 0.8]} />
        <directionalLight position={sol.pos} intensity={sol.i} color={sol.cor} />
        <Cenario tex={tex} />
        <Torre />
        <group position={MOUNT}>
          <BaseLancamento />
          <group position={[0, 2.0, 0]}><Booster /></group>
        </group>
        {mostrarNaveTorre && (
          <group rotation={[0, giro, 0]}>
            <Bracos y={Y_BRACO} abre={abre} tranco={tranco} />
            <group position={[0, naveY, NAVE_Z]}>
              <Nave f={f} chama={chama} />
            </group>
            {fase === 'captura' && [-1, 1].map((s) => (
              <Vapor key={s} f={f} pos={[s * 0.6, Y_BRACO, NAVE_Z]} forca={vapor} semente={`v${s}`} />
            ))}
          </group>
        )}
        {fase === 'captura' && <Vapor f={f} pos={[0, naveY - 1.2, NAVE_Z]} forca={chama} semente="esc" />}
      </ThreeCanvas>
      {erro && <div style={{position: 'absolute', top: 40, left: 20, color: 'red', fontSize: 30, background: 'white'}}>{erro}</div>}
    </>
  );
};
