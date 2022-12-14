class Input:
    TESSERACT = "tesseract"
    ABBYY = "abbyy"
    TRANSKRIBUS = "transkribus"


class Levels:
    page_num = 1
    block_num = 2
    par_num = 3
    line_num = 4
    word_num = 5

    @classmethod
    def VALID(self):
        return [
            x
            for x in self.__dict__.keys()
            if not x.startswith("__") and x not in ["VALID", "reverse"]
        ]

    @classmethod
    def reverse(self, pick):
        if pick == 1:
            return "page_num"
        if pick == 2:
            return "block_num"
        if pick == 3:
            return "par_num"
        if pick == 4:
            return "line_num"
        if pick == 5:
            return "word_num"

        raise SyntaxError("Incorrect Tesseract level provided")
