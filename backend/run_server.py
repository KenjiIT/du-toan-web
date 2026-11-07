"""
Standalone entry point for the FastAPI backend.

Used by the packaged Electron app to start the backend server.
In development, you can also run this directly:
    python run_server.py
"""

import sys
import os

if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle — adjust working directory
    os.chdir(os.path.dirname(sys.executable))
else:
    # Running as a script — make sure we're in the backend/ directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host='127.0.0.1',
        port=8000,
        log_level='info',
    )
