const log = require('electron-log');
const pc = require('picocolors');

// Configure electron-log
log.transports.file.level = 'info';
log.transports.file.maxSize = 5 * 1024 * 1024; // 5MB
log.transports.console.level = 'debug';

// Clean noisy characters (like Windows UTF-8 artifacts)
function cleanMessage(msg) {
  if (typeof msg !== 'string') return msg;
  // Remove strange characters like Γû▓ and Γ£ô
  return msg.replace(/[^\x20-\x7E\n]/g, '').trim();
}

const logger = {
  electron: (message) => {
    const clean = cleanMessage(message);
    log.info(`[Electron] ${clean}`);
    console.log(`${pc.cyan('[Electron]')} ${clean}`);
  },
  electronError: (message) => {
    const clean = cleanMessage(message);
    log.error(`[Electron ERROR] ${clean}`);
    console.error(`${pc.red(pc.bold('[Electron ERROR]'))} ${clean}`);
  },
  electronWarn: (message) => {
    const clean = cleanMessage(message);
    log.warn(`[Electron WARN] ${clean}`);
    console.warn(`${pc.yellow('[Electron WARN]')} ${clean}`);
  },
  backend: (message) => {
    const clean = cleanMessage(message);
    log.info(`[Backend] ${clean}`);
    console.log(`${pc.green('[Backend INFO]')} ${clean}`);
  },
  backendError: (message) => {
    const clean = cleanMessage(message);
    log.error(`[Backend ERROR] ${clean}`);
    console.error(`${pc.red('[Backend ERROR]')} ${clean}`);
  },
  frontend: (message) => {
    const clean = cleanMessage(message);
    log.info(`[Frontend] ${clean}`);
    console.log(`${pc.blue('[Frontend INFO]')} ${clean}`);
  },
  frontendError: (message) => {
    const clean = cleanMessage(message);
    log.error(`[Frontend ERROR] ${clean}`);
    console.error(`${pc.red('[Frontend ERROR]')} ${clean}`);
  },
  frontendWarn: (message) => {
    const clean = cleanMessage(message);
    log.warn(`[Frontend WARN] ${clean}`);
    console.warn(`${pc.yellow('[Frontend WARN]')} ${clean}`);
  },
  log: (prefix, message, color = 'white') => {
    const clean = cleanMessage(message);
    log.info(`[${prefix}] ${clean}`);
    const coloredPrefix = pc[color] ? pc[color](prefix) : prefix;
    console.log(`${coloredPrefix} ${clean}`);
  }
};

module.exports = logger;
