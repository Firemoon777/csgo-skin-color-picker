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

    response = requests.get(url)
    with output.open("wb+") as f:
        f.write(response.content)
