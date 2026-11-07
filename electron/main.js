const { app, BrowserWindow, Menu, Tray, nativeImage, dialog, protocol } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');
const url = require('url');

// ── Single instance lock ────────────────────────────────────────────
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
    app.quit();
}

let mainWindow;
let splashWindow;
let backendProcess;
let frontendProcess;
let staticServer;
let tray;
let isQuitting = false;

const isDev = !app.isPackaged;
const APP_ICON = path.join(__dirname, 'assets', 'icon.ico');

// ── Paths ───────────────────────────────────────────────────────────
const DEV_PYTHON_PATH =
    'C:\\Users\\minhk\\AppData\\Local\\Programs\\Python\\Python314\\python.exe';
const BACKEND_DIR_DEV = path.join(__dirname, '..', 'backend');
const FRONTEND_DIR_DEV = path.join(__dirname, '..', 'frontend');

// Production paths (inside the packaged app)
const RESOURCES_PATH = isDev ? __dirname : process.resourcesPath;
const BACKEND_DIR_PROD = path.join(RESOURCES_PATH, 'backend');
const FRONTEND_DIR_PROD = path.join(RESOURCES_PATH, 'frontend');
const PYTHON_DIR_PROD = path.join(RESOURCES_PATH, 'python');

// ── MIME types for static file server ───────────────────────────────
const MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.map': 'application/json',
    '.txt': 'text/plain; charset=utf-8',
    '.webp': 'image/webp',
};

// ── Splash screen ───────────────────────────────────────────────────
function showSplash() {
    splashWindow = new BrowserWindow({
        width: 400,
        height: 260,
        frame: false,
        resizable: false,
        alwaysOnTop: true,
        transparent: false,
        icon: APP_ICON,
        webPreferences: { nodeIntegration: false, contextIsolation: true },
    });

    const html = `
    <html>
    <body style="display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:'Segoe UI',sans-serif;background:#f8f9fa;">
      <div style="text-align:center;">
        <h2 style="margin-bottom:8px;">Dự Toán Web</h2>
        <p style="color:#666;">Đang khởi động...</p>
      </div>
    </body>
    </html>`;

    splashWindow.loadURL(
        'data:text/html;charset=utf-8,' + encodeURIComponent(html),
    );
}

// ── Start backend (FastAPI / uvicorn) ───────────────────────────────
function startBackend() {
    if (isDev) {
        backendProcess = spawn(
            DEV_PYTHON_PATH,
            ['-m', 'uvicorn', 'app.main:app', '--port', '8000'],
            {
                cwd: BACKEND_DIR_DEV,
                stdio: ['ignore', 'pipe', 'pipe'],
                env: { ...process.env },
            },
        );
    } else {
        // Production: use bundled Python to run run_server.py
        const pythonExe = path.join(PYTHON_DIR_PROD, 'python.exe');
        const runServer = path.join(BACKEND_DIR_PROD, 'run_server.py');
        backendProcess = spawn(pythonExe, [runServer], {
            cwd: BACKEND_DIR_PROD,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PYTHONPATH: BACKEND_DIR_PROD,
            },
        });
    }

    backendProcess.stdout.on('data', (d) =>
        console.log(`[Backend] ${d.toString().trimEnd()}`),
    );
    backendProcess.stderr.on('data', (d) =>
        console.log(`[Backend] ${d.toString().trimEnd()}`),
    );
    backendProcess.on('error', (err) =>
        console.error('Backend failed to start:', err),
    );
}

// ── Start frontend ─────────────────────────────────────────────────
function startFrontend() {
    if (isDev) {
        // Development: run Next.js dev server
        frontendProcess = spawn('npx', ['next', 'dev', '--port', '3000'], {
            cwd: FRONTEND_DIR_DEV,
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: true,
            env: { ...process.env },
        });

        frontendProcess.stdout.on('data', (d) =>
            console.log(`[Frontend] ${d.toString().trimEnd()}`),
        );
        frontendProcess.stderr.on('data', (d) =>
            console.log(`[Frontend] ${d.toString().trimEnd()}`),
        );
        frontendProcess.on('error', (err) =>
            console.error('Frontend failed to start:', err),
        );
    } else {
        // Production: serve static files from the exported Next.js build
        startStaticServer(FRONTEND_DIR_PROD, 3000);
    }
}

// ── Static file server for production frontend ─────────────────────
function startStaticServer(dir, port) {
    staticServer = http.createServer((req, res) => {
        const parsedUrl = url.parse(req.url);
        let pathname = decodeURIComponent(parsedUrl.pathname);

        // Security: prevent path traversal
        pathname = path.normalize(pathname).replace(/^(\.\.(\/|\\|$))+/, '');

        let filePath = path.join(dir, pathname);

        // Try to serve the file directly
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
            serveFile(filePath, res);
            return;
        }

        // Try with .html extension (Next.js static export convention)
        if (fs.existsSync(filePath + '.html')) {
            serveFile(filePath + '.html', res);
            return;
        }

        // Try index.html in directory
        const indexPath = path.join(filePath, 'index.html');
        if (fs.existsSync(indexPath)) {
            serveFile(indexPath, res);
            return;
        }

        // Fallback: serve index.html for client-side routing (SPA)
        // This handles dynamic routes like /du-toan/[id]
        const rootIndex = path.join(dir, 'index.html');
        if (fs.existsSync(rootIndex)) {
            serveFile(rootIndex, res);
            return;
        }

        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    });

    staticServer.listen(port, '127.0.0.1', () => {
        console.log(`[Frontend] Static server listening on http://127.0.0.1:${port}`);
    });
}

function serveFile(filePath, res) {
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    const stream = fs.createReadStream(filePath);
    res.writeHead(200, { 'Content-Type': contentType });
    stream.pipe(res);
    stream.on('error', () => {
        res.writeHead(500);
        res.end('Internal Server Error');
    });
}

// ── Wait for a server to respond ────────────────────────────────────
function waitForServer(url, maxRetries = 30, interval = 1000) {
    return new Promise((resolve, reject) => {
        let retries = 0;
        const check = () => {
            http.get(url, () => {
                resolve();
            }).on('error', () => {
                retries++;
                if (retries >= maxRetries) {
                    reject(new Error(`Server at ${url} did not start`));
                } else {
                    setTimeout(check, interval);
                }
            });
        };
        check();
    });
}

// ── App menu ────────────────────────────────────────────────────────
function buildMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'Thoát',
                    accelerator: 'CmdOrCtrl+Q',
                    click: () => {
                        isQuitting = true;
                        app.quit();
                    },
                },
            ],
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload', label: 'Reload' },
                { role: 'toggleDevTools', label: 'DevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
            ],
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Về ứng dụng',
                    click: () => {
                        dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'Dự Toán Web',
                            message: 'Dự Toán Web v1.0.0',
                            detail: 'Phần mềm dự toán xây dựng',
                        });
                    },
                },
            ],
        },
    ];

    Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ── Main window ─────────────────────────────────────────────────────
async function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        title: 'Dự Toán Web',
        icon: APP_ICON,
        show: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    mainWindow.loadURL('http://localhost:3000');

    mainWindow.once('ready-to-show', () => {
        if (splashWindow) {
            splashWindow.close();
            splashWindow = null;
        }
        mainWindow.show();
    });

    mainWindow.on('close', (e) => {
        if (!isQuitting) {
            e.preventDefault();
            mainWindow.hide();
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// ── Kill a process tree (Windows-safe) ──────────────────────────────
function killProcessTree(proc) {
    if (!proc || proc.killed) return;
    try {
        if (process.platform === 'win32') {
            spawn('taskkill', ['/pid', proc.pid.toString(), '/t', '/f']);
        } else {
            proc.kill('SIGTERM');
        }
    } catch (_) {
        // already dead — ignore
    }
}

// ── System tray ────────────────────────────────────────────────────
function createTray() {
    const icon = nativeImage.createFromPath(APP_ICON);
    tray = new Tray(icon.isEmpty() ? nativeImage.createEmpty() : icon);
    tray.setToolTip('Dự Toán Web');

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Mở lại',
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                    mainWindow.focus();
                }
            },
        },
        { type: 'separator' },
        {
            label: 'Thoát',
            click: () => {
                isQuitting = true;
                app.quit();
            },
        },
    ]);

    tray.setContextMenu(contextMenu);

    tray.on('double-click', () => {
        if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
        }
    });
}

// ── App lifecycle ───────────────────────────────────────────────────
app.on('second-instance', () => {
    if (mainWindow) {
        mainWindow.show();
        if (mainWindow.isMinimized()) mainWindow.restore();
        mainWindow.focus();
    }
});

app.on('ready', async () => {
    showSplash();
    buildMenu();
    createTray();

    startBackend();
    startFrontend();

    try {
        await waitForServer('http://localhost:8000');
        await waitForServer('http://localhost:3000');
        await createWindow();
    } catch (err) {
        if (splashWindow) {
            splashWindow.close();
            splashWindow = null;
        }
        dialog.showErrorBox('Lỗi khởi động', err.message);
        app.quit();
    }
});

app.on('before-quit', () => {
    isQuitting = true;
    killProcessTree(backendProcess);
    killProcessTree(frontendProcess);
    if (staticServer) {
        staticServer.close();
    }
});

app.on('window-all-closed', () => {
    // Don't quit — app stays in system tray
});
