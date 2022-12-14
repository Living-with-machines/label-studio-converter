__version__ = "0.0.1"

from .errors import (
    IncorrectImageFormat,
    IncorrectInputDataFormat,
    IncorrectlyFormattedInputData,
    IncorrectURLFormat,
    MultipageABBYY,
    MultipleBlocks,
    NoSuchConverter,
    PerLevelIncorrect,
    URLNotSet,
)
from .meta import Input, Levels
from .utils import (
    get_bbox_result,
    get_bbox,
    get_id,
    get_transcription_result,
    load_json,
    load_xml_as_json,
    open_image,
    url_to_image,
)

from PIL import Image
from typing import Union

import warnings


class LabelStudioConverter:
    """
    LabelStudioConverter parent converter class.
    (Inherited by ABBYYConverter, TranskribusConverter, TesseractConverter)
    """

    def __init__(self, input_format: Input = Input.TESSERACT):
        if not input_format:
            raise RuntimeError("input_format must be set.")

        if input_format not in [
            Input.TESSERACT,
            Input.ABBYY,
            Input.TRANSKRIBUS,
        ]:
            warnings.warn(f"input_format {input_format} is not implemented.")

        self.input_format = input_format

    def set_converter(self):
        if self.input_format == Input.TESSERACT:
            return TesseractConverter()
        elif self.input_format == Input.ABBYY:
            return ABBYYConverter()
        elif self.input_format == Input.TRANSKRIBUS:
            return TranskribusConverter()

        raise NoSuchConverter()

    def assertion(
        self, input_data: dict, image: Image.Image, url: str, **kwargs
    ) -> True:
        if not isinstance(input_data, dict):
            raise IncorrectInputDataFormat()

        if not isinstance(image, Image.Image):
            raise IncorrectImageFormat()

        if url and not isinstance(url, str):
            raise IncorrectURLFormat()

        if not len(input_data):
            raise SyntaxError(
                "Input data looks empty. Did you provide the correct data?"
            )

        return True

    def convert(
        self,
        image: Union[Image.Image, str],
        input_data: Union[dict, str],
        url: Union[str, None] = None,
        **kwargs,
    ) -> dict:
        # Start up the converter
        converter = self.set_converter()

        # If we get an image string, we try to open it (from URL or local).
        # Fail silently because it will otherwise be caught by assertion.
        if isinstance(image, str):
            if image.startswith("http") and url is None:
                url = image
                image = url_to_image(image)
            else:
                if url is None:
                    warnings.warn(
                        URLNotSet.MESSAGE,
                        URLNotSet,
                    )

                image = open_image(image)
                if isinstance(image, Image.Image) and url is None:
                    url = image.filename

        # If we get an input data string, we try to open it as a JSON file.
        # Fail silently because it will otherwise be caught by assertion.
        if isinstance(input_data, str):
            input_data = load_json(input_data)

        # If we still have an input data string, we try to open it as a XML
        # file (to a dict object).
        # Fail silently because it will otherwise be caught by assertion.
        if isinstance(input_data, str):
            input_data = load_xml_as_json(input_data)

        # Test whether types are correctly set up
        self.assertion(input_data, image, url)
        converter.assertion(input_data, image, url, **kwargs)

        # Pass on convert method to the converter class
        return converter.convert(input_data, image, url, **kwargs)


class ABBYYConverter(LabelStudioConverter):
    """
    ABBYY converter class.
    """

    @classmethod
    def assertion(self, input_data, image, url, **kwargs) -> True:
        if len(input_data["layout"]["pages"]) > 1:
            raise MultipageABBYY()

        for paragraph in input_data["content"]["paragraphs"]:
            if (
                not len([x["blockId"] for x in paragraph["layoutReferences"]])
                == 1
            ):
                raise MultipleBlocks()

        return True

    @classmethod
    def convert(self, input_data: dict, image: Image.Image, url=None):
        results, all_scores = [], []

        image_width, image_height = image.size

        page = input_data["layout"]["pages"][0]  # asserted in self.assertion
        blocks = {x["id"]: x for x in page["texts"]}

        # Extract all text from text blocks
        block_content = {key: [] for key in blocks.keys()}
        for paragraph in input_data["content"]["paragraphs"]:
            blockId = [x["blockId"] for x in paragraph["layoutReferences"]][0]
            block_content[blockId] += [(paragraph["text"], paragraph["role"])]

        for blockId, block_data in blocks.items():
            region_id = get_id()

            bbox = get_bbox(
                x=block_data["position"]["l"],
                y=block_data["position"]["t"],
                width=(
                    block_data["position"]["r"] - block_data["position"]["l"]
                ),
                height=(
                    block_data["position"]["b"] - block_data["position"]["t"]
                ),
                image_width=image_width,
                image_height=image_height,
            )

            bbox_result = get_bbox_result(region_id, bbox)

            # Collate all texts into `texts` list
            texts = [x[0] for x in block_content[blockId]]

            transcription_result = get_transcription_result(
                region_id, bbox, texts, score=block_data["confidence"]
            )

            # Extend/append all results and scores
            results.extend([bbox_result, transcription_result])
            all_scores.append(transcription_result["score"])

        score = sum(all_scores) / len(all_scores) if all_scores else 0

        return {
            "data": {"ocr": url},
            "predictions": [
                {
                    "result": results,
                    "score": score,
                }
            ],
        }


class TranskribusConverter(LabelStudioConverter):
    """
    Transkribus converter class.
    """

    @classmethod
    def assertion(
        self, input_data: dict, image: Image.Image, url: str
    ) -> True:
        try:
            input_data["alto"]["Layout"]["Page"]["PrintSpace"]["TextBlock"]
        except KeyError:
            raise IncorrectlyFormattedInputData(
                "It it valid output from Transkribus?"
            )

        return True

    @classmethod
    def convert(self, input_data: dict, image: Image.Image, url=None) -> dict:
        results, all_scores = [], []

        image_width, image_height = image.size

        page = input_data["alto"]["Layout"]["Page"]
        textblocks = page["PrintSpace"]["TextBlock"]

        for block in textblocks:
            region_id = get_id()

            bbox = get_bbox(
                x=block["@HPOS"],
                y=block["@VPOS"],
                width=block["@WIDTH"],
                height=block["@HEIGHT"],
                image_width=image_width,
                image_height=image_height,
            )

            bbox_result = get_bbox_result(region_id, bbox)

            # Collate all text into `texts` list
            texts = [line["String"]["@CONTENT"] for line in block["TextLine"]]

            transcription_result = get_transcription_result(
                region_id, bbox, texts, score=0
            )

            # Extend/append all results and scores
            results.extend([bbox_result, transcription_result])
            all_scores.append(transcription_result["score"])

        score = sum(all_scores) / len(all_scores) if all_scores else 0

        return {
            "data": {"ocr": url},
            "predictions": [
                {
                    "result": results,
                    "score": score,
                }
            ],
        }


class TesseractConverter(LabelStudioConverter):
    @classmethod
    def assertion(self, input_data, image, url, **kwargs) -> True:
        if kwargs.get("per_level") and not isinstance(
            kwargs["per_level"], int
        ):
            raise PerLevelIncorrect()

        return True

    @classmethod
    def convert(
        self, input_data: dict, image: Image.Image, url=None, **kwargs
    ) -> dict:
        results, all_scores = [], []

        image_width, image_height = image.size

        if kwargs.get("per_level"):
            per_level = kwargs["per_level"]
        else:
            per_level = Levels.block_num

        per_level_str = Levels.reverse(per_level)

        for i, level_idx in enumerate(input_data["level"]):
            if level_idx == per_level:
                region_id = get_id()

                bbox = get_bbox(
                    x=input_data["left"][i],
                    y=input_data["top"][i],
                    width=input_data["width"][i],
                    height=input_data["height"][i],
                    image_width=image_width,
                    image_height=image_height,
                )

                bbox_result = get_bbox_result(region_id, bbox)

                # Collate all text into `text` and all confidences
                # into `confidences`
                text, confidences = [], []
                for j, curr_id in enumerate(input_data[per_level_str]):
                    if curr_id != input_data[per_level_str][i]:
                        continue
                    word = input_data["text"][j]
                    confidence = input_data["conf"][j]
                    text.append(word)
                    if confidence != "-1":
                        confidences.append(float(confidence / 100.0))

                text = " ".join(text).strip()

                transcription_result = get_transcription_result(
                    region_id,
                    bbox,
                    text,
                    score=(
                        sum(confidences) / len(confidences)
                        if confidences
                        else 0
                    ),
                )

                # Extend/append all results and scores
                results.extend([bbox_result, transcription_result])
                all_scores.append(transcription_result["score"])

        score = sum(all_scores) / len(all_scores) if all_scores else 0

        if url is None:
            url = image.filename

        return {
            "data": {"ocr": url},
            "predictions": [
                {
                    "result": results,
                    "score": score,
                }
            ],
        }
