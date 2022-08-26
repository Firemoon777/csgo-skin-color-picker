import enum
from typing import Tuple, List, Dict


class PaintStyle(enum.IntEnum):
    default = 0
    solid_color = 1
    hydrographic = 2
    spray = 3
    anodized = 4
    anodized_multi = 5
    anodized_air = 6
    custom = 7
    antiqued = 8
    gunsmith = 9


class SkinType(enum.Enum):
    weapon = "WEAPON"
    gloves = "GLOVES"
    sticker = "STICKER"


class Skin:
    type: SkinType
    id: str
    name_en: str
    name_native: str
    style: PaintStyle
    pattern: str
    rarity: str
    file: str
    palette_rgb: List[Tuple[int, int, int]]
    palette_hsv: List[Tuple[int, int, int]]

    items: Dict[str, Dict[str, str]]

    def __init__(self):
        self.style = PaintStyle.default
        self.palette_hsv = list()
        self.palette_rgb = list()
        self.items = dict()

    def to_dict(self) -> dict:
        return dict(
            type=self.type.value,
            id=self.id,
            name_en=self.name_en,
            name_native=self.name_native,
            style=self.style.name,
            pattern=self.pattern,
            rarity=self.rarity,
            file=self.file,
            palette_rgb=self.palette_rgb,
            palette_hsv=self.palette_hsv,
            items=self.items
        )
