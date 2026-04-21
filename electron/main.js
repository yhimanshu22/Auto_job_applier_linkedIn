const { app, BrowserWindow, Menu, ipcMain, globalShortcut } = require('electron');
const path = require('path');
const { autoUpdater } = require('electron-updater');

let mainWindow;
let splashWindow;

const isDev = process.argv.includes('--dev');
// ❗ Update this with your production URL when ready
const APP_URL = isDev ? 'http://localhost:3000/login' : 'http://localhost:3000/login'; 

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
    },
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false,
    frame: false,
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
    },
    icon: path.join(__dirname, 'icon.ico'),
    title: 'LinkdApply',
  });

  mainWindow.loadURL(APP_URL);
  
  // Clean UI: Remove default menu
  mainWindow.removeMenu();

  // Smooth Transition: Hide splash and show main ONLY when content is ready
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[Electron] Main window loaded successfully');
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
    mainWindow.maximize();
  });

  // 📝 Terminal Logging: Pipe frontend logs to terminal
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    const levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
    console.log(`[Frontend ${levels[level] || 'LOG'}] ${message} (${path.basename(sourceId)}:${line})`);
  });

  // Error Handling: Handle load failures gracefully
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error(`[Electron ERROR] Failed to load ${validatedURL}: ${errorDescription} (${errorCode})`);
    mainWindow.loadURL('data:text/html,<html><body style="background:#09090b;color:white;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;"><h1>App failed to load</h1><p>Error: ' + errorDescription + '</p><p>Check if your local server is running on port 3000.</p></body></html>');
  });

  // Log navigation starts
  mainWindow.webContents.on('did-start-navigation', (event, url) => {
    console.log(`[Electron] Navigating to: ${url}`);
  });

  // Security: Prevent unauthorized external navigation
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    console.log(`[Electron] Attempting to open window: ${url}`);
    // Allow Google OAuth and app dashboard
    if (url.startsWith(APP_URL) || url.includes('accounts.google.com')) {
      console.log(`[Electron] Permitted external navigation: ${url}`);
      return { action: 'allow' };
    }
    console.warn(`[Electron] Blocked unauthorized window: ${url}`);
    return { action: 'deny' };
  });

  // DEV: Enable tools if requested
  if (!isDev) {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools();
    });
  }

  mainWindow.on('closed', () => (mainWindow = null));
}

// IPC Handlers for Custom Titlebar
ipcMain.on('minimize-window', () => mainWindow?.minimize());
ipcMain.on('maximize-window', () => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize();
  else mainWindow?.maximize();
});
ipcMain.on('close-window', () => mainWindow?.close());
ipcMain.on('open-external-url', (event, url) => {
  console.log(`[Electron] Opening external URL: ${url}`);
  require('electron').shell.openExternal(url);
});

// Protocol Handling Logic
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('linkdapply', process.execPath, [path.resolve(process.argv[1])]);
  }
} else {
  app.setAsDefaultProtocolClient('linkdapply');
}

function handleDeepLink(url) {
  console.log(`[Electron] Received deep link: ${url}`);
  
  try {
    const parsed = new URL(url);
    const token = parsed.searchParams.get('token');

    if (mainWindow) {
      if (token) {
        console.log('[Electron] Sending auth-success to renderer with token');
        mainWindow.webContents.send('auth-success', token);
      } else {
        console.log('[Electron] Deep link received without token, redirecting to login');
        mainWindow.loadURL(`${APP_URL}`);
      }
      
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  } catch (err) {
    console.error('[Electron] Error parsing deep link URL:', err);
  }
}

// Lifecycle Management
app.commandLine.appendSwitch('disable-gpu');
app.setPath('userData', path.join(app.getPath('temp'), 'linkdapply-v1'));

app.whenReady().then(() => {
  createSplashWindow();
  createMainWindow();

  // Native Shortcuts
  globalShortcut.register('CommandOrControl+Q', () => {
    app.quit();
  });
});

// Handle deep links on Windows (secondary instances)
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
    // Command line contains the deep link URL on Windows
    const url = commandLine.find(arg => arg.startsWith('linkdapply://'));
    if (url) {
      handleDeepLink(url);
    }
  });
}

// Handle deep links on macOS / Linux
app.on('open-url', (event, url) => {
  event.preventDefault();
  handleDeepLink(url);
});

// Auto-Updater Management
if (!isDev) {
  autoUpdater.on('update-available', () => {
    console.log('Update available. Downloading...');
  });
  autoUpdater.on('update-downloaded', () => {
    console.log('Update downloaded. Ready to install.');
    autoUpdater.quitAndInstall();
  });
  autoUpdater.checkForUpdatesAndNotify();
}
