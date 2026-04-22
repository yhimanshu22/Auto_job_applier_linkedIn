const pc = require('picocolors');

const logger = {
  electron: (message) => {
    console.log(`${pc.cyan('[Electron]')} ${message}`);
  },
  electronError: (message) => {
    console.error(`${pc.red(pc.bold('[Electron ERROR]'))} ${message}`);
  },
  electronWarn: (message) => {
    console.warn(`${pc.yellow('[Electron WARN]')} ${message}`);
  },
  backend: (message) => {
    console.log(`${pc.green('[Backend INFO]')} ${message}`);
  },
  backendError: (message) => {
    console.error(`${pc.red('[Backend ERROR]')} ${message}`);
  },
  frontend: (message) => {
    console.log(`${pc.blue('[Frontend INFO]')} ${message}`);
  },
  frontendError: (message) => {
    console.error(`${pc.red('[Frontend ERROR]')} ${message}`);
  },
  frontendWarn: (message) => {
    console.warn(`${pc.yellow('[Frontend WARN]')} ${message}`);
  },
  log: (prefix, message, color = 'white') => {
    const coloredPrefix = pc[color] ? pc[color](prefix) : prefix;
    console.log(`${coloredPrefix} ${message}`);
  }
};

module.exports = logger;
