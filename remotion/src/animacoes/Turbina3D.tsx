import React from 'react';
import * as THREE from 'three';
import {interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';

// 3D do vd005 (pássaros x aviões). Fases:
//  "ar"     — turbina com GRADE na frente: setas de ar entram, travam na grade (ficam vermelhas)
//  "quebra" — pássaro bate na grade, ela se parte, os pedaços entram nas pás (faíscas, pás tortas, fumaça)
//  "teste"  — bancada de teste: canhão dispara uma ave direto nas pás; o motor segue girando
//  "bando"  — avião subindo, bando de gansos entra nas duas turbinas, motores apagam, pouso no rio
// Tudo é função do quadro. eventos = quadros relativos à cena.

type Props = {fase: 'ar' | 'quebra' | 'teste' | 'bando'; dur: number; eventos: Record<string, number>};
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const R = 1.0;               // raio da entrada da turbina
const FRENTE = 0.8;          // z da boca da turbina

const Camera: React.FC<{pos: [number, number, number]; alvo: [number, number, number]}> = ({pos, alvo}) => {
  const {camera} = useThree();
  camera.position.set(...pos);
  camera.lookAt(...alvo);
  return null;
};

// ---------- turbina (nacele + fan + cone) ----------
const Motor: React.FC<{rot: number; dano?: number; escala?: number; pos?: [number, number, number]; semente?: string}> = ({rot, dano = 0, escala = 1, pos = [0, 0, 0], semente = 'm'}) => {
  const n = 20;
  return (
    <group position={pos} scale={escala}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[R * 1.08, R, 1.7, 48, 1, true]} />
        <meshStandardMaterial color="#d7dce2" metalness={0.6} roughness={0.35} side={THREE.DoubleSide} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, -0.05]}>
        <cylinderGeometry args={[R * 0.98, R * 0.95, 1.6, 48, 1, true]} />
        <meshStandardMaterial color="#2a2e35" side={THREE.BackSide} />
      </mesh>
      {/* lábio da entrada */}
      <mesh position={[0, 0, 0.85]}>
        <torusGeometry args={[R * 1.03, 0.07, 12, 48]} />
        <meshStandardMaterial color="#eef1f4" metalness={0.5} roughness={0.3} />
      </mesh>
      <group position={[0, 0, 0.35]} rotation={[0, 0, rot]}>
        {Array.from({length: n}, (_, i) => {
          const a = (i / n) * Math.PI * 2;
          const torta = dano * (random(`${semente}${i}`) - 0.3) * 1.2;
          return (
            <group key={i} rotation={[0, 0, a]}>
              <mesh position={[0, 0.52, 0]} rotation={[0, 0.55 + torta, torta * 0.6]}>
                <boxGeometry args={[0.2, 0.86, 0.025]} />
                <meshStandardMaterial color={dano > 0.3 && random(`d${semente}${i}`) < dano ? '#5a4a40' : '#a7b0ba'} metalness={0.8} roughness={0.3} />
              </mesh>
            </group>
          );
        })}
      </group>
      <mesh position={[0, 0, 0.55]} rotation={[Math.PI / 2, 0, 0]}>
        <coneGeometry args={[0.26, 0.5, 32]} />
        <meshStandardMaterial color="#f2f2f2" metalness={0.3} roughness={0.4} />
      </mesh>
    </group>
  );
};

// ---------- grade na frente da turbina ----------
const Grade: React.FC<{quebra: number; f: number}> = ({quebra, f}) => {
  const barras: {x: number; y: number; vert: boolean; len: number; k: number}[] = [];
  const passos = [-0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8];
  passos.forEach((p, i) => {
    const len = 2 * Math.sqrt(Math.max(R * R - p * p, 0.01));
    barras.push({x: p, y: 0, vert: true, len, k: i});
    barras.push({x: 0, y: p, vert: false, len, k: i + 20});
  });
  return (
    <group position={[0, 0, FRENTE + 0.3]}>
      {barras.flatMap((b, i) => [0, 1].map((metade) => {
        // cada barra vira 2 pedaços que voam para dentro da turbina e giram
        const sx = (random(`gx${i}${metade}`) - 0.5) * 1.4;
        const sy = (random(`gy${i}${metade}`) - 0.5) * 1.4;
        const z = -quebra * (1.1 + random(`gz${i}${metade}`) * 0.6);
        const giro = quebra * (random(`gr${i}${metade}`) - 0.5) * 9;
        const off = (metade - 0.5) * b.len / 2;
        const px = b.vert ? b.x : off;
        const py = b.vert ? off : b.y;
        const contrai = 1 - quebra * 0.6;         // sugados para o centro
        return (
          <mesh key={`${i}${metade}`} position={[(px + sx * quebra * 0.4) * contrai, (py + sy * quebra * 0.4) * contrai, z]}
            rotation={[b.vert ? 0 : 0, 0, (b.vert ? 0 : Math.PI / 2) + giro]}>
            <boxGeometry args={[0.045, b.len / 2 - 0.02, 0.045]} />
            <meshStandardMaterial color={quebra > 0 ? '#c9ccd1' : '#b9bec5'} metalness={0.9} roughness={0.25}
              emissive={quebra > 0.05 ? '#ff6a00' : '#000000'} emissiveIntensity={quebra > 0.05 ? 0.35 * (1 - quebra) : 0} />
          </mesh>
        );
      }))}
    </group>
  );
};

// ---------- pássaro low-poly ----------
const Passaro: React.FC<{pos: [number, number, number]; f: number; escala?: number; cor?: string; rumo?: number}> = ({pos, f, escala = 1, cor = '#5b4a3c', rumo = 0}) => {
  const asa = Math.sin(f * 0.9) * 0.7;
  return (
    <group position={pos} scale={escala} rotation={[0, rumo, 0]}>
      <mesh scale={[0.16, 0.13, 0.42]}>
        <sphereGeometry args={[1, 10, 8]} />
        <meshStandardMaterial color={cor} flatShading />
      </mesh>
      <mesh position={[0, 0.06, 0.38]} scale={[0.09, 0.08, 0.11]}>
        <sphereGeometry args={[1, 8, 6]} />
        <meshStandardMaterial color="#222" flatShading />
      </mesh>
      {[-1, 1].map((l) => (
        <mesh key={l} position={[l * 0.3, 0.02, 0]} rotation={[0, 0, l * asa]}>
          <boxGeometry args={[0.55, 0.02, 0.22]} />
          <meshStandardMaterial color={cor} flatShading />
        </mesh>
      ))}
    </group>
  );
};

const Particulas: React.FC<{centro: [number, number, number]; t: number; n: number; cor: string; tam: number; espalha: number; semente: string; sobe?: number}> = ({centro, t, n, cor, tam, espalha, semente, sobe = 0}) => {
  if (t <= 0 || t >= 1) return null;
  return (
    <group>
      {Array.from({length: n}, (_, i) => {
        const dx = (random(`${semente}x${i}`) - 0.5) * espalha * t;
        const dy = (random(`${semente}y${i}`) - 0.5) * espalha * t + sobe * t;
        const dz = (random(`${semente}z${i}`) - 0.5) * espalha * t;
        return (
          <mesh key={i} position={[centro[0] + dx, centro[1] + dy, centro[2] + dz]} scale={tam * (1 - t * 0.5)}>
            <sphereGeometry args={[1, 6, 5]} />
            <meshBasicMaterial color={cor} transparent opacity={1 - t} />
          </mesh>
        );
      })}
    </group>
  );
};

const Fumaca: React.FC<{centro: [number, number, number]; f: number; forca: number; semente: string}> = ({centro, f, forca, semente}) => (
  <group>
    {forca > 0.01 && Array.from({length: 10}, (_, i) => {
      const c = (f * 0.03 + random(`${semente}${i}`)) % 1;
      return (
        <mesh key={i} position={[centro[0] + Math.sin(i * 2.1) * 0.3, centro[1] + c * 2.2, centro[2] - c * 1.5]} scale={0.25 + c * 0.9}>
          <sphereGeometry args={[1, 8, 6]} />
          <meshStandardMaterial color="#3d3d3d" transparent opacity={(1 - c) * 0.55 * forca} depthWrite={false} />
        </mesh>
      );
    })}
  </group>
);

const Seta: React.FC<{pos: [number, number, number]; cor: string; op: number}> = ({pos, cor, op}) => (
  <group position={pos} rotation={[-Math.PI / 2, 0, 0]}>
    <mesh position={[0, 0.2, 0]}>
      <cylinderGeometry args={[0.07, 0.07, 0.55, 8]} />
      <meshBasicMaterial color={cor} transparent opacity={op} />
    </mesh>
    <mesh position={[0, 0.5, 0]}>
      <coneGeometry args={[0.18, 0.32, 10]} />
      <meshBasicMaterial color={cor} transparent opacity={op} />
    </mesh>
  </group>
);

// ---------- avião comercial ----------
const Aviao: React.FC<{rot: number; dano: number}> = ({rot, dano}) => (
  <group>
    <mesh rotation={[Math.PI / 2, 0, 0]}>
      <capsuleGeometry args={[0.42, 4.2, 8, 20]} />
      <meshStandardMaterial color="#f4f6f8" metalness={0.2} roughness={0.5} />
    </mesh>
    {/* janelas */}
    <mesh position={[0.43, 0.08, 0]}>
      <boxGeometry args={[0.01, 0.1, 3.2]} />
      <meshBasicMaterial color="#26384f" />
    </mesh>
    <mesh position={[-0.43, 0.08, 0]}>
      <boxGeometry args={[0.01, 0.1, 3.2]} />
      <meshBasicMaterial color="#26384f" />
    </mesh>
    <mesh position={[0, -0.1, 0.2]} rotation={[0, 0, 0]}>
      <boxGeometry args={[5.6, 0.07, 1.1]} />
      <meshStandardMaterial color="#e3e7ec" />
    </mesh>
    <mesh position={[0, 0.65, -2.3]}>
      <boxGeometry args={[0.07, 1.0, 0.8]} />
      <meshStandardMaterial color="#1d5fa8" />
    </mesh>
    <mesh position={[0, 0.15, -2.35]}>
      <boxGeometry args={[1.8, 0.05, 0.55]} />
      <meshStandardMaterial color="#e3e7ec" />
    </mesh>
    {[-1.25, 1.25].map((x, i) => (
      <group key={i}>
        <Motor rot={rot} dano={dano} escala={0.24} pos={[x, -0.42, 0.75]} semente={`a${i}`} />
        <Fumaca centro={[x, -0.3, 0.2]} f={rot * 3} forca={dano} semente={`f${i}`} />
      </group>
    ))}
  </group>
);

export const Turbina3D: React.FC<Props> = ({fase, dur, eventos}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const fundo = fase === 'bando' ? '#9fc8ea' : fase === 'teste' ? '#2b3038' : '#bcd6ec';

  let conteudo: React.ReactNode = null;
  let cam: [number, number, number] = [3.2, 1.2, 5.2];
  let alvo: [number, number, number] = [0, 0, 0.5];

  if (fase === 'ar') {
    const tTrava = eventos.travaria ?? Math.round(dur * 0.7);
    const rotVel = interpolate(f, [tTrava, tTrava + 20], [0.45, 0.2], cl);
    const rot = f * 0.45 - Math.max(0, f - tTrava) * (0.45 - rotVel);
    cam = [interpolate(f, [0, dur], [5.6, 4.6], cl), interpolate(f, [0, dur], [1.4, 1.0], cl), interpolate(f, [0, dur], [3.4, 3.0], cl)];
    alvo = [0, 0, 1.3];
    conteudo = (
      <>
        <Motor rot={rot} />
        <Grade quebra={0} f={f} />
        {Array.from({length: 22}, (_, i) => {
          const ang = random(`sa${i}`) * Math.PI * 2;
          const rr = Math.sqrt(random(`sr${i}`)) * 0.85;
          const x = Math.cos(ang) * rr;
          const y = Math.sin(ang) * rr;
          const ciclo = (f * 0.035 + random(`sc${i}`)) % 1;
          let z = 5.2 - ciclo * 4.2;                          // da frente até a boca
          const travado = f > tTrava;
          if (travado) z = Math.max(z, FRENTE + 0.55 + random(`st${i}`) * 0.6);  // empilha na grade
          const cor = travado && z < FRENTE + 1.3 ? '#ff3b30' : '#0aa6ff';
          const op = interpolate(z, [FRENTE + 0.3, FRENTE + 0.7, 4.6, 5.2], [0, 1, 1, 0], cl);
          return <Seta key={i} pos={[x, y, z]} cor={cor} op={op} />;
        })}
      </>
    );
  } else if (fase === 'quebra') {
    const tBate = eventos.batesse ?? 30;
    const tMetal = eventos.metal ?? 100;
    const zPassaro = interpolate(f, [0, tBate], [7, FRENTE + 0.35], cl);
    const quebra = interpolate(f, [tBate, tBate + 18], [0, 1], cl);
    const dano = interpolate(f, [tBate + 14, tMetal], [0, 1], cl);
    const vel = interpolate(f, [tBate + 14, dur], [0.4, 0.12], cl);
    let rot = 0;
    for (let k = 0; k < f; k++) rot += interpolate(k, [tBate + 14, dur], [0.4, 0.12], cl);
    const tremor = dano > 0 ? Math.sin(f * 2.3) * 0.03 * dano : 0;
    cam = [interpolate(f, [0, dur], [2.8, 1.6], cl) + tremor, interpolate(f, [0, dur], [1.0, 0.6], cl), interpolate(f, [0, dur], [5.4, 3.4], cl)];
    conteudo = (
      <>
        <Motor rot={rot} dano={dano} />
        <Grade quebra={quebra} f={f} />
        {f < tBate && <Passaro pos={[0.15, 0.1 + Math.sin(f * 0.2) * 0.1, zPassaro]} f={f} escala={1.1} rumo={Math.PI} />}
        <Particulas centro={[0.1, 0.1, FRENTE + 0.4]} t={(f - tBate) / 22} n={18} cor="#efe6d8" tam={0.05} espalha={2.2} semente="pena" />
        <Particulas centro={[0, 0, FRENTE - 0.2]} t={(f - tBate - 12) / 16} n={22} cor="#ffcc33" tam={0.035} espalha={2.4} semente="faisca" />
        <Particulas centro={[0, 0, FRENTE - 0.2]} t={(f - tMetal + 20) / 18} n={16} cor="#ff7a1a" tam={0.03} espalha={2.0} semente="faisca2" />
        <Fumaca centro={[0, 0.2, 0.3]} f={f} forca={dano} semente="fq" />
        <pointLight position={[0, 0, 1.2]} color="#ff8a3d" intensity={quebra > 0 && quebra < 1 ? 6 : 0} distance={4} />
        {vel < 0 && null}
      </>
    );
  } else if (fase === 'teste') {
    const tTiro = eventos.disparados ?? Math.round(dur * 0.6);
    const rot = f * 0.45;
    const ini = new THREE.Vector3(-1.9, 0.05, 3.4);
    const fim = new THREE.Vector3(0, 0, FRENTE + 0.2);
    const tt = interpolate(f, [tTiro, tTiro + 7], [0, 1], cl);
    const p = ini.clone().lerp(fim, tt);
    const dir = fim.clone().sub(ini);
    const angY = Math.atan2(dir.x, dir.z);
    cam = [interpolate(f, [0, dur], [-0.4, -0.2], cl), interpolate(f, [0, dur], [2.6, 2.2], cl), interpolate(f, [0, dur], [11.0, 9.8], cl)];
    alvo = [-1.0, -0.2, 2.0];
    conteudo = (
      <>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.35, 0]}>
          <planeGeometry args={[30, 30]} />
          <meshStandardMaterial color="#5b6168" />
        </mesh>
        <mesh position={[0, 2, -6]}>
          <planeGeometry args={[30, 10]} />
          <meshStandardMaterial color="#3a4048" />
        </mesh>
        {/* bancada */}
        {[-0.7, 0.7].map((x) => (
          <mesh key={x} position={[x, -1.15, 0]}>
            <boxGeometry args={[0.15, 0.4, 1.4]} />
            <meshStandardMaterial color="#1f5fbf" />
          </mesh>
        ))}
        <Motor rot={rot} />
        {/* canhão de aves */}
        <group position={[ini.x, ini.y, ini.z]} rotation={[0, angY, 0]}>
          <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, -1.4]}>
            <cylinderGeometry args={[0.16, 0.18, 3.2, 20]} />
            <meshStandardMaterial color="#454b52" metalness={0.7} roughness={0.35} />
          </mesh>
          <mesh position={[0, -0.55, -2.4]}>
            <boxGeometry args={[0.3, 0.9, 0.3]} />
            <meshStandardMaterial color="#2c3036" />
          </mesh>
        </group>
        {tt > 0 && tt < 1 && <Passaro pos={[p.x, p.y, p.z]} f={0} escala={0.7} cor="#e9e0d0" rumo={angY} />}
        <Particulas centro={[0, 0, FRENTE + 0.2]} t={(f - tTiro - 7) / 24} n={30} cor="#f3ecdf" tam={0.05} espalha={2.6} semente="tpena" />
        <pointLight position={[2, 3, 3]} intensity={30} distance={14} color="#ffffff" />
      </>
    );
  } else {
    // bando: o avião sobe, gansos entram nas duas turbinas, motores apagam, planeia e pousa no rio
    const tBate = eventos.turbinas ?? Math.round(dur * 0.4);
    const tPousa = eventos.pousou ?? Math.round(dur * 0.75);
    const tVivos = eventos.todos ?? Math.round(dur * 0.88);
    const dano = interpolate(f, [tBate, tBate + 10], [0, 1], cl);
    let rot = 0;
    for (let k = 0; k < f; k++) rot += interpolate(k, [tBate, tBate + 25], [0.6, 0], cl);
    const alt = f < tBate ? interpolate(f, [0, tBate], [2.6, 3.4], cl) : interpolate(f, [tBate, tPousa], [3.4, 0.35], cl);
    const pitch = f < tBate ? -0.12 : interpolate(f, [tBate, tPousa - 8, tPousa], [-0.05, 0.08, -0.12], cl);
    const velZ = f < tPousa ? 0.09 : interpolate(f, [tPousa, dur], [0.09, 0.01], cl);
    let z = 0;
    for (let k = 0; k < f; k++) z -= (k < tPousa ? 0.09 : interpolate(k, [tPousa, dur], [0.09, 0.01], cl));
    const plano: [number, number, number] = [0, alt, z];
    cam = [plano[0] + 5.5, plano[1] + 2.2, plano[2] + 9.5];
    alvo = [plano[0] - 0.4, plano[1] - 0.2, plano[2] - 1.0];
    const splash = (f - tPousa) / 26;
    conteudo = (
      <>
        <fog attach="fog" args={['#9fc8ea', 18, 60]} />
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, z - 20]}>
          <planeGeometry args={[14, 140]} />
          <meshStandardMaterial color="#3e6f96" metalness={0.3} roughness={0.25} />
        </mesh>
        {[-1, 1].map((l) => (
          <group key={l}>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[l * 17, -0.01, z - 20]}>
              <planeGeometry args={[20, 140]} />
              <meshStandardMaterial color="#6f7d64" />
            </mesh>
            {Array.from({length: 40}, (_, i) => {
              const bz = Math.floor(z / 3) * 3 - i * 3 + 30;
              const h = 1.5 + random(`pr${l}${Math.round(bz)}`) * 6;
              return (
                <mesh key={i} position={[l * (8.5 + random(`px${l}${Math.round(bz)}`) * 6), h / 2, bz]}>
                  <boxGeometry args={[1.6, h, 1.6]} />
                  <meshStandardMaterial color={['#8d97a3', '#a7b0b9', '#6e7884'][Math.abs(Math.round(bz)) % 3]} />
                </mesh>
              );
            })}
          </group>
        ))}
        <group position={plano} rotation={[pitch, 0, 0]}>
          <Aviao rot={rot} dano={dano} />
          {f >= tVivos && [-2.2, -1.7, -1.2, 1.2, 1.7, 2.2].map((x, i) => (
            <mesh key={i} position={[x, 0.12, 0.2 + (i % 2) * 0.25]} scale={interpolate(f, [tVivos + i * 2, tVivos + i * 2 + 6], [0, 1], cl)}>
              <capsuleGeometry args={[0.06, 0.16, 4, 8]} />
              <meshStandardMaterial color="#ff8a1f" />
            </mesh>
          ))}
        </group>
        {/* bando em V vindo de frente, na altura do avião */}
        {f < tBate + 4 && Array.from({length: 13}, (_, i) => {
          const fila = Math.ceil(i / 2);
          const lado = i === 0 ? 0 : (i % 2 ? -1 : 1);
          const prog = interpolate(f, [0, tBate], [0, 1], cl);
          const gz = z - 2.2 + 0.75 - (1 - prog) * 14 + fila * 0.5;
          const alvoX = i % 2 ? -1.25 : 1.25;
          const gx = interpolate(prog, [0, 1], [lado * fila * 0.45, alvoX + lado * 0.08], cl);
          const gy = alt - 0.42 + (1 - prog) * 0.6 + Math.sin(f * 0.3 + i) * 0.05;
          return <Passaro key={i} pos={[gx, gy, gz]} f={f + i * 3} escala={0.45} cor="#3b3229" />;
        })}
        <Particulas centro={[-1.25, alt - 0.42, z + 0.75]} t={(f - tBate) / 20} n={14} cor="#ffb347" tam={0.08} espalha={1.4} semente="b1" />
        <Particulas centro={[1.25, alt - 0.42, z + 0.75]} t={(f - tBate) / 20} n={14} cor="#ffb347" tam={0.08} espalha={1.4} semente="b2" />
        <Particulas centro={[0, 0.1, z]} t={splash} n={40} cor="#e8f4ff" tam={0.12} espalha={5} semente="sp" sobe={1.4} />
        {velZ < 0 && null}
      </>
    );
  }

  // CORTE DE CÂMERA dentro da cena (ritmo de ~1,5–3 s por plano, como nos canais do nicho)
  const tCorte = fase === 'ar' ? (eventos.travaria ?? 999) : fase === 'quebra' ? (eventos.metal ?? 999) - 25
    : fase === 'teste' ? (eventos.disparados ?? 999) + 3 : (eventos.pousou ?? 999) - 12;
  if (f >= tCorte) {
    if (fase === 'ar') { cam = [2.6, 0.9, 4.2]; alvo = [0, 0, 1.0]; }
    else if (fase === 'quebra') { cam = [0.25, 0.15, 2.3 + Math.sin(f * 2.3) * 0.02]; alvo = [0, 0, 0.3]; }
    else if (fase === 'teste') { cam = [0.9, 0.3, 2.6]; alvo = [0, 0, 0.6]; }
    else { cam = [alvo[0] - 6.5, alvo[1] + 1.6, alvo[2] + 5]; }
  }
  return (
    <ThreeCanvas width={width} height={height} style={{backgroundColor: fundo}} camera={{fov: 50, position: cam, near: 0.1, far: 200}}>
      <Camera pos={cam} alvo={alvo} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[-4, 8, 6]} intensity={1.8} />
      <directionalLight position={[5, 2, -3]} intensity={0.5} color="#bcd6ff" />
      {conteudo}
    </ThreeCanvas>
  );
};
