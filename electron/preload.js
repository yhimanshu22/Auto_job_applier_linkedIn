const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  minimize: () => ipcRenderer.send('minimize-window'),
  maximize: () => ipcRenderer.send('maximize-window'),
  close: () => ipcRenderer.send('close-window'),
  openExternal: (url) => require('electron').shell.openExternal(url),
});

window.addEventListener('DOMContentLoaded', () => {
  console.log('LinkdApply Electron Wrapper Loaded');
});
