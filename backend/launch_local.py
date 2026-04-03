from pathlib import Path
import os
import sys

import uvicorn


BACKEND_DIR = Path(__file__).resolve().parent
LEGACY_SITE_PACKAGES = BACKEND_DIR.parent / ".venv_broken" / "Lib" / "site-packages"

if LEGACY_SITE_PACKAGES.exists():
    legacy_path = str(LEGACY_SITE_PACKAGES)
    if legacy_path not in sys.path:
        sys.path.append(legacy_path)

os.chdir(BACKEND_DIR)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
