# csgo-skin-color-picker

Search available in-game skins by color.

## Requirements

- Python 3.6 and above

## Installation

```bash
python -m pip install -r requirements.txt
```

## Usage

### skinextractor

```bash
python -m skinextractor "C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive"
```

This action creates `items.json` in current working directory. `items.json` is JSON version of `csgo\scripts\items\items_game.txt` with additional info in `paint_kits`.

### skinviewer

```bash
python -m uvicorn skinviewer.app:app --host=127.0.0.1 --port=9000 --root-path /winx
```

This starts webapp for reverse proxy on http://127.0.0.1:9000 with root path in `/winx`.

`items.json` MUST BE in current directory.