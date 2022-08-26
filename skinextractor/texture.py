import colorsys
import json
import logging
from pathlib import Path

import colorthief
import numpy as np
import vtf2img
from PIL import Image

from skinextractor import PaintStyle


def assembly_texture(pk: dict, res_dir: Path) -> None:
    if "style" not in pk:
        # No texture for gloves
        return

    style = PaintStyle(int(pk["style"])).name
    pattern = pk.get("pattern")

    if not pattern:
        return

    out_vtf = res_dir / "paints" / style / f"{pattern}.vtf"
    out_png = res_dir / "paints" / style / f"{pattern}.png"

    if out_png.exists():
        return

    parser = vtf2img.Parser(str(out_vtf))
    image = parser.get_image()

    if len(pk["color"]) == 4 and pk["style"] != "gunsmith" and pk["style"] != "antiqued":
        channels = image.split()
        channels = channels[:3]

        texture = Image.new("RGB", (parser.header.width, parser.header.height), get_color(pk, 0))

        for index, mask in enumerate(channels, 1):
            filler = Image.new("RGB", (parser.header.width, parser.header.height), get_color(pk, index))
            texture = Image.composite(filler, texture, mask)
    else:
        texture = image

    if texture.mode in ('RGBA', 'LA') or (texture.mode == 'P' and 'transparency' in texture.info):
        arr = np.array(texture)
        arr[..., 3] = 255
        texture = Image.fromarray(arr)

    try:
        with out_png.open("wb+") as tmp:
            texture.save(tmp, "PNG")
    except Exception as e:
        print(f"{pk} triggered general fallback")
        raise e


def calculate_palette(pk: dict, res_dir: Path, palette_dir: Path) -> None:
    pk_id = pk["name"]
    pattern = pk.get("pattern")

    palette_file = palette_dir / f"{pk_id}.json"
    if palette_file.exists() is True:
        return

    result = dict()

    if pattern:
        style = PaintStyle(int(pk["style"])).name
        file = res_dir / "paints" / style / f"{pattern}.png"
        assert file.exists() is True, f"{file} is not exists"

        with file.open("rb") as f:
            cf = colorthief.ColorThief(f)
            result["palette_rgb"] = cf.get_palette(color_count=3, quality=1)
    else:
        if "color0" not in pk:
            return

        result["palette_rgb"] = []
        for i in range(0, 4):
            if f"color{i}" in pk:
                color_str = pk[f"color{i}"]
                channels = color_str.strip().split(" ")
                result["palette_rgb"].append(
                    (int(channels[0]), int(channels[1]), int(channels[2]))
                )

        l = len(result["palette_rgb"])
        for i in range(l, 4):
            result["palette_rgb"].append(result["palette_rgb"][i % l])

    result["palette_hsv"] = []

    for r, g, b in result["palette_rgb"]:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        result["palette_hsv"].append(
            (h * 360, s * 100, v * 100)
        )

    with palette_file.open("w+") as f:
        json.dump(result, f, indent=4)