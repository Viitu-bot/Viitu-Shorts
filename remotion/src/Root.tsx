import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Short, Plano} from './Short';
import {Reabastece3D} from './animacoes/Reabastece3D';
import {Abrams3D} from './animacoes/Abrams3D';
import {Bola3D} from './animacoes/Bola3D';
import {Prensa3D} from './animacoes/Prensa3D';
import {Gude3D} from './animacoes/Gude3D';
import {Bulbo3D} from './animacoes/Bulbo3D';
import {Porta3D} from './animacoes/Porta3D';
import {Porca3D} from './animacoes/Porca3D';
import {Vertedouro3D} from './animacoes/Vertedouro3D';
import {Estrada3D} from './animacoes/Estrada3D';
import {BanheiroTrem3D} from './animacoes/BanheiroTrem3D';
import {Canhao3D} from './animacoes/Canhao3D';
import {Stuka3D} from './animacoes/Stuka3D';

// Teste3D: confere quadros soltos de uma animação sem montar o Short inteiro
// npx remotion still src/index.ts Teste3D x.png --frame=N --props='{"fase":"completo","dur":180,"eventos":{"tanque":60,"lanca":110}}'
const Teste3D: React.FC<{nome?: string; fase: string; dur: number; eventos: Record<string, number>; debug?: boolean}> = (p) =>
  p.nome === 'abrams3d' ? <Abrams3D {...p} /> : p.nome === 'bola3d' ? <Bola3D {...p} /> : p.nome === 'prensa3d' ? <Prensa3D {...p} /> : p.nome === 'gude3d' ? <Gude3D {...p} /> : p.nome === 'bulbo3d' ? <Bulbo3D {...p} /> : p.nome === 'porta3d' ? <Porta3D {...p} /> : p.nome === 'porca3d' ? <Porca3D {...p} /> : p.nome === 'vertedouro3d' ? <Vertedouro3D {...p} /> : p.nome === 'estrada3d' ? <Estrada3D {...p} /> : p.nome === 'banheiro3d' ? <BanheiroTrem3D {...p} /> : p.nome === 'canhao3d' ? <Canhao3D {...p} /> : p.nome === 'stuka3d' ? <Stuka3D {...p} /> : <Reabastece3D {...p} />;

export const RemotionRoot: React.FC = () => (
  <>
  <Composition id="Teste3D" component={Teste3D} width={1080} height={1920} fps={30} durationInFrames={300}
    defaultProps={{fase: 'completo', dur: 180, eventos: {tanque: 60, lanca: 110}}} />
  <Composition
    id="Short"
    component={Short}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={300}
    defaultProps={{plano: null as unknown as Plano}}
    calculateMetadata={async () => {
      const plano: Plano = await fetch(staticFile('plano.json')).then((r) => r.json());
      return {durationInFrames: plano.duracao_frames, fps: plano.fps, props: {plano}};
    }}
  />
  </>
);
