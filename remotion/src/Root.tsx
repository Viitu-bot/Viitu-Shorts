import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Short, Plano} from './Short';

export const RemotionRoot: React.FC = () => (
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
);
