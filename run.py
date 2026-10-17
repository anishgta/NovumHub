"""
run.py
================================================================================
HACKREC LOCAL DEVELOPMENT RUNNER
To start the Hackrec server, simply run:
    python run.py

Then open your browser and navigate to:
    http://127.0.0.1:5000
================================================================================
"""

import os
import sys
import subprocess

# If the active Python environment is missing dependencies (e.g. MSYS2 python or unactivated shell),
# automatically relaunch using the project's local virtual environment (.venv).
venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
if os.path.exists(venv_python) and os.path.normcase(os.path.abspath(sys.executable)) != os.path.normcase(os.path.abspath(venv_python)):
    try:
        import flask  # noqa: F401
    except ImportError:
        result = subprocess.run([venv_python] + sys.argv)
        sys.exit(result.returncode)

from app import create_app

# Create our application using the factory function defined in app/__init__.py
app = create_app()

if __name__ == "__main__":
    # In development mode, auto-reloading and helpful debug error pages are active.
    # You can turn off debug mode by setting the environment variable FLASK_DEBUG=0.
    debug_mode = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")

    print("=" * 70)
    print("[HACKREC PORTAL] - ARMY INSTITUTE OF TECHNOLOGY (AIT)")
    print("=" * 70)
    print("Running locally at: http://127.0.0.1:5000")
    print("To quit, press CTRL+C")
    print("=" * 70)

    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
