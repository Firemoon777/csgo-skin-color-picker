import colorsys
import json
import logging
from pathlib import Path
from typing import Union, Tuple, List

from fastapi import FastAPI, Query
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

app = FastAPI()
app.mount("/res", StaticFiles(directory="res"), name="static")

templates = Jinja2Templates(directory="templates")
items = dict()


@app.on_event("startup")
def startup():
    global items
    items_file = Path("items.json")
    with items_file.open(encoding="utf-8") as f:
        items = json.load(f)


def get_delta_v(palette: list, color: list):
    for i in range(len(color), len(palette)):
        color.append(color[0])

    result = 0
    for i in range(len(palette)):
        ra, ga, ba = palette[i]
        rb, gb, bb = color[i]

        result += (ra - rb)**2 + (ga - gb)**2 + (ba- bb)**2

    return int(result**0.5)


@app.get("/")
def read_item(request: Request, color: List[str] = Query(default=[]), n: int = 3, mode: str = "hsv"):
    candidates = dict()

    if color:
        try:
            parsed_colors_rgb = []
            for c in color:
                if c.startswith("#"):
                    c = c[1:]
                parsed_colors_rgb.append((
                    int(c[0:2], 16),
                    int(c[2:4], 16),
                    int(c[4:6], 16),
                ))

            parsed_colors_hsv = []
            for r, g, b in parsed_colors_rgb:
                h, s,v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                parsed_colors_hsv.append(
                    (h * 360, s * 100, v * 100)
                )
        except:
            parsed_colors_rgb = [(0, 0, 0)]
            parsed_colors_hsv = [(0, 0, 0)]

        for paintkit in items["items_game"]["paint_kits"].values():
            if not paintkit["weapons"]:
                continue

            for weapon, weapon_data in paintkit["weapons"].items():
                logging.info(f"mode = {mode}")
                if mode == "hsv":
                    paintkit["weapons"][weapon]["delta"] = get_delta_v(
                        paintkit["weapons"][weapon]["palette_hsv"],
                        parsed_colors_hsv
                    )
                else:
                    paintkit["weapons"][weapon]["delta"] = get_delta_v(
                        paintkit["weapons"][weapon]["palette_rgb"],
                        parsed_colors_rgb
                    )

                if weapon not in candidates:
                    candidates[weapon] = list()

                palette_url = f"?mode={mode}"
                for r, g, b in paintkit["weapons"][weapon]["palette_rgb"]:
                    palette_url += f"&color={r:02x}{g:02x}{b:02x}"
                paintkit["weapons"][weapon]["palette_url"] = palette_url

                candidates[weapon].append(
                    paintkit
                )

        for weapon, pk_list in candidates.items():
            pk_list.sort(key=lambda x: x["weapons"][weapon]["delta"])
            candidates[weapon] = pk_list[:n]

    data = dict(request=request, candidates=candidates)

    return templates.TemplateResponse("index.html", data)
