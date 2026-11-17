import React from 'react';
import {interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';

// Maquete 3D vista do alto (estilo diorama): incêndio no topo, estrada com brigadistas e casas embaixo.
// fase "ar": o incêndio grande PUXA O AR — setas de vento correm pelo chão em direção a ele.
// fase "encontro": o contrafogo sai da estrada puxado pelo vento, os dois fogos se encontram e APAGAM.
// Tudo é função do quadro (determinístico). eventos = quadros relativos à cena.

type Props = {fase: 'ar' | 'encontro'; dur: number; eventos: Record<string, number>};

const ESTRADA_Z = 3.0;
const ENCONTRO_Z = -0.6;
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const ARVORES = Array.from({length: 230}, (_, i) => {
  const x = (random(`tx${i}`) - 0.5) * 11;
  const z = -7.5 + random(`tz${i}`) * 10.2;           // da borda do topo até antes da estrada
  return {x, z, s: 0.55 + random(`ts${i}`) * 0.5, c: ['#2f6b2a', '#3a7d31', '#285c24'][i % 3]};
}).filter((a) => a.z < ESTRADA_Z - 0.45);

const Chamas: React.FC<{z: number; altura: number; f: number; semente: string; largura?: number}> = ({z, altura, f, semente, largura = 11}) => {
  if (altura < 0.02) return null;
  const n = 26;
  return (
    <group>
      {Array.from({length: n}, (_, i) => {
        const x = -largura / 2 + (i + 0.5) * (largura / n);
        const fl = 0.75 + 0.35 * Math.abs(Math.sin(f * 0.45 + i * 1.9 + random(`${semente}${i}`) * 6));
        const h = altura * fl;
        const dz = Math.sin(i * 2.3) * 0.18;
        return (
          <group key={i} position={[x, 0, z + dz]}>
            <mesh position={[0, h / 2, 0]}>
              <coneGeometry args={[0.28, h, 6]} />
              <meshBasicMaterial color="#ff5a1f" />
            </mesh>
            <mesh position={[0, h * 0.38, 0.05]}>
              <coneGeometry args={[0.16, h * 0.7, 6]} />
              <meshBasicMaterial color="#ffd23f" />
            </mesh>
          </group>
        );
      })}
      <pointLight position={[0, 1.2, z]} color="#ff7b2e" intensity={8 * altura} distance={9} />
    </group>
  );
};

const Fumaca: React.FC<{z: number; f: number; forca: number}> = ({z, f, forca}) => (
  <group>
    {Array.from({length: 22}, (_, i) => {
      const ciclo = ((f * 0.025 + random(`fc${i}`)) % 1);
      const x = (random(`fx${i}`) - 0.5) * 10 + Math.sin(f * 0.02 + i) * 0.3;
      return (
        <mesh key={i} position={[x, 0.8 + ciclo * 4.5, z - 0.6 - ciclo * 1.5]} scale={0.6 + ciclo * 1.4}>
          <sphereGeometry args={[0.6, 10, 8]} />
          <meshStandardMaterial color="#8f8f8f" transparent opacity={(1 - ciclo) * 0.4 * forca} depthWrite={false} />
        </mesh>
      );
    })}
  </group>
);

// seta de vento (corpo + ponta), apontando para −z (em direção ao incêndio)
const Seta: React.FC<{x: number; z: number; op: number; s: number}> = ({x, z, op, s}) => (
  <group position={[x, 1.9, z]} rotation={[-Math.PI / 2, 0, 0]} scale={s}>
    <mesh position={[0, 0.25, 0]}>
      <boxGeometry args={[0.14, 0.7, 0.04]} />
      <meshBasicMaterial color="#8af0ff" transparent opacity={op} />
    </mesh>
    <mesh position={[0, 0.75, 0]}>
      <coneGeometry args={[0.24, 0.4, 3]} />
      <meshBasicMaterial color="#8af0ff" transparent opacity={op} />
    </mesh>
  </group>
);

export const Contrafogo3D: React.FC<Props> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();

  // posições das frentes de fogo
  const tPuxa = eventos.puxa ?? Math.round(dur * 0.3);
  const tApaga = eventos.apagam ?? Math.round(dur * 0.75);
  const fogoZ = fase === 'ar'
    ? interpolate(f, [0, dur], [-5.4, -4.6], cl)
    : interpolate(f, [0, tApaga], [-4.6, ENCONTRO_Z], cl);
  const contraZ = fase === 'ar' ? ESTRADA_Z - 0.4
    : interpolate(f, [0, tPuxa, tApaga], [ESTRADA_Z - 0.4, ESTRADA_Z - 1.0, ENCONTRO_Z], cl);
  const alturaFogo = fase === 'ar' ? 1.5 : 1.5 * interpolate(f, [tApaga, tApaga + 18], [1, 0], cl);
  const alturaContra = fase === 'ar' ? 0 : interpolate(f, [0, 8], [0.25, 0.75], cl) * interpolate(f, [tApaga, tApaga + 18], [1, 0], cl);
  const fumacaForca = fase === 'encontro' ? 1 + interpolate(f, [tApaga, tApaga + 20], [0, 0.8], cl) : 1;

  // setas: aparecem em "puxa" e aceleram
  const tSetas = fase === 'ar' ? (eventos.puxa ?? 20) : 0;
  const setasOp = interpolate(f, [tSetas, tSetas + 8], [0, 0.95], cl) *
    (fase === 'encontro' ? interpolate(f, [tApaga - 4, tApaga + 6], [1, 0], cl) : 1);
  const vel = fase === 'ar' ? interpolate(f, [tSetas, dur], [0.06, 0.16], cl) : 0.13;

  // câmera: empurra devagar e gira um pouco (sensação de 3D)
  const ang = interpolate(f, [0, dur], fase === 'ar' ? [-0.12, 0.02] : [0.02, 0.16], cl);
  const dist = interpolate(f, [0, dur], fase === 'ar' ? [17.5, 16.0] : [16.0, 15.2], cl);
  const cam: [number, number, number] = [Math.sin(ang) * dist * 0.5, dist * 1.0, 1.2 + Math.cos(ang) * dist * 0.5];

  return (
    <ThreeCanvas width={width} height={height} style={{backgroundColor: '#a9cfe6'}}
      camera={{fov: 50, position: cam, near: 0.1, far: 80}}
      onCreated={({camera}) => camera.lookAt(0, 0, 0.2)}>
      <CameraOlha cam={cam} />
      <fog attach="fog" args={['#a9cfe6', 16, 34]} />
      <ambientLight intensity={0.75} />
      <directionalLight position={[-4, 10, 4]} intensity={1.6} />

      {/* chão, área queimada pelo incêndio e pelo contrafogo, estrada */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -1]}>
        <planeGeometry args={[14, 20]} />
        <meshStandardMaterial color="#5d8f3c" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, (fogoZ - 11) / 2]}>
        <planeGeometry args={[14, Math.max(fogoZ + 11, 0.01)]} />
        <meshStandardMaterial color="#231a14" />
      </mesh>
      {fase === 'encontro' && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.012, (contraZ + ESTRADA_Z - 0.4) / 2]}>
          <planeGeometry args={[14, Math.max(ESTRADA_Z - 0.4 - contraZ, 0.01)]} />
          <meshStandardMaterial color="#2b2119" />
        </mesh>
      )}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, ESTRADA_Z]}>
        <planeGeometry args={[14, 0.8]} />
        <meshStandardMaterial color="#a8865a" />
      </mesh>

      {/* árvores: queimadas viram tronco preto */}
      {ARVORES.map((a, i) => {
        const queimada = a.z < fogoZ + 0.15 || (fase === 'encontro' && a.z > contraZ - 0.15);
        return (
          <group key={i} position={[a.x, 0, a.z]} scale={a.s}>
            <mesh position={[0, 0.25, 0]}>
              <cylinderGeometry args={[0.07, 0.09, 0.5, 5]} />
              <meshStandardMaterial color={queimada ? '#1a1410' : '#6b4a2b'} />
            </mesh>
            {!queimada && (
              <mesh position={[0, 0.95, 0]}>
                <coneGeometry args={[0.42, 1.2, 7]} />
                <meshStandardMaterial color={a.c} flatShading />
              </mesh>
            )}
          </group>
        );
      })}

      <Chamas z={fogoZ} altura={alturaFogo} f={f} semente="m" />
      <Fumaca z={fogoZ} f={f} forca={fumacaForca} />
      {fase === 'encontro' && <Chamas z={contraZ} altura={alturaContra} f={f} semente="c" />}

      {/* setas de vento: do lado das casas em direção ao incêndio */}
      {setasOp > 0.01 && Array.from({length: 18}, (_, i) => {
        const x = -4.4 + (i % 6) * 1.75 + (Math.floor(i / 6) % 2) * 0.85;
        const faixa = 7.5;
        const z = 5.5 - (((f * vel + i * 0.43) % 1) * faixa);
        const op = setasOp * interpolate(z, [fogoZ + 0.3, fogoZ + 1.6, 4.6, 5.5], [0, 1, 1, 0], cl);
        return <Seta key={i} x={x} z={z} op={op} s={1.6} />;
      })}

      {/* brigadistas na estrada */}
      {[-1.2, 0, 1.2].map((x, i) => (
        <group key={i} position={[x, 0, ESTRADA_Z + 0.15]}>
          <mesh position={[0, 0.32, 0]}>
            <capsuleGeometry args={[0.12, 0.34, 4, 8]} />
            <meshStandardMaterial color="#f2c230" />
          </mesh>
          <mesh position={[0, 0.66, 0]}>
            <sphereGeometry args={[0.1, 10, 8]} />
            <meshStandardMaterial color="#d6322b" />
          </mesh>
        </group>
      ))}

      {/* casas protegidas */}
      {[-3.6, -1.2, 1.2, 3.6].map((x, i) => (
        <group key={i} position={[x, 0, 5.0 + (i % 2) * 0.5]}>
          <mesh position={[0, 0.35, 0]}>
            <boxGeometry args={[0.9, 0.7, 0.8]} />
            <meshStandardMaterial color="#efe3c8" />
          </mesh>
          <mesh position={[0, 0.9, 0]} rotation={[0, Math.PI / 4, 0]}>
            <coneGeometry args={[0.8, 0.5, 4]} />
            <meshStandardMaterial color="#b5442c" flatShading />
          </mesh>
        </group>
      ))}
    </ThreeCanvas>
  );
};

// mantém a câmera olhando para o centro da maquete a cada quadro
const CameraOlha: React.FC<{cam: [number, number, number]}> = ({cam}) => {
  const {camera} = useThree();
  camera.position.set(...cam);
  camera.lookAt(0, 0, 0.6);
  return null;
};
