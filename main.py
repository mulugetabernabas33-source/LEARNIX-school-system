import sys
import os

# ---------------------------------------------------------------------------
# Fix sys.path so flet_learnix packages are importable in both dev and packaged
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # Packaged: all Python source is bundled under sys._MEIPASS
    _base = sys._MEIPASS
else:
    # Development: source lives next to this file
    _base = os.path.dirname(os.path.abspath(__file__))

# Make flet_learnix importable
_flet_learnix_root = os.path.join(_base, "flet_learnix")
if _flet_learnix_root not in sys.path:
    sys.path.insert(0, _flet_learnix_root)

# Make app/backend importable (db_functions, etc.)
_backend_root = os.path.join(_base, "app", "backend")
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

# ---------------------------------------------------------------------------
# Seed writable data from bundle (runs BEFORE app startup)
# Must happen here, before any DB connection is attempted.
# ---------------------------------------------------------------------------
try:
    from flet_learnix.services.paths import seed_data_from_bundle, get_assets_dir
    seed_data_from_bundle()
    _assets_dir = get_assets_dir()
except Exception as _e:
    print(f"[WARN] seed_data_from_bundle failed: {_e}")
    # Fallback assets dir
    _assets_dir = os.path.join(_base, "assets")

# ---------------------------------------------------------------------------
# Launch the Flet application
# ---------------------------------------------------------------------------
import flet as ft
from flet_learnix.main import run_flet_app

if __name__ == "__main__":
    ft.app(target=run_flet_app, assets_dir=_assets_dir)
