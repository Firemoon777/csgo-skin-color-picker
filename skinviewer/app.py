import colorsys
import json
from pathlib import Path
from typing import Union, Tuple

from fastapi import FastAPI
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


def get_delta_rgb(palette: list, color: Tuple[int, int, int]):
    best = 3 * (255 ** 2)

    r, g, b = color
    for wr, wg, wb in palette:
        best = min((r - wr) ** 2 + (g - wg) ** 2 + (b - wb) ** 2, best)

    return int(best**0.5)


def get_delta_hsv(palette: list, color: Tuple[int, int, int]):
    best = 3 * (255 ** 2)

    r, g, b = color
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = h * 255

    best = 255

    for wr, wg, wb in palette:
        wh, ws, wv = colorsys.rgb_to_hsv(wr / 255, wg / 255, wb / 255)
        wh = wh * 255

        best = min(abs(h - wh), best)

    return int(best)


@app.get("/")
def read_item(request: Request, color: str = None, threshold: int = 50, mode: str = "hsv"):
    candidates = dict()

    if color:
        try:
            color = color[1:]
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
        except:
            r, g, b = 0, 0, 0

        for paintkit in items["items_game"]["paint_kits"].values():
            if not paintkit["weapons"]:
                continue

            for weapon, weapon_data in paintkit["weapons"].items():
                if mode == "hsv":
                    paintkit["weapons"][weapon]["delta"] = get_delta_hsv(paintkit["weapons"][weapon]["palette"], (r, g, b))
                else:
                    paintkit["weapons"][weapon]["delta"] = get_delta_rgb(paintkit["weapons"][weapon]["palette"], (r, g, b))

                if paintkit["weapons"][weapon]["delta"] <= threshold:
                    if weapon not in candidates:
                        candidates[weapon] = list()
                    candidates[weapon].append(
                        paintkit
                    )

        for weapon, pk_list in candidates.items():
            pk_list.sort(key=lambda x: x["weapons"][weapon]["delta"])

    data = dict(request=request, candidates=candidates)

    return templates.TemplateResponse("index.html", data)
