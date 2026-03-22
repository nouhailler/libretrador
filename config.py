from pathlib import Path
import os

APP_NAME = "LibreTrador"
APP_VERSION = "0.1.0"
APP_ID = "libretrador"

XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_DATA   = Path(os.environ.get("XDG_DATA_HOME",   Path.home() / ".local/share"))

CONFIG_DIR  = XDG_CONFIG / "libretrador"
DATA_DIR    = XDG_DATA   / "libretrador"
DB_PATH     = DATA_DIR   / "history.db"
MODELS_DIR  = DATA_DIR   / "argos-models"
LOG_FILE    = DATA_DIR   / "libretrador.log"

MAX_CHARS       = 5000
MAX_HISTORY     = 500
CLIPBOARD_POLL_MS = 500
TTS_SPEED       = 145

SOURCE_LANG = "en"
TARGET_LANG = "fr"
