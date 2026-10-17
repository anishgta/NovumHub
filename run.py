"""
run.py
================================================================================
NOVUMHUB LOCAL DEVELOPMENT RUNNER
To start the NovumHub server locally:
    python run.py
================================================================================
"""

import os
import sys

# Ensure repository root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create application instance
app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")

    print("=" * 70)
    print("[NOVUMHUB PORTAL] - ARMY INSTITUTE OF TECHNOLOGY (AIT)")
    print("=" * 70)
    print("Running locally at: http://127.0.0.1:5000")
    print("To quit, press CTRL+C")
    print("=" * 70)

    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
