'use strict';
// Minimal preload — keeps renderer sandboxed.
// Add contextBridge APIs here if the renderer ever needs Node access.
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('dataforge', {
    version: '1.0.0'
});
