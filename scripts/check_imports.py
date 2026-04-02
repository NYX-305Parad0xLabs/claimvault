from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
API_PATH = REPO / "apps" / "api"
APP_PATH = API_PATH / "app"


def _add_to_path(path: Path) -> None:
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)


def _import_package(package_name: str, discovery_path: Path) -> None:
    errors: list[tuple[str, Exception]] = []
    for finder, name, ispkg in pkgutil.walk_packages([str(discovery_path)], prefix=f"{package_name}."):
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - this script is defensive
            errors.append((name, exc))
    if errors:
        for name, exc in errors:
            print(f"failed to import {name}: {exc}")
        raise SystemExit(f"{len(errors)} module(s) failed to import")


def main() -> None:
    _add_to_path(API_PATH)
    if not APP_PATH.is_dir():
        raise SystemExit("Unable to locate the API package for import verification.")
    print("Checking API imports...")
    _import_package("app", APP_PATH)
    print("API imports look clean.")


if __name__ == "__main__":
    main()
