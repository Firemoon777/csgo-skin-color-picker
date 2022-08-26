import json
import logging
from pathlib import Path
from typing import List

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)

import vtf2img

from skinextractor.model import Skin, SkinType, PaintStyle
from skinextractor.cfgwrapper import ItemsWrapper, CDNWrapper
from skinextractor.hlextractor import HLExtractor
from skinextractor.locale import LocaleWrapper
from skinextractor.texture import assembly_texture, calculate_palette
from skinextractor.utils import check_exists, download_image, write_json


class SkinExtractor:

    game_root: Path
    output_dir: Path
    res_dir: Path
    palette_dir: Path

    locale_en: LocaleWrapper
    locale_native: LocaleWrapper

    items: ItemsWrapper
    cdn: CDNWrapper

    colors: dict
    rarities: dict
    skins: List[Skin]

    def __init__(self, root: str, output: str, locale: str):
        self.game_root = Path(root)
        self.output_dir = Path(output)
        self.res_dir = self.output_dir / "res"
        self.res_dir.mkdir(exist_ok=True)
        self.palette_dir = self.res_dir / "palette"
        self.palette_dir.mkdir(exist_ok=True)

        self.locale_en = LocaleWrapper(self.game_root, "english")
        self.locale_native = LocaleWrapper(self.game_root, locale)

        self.vpk_dir = HLExtractor(self.game_root / "csgo" / "pak01_dir.vpk")

        self.items = ItemsWrapper(self.game_root / "csgo" / "scripts" / "items" / "items_game.txt")
        self.cdn = CDNWrapper(self.game_root / "csgo" / "scripts" / "items" / "items_game_cdn.txt")

        self.colors = dict()
        self.rarities = dict()
        self.skins = list()

    def extract_textures(self):
        logging.info("Extracting paints...")
        self.vpk_dir.extract("materials/models/weapons/customization/paints", str(self.res_dir))
        # logging.info("Extracting gloves paints...")
        # self.vpk_dir.extract("materials/models/weapons/customization/paints_gloves", str(self.res_dir))
        logging.info("Extracting stickers...")
        self.vpk_dir.extract("materials/models/weapons/customization/stickers", str(self.res_dir))

    def load_colors(self):
        logging.info("Loading colors...")
        for key, data in self.items("colors"):
            self.colors[key] = data["hex_color"]

    def load_rarities(self):
        logging.info("Loading rarities...")
        for key, data in self.items("rarities"):
            self.rarities[key] = {
                "loc_key": self.locale_native(data["loc_key"]),
                "loc_key_weapon": self.locale_native(data["loc_key_weapon"]),
                "loc_key_character": self.locale_native(data["loc_key_character"]),
                "color": self.colors[data["color"]]
            }

    def load_previews(self):
        logging.info("Downloading preview images...")
        for _, url in self.cdn.all():
            filename = url.split("/")[-1]
            local = self.res_dir / "preview" / filename
            download_image(url, local)

    def build_textures(self):
        logging.info("Building textures...")
        for _, pk in self.items("paint_kits"):
            if "style" in pk and PaintStyle(int(pk["style"])) == PaintStyle.default:
                continue

            assembly_texture(pk, self.res_dir)
            calculate_palette(pk, self.res_dir, self.palette_dir)

    def build_paint_kits(self):
        logging.info("Building paint kits info...")
        for _, pk in self.items("paint_kits"):
            if "style" in pk and PaintStyle(int(pk["style"])) == PaintStyle.default:
                # default and workshop_default
                continue

            s = Skin()
            s.id = pk["name"]
            s.name_en = self.locale_en(pk["description_tag"])
            s.name_native = self.locale_native(pk["description_tag"])
            s.style = PaintStyle(int(pk.get("style", 0)))
            s.pattern = pk.get("pattern")

            if "style" in pk:
                s.type = SkinType.weapon
            else:
                s.type = SkinType.gloves

            s.rarity = self.items.get_rarity_id(s.id)

            palette_file = self.palette_dir / f"{s.id}.json"
            if palette_file.exists() is False:
                continue
            # assert palette_file.exists() is True, f"{palette_file} doesn't exists!"

            with palette_file.open() as f:
                data = json.load(f)
                s.palette_rgb = data["palette_rgb"]
                s.palette_hsv = data["palette_hsv"]

            for weapon, data in self.cdn.find(s.id):
                s.items[weapon] = data

            self.skins.append(s)

    def build_sticker_textures(self):
        logging.info("Building sticker textures")

        for key, sticker in self.items("sticker_kits"):
            if key == "0":
                continue

            sticker_id = sticker["name"]
            pattern = sticker.get("sticker_material") or sticker.get("patch_material")
            assert pattern is not None

            vtf = self.res_dir / "stickers" / f"{pattern}.vtf"
            if vtf.exists() is False:
                continue

            out = self.res_dir / "preview" / f"{sticker_id}.png"
            if out.exists():
                continue

            parser = vtf2img.Parser(str(vtf))
            image = parser.get_image()
            image.save(out)


    def build_stickers(self):
        logging.info("Building sticker info...")
        for key, sticker in self.items("sticker_kits"):
            if key == "0":
                continue

            s = Skin()
            s.type = SkinType.sticker
            s.id = sticker["name"]
            s.name_en = self.locale_en(sticker["item_name"])
            s.name_native = self.locale_native(sticker["item_name"])
            s.rarity = sticker.get("item_rarity", "common")
            s.pattern = sticker.get("sticker_material") or sticker.get("patch_material")
            self.skins.append(s)

    def save(self, indent=None):
        logging.info("Saving jsons...")
        write_json(self.output_dir / "colors.json", self.colors, indent=indent)
        write_json(self.output_dir / "rarities.json", self.rarities, indent=indent)
        write_json(self.output_dir / "items.json", [skin.to_dict() for skin in self.skins], indent=indent)

    def run(self):
        # self.extract_textures()
        self.load_colors()
        self.load_rarities()
        self.load_previews()

        self.build_textures()
        self.build_paint_kits()

        self.build_sticker_textures()
        self.build_stickers()

        self.save(indent=4)


