from ls_converter import __version__, LabelStudioConverter, Input, Levels
from ls_converter.utils import url_to_tesseract_data
import requests

PUBLIC_URL = "http://specialcollections.le.ac.uk/iiif/2/p16445coll4:8897/full/730,/0/default.jpg?page=27"  # noqa


def test_version():
    assert __version__ == "0.0.1"


def test_url():
    """Ensure publicly available URL actually exists and works (for test_tesseract)"""
    r = requests.get(PUBLIC_URL)
    assert r.status_code == 200
    assert isinstance(r.content, bytes)


def test_tesseract():
    converter = LabelStudioConverter(input_format=Input.TESSERACT)

    data = converter.convert(
        image=PUBLIC_URL,
        input_data=url_to_tesseract_data(PUBLIC_URL),
    )

    assert data
    assert isinstance(data, dict)


def test_levels():
    assert Levels.page_num == 1
    assert Levels.block_num == 2
    assert Levels.par_num == 3
    assert Levels.line_num == 4
    assert Levels.word_num == 5
