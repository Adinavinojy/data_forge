'use strict';

const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// ── Paths ──────────────────────────────────────────────────────────────────

// electron-app/ lives inside the project root
const PROJECT_ROOT = path.resolve(__dirname, '..');
const VENV_PYTHON = path.join(PROJECT_ROOT, 'venv', 'bin', 'python3');
const BACKEND_DIR = path.join(PROJECT_ROOT, 'backend');
const FRONTEND_DIR = path.join(PROJECT_ROOT, 'frontend');

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;

// ── State ──────────────────────────────────────────────────────────────────

let mainWindow = null;
let backendProc = null;
let frontendProc = null;

// ── Helpers ─────────────────────────────────────────────────────────────────

function log(msg) {
    console.log(`[DataForge] ${msg}`);
}

/**
 * Poll a URL until it responds 200 (or timeout).
 * Returns a Promise that resolves when ready.
 */
function waitForUrl(url, timeoutMs = 30000, intervalMs = 500) {
    const http = require('http');
    return new Promise((resolve, reject) => {
        const start = Date.now();
        const check = () => {
            http.get(url, (res) => {
                if (res.statusCode < 500) {
                    resolve();
                } else {
                    retry();
                }
                res.resume();
            }).on('error', retry);
        };
        const retry = () => {
            if (Date.now() - start > timeoutMs) {
                reject(new Error(`Timed out waiting for ${url}`));
                return;
            }
            setTimeout(check, intervalMs);
        };
        check();
    });
}

// ── Child Process Management ─────────────────────────────────────────────────

function startBackend() {
    log('Starting FastAPI backend...');

    // Use the venv python if it exists, otherwise fall back to system python3
    const python = fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python3';

    backendProc = spawn(python, [
        '-m', 'uvicorn',
        'app.main:app',
        '--host', '127.0.0.1',
        '--port', String(BACKEND_PORT),
        '--reload'
    ], {
        cwd: BACKEND_DIR,
        env: { ...process.env, PYTHONPATH: BACKEND_DIR }
    });

    backendProc.stdout.on('data', d => log(`[backend] ${d.toString().trim()}`));
    backendProc.stderr.on('data', d => log(`[backend:err] ${d.toString().trim()}`));
    backendProc.on('exit', code => log(`Backend exited with code ${code}`));
}

function startFrontend() {
    log('Starting Vite frontend...');

    frontendProc = spawn('npm', ['run', 'dev'], {
        cwd: FRONTEND_DIR,
        shell: true,
        env: { ...process.env }
    });

    frontendProc.stdout.on('data', d => log(`[frontend] ${d.toString().trim()}`));
    frontendProc.stderr.on('data', d => log(`[frontend:err] ${d.toString().trim()}`));
    frontendProc.on('exit', code => log(`Frontend exited with code ${code}`));
}

function killChildren() {
    log('Killing child processes...');

    if (backendProc && !backendProc.killed) {
        // On Mac/Linux kill the process group to catch child uvicorn workers
        try { process.kill(-backendProc.pid, 'SIGTERM'); } catch (_) { }
        backendProc.kill();
    }
    if (frontendProc && !frontendProc.killed) {
        try { process.kill(-frontendProc.pid, 'SIGTERM'); } catch (_) { }
        frontendProc.kill();
    }
}

// ── Window ───────────────────────────────────────────────────────────────────

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1440,
        height: 900,
        minWidth: 1024,
        minHeight: 650,
        backgroundColor: '#0f0f0f',
        titleBarStyle: 'hiddenInset', // cleaner title bar on macOS
        title: 'DataForge',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: false
        }
    });

    // Show loading screen immediately
    mainWindow.loadFile(path.join(__dirname, 'loading.html'));
    mainWindow.show();

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// ── App Lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
    createWindow();
    startBackend();
    startFrontend();

    const backendUrl = `http://127.0.0.1:${BACKEND_PORT}/api/v1/datasets/`;
    const frontendUrl = `http://localhost:${FRONTEND_PORT}`;

    log('Waiting for backend and frontend to be ready...');

    try {
        // Wait for both in parallel
        await Promise.all([
            waitForUrl(backendUrl, 30000),
            waitForUrl(frontendUrl, 30000)
        ]);

        log('Both services ready — loading app...');
        if (mainWindow) {
            mainWindow.loadURL(FRONTEND_URL);
        }
    } catch (err) {
        log(`Startup error: ${err.message}`);
        dialog.showErrorBox(
            'DataForge failed to start',
            `Could not connect to services:\n${err.message}\n\nCheck that Python 3 and Node.js are installed.`
        );
        app.quit();
    }
});

app.on('window-all-closed', () => {
    killChildren();
    app.quit();
});

app.on('before-quit', () => {
    killChildren();
});

// Re-create window on macOS dock click (standard behaviour)
app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
