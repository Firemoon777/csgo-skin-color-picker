import json
import logging
from pathlib import Path

import requests


def check_exists(f: Path):
    if f.exists() is False:
        logging.error(f"{f} not exists!")
        exit(1)


def download_image(url: str, output: Path):
    if output.exists():
        return

    logging.info(f"Downloading {url}")
    response = requests.get(url)
    with output.open("wb+") as f:
        f.write(response.content)


def write_json(file: Path, payload, indent=None) -> None:
    with file.open("w+", encoding="utf-8") as f:
        json.dump(payload, f, indent=indent, ensure_ascii=False)