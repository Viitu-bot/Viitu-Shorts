import React from 'react';
import {interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';

// 3D do vd006 (diferencial). Fases:
//  "dentro" — eixo traseiro aberto: cardã + pinhão giram a coroa; a caixa de satélites leva as 2 semi-árvores.
//             Na reta as rodas giram iguais; no evento "curva" a roda de dentro desacelera, a de fora acelera e
//             as SATÉLITES começam a girar no próprio eixo (é isso que deixa cada roda no seu ritmo).
//  "lama"   — a roda esquerda na lama gira à toa (lama voando), a direita parada, o carro não anda; no evento
//             "bloqueio" um anel vermelho trava o diferencial, as duas rodas giram juntas e o eixo sai da lama.
// Tudo é função do quadro. eventos = quadros relativos à cena.

type Props = {fase: 'dentro' | 'lama'; dur: number; eventos: Record<string, number>};
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const AÇO = '#b9c0c8';
const OURO = '#d6a64a';

// up = vetor 'para cima' da tela. Com up = eixo X, o eixo das rodas fica na VERTICAL (aproveita a tela em pé)
const Camera: React.FC<{pos: [number, number, number]; alvo: [number, number, number]; up?: [number, number, number]}> = ({pos, alvo, up = [0, 1, 0]}) => {
  const {camera} = useThree();
  camera.up.set(...up);
  camera.position.set(...pos);
  camera.lookAt(...alvo);
  return null;
};

// engrenagem cônica simples: corpo + dentes; gira em torno do próprio eixo Y local
const Engrenagem: React.FC<{raio: number; dentes: number; ang: number; cor?: string; espessura?: number}> = ({raio, dentes, ang, cor = OURO, espessura = 0.12}) => (
  <group rotation={[0, ang, 0]}>
    <mesh>
      <cylinderGeometry args={[raio * 0.92, raio * 0.75, espessura, 32]} />
      <meshStandardMaterial color={cor} metalness={0.75} roughness={0.3} />
    </mesh>
    {Array.from({length: dentes}, (_, i) => {
      const a = (i / dentes) * Math.PI * 2;
      return (
        <mesh key={i} position={[Math.cos(a) * raio * 0.95, espessura * 0.45, Math.sin(a) * raio * 0.95]} rotation={[0, -a, 0]}>
          <boxGeometry args={[raio * 0.16, espessura * 0.9, raio * 0.09]} />
          <meshStandardMaterial color={cor} metalness={0.75} roughness={0.3} />
        </mesh>
      );
    })}
  </group>
);

// roda com raios + faixa vermelha para enxergar a velocidade
const Roda: React.FC<{ang: number; x: number; lama?: boolean}> = ({ang, x}) => (
  <group position={[x, 0, 0]} rotation={[ang, 0, 0]}>
    <mesh rotation={[0, 0, Math.PI / 2]}>
      <cylinderGeometry args={[0.95, 0.95, 0.55, 40]} />
      <meshStandardMaterial color="#1d1f22" roughness={0.9} />
    </mesh>
    <mesh rotation={[0, 0, Math.PI / 2]} position={[Math.sign(x) * 0.28, 0, 0]}>
      <cylinderGeometry args={[0.6, 0.6, 0.02, 32]} />
      <meshStandardMaterial color="#c9ced4" metalness={0.8} roughness={0.25} />
    </mesh>
    {[0, 1, 2, 3, 4].map((k) => (
      <mesh key={k} position={[Math.sign(x) * 0.3, 0, 0]} rotation={[(k / 5) * Math.PI * 2, 0, 0]}>
        <boxGeometry args={[0.03, 1.1, 0.09]} />
        <meshStandardMaterial color="#8d949b" metalness={0.7} />
      </mesh>
    ))}
    <mesh position={[Math.sign(x) * 0.29, 0.78, 0]}>
      <boxGeometry args={[0.05, 0.3, 0.3]} />
      <meshBasicMaterial color="#ff2a2a" />
    </mesh>
  </group>
);

const Particulas: React.FC<{centro: [number, number, number]; f: number; ativa: number; semente: string}> = ({centro, f, ativa, semente}) => (
  <group>
    {ativa > 0.01 && Array.from({length: 26}, (_, i) => {
      const c = (f * 0.06 + random(`${semente}${i}`)) % 1;
      const dir = (random(`${semente}d${i}`) - 0.5) * 1.2;
      return (
        <mesh key={i} position={[centro[0] + dir * 0.6, centro[1] + c * 1.6 - c * c * 1.4, centro[2] + 0.6 + c * 2.2]} scale={0.07 * (1 - c * 0.4)}>
          <sphereGeometry args={[1, 6, 5]} />
          <meshStandardMaterial color="#5a3f22" transparent opacity={ativa * (1 - c)} />
        </mesh>
      );
    })}
  </group>
);

export const Diferencial3D: React.FC<Props> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  let conteudo: React.ReactNode = null;
  let cam: [number, number, number] = [3.4, 2.4, 5.2];
  let alvo: [number, number, number] = [0, 0, 0];
  let fundo = '#20252d';
  let up: [number, number, number] = [0, 1, 0];

  if (fase === 'dentro') {
    const tCurva = eventos.curva ?? Math.round(dur * 0.45);
    const w = 0.12;                                       // giro da caixa de satélites (rad/quadro)
    const d = interpolate(f, [tCurva, tCurva + 15], [0, 0.55], cl);   // diferença dentro/fora
    let caixa = 0, esq = 0, dir = 0;
    for (let k = 0; k < f; k++) {
      const dk = interpolate(k, [tCurva, tCurva + 15], [0, 0.55], cl);
      caixa += w; esq += w * (1 - dk); dir += w * (1 + dk);
    }
    const satelite = (dir - esq) * 1.6;                  // satélites giram quando as rodas diferem
    // vertical é estreito: câmera alta e longe para caber o eixo inteiro com as 2 rodas
    cam = [0, interpolate(f, [0, dur], [7.6, 7.0], cl), interpolate(f, [0, dur], [3.8, 3.4], cl)];
    alvo = [0, 0, 0];
    up = [-1, 0, 0];                                                   // roda esquerda em cima, direita embaixo
    if (f >= tCurva + 4 && f < tCurva + 70) { cam = [-1.7, 1.5, 1.7]; alvo = [0.1, 0, 0]; up = [0, 1, 0]; }   // corte: close nas satélites girando    // corte: close nas satélites girando
    conteudo = (
      <>
        {/* cardã + pinhão (vem da frente do carro) */}
        <group position={[0, 0, 1.0]} rotation={[Math.PI / 2, 0, 0]}>
          <group rotation={[0, caixa * 3.1, 0]}>
            <mesh position={[0, 1.1, 0]}>
              <cylinderGeometry args={[0.09, 0.09, 2.2, 16]} />
              <meshStandardMaterial color={AÇO} metalness={0.8} roughness={0.25} />
            </mesh>
            <Engrenagem raio={0.3} dentes={10} ang={0} cor="#c7cdd3" espessura={0.18} />
          </group>
        </group>
        {/* coroa + caixa de satélites, giram em torno do eixo X */}
        <group rotation={[caixa, 0, 0]}>
          <group position={[0.42, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
            <Engrenagem raio={0.95} dentes={34} ang={0} espessura={0.14} />
          </group>
          {[-0.45, 0.45].map((x) => (
            <mesh key={x} position={[x, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
              <torusGeometry args={[0.42, 0.05, 8, 24]} />
              <meshStandardMaterial color="#8b939c" metalness={0.8} />
            </mesh>
          ))}
          {/* pino + satélites (giram no próprio eixo Y quando as rodas diferem) */}
          <mesh>
            <cylinderGeometry args={[0.05, 0.05, 0.9, 12]} />
            <meshStandardMaterial color={AÇO} metalness={0.8} />
          </mesh>
          {[-1, 1].map((l) => (
            <group key={l} position={[0, l * 0.3, 0]} rotation={[l === 1 ? 0 : Math.PI, 0, 0]}>
              <Engrenagem raio={0.2} dentes={9} ang={satelite} cor="#e3b85c" espessura={0.12} />
            </group>
          ))}
        </group>
        {/* planetárias + semi-árvores + rodas (cada uma no seu ritmo) */}
        {[['esq', -1], ['dir', 1]].map(([n, l]) => {
          const ang = l === -1 ? esq : dir;
          return (
            <group key={n as string}>
              <group position={[(l as number) * 0.3, 0, 0]} rotation={[ang, 0, (l as number) * Math.PI / 2]}>
                <Engrenagem raio={0.24} dentes={12} ang={0} cor="#c7cdd3" espessura={0.12} />
              </group>
              <mesh position={[(l as number) * 1.45, 0, 0]} rotation={[ang, 0, Math.PI / 2]}>
                <cylinderGeometry args={[0.07, 0.07, 2.2, 12]} />
                <meshStandardMaterial color={AÇO} metalness={0.8} roughness={0.25} />
              </mesh>
              <Roda ang={ang} x={(l as number) * 2.75} />
            </group>
          );
        })}
        <pointLight position={[0, 2.5, 2.5]} intensity={18} distance={10} color="#fff4e0" />
        {d < 0 && null}
      </>
    );
  } else {
    // lama: roda esquerda na lama gira à toa; bloqueio trava e as duas puxam juntas
    const tTrava = eventos.bloqueio ?? Math.round(dur * 0.65);
    fundo = '#9fb7c9';
    let esq = 0, dir = 0, z = 0;
    for (let k = 0; k < f; k++) {
      if (k < tTrava) { esq += 0.45; }
      else { esq += 0.14; dir += 0.14; z += 0.025; }
    }
    const anel = interpolate(f, [tTrava - 6, tTrava], [0.9, 0.0], cl);
    const lamaVoa = f < tTrava ? 1 : interpolate(f, [tTrava, tTrava + 10], [1, 0.25], cl);
    cam = [0, interpolate(f, [0, dur], [7.4, 6.8], cl), interpolate(f, [0, dur], [-4.6, -4.0], cl) + z];   // de cima e de trás
    alvo = [0, -0.4, z];
    up = [1, 0, 0];
    conteudo = (
      <>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.95, -4]}>
          <planeGeometry args={[30, 40]} />
          <meshStandardMaterial color="#8b7d66" roughness={1} />
        </mesh>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-2.75, -0.93, 0.2]}>
          <circleGeometry args={[1.6, 32]} />
          <meshStandardMaterial color="#4a3520" roughness={0.6} metalness={0.1} />
        </mesh>
        <group position={[0, 0, z]}>
          {/* (sem carroceria: a câmera olha de cima e ela taparia o eixo) */}
          <mesh rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.08, 0.08, 5.0, 12]} />
            <meshStandardMaterial color={AÇO} metalness={0.8} />
          </mesh>
          <mesh>
            <sphereGeometry args={[0.45, 20, 14]} />
            <meshStandardMaterial color="#6c737b" metalness={0.7} roughness={0.35} />
          </mesh>
          {/* anel de bloqueio desliza e trava */}
          <mesh position={[0.45 + anel, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
            <torusGeometry args={[0.3, 0.09, 10, 24]} />
            <meshStandardMaterial color="#ff2a2a" emissive="#ff2a2a" emissiveIntensity={f >= tTrava ? 0.6 : 0.1} />
          </mesh>
          <Roda ang={esq} x={-2.75} lama />
          <Roda ang={dir} x={2.75} />
        </group>
        <Particulas centro={[-2.75, -0.6, z]} f={f} ativa={lamaVoa} semente="lm" />
      </>
    );
  }

  return (
    <ThreeCanvas width={width} height={height} style={{backgroundColor: fundo}} camera={{fov: 50, position: cam, near: 0.1, far: 120}}>
      <Camera pos={cam} alvo={alvo} up={up} />
      <ambientLight intensity={0.65} />
      <directionalLight position={[-4, 6, 5]} intensity={1.7} />
      <directionalLight position={[4, 2, -3]} intensity={0.5} color="#bcd6ff" />
      {conteudo}
    </ThreeCanvas>
  );
};
