/**
 * Master build script for Du Toan Web desktop app.
 *
 * Usage:  node scripts/package.js [--skip-frontend] [--skip-python]
 *
 * Produces:
 *   release/DuToanWeb-Portable-1.0.0.exe  (portable, no install)
 *   release/Du Toan Web Setup 1.0.0.exe   (NSIS installer)
 *
 * Prerequisites:
 *   - Node.js and npm installed
 *   - Python 3.12+ installed (for backend dependencies)
 *   - npm install done in both frontend/ and electron/
 *
 * Steps:
 *   1. Clean dist/ and release/ directories
 *   2. Build Next.js frontend static export -> dist/frontend/
 *   3. Copy backend Python source files -> dist/backend/
 *   4. Download & set up Python embeddable -> dist/python/
 *   5. Install backend dependencies into embeddable Python
 *   6. Run electron-builder to create portable + installer
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');
const { createWriteStream } = require('fs');

// ── Paths ───────────────────────────────────────────────────────────
const ELECTRON_DIR = path.join(__dirname, '..');
const ROOT = path.join(ELECTRON_DIR, '..');
const DIST = path.join(ELECTRON_DIR, 'dist');
const RELEASE = path.join(ELECTRON_DIR, 'release');
const FRONTEND_DIR = path.join(ROOT, 'frontend');
const BACKEND_DIR = path.join(ROOT, 'backend');

// Python embeddable distribution (Windows x64)
// Using 3.12 for better stability with PyInstaller/embeddable
const PYTHON_VERSION = '3.12.7';
const PYTHON_ZIP_NAME = `python-${PYTHON_VERSION}-embed-amd64.zip`;
const PYTHON_URL = `https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_ZIP_NAME}`;
const PYTHON_CACHE = path.join(ELECTRON_DIR, '.cache', PYTHON_ZIP_NAME);

// ── CLI flags ───────────────────────────────────────────────────────
const args = process.argv.slice(2);
const skipFrontend = args.includes('--skip-frontend');
const skipPython = args.includes('--skip-python');

// ── Helpers ─────────────────────────────────────────────────────────
function run(cmd, cwd) {
    console.log(`  > ${cmd}`);
    execSync(cmd, { cwd, stdio: 'inherit' });
}

function cleanDir(dir) {
    if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
    }
    fs.mkdirSync(dir, { recursive: true });
}

function copyDir(src, dest) {
    fs.cpSync(src, dest, { recursive: true });
}

function downloadFile(url, dest) {
    return new Promise((resolve, reject) => {
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        const file = createWriteStream(dest);
        https.get(url, (response) => {
            // Handle redirects
            if (response.statusCode === 301 || response.statusCode === 302) {
                file.close();
                fs.unlinkSync(dest);
                downloadFile(response.headers.location, dest).then(resolve).catch(reject);
                return;
            }
            if (response.statusCode !== 200) {
                file.close();
                fs.unlinkSync(dest);
                reject(new Error(`Download failed: HTTP ${response.statusCode}`));
                return;
            }
            const total = parseInt(response.headers['content-length'], 10);
            let downloaded = 0;
            response.on('data', (chunk) => {
                downloaded += chunk.length;
                if (total) {
                    const pct = Math.round((downloaded / total) * 100);
                    process.stdout.write(`\r  Downloading... ${pct}%`);
                }
            });
            response.pipe(file);
            file.on('finish', () => {
                file.close();
                console.log('');
                resolve();
            });
        }).on('error', (err) => {
            file.close();
            fs.unlinkSync(dest);
            reject(err);
        });
    });
}

// ── Main ────────────────────────────────────────────────────────────
async function main() {
    const startTime = Date.now();
    console.log('========================================');
    console.log(' Du Toan Web — Build & Package');
    console.log('========================================\n');

    // ── Step 1: Clean ───────────────────────────────────────────────
    console.log('[1/6] Cleaning dist/ and release/...');
    cleanDir(DIST);
    if (fs.existsSync(RELEASE)) {
        fs.rmSync(RELEASE, { recursive: true, force: true });
    }

    // ── Step 2: Build frontend ──────────────────────────────────────
    if (skipFrontend) {
        console.log('[2/6] Skipping frontend build (--skip-frontend)');
    } else {
        console.log('[2/6] Building Next.js frontend (static export)...');
        run('npm run build', FRONTEND_DIR);
    }

    // Copy frontend build output to dist/frontend/
    console.log('  Copying frontend/out/ -> dist/frontend/...');
    const frontendOut = path.join(FRONTEND_DIR, 'out');
    if (!fs.existsSync(frontendOut)) {
        throw new Error(
            'frontend/out/ does not exist. Run "npm run build" in frontend/ first.\n' +
            'Make sure next.config.ts has output: "export".',
        );
    }
    copyDir(frontendOut, path.join(DIST, 'frontend'));

    // ── Step 3: Copy backend ────────────────────────────────────────
    console.log('[3/6] Copying backend files...');
    const backendDist = path.join(DIST, 'backend');
    fs.mkdirSync(backendDist, { recursive: true });

    // Copy Python source (app/ directory)
    copyDir(path.join(BACKEND_DIR, 'app'), path.join(backendDist, 'app'));

    // Copy run_server.py
    fs.copyFileSync(
        path.join(BACKEND_DIR, 'run_server.py'),
        path.join(backendDist, 'run_server.py'),
    );

    // Copy the database file (106MB)
    console.log('  Copying dutoan.db (this may take a moment)...');
    const dataDir = path.join(backendDist, 'data');
    fs.mkdirSync(dataDir, { recursive: true });
    const dbSrc = path.join(BACKEND_DIR, 'data', 'dutoan.db');
    if (fs.existsSync(dbSrc)) {
        fs.copyFileSync(dbSrc, path.join(dataDir, 'dutoan.db'));
    } else {
        console.warn('  WARNING: dutoan.db not found at', dbSrc);
    }

    // Copy pyproject.toml (for reference)
    if (fs.existsSync(path.join(BACKEND_DIR, 'pyproject.toml'))) {
        fs.copyFileSync(
            path.join(BACKEND_DIR, 'pyproject.toml'),
            path.join(backendDist, 'pyproject.toml'),
        );
    }

    // ── Step 4: Download Python embeddable ──────────────────────────
    if (skipPython) {
        console.log('[4/6] Skipping Python download (--skip-python)');
    } else {
        console.log(`[4/6] Setting up Python ${PYTHON_VERSION} embeddable...`);
        const pythonDist = path.join(DIST, 'python');

        if (fs.existsSync(PYTHON_CACHE)) {
            console.log('  Using cached download:', PYTHON_CACHE);
        } else {
            console.log('  Downloading from', PYTHON_URL);
            await downloadFile(PYTHON_URL, PYTHON_CACHE);
        }

        // Extract the zip (use PowerShell on Windows)
        fs.mkdirSync(pythonDist, { recursive: true });
        console.log('  Extracting...');
        run(
            `powershell -Command "Expand-Archive -Path '${PYTHON_CACHE}' -DestinationPath '${pythonDist}' -Force"`,
            ELECTRON_DIR,
        );

        // Enable pip: uncomment 'import site' in python312._pth
        const pthFile = path.join(pythonDist, `python312._pth`);
        if (fs.existsSync(pthFile)) {
            let content = fs.readFileSync(pthFile, 'utf-8');
            content = content.replace(/^#\s*import site/m, 'import site');
            // Add the backend dir to the path
            content += '\n..\\backend\n';
            fs.writeFileSync(pthFile, content, 'utf-8');
            console.log('  Enabled site-packages in ._pth');
        }

        // ── Step 5: Install pip and dependencies ────────────────────
        console.log('[5/6] Installing pip and backend dependencies...');
        const pythonExe = path.join(pythonDist, 'python.exe');

        // Download get-pip.py
        const getPipPath = path.join(ELECTRON_DIR, '.cache', 'get-pip.py');
        if (!fs.existsSync(getPipPath)) {
            console.log('  Downloading get-pip.py...');
            await downloadFile('https://bootstrap.pypa.io/get-pip.py', getPipPath);
        }

        // Install pip
        console.log('  Installing pip...');
        run(`"${pythonExe}" "${getPipPath}" --no-warn-script-location`, pythonDist);

        // Install backend dependencies
        console.log('  Installing backend dependencies...');
        const deps = [
            'fastapi>=0.115',
            'uvicorn[standard]>=0.30',
            'sqlalchemy>=2.0',
            'pydantic>=2.0',
            'python-multipart>=0.0.9',
            'openpyxl>=3.1',
            'reportlab>=4.0',
            'bcrypt>=4.0',
            'PyJWT>=2.8',
        ];
        // Note: pyodbc excluded — not needed for SQLite, and requires ODBC drivers
        const depsStr = deps.map((d) => `"${d}"`).join(' ');
        run(
            `"${pythonExe}" -m pip install ${depsStr} --no-warn-script-location --target "${path.join(pythonDist, 'Lib', 'site-packages')}"`,
            pythonDist,
        );
    }

    // ── Step 6: Package with electron-builder ───────────────────────
    console.log('[6/6] Packaging with electron-builder...');
    run('npx electron-builder --win --x64', ELECTRON_DIR);

    // ── Done ────────────────────────────────────────────────────────
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log('\n========================================');
    console.log(` Build complete in ${elapsed}s`);
    console.log('========================================');
    console.log(`\nOutput in: ${RELEASE}`);

    // List output files
    if (fs.existsSync(RELEASE)) {
        const files = fs.readdirSync(RELEASE).filter((f) => f.endsWith('.exe'));
        files.forEach((f) => {
            const size = (fs.statSync(path.join(RELEASE, f)).size / 1024 / 1024).toFixed(1);
            console.log(`  ${f}  (${size} MB)`);
        });
    }
}

main().catch((err) => {
    console.error('\nBuild failed:', err.message);
    process.exit(1);
});
