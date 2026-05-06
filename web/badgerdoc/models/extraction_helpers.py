from dataclasses import dataclass, field

from badgerdoc.models import extraction_page


@dataclass
class BadgerdocExtractionXpath:
    extraction_page: extraction_page.ExtractionPage
    xpath: str
    element_on_xpath: str | None = field(default=None)
