from pathlib import Path
from typing import List

from skinextractor import cfgparser


class CfgBaseWrapper:
    _data: dict

    def __init__(self, file: Path, kv: bool = False):
        assert file.exists() is True, f"{file} doesn't exists!"

        if kv:
            self._data = cfgparser.load_kv(file)
        else:
            self._data = cfgparser.load(file)


class CDNWrapper(CfgBaseWrapper):
    def __init__(self, file: Path):
        super().__init__(file, kv=True)

    def __call__(self, key):
        return self._data.get(key)

    def all(self):
        yield from self._data.items()

    def find(self, suffix: str) -> List:
        for key, url in self._data.items():
            if key.endswith(suffix):
                weapon = key.replace(f"_{suffix}", "")
                file = url.split("/")[-1]
                yield weapon, {
                    "url": url,
                    "file": file
                }


class ItemsWrapper(CfgBaseWrapper):
    def __init__(self, file: Path):
        super().__init__(file, kv=False)

    def __call__(self, section: str):
        yield from self._data["items_game"][section].items()

    def get_rarity_id(self, name: str) -> str:
        return self._data["items_game"]["paint_kits_rarity"].get(name.lower())
