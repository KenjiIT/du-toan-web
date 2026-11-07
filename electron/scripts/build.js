/**
 * Quick build script — builds frontend only (for dev testing).
 *
 * Usage:  node scripts/build.js
 *
 * For full packaging (portable + installer), use:
 *   node scripts/package.js
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');
const FRONTEND_DIR = path.join(ROOT, 'frontend');
const DIST = path.join(__dirname, '..', 'dist');

function run(cmd, cwd) {
    console.log(`> ${cmd}  (in ${cwd})`);
    execSync(cmd, { cwd, stdio: 'inherit' });
}

async function main() {
    console.log('=== Building frontend (static export) ===');
    run('npm run build', FRONTEND_DIR);

    // Copy output
    const frontendOut = path.join(FRONTEND_DIR, 'out');
    const frontendDist = path.join(DIST, 'frontend');

    if (!fs.existsSync(frontendOut)) {
        throw new Error(
            'frontend/out/ not found. Ensure next.config.ts has output: "export".',
        );
    }

    if (fs.existsSync(frontendDist)) {
        fs.rmSync(frontendDist, { recursive: true, force: true });
    }
    fs.cpSync(frontendOut, frontendDist, { recursive: true });
    console.log(`Copied frontend build to ${frontendDist}`);

    console.log('=== Done ===');
    console.log('To create installers, run: node scripts/package.js');
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
