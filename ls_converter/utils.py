from .errors import (
    ExpatError,
    NotAnInteger,
    RequirePyTesseract,
    UnexpectedHTTPResponse,
    UnexpectedType,
    UnidentifiedImageError,
)

from io import BytesIO
from pathlib import Path
from PIL import Image
from uuid import uuid4
from typing import Union

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
) -> dict:
    """
    Given a URL to a valid image, this is a shortcut to provide the
    PyTesseract's image_to_data function's dict response.
    """

    # First, ensure PyTesseract is installed
    try:
        from pytesseract import image_to_data, Output
    except ImportError:
        raise RequirePyTesseract()

    # Download image
    image = url_to_image(url)

    # Return Tesseract's interpretation of the image
    return image_to_data(image, output_type=Output.DICT, **config)


def url_to_image(url: str, fail: bool = False) -> Union[Image.Image, str]:
    """
    Given a URL to a valid image, this is a shortcut function that provides
    the URL's contents as a PIL.Image object. If fail is False, it will not
    crash but return back the url.
    """

    # Get response
    response = requests.get(url)

    # Check for correct response code
    if response.status_code != 200:
        raise RuntimeError(
            f"{url} returned status code {response.status_code}."
        )

    # Try parsing the content as bytes
    if not isinstance(response.content, bytes):
        if fail is False:
            return url

        raise UnexpectedHTTPResponse(url)

    # Try opening content as in-memory bytes buffer
    try:
        b = BytesIO(response.content)
    except TypeError:
        if fail is False:
            return url

        raise TypeError(
            f"Unexpected content received from attempt to download {url}."
        )

    # Try opening as PIL.Image
    try:
        return Image.open(b)
    except UnidentifiedImageError:
        if fail is False:
            return url

    raise UnidentifiedImageError(f"Unable to load image from {url}")


def set_int(val: Union[int, str]) -> int:
    """
    Given a value, ensures that it is an integer. If impossible, raises a
    NotAnInteger exception with explanation.
    """

    # Return fast if already integer
    if isinstance(val, int):
        return val

    # Try to return integer
    try:
        return int(val)
    except ValueError:
        raise NotAnInteger(val)


def get_bbox(
    x: Union[int, str],
    y: Union[int, str],
    width: Union[int, str],
    height: Union[int, str],
    image_width: Union[int, str],
    image_height: Union[int, str],
    rotation: Union[int, str] = 0,
) -> dict:
    """
    Given a x, y, width, height, and rotation value, together with the total
    image width and image height, this function ensures all types are set
    correctly and returns a dictionary with the information correctly
    formatted for Label Studio.

    (See also get_get_bbox_result.)
    """

    # Ensure all integers are set up correctly
    x = set_int(x)
    y = set_int(y)
    width = set_int(width)
    height = set_int(height)
    image_width = set_int(image_width)
    image_height = set_int(image_height)
    rotation = set_int(rotation)

    # Return correct format
    return {
        "x": 100 * x / image_width,
        "y": 100 * y / image_height,
        "width": 100 * width / image_width,
        "height": 100 * height / image_height,
        "rotation": rotation,
    }


def get_bbox_result(id: str, bbox: dict) -> dict:
    """
    Given an id and a bbox item (see get_bbox), this function ensures a
    dictionary with the information correctly formatted for Label Studio is
    returned.
    """

    # Return correct format
    return {
        "id": id,
        "from_name": "bbox",
        "to_name": "image",
        "type": "rectangle",
        "value": bbox,
    }


def get_transcription_result(
    id: str,
    bbox: dict,
    text: Union[list, str],
    score: int,
    line_delimiter: str = "\n",
) -> dict:
    """
    Given an id, a bbox (see get_bbox), the text (either as string or as list)
    and a score, this function ensures all types are set correctly and returns
    a dictionary with the information correctly formatted for Label Studio.

    (See also get_get_bbox_result.)
    """

    if not isinstance(line_delimiter, str):
        raise SyntaxError("Provided line delimiter must be a string.")

    # If text is line, join using line_delimiter and strip the resulting text
    if isinstance(text, list):
        text = line_delimiter.join(text).strip()

    # Check that text is now string
    if not isinstance(text, str):
        raise SyntaxError("Expected text to be string.")

    # Return correct format
    return {
        "id": id,
        "from_name": "transcription",
        "to_name": "image",
        "type": "textarea",
        "value": dict(text=[text], **bbox),
        "score": score,
    }


def get_id(length: Union[int, str] = 10) -> str:
    """
    Returns a string representation of a UUID4, of a given length.
    """

    # Ensure length is an integer
    length = set_int(length)

    # Ensure id string
    return str(uuid4())[:length]


def open_image(image_path: str, fail: bool = False) -> Union[Image.Image, str]:
    """
    Given an image_path, this function will ensure that the file exists, and
    try to return it as a PIL.Image object. If fail is set to False, it will
    not crash but return the image_path back.
    """

    # Check if the image_path exists
    if not Path(image_path).exists():
        raise FileNotFoundError(image_path)

    # Try returning it as a PIL.Image object
    try:
        return Image.open(image_path)
    except UnidentifiedImageError:
        if fail is False:
            return image_path

        raise UnidentifiedImageError(f"Unable to open image {image_path}")


def load_contents(path: Path) -> str:
    """
    Given a path, ensures that the path exists and returns the plain text from
    the path.
    """

    # Check if path exists
    if not path.exists():
        raise FileNotFoundError(f"File could not be found: {path}.")

    # Read contents
    return path.read_text()


def load_json(path: str, fail: bool = False) -> Union[dict, str]:
    """
    Given a path, this function will return its contents as a dictionary. If
    fail is set to False, it will not crash if an error occurs but return the
    path back.

    If provided something with a .xml file ending, it will return the results
    from load_xml_as_json (see below).
    """

    # If path looks like XML, call the correct function
    if Path(path).suffix == ".xml":
        return load_xml_as_json(path, fail=fail)

    # Load contents
    contents = load_contents(path)

    # Return parsed contents as dictionary or fail
    try:
        return json.loads(contents)
    except json.JSONDecodeError:
        if fail is False:
            return path

        raise json.JSONDecodeError(f"JSON could not be loaded from {path}.")


def load_xml_as_json(path: str, fail: bool = False) -> Union[dict, str]:
    """
    Given a path, this function will return its contents as a dictionary
    (parsed using xmltodict). If fail is set to False, it will not crash if an
    error occurs but return the path back.
    """

    # Load contents
    contents = load_contents(path)

    # Return parsed contents as dictionary or fail
    try:
        return xmltodict.parse(contents)
    except ExpatError:
        if fail is False:
            return path

        raise ExpatError(f"XML could not be loaded from {path}.")


def save_json(data: Union[dict, list], path: str) -> True:
    """
    Given a dictionary or list (data) and a path, this function will ensure
    that the parent directory exists, and that the data passed will be saved
    as a JSON file in the path provided.

    Returns True when finished.
    """

    # Make path into Path object
    if isinstance(path, str):
        path = Path(path)

    if not isinstance(path, Path):
        raise UnexpectedType(f"{type(path)} instead of Path.")

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON to path
    path.write_text(json.dumps(data))

    return True
