import argparse

from skinextractor import SkinExtractor


parser = argparse.ArgumentParser(description='Extracts skins from CS:GO')
parser.add_argument("--game-root", type=str, required=True)
parser.add_argument("--output", type=str, required=False, default=".")
parser.add_argument("--locale", type=str, required=False, default="russian")

args = parser.parse_args()

SkinExtractor(
    root=args.game_root,
    output=args.output,
    locale=args.locale
).run()