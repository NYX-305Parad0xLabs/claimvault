from __future__ import annotations

import os
from pathlib import Path


def app_data_dir(app_name: str = "claimvault") -> Path:
    explicit = os.getenv("CLAIMVAULT_DATA_DIR")
    if explicit:
        base = Path(explicit)
    elif os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    path = base / app_name
    path.mkdir(parents=True, exist_ok=True)
    return path
