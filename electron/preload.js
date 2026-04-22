const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  minimize: () => ipcRenderer.send('minimize-window'),
  maximize: () => ipcRenderer.send('maximize-window'),
  close: () => ipcRenderer.send('close-window'),
  openExternal: (url) => {
    // Basic validation before sending to main process
    if (typeof url === 'string' && url.startsWith('http')) {
      ipcRenderer.send('open-external-url', url);
    }
  },
  onAuthSuccess: (callback) => {
    const subscription = (event, token) => callback(token);
    ipcRenderer.on('auth-success', subscription);
    return () => ipcRenderer.removeListener('auth-success', subscription);
  },
  isDev: process.argv.includes('--is-dev'),
});

window.addEventListener('DOMContentLoaded', () => {
  console.log('LinkdApply Electron Wrapper Loaded');
});
