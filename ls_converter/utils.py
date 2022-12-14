from .errors import (
    RequirePyTesseract,
    UnidentifiedImageError,
    ExpatError,
    UnexpectedType,
)

from io import BytesIO
from PIL import Image
from uuid import uuid4
from pathlib import Path

import json
import requests
import xmltodict


def url_to_tesseract_data(
    url: str,
    config: dict = {
        "lang": None,
        "config": "",
        "nice": 0,
        "timeout": 0,
    },
):
    """
    Given a URL to a valid image, this is a shortcut to provide the
    PyTesseract's image_to_data function's dict response.
    """

    try:
        from pytesseract import image_to_data, Output
    except ImportError:
        raise RequirePyTesseract()

    # Download image
    image = url_to_image(url)

    # Return Tesseract's interpretation of the image
    return image_to_data(image, output_type=Output.DICT, **config)


def url_to_image(url: str, fail: bool = False) -> Image.Image:
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(
            f"{url} returned status code {response.status_code}."
        )

    try:
        bytes = BytesIO(response.content)
    except TypeError:
        if fail is False:
            return url

        raise TypeError(
            f"Unexpected content received from attempt to download {url}."
        )

    try:
        return Image.open(bytes)
    except UnidentifiedImageError:
        if fail is False:
            return url

        raise UnidentifiedImageError(f"Unable to load image from {url}")


def get_bbox(
    x: int,
    y: int,
    width: int,
    height: int,
    image_width: int,
    image_height: int,
    rotation: int = 0,
) -> dict:
    if not isinstance(x, int):
        try:
            x = int(x)
        except ValueError:
            raise ValueError(
                f"An incorrect x value was passed: {x} (not an int)"
            )

    if not isinstance(y, int):
        try:
            y = int(y)
        except ValueError:
            raise ValueError(
                f"An incorrect y value was passed: {y} (not an int)"
            )

    if not isinstance(width, int):
        try:
            width = int(width)
        except ValueError:
            raise ValueError(
                f"An incorrect width value was passed: {width} (not an int)"
            )

    if not isinstance(height, int):
        try:
            height = int(height)
        except ValueError:
            raise ValueError(
                f"An incorrect height value was passed: {height} (not an int)"
            )

    if not isinstance(image_width, int):
        try:
            image_width = int(image_width)
        except ValueError:
            raise ValueError(
                f"An incorrect image_width value was passed: {image_width} (not an int)"  # noqa
            )

    if not isinstance(image_height, int):
        try:
            image_height = int(image_height)
        except ValueError:
            raise ValueError(
                f"An incorrect image_height value was passed: {image_height} (not an int)"  # noqa
            )

    if not isinstance(rotation, int):
        try:
            rotation = int(rotation)
        except ValueError:
            raise ValueError(
                f"An incorrect rotation value was passed: {rotation} (not an int)"  # noqa
            )

    return {
        "x": 100 * x / image_width,
        "y": 100 * y / image_height,
        "width": 100 * width / image_width,
        "height": 100 * height / image_height,
        "rotation": rotation,
    }


def get_bbox_result(id, bbox):
    return {
        "id": id,
        "from_name": "bbox",
        "to_name": "image",
        "type": "rectangle",
        "value": bbox,
    }


def get_transcription_result(id, bbox, text, score):
    if isinstance(text, list):
        text = "\n".join(text).strip()

    if not isinstance(text, str):
        raise SyntaxError("Expected text to be string.")

    return {
        "id": id,
        "from_name": "transcription",
        "to_name": "image",
        "type": "textarea",
        "value": dict(text=[text], **bbox),
        "score": score,
    }


def get_id(length=10):
    return str(uuid4())[:length]


def open_image(image: str, fail: bool = False):
    if not Path(image).exists():
        raise FileNotFoundError(image)

    try:
        return Image.open(image)
    except UnidentifiedImageError:
        if fail is False:
            return image

        raise UnidentifiedImageError(f"Unable to open image {image}")


def load_json(path: str, fail: bool = False):
    if Path(path).exists():
        contents = Path(path).read_text()

        try:
            return json.loads(contents)
        except json.JSONDecodeError:
            if fail is False:
                return path

            raise json.JSONDecodeError(
                f"JSON could not be loaded from {path}."
            )
    else:
        raise FileNotFoundError(f"File could not be found: {path}.")


def load_xml_as_json(path: str, fail: bool = False):
    if Path(path).exists():
        contents = Path(path).read_text()

        try:
            return xmltodict.parse(contents)
        except ExpatError:
            if fail is False:
                return path

            raise ExpatError(f"XML could not be loaded from {path}.")

    else:
        raise FileNotFoundError(f"File could not be found: {path}.")


def save_json(data: dict, path: str) -> True:
    if isinstance(path, str):
        path = Path(path)

    if not isinstance(path, Path):
        raise UnexpectedType(f"{type(path)} instead of Path.")

    path.write_text(json.dumps(data))

    return True
