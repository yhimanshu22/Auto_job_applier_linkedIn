const { app, BrowserWindow, Menu, ipcMain, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');
const { autoUpdater } = require('electron-updater');
const { spawn, spawnSync, execSync } = require('child_process');
const logger = require('./logger');

let mainWindow;
let splashWindow;

const isDev = !app.isPackaged || process.argv.includes('--dev');
// ❗ Update this with your production URL when ready
const APP_URL = isDev ? 'http://localhost:3000/login' : 'http://localhost:3000/login'; 

const BACKEND_URL = 'http://localhost:8000/api/bot/status'; // Health check endpoint
const MAX_RESTARTS = 3;
let backendRestartCount = 0;
let frontendRestartCount = 0;
let isShuttingDown = false;

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
      allowRunningInsecureContent: false,
    },
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

// Startup logic simplified at user request

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    show: false,
    frame: isDev,
    backgroundColor: '#ffffff',
    autoHideMenuBar: true,
    resizable: true,
    minimizable: true,
    maximizable: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: true,
      enableRemoteModule: false,
      webSecurity: true,
      allowRunningInsecureContent: false,
      additionalArguments: [isDev ? '--is-dev' : ''],
    },
    icon: path.join(__dirname, 'icon.ico'),
    title: 'LinkdApply',
  });

  // Load the app after a short delay to allow services to warm up
  setTimeout(() => {
    if (!isShuttingDown && mainWindow) {
      logger.electron('Loading main application...');
      mainWindow.loadURL(APP_URL);
    }
  }, 10000);
  
  mainWindow.removeMenu();

  mainWindow.webContents.on('did-finish-load', () => {
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  // Native logging pipe
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
        logger.electron(`Permitted external navigation: ${url}`);
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

// IPC Handlers
ipcMain.on('minimize-window', () => mainWindow?.minimize());
ipcMain.on('maximize-window', () => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize();
  else mainWindow?.maximize();
});
ipcMain.on('close-window', () => mainWindow?.close());
ipcMain.on('open-external-url', (event, url) => {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') return;
    logger.electron(`Opening external URL: ${url}`);
    require('electron').shell.openExternal(url);
  } catch (err) {
    logger.electronError(`Invalid URL blocked in open-external-url: ${url}`);
  }
});

// Protocol Handling
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

app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-gpu-shader-disk-cache');

let backendProcess;
let frontendProcess;

function clearPort(port) {
  if (process.platform !== 'win32') return;
  try {
    const netstat = spawnSync('netstat', ['-ano'], { shell: false });
    const output = netstat.stdout.toString();
    const lines = output.split('\n');
    lines.forEach(line => {
      // Look for the port in the local address column and ensure it is LISTENING
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

function startBackend() {
  if (backendProcess && !backendProcess.killed) return;
  clearPort(8000);
  try {
    const backendDir = app.isPackaged 
      ? path.join(process.resourcesPath, 'backend')
      : path.resolve(__dirname, '..', 'backend');
    
    const serverPath = path.join(backendDir, 'server.py');
    const pythonExe = app.isPackaged 
      ? path.join(backendDir, 'server.exe')
      : path.resolve(__dirname, '..', 'backend', 'dist', 'server.exe');

    let spawnCommand = fs.existsSync(pythonExe) ? pythonExe : 'python';
    let spawnArgs = spawnCommand === 'python' ? [serverPath] : [];

    logger.electron(`Starting backend process...`);
    
    backendProcess = spawn(spawnCommand, spawnArgs, {
      cwd: backendDir,
      shell: false, 
      env: { ...process.env, PYTHONUNBUFFERED: "1" }
    });

    backendProcess.stdout.on('data', (d) => logger.backend(d.toString().trim()));
    backendProcess.stderr.on('data', (d) => logger.backendError(d.toString().trim()));

    backendProcess.on('exit', (code) => {
      logger.electron(`Backend exited with code ${code}`);
      if (!isShuttingDown && backendRestartCount < MAX_RESTARTS) {
        backendRestartCount++;
        logger.electron(`Restarting backend (${backendRestartCount}/${MAX_RESTARTS})...`);
        setTimeout(startBackend, 3000);
      }
    });

    backendProcess.on('error', (err) => logger.electronError(`Backend spawn error: ${err.message}`));
  } catch (err) {
    logger.electronError(`Critical startBackend failure: ${err.message}`);
  }
}

function startFrontend() {
  if (frontendProcess && !frontendProcess.killed) return;
  clearPort(3000);
  try {
    const frontendDir = path.resolve(__dirname, '..', 'frontend');
    const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';
    const spawnArgs = isDev ? ['run', 'dev'] : ['run', 'start'];

    logger.electron(`Starting frontend process (${spawnArgs.join(' ')})...`);
    
    frontendProcess = spawn(npmCommand, spawnArgs, {
      cwd: frontendDir,
      shell: false, 
      env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" }
    });

    frontendProcess.stdout.on('data', (d) => logger.frontend(d.toString().trim()));
    frontendProcess.stderr.on('data', (d) => logger.frontendError(d.toString().trim()));

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

function stopProcess(proc, name) {
  if (proc && !proc.killed) {
    logger.electron(`Stopping ${name}...`);
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/F', '/T', '/PID', proc.pid.toString()], { shell: false });
    } else {
      proc.kill('SIGTERM');
    }
  }
}

app.whenReady().then(() => {
  startBackend();
  startFrontend();
  createSplashWindow();
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
  autoUpdater.checkForUpdatesAndNotify();
}
