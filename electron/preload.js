const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  minimize: () => ipcRenderer.send('minimize-window'),
  maximize: () => ipcRenderer.send('maximize-window'),
  close: () => ipcRenderer.send('close-window'),
  openExternal: (url) => ipcRenderer.send('open-external-url', url),
  onAuthSuccess: (callback) => ipcRenderer.on('auth-success', (event, token) => callback(token)),
});

window.addEventListener('DOMContentLoaded', () => {
  console.log('LinkdApply Electron Wrapper Loaded');
});
