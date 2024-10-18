from dataclasses import dataclass
from typing import Dict


@dataclass
class Revision:
    revision_id: str
    tenant: str
    job_id: int
    file_id: int
    annotations: Dict[str, str]
