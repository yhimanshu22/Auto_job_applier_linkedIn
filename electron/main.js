const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');
const { autoUpdater } = require('electron-updater');

let mainWindow;
let splashWindow;

const isDev = process.argv.includes('--dev');
const APP_URL = isDev ? 'http://localhost:3000/dashboard' : 'http://localhost:3000/dashboard'; // Replace with deployed URL

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 500,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.on('closed', () => (splashWindow = null));
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false, // Hide until ready-to-show
    frame: false, // Remove default chrome UI
    backgroundColor: '#ffffff',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    icon: path.join(__dirname, 'icon.ico'),
    title: 'LinkdApply',
  });

  // Load the web app
  mainWindow.loadURL(APP_URL);

  // Native Feel: Remove default menu
  mainWindow.removeMenu();

  // Block navigation to other domains
  mainWindow.webContents.setWindowOpenHandler(() => {
    return { action: 'deny' };
  });

  // Disable DevTools in production
  if (!isDev) {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools();
    });
  }

  // Show main window when ready
  mainWindow.once('ready-to-show', () => {
    if (splashWindow) {
      splashWindow.close();
    }
    mainWindow.show();
    mainWindow.maximize();
  });

  mainWindow.on('closed', () => (mainWindow = null));

  // Auto-updater check
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
}

// IPC Handlers for Window Controls
ipcMain.on('minimize-window', () => {
  mainWindow.minimize();
});

ipcMain.on('maximize-window', () => {
  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow.maximize();
  }
});

ipcMain.on('close-window', () => {
  mainWindow.close();
});

app.on('ready', () => {
  createSplashWindow();
  setTimeout(createMainWindow, 500);
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
