from dataclasses import dataclass

PAGE_NUM = int
HOCR_PATH = str


@dataclass
class BadgerdocHOCRPageResult:
    h_ocr: dict[PAGE_NUM, HOCR_PATH]
