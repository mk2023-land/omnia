"""Foto's van klanten opslaan en klaarmaken voor de AI.

Telefoonfoto's zijn vaak groter dan de AI accepteert (max. 5 MB); we verkleinen
ze tot hoogstens 1568 pixels aan de lange kant, dat is ook wat Claude zelf gebruikt.
"""

import io
import uuid
from pathlib import Path

from PIL import Image, ImageOps

MAX_ZIJDE = 1568


class FotoFout(Exception):
    pass


def verwerk(data: bytes, map_: Path) -> tuple[bytes, str, str]:
    """Geeft (jpeg-bytes, media_type, bestandsnaam) terug en slaat de foto op in map_."""
    try:
        beeld = Image.open(io.BytesIO(data))
        beeld = ImageOps.exif_transpose(beeld)  # telefoonfoto's rechtop zetten
    except Exception as fout:  # noqa: BLE001 - elk onleesbaar bestand
        raise FotoFout("Dit bestand is geen leesbare foto.") from fout

    beeld = beeld.convert("RGB")
    beeld.thumbnail((MAX_ZIJDE, MAX_ZIJDE))
    uit = io.BytesIO()
    beeld.save(uit, format="JPEG", quality=85)
    jpeg = uit.getvalue()

    map_.mkdir(parents=True, exist_ok=True)
    naam = f"{uuid.uuid4().hex}.jpg"
    (map_ / naam).write_bytes(jpeg)
    return jpeg, "image/jpeg", naam
