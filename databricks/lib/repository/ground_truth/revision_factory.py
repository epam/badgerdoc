from typing import Any, Dict, List

from lib.badgerdoc.service import BadgerDocService
from lib.repository.ground_truth.models import Revision


class RevisionFactory:
    @staticmethod
    def create_revisions(
        badgerdoc: BadgerDocService,
        tenant: str,
        revisions_dict: List[Dict[str, Any]],
    ) -> List[Revision]:
        revisions = []
        for file in revisions_dict:
            job_id = int(file["input"]["job_id"])
            file_id = int(file["file_id"])
            revision_id = file["revision"]
            annotations = badgerdoc.get_annotations(
                tenant, job_id, file_id, revision_id
            )

            revisions.append(
                Revision(
                    revision_id=revision_id,
                    tenant=tenant,
                    job_id=job_id,
                    file_id=file_id,
                    annotations=annotations,
                )
            )

        return revisions
