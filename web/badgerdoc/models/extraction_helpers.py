from dataclasses import dataclass

from badgerdoc.models import extraction_page


@dataclass
class BadgerdocExtractionXpath:
    extraction_page: extraction_page.ExtractionPage
    xpath: str
