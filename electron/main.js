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
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
    mainWindow.maximize();
  });

  // Error Handling: Handle load failures gracefully
  mainWindow.webContents.on('did-fail-load', () => {
    mainWindow.loadURL('data:text/html,<html><body style="background:#09090b;color:white;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;"><h1>App failed to load</h1><p>Please ensure the local server is running or check your connection.</p></body></html>');
  });

  // Security: Prevent unauthorized external navigation
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith(APP_URL)) return { action: 'allow' };
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

// Lifecycle Management
app.whenReady().then(() => {
  createSplashWindow();
  createMainWindow();

  // Native Shortcuts
  globalShortcut.register('CommandOrControl+Q', () => {
    app.quit();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createMainWindow();
  }
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
