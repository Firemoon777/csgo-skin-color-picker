from pathlib import Path
from typing import Dict

from skinextractor import cfgparser


class LocaleWrapper:

    _data: Dict

    def __init__(self, root: Path, locale: str):
        locale_path = root / "csgo" / "resource" / f"csgo_{locale}.txt"
        assert locale_path.exists() is True, f"Locale {locale} not found!"
        self._data = cfgparser.load(locale_path, encoding="UTF-16")

    def __call__(self, key: str) -> str:
        clear_key = key.lower()
        if clear_key.startswith("#"):
            clear_key = clear_key[1:]
        return self._data.get("lang", {}).get("tokens", {}).get(clear_key, key)
