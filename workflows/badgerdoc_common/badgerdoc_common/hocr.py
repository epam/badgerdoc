from dataclasses import dataclass

PAGE_NUM = str
HOCR_PATH = str
OCR_PATH = str


@dataclass
class BadgerdocHOCRPageResult:
    """hOCR result shared with Badgerdoc.

    Maps each page number to the path of its hOCR file. This is the
    normalised, engine-agnostic representation that Badgerdoc consumes
    to create :class:`~badgerdoc.models.ExtractionPage` records.
    """

    # todo: rename to hocr
    h_ocr: dict[PAGE_NUM, HOCR_PATH]


@dataclass
class BadgerdocOCRPageResult:
    """Internal OCR result produced by an OCR engine.

    Maps each page number to a list of paths pointing to the raw OCR
    output files. The format of those files is engine-specific (e.g.
    JSON, XML, plain text) and is not interpreted by Badgerdoc directly.
    This class is intended for intermediate processing within a worker
    before the results are converted to :class:`BadgerdocHOCRPageResult`.
    """

    ocr: dict[PAGE_NUM, list[OCR_PATH]]
