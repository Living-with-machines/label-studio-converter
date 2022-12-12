from PIL import UnidentifiedImageError
from xml.parsers.expat import ExpatError


UnidentifiedImageError, ExpatError


class NoSuchConverter(NotImplementedError):
    def __init__(self, message="Converter is not implemented."):
        self.message = message
        super().__init__(self.message)


class MultipageABBYY(NotImplementedError):
    def __init__(self, message="Cannot handle multi-page Abbyy results."):
        self.message = message
        super().__init__(self.message)


class MultipleBlocks(NotImplementedError):
    def __init__(self, message="Found multiple blocks with the same ID."):
        self.message = message
        super().__init__(self.message)


class IncorrectImageFormat(SyntaxError):
    def __init__(
        self, message="Image provided must be of `PIL.Image` format."
    ):
        self.message = message
        super().__init__(self.message)


class IncorrectInputDataFormat(SyntaxError):
    def __init__(
        self, message="Input data provided must be of `dict` format."
    ):
        self.message = message
        super().__init__(self.message)


class IncorrectlyFormattedInputData(SyntaxError):
    def __init__(self, message=""):
        self.message = (
            f"Input data incorrectly formatted: {message}"
            if message
            else "Input data incorrectly formatted."
        )
        super().__init__(self.message)


class IncorrectURLFormat(SyntaxError):
    def __init__(
        self,
        message="A specified URL must be of `str` format.",
    ):
        self.message = message
        super().__init__(self.message)


class PerLevelIncorrect(SyntaxError):
    def __init__(
        self,
        message="per_level should be an integer or a Levels object's named property.",  # noqa
    ):
        self.message = message
        super().__init__(self.message)


class RequirePyTesseract(ImportError):
    def __init__(
        self,
        message="This utility requires PyTesseract, install it before use.",
    ):
        self.message = message
        super().__init__(self.message)


class UnexpectedType(SyntaxError):
    def __init__(
        self,
        message="",
    ):
        self.message = f"An unexpected type encountered: {message}"
        super().__init__(self.message)


class URLNotSet(Warning):
    MESSAGE = "URL should be set when converting local files. Otherwise, they will not be automatically linked to your LabelStudio entry."  # noqa

    def __init__(
        self,
        _="",
    ):
        self.message = self.MESSAGE

    def __str__(self):
        return repr(self.message)
