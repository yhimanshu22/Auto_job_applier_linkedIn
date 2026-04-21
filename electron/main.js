const { app, BrowserWindow, Menu } = require('electron');
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
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    icon: path.join(__dirname, 'icon.ico'), // Placeholder for icon
    title: 'LinkdApply',
  });

  // Load the web app
  mainWindow.loadURL(APP_URL);

  // Disable DevTools in production
  if (!isDev) {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools();
    });
    // Remove default menu in production
    Menu.setApplicationMenu(null);
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

app.on('ready', () => {
  createSplashWindow();
  // Brief delay to ensure splash is visible before main starts loading
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
