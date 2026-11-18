import React, {useEffect, useMemo, useState} from 'react';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as THREE from 'three';
import {continueRender, delayRender, staticFile} from 'remotion';
import {useThree} from '@react-three/fiber';

// Peças comuns das animações 3D (padrão desde o vd007): texturas que só liberam o quadro depois de carregar,
// céu HDRI real (Poly Haven, CC0) como iluminação e reflexo, câmera por quadro.
export type Tex = Record<string, THREE.Texture>;

export const useTexturas = (nomes: string[]) => {
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
      if (n.endsWith('_hdri')) t.mapping = THREE.EquirectangularReflectionMapping;
      o[n] = t;
    });
    return o;
  }, []);
  return {tex, erro, pronto: ok, h};
};

// TODO ThreeCanvas que usa useTexturas precisa disto (senão o render trava por timeout)
export const Liberar: React.FC<{pronto: boolean; h: number}> = ({pronto, h}) => {
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

export const Camera: React.FC<{pos: [number, number, number]; alvo: [number, number, number]}> = ({pos, alvo}) => {
  const {camera} = useThree();
  camera.position.set(...pos);
  camera.lookAt(...alvo);
  return null;
};

export const Ambiente: React.FC<{tex?: THREE.Texture; fundo: boolean; forca?: number}> = ({tex, fundo, forca = 1}) => {
  const {scene} = useThree();
  useEffect(() => {
    if (!tex) return;
    scene.environment = tex;
    (scene as any).environmentIntensity = forca;
    if (fundo) scene.background = tex;
  }, [tex, fundo, forca]);
  return null;
};

export const rep = (t: THREE.Texture | undefined, x: number, y: number, ox = 0) => {
  if (t) { t.repeat.set(x, y); t.offset.x = ox; }
  return t;
};

// MODELO PRONTO (GLB do Sketchfab/Poly Haven): carrega uma vez, segura o quadro até chegar, devolve a cena
// já centrada e com o comprimento maior em metros reais. Use <primitive object={m.cena} /> (clone se for usar 2x).
export const useModelo = (arquivo: string) => {
  const [cena, setCena] = useState<THREE.Group | null>(null);
  const [h] = useState(() => delayRender(`modelo ${arquivo}`));
  useEffect(() => {
    new GLTFLoader().load(staticFile(`modelos/${arquivo}`), (g) => {
      const raiz = new THREE.Group();
      raiz.add(g.scene);
      g.scene.updateMatrixWorld(true);
      const caixa = new THREE.Box3().setFromObject(g.scene);
      const centro = caixa.getCenter(new THREE.Vector3());
      g.scene.position.sub(centro);
      raiz.userData.tamanho = caixa.getSize(new THREE.Vector3());
      setCena(raiz);
      continueRender(h);
    }, undefined, (e) => { console.error(e); continueRender(h); });
  }, []);
  return cena;
};
