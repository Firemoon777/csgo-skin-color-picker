import io
import logging
import os
from pathlib import Path
from typing import Tuple, List

import colorthief
import vtf2img
from PIL import Image

from skinextractor.hlextractor import HLExtractor


def get_color(pk, index) -> Tuple[int, int, int]:
    channels = pk["color"][index].strip().split(" ")
    return int(channels[0]), int(channels[1]), int(channels[2])


def assembly_texture(pk: dict, vpk: Path) -> List[Tuple[int, int, int]]:
    style = pk["style"]
    pattern = pk["pattern"]

    vpk_path = f"materials/models/weapons/customization/paints/{style}/{pattern}.vtf"
    logging.debug(f"Extracting {vpk_path}")

    hl = HLExtractor()
    extracted = hl.extract_single(vpk, vpk_path)

    parser = vtf2img.Parser(extracted)
    image = parser.get_image()

    if len(pk["color"]) != 0:
        channels = image.split()
        channels = channels[:3]

        texture = Image.new("RGB", (parser.header.width, parser.header.height), get_color(pk, 0))

        for index, mask in enumerate(channels, 1):
            filler = Image.new("RGB", (parser.header.width, parser.header.height), get_color(pk, index))
            texture = Image.composite(filler, texture, mask)
    else:
        texture = image

    os.remove(extracted.absolute())

    try:
        with io.BytesIO() as tmp:
            texture.save(tmp, "PNG")
            cf = colorthief.ColorThief(tmp)
            return cf.get_palette(color_count=3, quality=1)
    except Exception:
        # fallback for fully transparent skins
        alpha_composite = texture.convert("RGB")

        with io.BytesIO() as tmp:
            alpha_composite.save(tmp, "JPEG")
            cf = colorthief.ColorThief(tmp)
            return cf.get_palette(color_count=3, quality=1)


def calculate_texture(pk: dict, vpk: Path) -> List[Tuple[int, int, int]]:
    if not pk["pattern"]:
        l = len(pk["color"])
        return [get_color(pk, i % l) for i in range(4)]

    return assembly_texture(pk, vpk)

