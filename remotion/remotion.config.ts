import {Config} from '@remotion/cli/config';
// efeitos WebGL (zoom blur, aberração cromática) precisam de OpenGL no Chrome headless
Config.setChromiumOpenGlRenderer('swangle');  // WebGL por software (a nuvem não tem GPU)
