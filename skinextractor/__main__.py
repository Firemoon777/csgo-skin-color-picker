import colorsys
import json
import sys
import logging
from pathlib import Path

from colorthief import ColorThief
import requests

from skinextractor import cfgparser

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)


def check_exists(f: Path):
    if f.exists() is False:
        logging.error(f"{f} not exists!")
        exit(1)


if len(sys.argv) != 2:
    print("Usage:", file=sys.stderr)
    print(f"\t{sys.argv[0]} path/to/Counter-Strike Global Offensive", file=sys.stderr)
    exit(1)

base_dir = Path(sys.argv[1])
logging.info(f"CSGO directory: {base_dir}")

lang_en_file = base_dir / "csgo" / "resource" / "csgo_english.txt"
lang_native_file = base_dir / "csgo" / "resource" / "csgo_russian.txt"   # Change here if needed
items_game_file = base_dir / "csgo" / "scripts" / "items" / "items_game.txt"
items_game_cdn_file = base_dir / "csgo" / "scripts" / "items" / "items_game_cdn.txt"

res_dir = Path("res")
res_dir.mkdir(exist_ok=True)

check_exists(lang_en_file)
check_exists(lang_native_file)
check_exists(items_game_file)
check_exists(items_game_cdn_file)

items = cfgparser.load(items_game_file)
cdn_links = cfgparser.load_kv(items_game_cdn_file)
lang_en = cfgparser.load(lang_en_file, encoding="utf16")
lang_native = cfgparser.load(lang_native_file, encoding="utf16")

# print(json.dumps(list(items["items_game"]["rarities"].items()), indent=4))

total = len(items["items_game"]["paint_kits"].keys())
for i, paintkit in enumerate(items["items_game"]["paint_kits"].values()):
    name = paintkit["name"].lower()

    # Append l18n name
    if "description_tag" in paintkit and paintkit["description_tag"].startswith("#"):
        token = paintkit["description_tag"][1:].lower()
        try:
            paintkit["description_tag_en"] = lang_en["lang"]["tokens"][token]
            paintkit["description_tag_native"] = lang_native["lang"]["tokens"][token]
        except KeyError as e:
            logging.warning(f"Paintkit {name} have incorrect language tag: {e}")

    # Rarity
    try:
        paintkit["rarity"] = items["items_game"]["paint_kits_rarity"][name]
    except KeyError as e:
        logging.warning(f"Paintkit {name} has no defined rarity (expected {e})")

    # img from CDN
    paintkit["weapons"] = dict()
    for key, link in cdn_links.items():
        if key.endswith(name):
            weapon = key.replace(f"_{name}", "")[7:]
            output = res_dir / link.split("/")[-1]

            paintkit["weapons"][weapon] = {
                "link": link,
                "local": str(output)
            }

            if output.exists() is False:
                logging.info(f"Downloading {link}")
                response = requests.get(link)
                with output.open("wb+") as f:
                    f.write(response.content)

            # ct = ColorThief(output.absolute())
            # paintkit["weapons"][weapon]["palette"] = ct.get_palette(3)

            # sys palette
            ct = ColorThief(output.absolute())
            # rgb
            paintkit["weapons"][weapon]["palette_rgb"] = ct.get_palette(color_count=3, quality=1)
            # hsv
            paintkit["weapons"][weapon]["palette_hsv"] = list()
            for r, g, b in paintkit["weapons"][weapon]["palette_rgb"]:
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                paintkit["weapons"][weapon]["palette_hsv"].append(
                    (h * 360, s * 100, v * 100)
                )

    logging.info(f"Parsed {i} out of {total} paintkits")
    # print(json.dumps(paintkit, indent=4, ensure_ascii=False))


with open("items.json", "w+", encoding="utf-8") as f:
    json.dump(items, f, indent=4, ensure_ascii=False)
