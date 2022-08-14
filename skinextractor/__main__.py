import colorsys
import logging

from joblib import Parallel, delayed

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)

import argparse
import json
from pathlib import Path

from skinextractor import cfgparser
from skinextractor.const import PaintStyle
from skinextractor.texture import calculate_texture
from skinextractor.utils import check_exists, download_image


logging.error("123")

parser = argparse.ArgumentParser(description='Extracts skins from CS:GO')
parser.add_argument("--game-root", type=str, required=True)
parser.add_argument("--output", type=str, required=False, default=None)
parser.add_argument("--locale", type=str, required=False, default="russian")

args = parser.parse_args()

base_dir = Path(args.game_root)

if args.output:
    output_dir = Path(args.output)
else:
    output_dir = Path(".")

logging.info(f"Checking gamefiles in {base_dir}")

lang_en_file = base_dir / "csgo" / "resource" / "csgo_english.txt"
lang_native_file = base_dir / "csgo" / "resource" / f"csgo_{args.locale}.txt"
items_game_file = base_dir / "csgo" / "scripts" / "items" / "items_game.txt"
items_game_cdn_file = base_dir / "csgo" / "scripts" / "items" / "items_game_cdn.txt"
materials_vpk = base_dir / "csgo" / "pak01_dir.vpk"

check_exists(lang_en_file)
check_exists(lang_native_file)
check_exists(items_game_file)
check_exists(items_game_cdn_file)
check_exists(materials_vpk)

output_dir.mkdir(exist_ok=True)
res_dir = output_dir / "res"
res_dir.mkdir(exist_ok=True)

logging.info("Loading items...")
items = cfgparser.load(items_game_file)

logging.info("Loading CDN urls...")
cdn_links = cfgparser.load_kv(items_game_cdn_file)

logging.info("Loading english locale...")
lang_en = cfgparser.load(lang_en_file, encoding="utf16")

logging.info(f"Loading {args.locale} locale...")
lang_native = cfgparser.load(lang_native_file, encoding="utf16")

logging.info("Building rarity file")
rarities = dict()

for name, data in items["items_game"]["rarities"].items():
    display_name_token = data["loc_key_weapon"].lower()
    color_token = data["color"].lower()

    try:
        rarities[name] = {
            "name": lang_native["lang"]["tokens"][display_name_token],
            "color": items["items_game"]["colors"][color_token]["hex_color"]
        }
    except KeyError:
        pass

logging.info(f"Saving rarities to rarities.json")
with open("rarities.json", "w+", encoding="utf-8") as f:
    json.dump(rarities, f, indent=4, ensure_ascii=False)

total = len(items["items_game"]["paint_kits"])
logging.info(f"Found {total} paint kits")
logging.info("Collecting skins info")

paint_kits = []

for pk in items["items_game"]["paint_kits"].values():
    parsed = dict()

    # skin id
    name_id = pk["name"].lower()
    parsed["id"] = name_id

    # Append l18n name
    if "description_tag" in pk and pk["description_tag"].startswith("#"):
        token = pk["description_tag"][1:].lower()
        try:
            parsed["name_en"] = lang_en["lang"]["tokens"][token]
            parsed["name_native"] = lang_native["lang"]["tokens"][token]
        except KeyError as e:
            logging.warning(f"Paint kit {name_id} have incorrect language tag: {e}")

    # Pattern
    if "style" in pk:
        # weapon
        parsed["style"] = PaintStyle(int(pk["style"])).name
        parsed["pattern"] = pk.get("pattern")
    elif "vmt_path" in pk:
        # gloves
        continue

    # Colors for specific styles
    parsed["color"] = list()
    for i in range(4):
        color_id = f"color{i}"
        if color_id in pk:
            parsed["color"].append(pk[color_id])
        else:
            break

    # Rarity
    parsed["rarity"] = items["items_game"]["paint_kits_rarity"].get(name_id)

    # Placeholder for suitable weapons
    parsed["items"] = dict()

    paint_kits.append(parsed)

logging.info("Binding items with paint kits...")
for pk in paint_kits:
    pk_id = pk["id"]

    for key, url in cdn_links.items():
        suffix = f"_{pk_id}"

        if key.endswith(suffix) is False:
            continue

        item_id = key.replace(suffix, "")
        img_name = url.split("/")[-1]
        local = res_dir / img_name

        download_image(url, local)

        pk["items"][item_id] = {
            "link": url,
            "local": str(local)
        }


def calculate_palette(i:int, pk: dict):
    logging.info(f"Done {i} out of {total} paint kits, now: {pk['id']}")
    if pk["style"] == "default":
        return

    # if pk["id"] != "sp_hazard_bravo":
    #     continue

    try:
        pk["palette_rgb"] = calculate_texture(pk, materials_vpk)
    except Exception as e:
        print(f"{pk['id']} raises exception: {e}")
        return

    pk["palette_hsv"] = []
    for r, g, b in pk["palette_rgb"]:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        pk["palette_hsv"].append(
            (h * 360, s * 100, v * 100)
        )


# Calculate textures
# Parallel(n_jobs=12)(delayed(calculate_palette)(i, pk) for i, pk in enumerate(paint_kits))
for i, pk in enumerate(paint_kits):
    calculate_palette(i, pk)

logging.info(f"Saving paint kits to paint_kits.json...")

with open("paint_kits.json", "w+", encoding="utf-8") as f:
    json.dump(paint_kits, f, indent=4, ensure_ascii=False)
