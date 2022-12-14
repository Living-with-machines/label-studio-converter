from PIL import Image

import requests

from ls_converter import __version__, LabelStudioConverter, Input, Levels
from ls_converter.utils import url_to_tesseract_data, url_to_image


PUBLIC_URL = "http://specialcollections.le.ac.uk/iiif/2/p16445coll4:8897/full/730,/0/default.jpg?page=27"  # noqa


def test_version():
    assert __version__ == "0.0.2"


def test_url_returns_bytes(url=PUBLIC_URL):
    """Ensure publicly available URL actually exists and returns."""
    r = requests.get(PUBLIC_URL)
    assert r.status_code == 200
    assert isinstance(r.content, bytes)


def test_tesseract(url=PUBLIC_URL):
    converter = LabelStudioConverter(input_format=Input.TESSERACT)

    data = converter.convert(
        image=url,
        input_data=url_to_tesseract_data(url),
    )

    assert data
    assert isinstance(data, dict)

    # The url provided should be embedded in the result
    assert data["data"]["ocr"] == url

    # All scores should be floats or integers (0)
    assert all(
        [isinstance(x["score"], (float, int)) for x in data["predictions"]]
    )

    # All results from_names should be either "bbox" or "transcription"
    assert all(
        [
            (
                result["from_name"] == "bbox"
                or result["from_name"] == "transcription"
            )
            for x in data["predictions"]
            for result in x["result"]
        ]
    )

    # All results to_names should be "image"
    assert all(
        [
            result["to_name"] == "image"
            for x in data["predictions"]
            for result in x["result"]
        ]
    )

    # All results types should be "textarea" or "rectangle"
    assert all(
        [
            (result["type"] == "textarea" or result["type"] == "rectangle")
            for x in data["predictions"]
            for result in x["result"]
        ]
    )


def test_levels():
    assert Levels.page_num == 1
    assert Levels.block_num == 2
    assert Levels.par_num == 3
    assert Levels.line_num == 4
    assert Levels.word_num == 5


def test_url_to_tesseract_data(url=PUBLIC_URL):
    data = url_to_tesseract_data(PUBLIC_URL)

    assert isinstance(data, dict)
    assert sorted(list(data.keys())) == [
        "block_num",
        "conf",
        "height",
        "left",
        "level",
        "line_num",
        "page_num",
        "par_num",
        "text",
        "top",
        "width",
        "word_num",
    ]


def test_url_to_image(url=PUBLIC_URL):
    im = url_to_image(PUBLIC_URL)
    assert isinstance(im, Image.Image)
