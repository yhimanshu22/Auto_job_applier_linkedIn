const { app, BrowserWindow, ipcMain, globalShortcut, shell, session } = require('electron');
const path = require('path');
const fs = require('fs');
const { autoUpdater } = require('electron-updater');
const { spawn, spawnSync } = require('child_process');
const http = require('http');
const logger = require('./logger');

function resolveAppIcon() {
  const candidates = [
    path.join(__dirname, 'app-icon.png'),
    path.join(__dirname, 'logo.png'),
    path.join(__dirname, 'icon.ico'),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return path.join(__dirname, 'app-icon.png');
}

const APP_ICON = resolveAppIcon();

// ==========================================
// 1. CONSTANTS & CONFIG
// ==========================================
const isDev = !app.isPackaged || process.argv.includes('--dev');
const FRONTEND_HOST = 'localhost';
const FRONTEND_PORT = 3000;
const FRONTEND_URL = `http://${FRONTEND_HOST}:${FRONTEND_PORT}`;
const APP_URL = `${FRONTEND_URL}/login`;

const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = 8000;
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
const BACKEND_HEALTH_URL = `${BACKEND_URL}/api/health`; // Using /api/health instead of /api/bot/status for faster check

const MAX_RESTARTS = 5;
/** Max attempts × STARTUP_POLL_MS ≈ worst-case wait per service (here ~60s). */
const STARTUP_TIMEOUT_RETRIES = 120;
const STARTUP_POLL_MS = 500;

// Global State
let mainWindow = null;
let splashWindow = null;
let backendProcess = null;
let frontendProcess = null;
let backendRestartCount = 0;
let frontendRestartCount = 0;
let isShuttingDown = false;

// ==========================================
// 2. PATH RESOLUTION
// ==========================================
const getBackendDir = () => app.isPackaged 
  ? path.join(process.resourcesPath, 'backend')
  : path.resolve(__dirname, '..', 'backend');

const getFrontendDir = () => app.isPackaged
  ? path.join(process.resourcesPath, 'frontend_standalone')
  : path.resolve(__dirname, '..', 'frontend');

/** Writable DB/logs/uploads/chrome profiles (Program Files install is not writable). */
function getPackagedBackendUserData() {
  if (!app.isPackaged) return '';
  const dir = path.join(app.getPath('userData'), 'backend-runtime');
  try {
    fs.mkdirSync(dir, { recursive: true });
  } catch (err) {
    logger.electronError(`Could not create backend userData dir: ${err.message}`);
  }
  return dir;
}

/**
 * Dev-only: resolve Python for the backend. Production uses bundled server.exe (never calls this).
 *
 * Order: LINKDAPPLY_PYTHON if set and exists → repo .venv → backend/.venv → null (caller uses PATH python).
 */
function getDevPythonExe() {
  const fromEnv = process.env.LINKDAPPLY_PYTHON?.trim();
  if (fromEnv) {
    const abs = path.isAbsolute(fromEnv) ? fromEnv : path.resolve(fromEnv);
    if (fs.existsSync(abs)) return abs;
  }
  const repoRoot = path.resolve(__dirname, '..');
  const win = process.platform === 'win32';
  const candidates = win
    ? [
        path.join(repoRoot, '.venv', 'Scripts', 'python.exe'),
        path.join(repoRoot, 'backend', '.venv', 'Scripts', 'python.exe'),
      ]
    : [
        path.join(repoRoot, '.venv', 'bin', 'python'),
        path.join(repoRoot, 'backend', '.venv', 'bin', 'python'),
      ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return null;
}

// ==========================================
// 3. UTILITY FUNCTIONS
// ==========================================
function clearPort(port) {
  if (process.platform !== 'win32') return;
  try {
    const netstat = spawnSync('netstat', ['-ano'], { shell: false });
    const lines = netstat.stdout.toString().split('\n');
    lines.forEach(line => {
      if (line.includes(`:${port}`) && line.includes('LISTENING')) {
        const parts = line.trim().split(/\s+/);
        const pid = parts[parts.length - 1];
        if (pid && !isNaN(pid) && pid !== '0') {
           logger.electron(`Forcefully clearing port ${port} (PID: ${pid})`);
           spawnSync('taskkill', ['/F', '/T', '/PID', pid], { shell: false });
        }
      }
    });
  } catch (err) {
    logger.electronError(`Error clearing port ${port}: ${err.message}`);
  }
}

function stopProcess(proc, name) {
  if (proc && !proc.killed) {
    logger.electron(`Stopping ${name}...`);
    try {
      if (process.platform === 'win32') {
        spawnSync('taskkill', ['/F', '/T', '/PID', proc.pid.toString()], { shell: false });
      } else {
        proc.kill('SIGTERM');
      }
    } catch (e) {
      logger.electronError(`Failed to stop ${name}: ${e.message}`);
    }
  }
}

// Polling health check
async function waitForUrl(url, retries = 60, delay = STARTUP_POLL_MS) {
  for (let i = 1; i <= retries; i++) {
    if (isShuttingDown) return;
    try {
      const res = await fetch(url);
      if (res.ok || res.status < 500) {
        logger.electron(`Ready: ${url}`);
        return true;
      }
    } catch (err) {
      // Ignore
    }
    logger.electron(`Waiting for ${url} (${i}/${retries})...`);
    await new Promise((resolve) => setTimeout(resolve, delay));
  }
  throw new Error(`Timeout waiting for ${url}`);
}

// ==========================================
// 4. PROCESS STARTUP
// ==========================================
function startBackend() {
  if (backendProcess && !backendProcess.killed) return;
  clearPort(BACKEND_PORT);
  
  try {
    const backendDir = getBackendDir();
    const serverPath = path.join(backendDir, 'server.py');
    const packagedExe = path.join(backendDir, 'server.exe');
    const backendUserData = getPackagedBackendUserData();

    if (app.isPackaged) {
      if (!fs.existsSync(packagedExe)) {
        logger.electronError(`Bundled backend missing: ${packagedExe}`);
        if (splashWindow && !splashWindow.isDestroyed()) {
          splashWindow.webContents.send('backend-error', 'Backend executable not found. Reinstall LinkdApply.');
        }
      }
      const internalDir = path.join(backendDir, '_internal');
      if (!fs.existsSync(internalDir)) {
        logger.electronError(`Bundled backend incomplete (expected _internal): ${internalDir}`);
        if (splashWindow && !splashWindow.isDestroyed()) {
          splashWindow.webContents.send('backend-error', 'Backend bundle is incomplete. Reinstall LinkdApply.');
        }
      }
      if (backendUserData) {
        logger.electron(`Backend writable data: ${backendUserData}`);
      }
    }

    let spawnCommand;
    let spawnArgs;

    if (app.isPackaged && fs.existsSync(packagedExe)) {
      spawnCommand = packagedExe;
      spawnArgs = [];
    } else if (!app.isPackaged) {
      const venvPython = getDevPythonExe();
      if (venvPython) {
        spawnCommand = venvPython;
        spawnArgs = [serverPath];
        logger.electron(`Backend using project venv: ${venvPython}`);
      } else {
        spawnCommand = 'python';
        spawnArgs = [serverPath];
        logger.electronWarn(
          'No .venv found (repo root or backend). Install deps: cd backend && uv sync — using python on PATH.'
        );
      }
    } else {
      spawnCommand = 'python';
      spawnArgs = [serverPath];
    }

    logger.electron(`Starting backend process...`);
    
    const backendOpts = {
      cwd: backendDir,
      shell: false,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        ...(backendUserData ? { LINKDAPPLY_USER_DATA: backendUserData } : {}),
      },
    };
    if (process.platform === 'win32') backendOpts.windowsHide = true;
    backendProcess = spawn(spawnCommand, spawnArgs, backendOpts);

    backendProcess.stdout.on('data', (d) => logger.backend(d.toString()));
    
    // Fix 5: Filter backend stderr for actual errors
    backendProcess.stderr.on('data', (d) => {
      const text = d.toString();
      if (text.includes("ERROR") || text.includes("Traceback") || text.includes("Exception")) {
        logger.backendError(text);
      } else {
        logger.backend(text);
      }
    });

    backendProcess.on('exit', (code) => {
      logger.electron(`Backend exited with code ${code}`);
      if (!isShuttingDown && backendRestartCount < MAX_RESTARTS) {
        backendRestartCount++;
        logger.electron(`Restarting backend (${backendRestartCount}/${MAX_RESTARTS})...`);
        setTimeout(startBackend, 3000);
      }
    });

    backendProcess.on('error', (err) => {
      logger.electronError(`Backend spawn error: ${err.message}`);
      if (splashWindow) splashWindow.webContents.send('backend-error', `Backend failed: ${err.message}`);
    });
  } catch (err) {
    logger.electronError(`Critical startBackend failure: ${err.message}`);
  }
}

function startFrontend() {
  if (frontendProcess && !frontendProcess.killed) return;
  clearPort(FRONTEND_PORT);
  
  try {
    let spawnCommand, spawnArgs, cwd;

    if (app.isPackaged) {
      cwd = getFrontendDir();
      spawnCommand = path.join(process.resourcesPath, 'node.exe');
      spawnArgs = ['server.js'];
      
      if (!fs.existsSync(spawnCommand)) {
        logger.electronWarn('Bundled node.exe not found, falling back to system node');
        spawnCommand = 'node';
      }
    } else {
      cwd = getFrontendDir();
      spawnCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';
      spawnArgs = ['run', isDev ? 'dev' : 'start'];
    }

    logger.electron(`Starting frontend process (${spawnCommand} ${spawnArgs.join(' ')})...`);
    
    // Standalone Next binds using HOSTNAME; 127.0.0.1 matches APP_URL / health checks on Windows.
    const env = {
      ...process.env,
      NEXT_TELEMETRY_DISABLED: "1",
      PORT: FRONTEND_PORT.toString(),
      ...(app.isPackaged ? { HOSTNAME: "127.0.0.1" } : {}),
    };
    
    const frontendOpts = { cwd: cwd, shell: false, env: env };
    if (process.platform === 'win32') frontendOpts.windowsHide = true;
    frontendProcess = spawn(spawnCommand, spawnArgs, frontendOpts);

    frontendProcess.stdout.on('data', (d) => logger.frontend(d.toString()));
    frontendProcess.stderr.on('data', (d) => {
      const text = d.toString();
      // Next.js logs some warnings to stderr, only treat actual errors as errors
      if (text.includes("Error") || text.includes("FAIL")) {
        logger.frontendError(text);
      } else {
        logger.frontend(text);
      }
    });

    frontendProcess.on('exit', (code) => {
      logger.electron(`Frontend exited with code ${code}`);
      if (!isShuttingDown && frontendRestartCount < MAX_RESTARTS) {
        frontendRestartCount++;
        logger.electron(`Restarting frontend (${frontendRestartCount}/${MAX_RESTARTS})...`);
        setTimeout(startFrontend, 5000);
      }
    });
  } catch (err) {
    logger.electronError(`Critical startFrontend failure: ${err.message}`);
  }
}

// ==========================================
// 5. WINDOW MANAGEMENT
// ==========================================
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 600,
    height: 400,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      enableRemoteModule: false,
      webSecurity: true,
    },
    icon: APP_ICON,
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  
  // Fix 3: Environment-aware CSP
  const devCsp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:3000",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self' http://localhost:3000 ws://localhost:3000 http://127.0.0.1:8000",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
  ].join("; ");

  const prodCsp = [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self' http://127.0.0.1:8000",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
  ].join("; ");

  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [isDev ? devCsp : prodCsp]
      }
    });
  });
}

async function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1100,
    minHeight: 720,
    show: false,
    frame: isDev,
    backgroundColor: '#0f172a', // Dark theme matching slate-900
    autoHideMenuBar: true,
    resizable: true,
    minimizable: true,
    maximizable: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      enableRemoteModule: false,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js'),
      additionalArguments: [isDev ? '--is-dev' : ''],
    },
    icon: APP_ICON,
    title: 'LinkdApply',
  });

  mainWindow.removeMenu();

  // Fix 1: Wait for BOTH backend and frontend
  try {
    logger.electron('Waiting for services to be ready...');
    await waitForUrl(BACKEND_HEALTH_URL, STARTUP_TIMEOUT_RETRIES);
    await waitForUrl(APP_URL, STARTUP_TIMEOUT_RETRIES);

    if (!isShuttingDown && mainWindow) {
      logger.electron('Services ready. Loading app...');
      mainWindow.loadURL(APP_URL);
    }
  } catch (err) {
    logger.electronError(`Startup failed: ${err.message}`);
    if (splashWindow) {
      const logPath = path.join(app.getPath('userData'), 'logs', 'main.log');
      splashWindow.webContents.send('backend-error', `Failed to connect to services. Check logs at: ${logPath}`);
    }
  }

  mainWindow.webContents.on('did-finish-load', () => {
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  // Log pipe
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    const levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
    const label = levels[level] || 'LOG';
    const msg = `${message} (${path.basename(sourceId)}:${line})`;
    if (label === 'ERROR') logger.frontendError(msg);
    else if (label === 'WARN') logger.frontendWarn(msg);
    else logger.frontend(msg);
  });

  // Security: Prevent unauthorized external navigation
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsedUrl = new URL(url);
      const allowedHostname = 'accounts.google.com';
      const appOrigin = new URL(APP_URL).origin;

      if (parsedUrl.origin === appOrigin || parsedUrl.hostname === allowedHostname) {
        return { action: 'allow' };
      }
      logger.electronWarn(`Blocked unauthorized window: ${url}`);
    } catch (err) {
      logger.electronError(`Invalid URL in window-open-handler: ${url}`);
    }
    return { action: 'deny' };
  });

  // Security: Block navigation completely
  mainWindow.webContents.on('will-navigate', (e, url) => {
    try {
      const parsedUrl = new URL(url);
      const appOrigin = new URL(APP_URL).origin;
      if (parsedUrl.origin !== appOrigin && parsedUrl.hostname !== 'accounts.google.com') {
        logger.electronWarn(`Blocked unauthorized navigation attempt to: ${url}`);
        e.preventDefault();
      }
    } catch (err) {
      logger.electronError(`Invalid URL in will-navigate: ${url}`);
      e.preventDefault();
    }
  });

  if (!isDev) {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools();
    });
  }

  mainWindow.on('closed', () => (mainWindow = null));
}

// ==========================================
// 6. IPC HANDLERS
// ==========================================
ipcMain.on('minimize-window', () => mainWindow?.minimize());
ipcMain.on('maximize-window', () => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize();
  else mainWindow?.maximize();
});
ipcMain.on('close-window', () => mainWindow?.close());
ipcMain.on('open-external-url', (event, url) => {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
      logger.electron(`Opening external URL: ${url}`);
      shell.openExternal(url);
    }
  } catch (err) {
    logger.electronError(`Invalid URL blocked in open-external-url: ${url}`);
  }
});
ipcMain.handle('get-app-version', () => app.getVersion());

// ==========================================
// 7. DEEP LINKING
// ==========================================
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('linkdapply', process.execPath, [path.resolve(process.argv[1])]);
  }
} else {
  app.setAsDefaultProtocolClient('linkdapply');
}

function handleDeepLink(url) {
  logger.electron(`Received deep link: ${url}`);
  try {
    const parsed = new URL(url);
    const token = parsed.searchParams.get('token');
    if (mainWindow) {
      if (token) mainWindow.webContents.send('auth-success', token);
      else mainWindow.loadURL(APP_URL);
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  } catch (err) {
    logger.electronError(`Error parsing deep link URL: ${err.message}`);
  }
}

// ==========================================
// 8. APP LIFECYCLE
// ==========================================
app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-gpu-shader-disk-cache');

app.whenReady().then(() => {
  createSplashWindow();
  startBackend();
  startFrontend();
  createMainWindow();

  globalShortcut.register('CommandOrControl+Q', () => app.quit());
});

app.on('before-quit', () => {
  isShuttingDown = true;
  stopProcess(backendProcess, 'backend');
  stopProcess(frontendProcess, 'frontend');
});

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
    const url = commandLine.find(arg => arg.startsWith('linkdapply://'));
    if (url) handleDeepLink(url);
  });
}

app.on('open-url', (event, url) => {
  event.preventDefault();
  handleDeepLink(url);
});

if (!isDev) {
  autoUpdater.on('update-available', () => logger.electron('Update available.'));
  autoUpdater.on('update-downloaded', () => autoUpdater.quitAndInstall());
  autoUpdater.on('error', (err) => {
    logger.electronWarn(`Auto-updater: ${err?.message || err}`);
  });
  autoUpdater.checkForUpdatesAndNotify().catch((err) => {
    logger.electronWarn(`Auto-updater check failed: ${err?.message || err}`);
  });
}
