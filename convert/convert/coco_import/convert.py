import abc
import glob
import json
import os.path
from pathlib import Path
from typing import Any, Dict, Set

from convert.config import get_request_session, settings
from convert.logger import get_logger
from convert.models.coco import DataS3
from convert.utils.json_utils import import_save_to_json, load_from_json
from convert.utils.s3_utils import S3Manager, s3_download_files

LOGGER = get_logger(__file__)
SESSION = get_request_session()


class ImportConvertBase:
    def __init__(
        self,
        local_path: Path,
        s3_data: DataS3,
        token: str,
        current_tenant: str,
    ) -> None:
        self.local_path = local_path
        self.s3_data = s3_data
        self.token = token
        self.current_tenant = current_tenant

    @staticmethod
    def prepare_data(local_path: Path) -> Any:
        return load_from_json(str(local_path))

    @abc.abstractmethod
    def convert(self) -> None:
        pass

    def upload_annotations(
        self, job_id: int, path: str, annotation_by_image: Dict[int, int]
    ) -> None:
        os.chdir(path)
        included_files = glob.glob("**/*.json")

        headers = {
            "X-Current-Tenant": self.current_tenant,
            "Authorization": self.token,
        }
        for file in included_files:
            file_id = int(str(Path(file).parent))
            with open(file) as f_o:
                pages = [json.load(f_o)]
            body = {"pages": pages, "pipeline": 1, "validated": [1]}
            response = SESSION.post(
                url=f"{settings.annotation_service_url}annotation/{job_id}/{annotation_by_image[file_id]}",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            LOGGER.info(response.json())
        LOGGER.info("Uploading annotations has been finished")

    def upload_image(self, file: str, image_id: int) -> Dict[int, int]:
        assets_url = settings.assets_service_url
        body = {"files": (file, open(file, "rb"))}
        headers = {
            "X-Current-Tenant": self.current_tenant,
            "Authorization": self.token,
        }
        response = SESSION.post(url=assets_url, files=body, headers=headers)
        response.raise_for_status()
        LOGGER.info(response.json())
        return {image_id: response.json()[0].get("id")}

    def download_images(self, s3_manager: S3Manager) -> Dict[int, int]:
        images = self.prepare_data(self.local_path)["images"]
        annotation_by_image = {}
        for image in images:
            image_path = image["path"][1:]
            s3_download_files(s3_manager, self.s3_data.bucket_s3, [image_path])
            LOGGER.info(
                "%s is downloaded from bucket %s",
                image_path,
                self.s3_data.bucket_s3,
            )
            result = self.upload_image(Path(image_path).name, image["id"])
            annotation_by_image.update(result)
        return annotation_by_image

    def check_category(self) -> Set[str]:
        categories = self.prepare_data(self.local_path)["categories"]
        categories_services_url = settings.category_service_url
        headers = {
            "X-Current-Tenant": self.current_tenant,
            "Authorization": self.token,
        }
        for category in categories:
            body = {
                "name": category["name"],
                "parent": None,
                "metadata": {"color": category["color"]},
                "is_link": False,
            }
            get_category_details_url = f"{categories_services_url}{category['id']}"
            response = SESSION.get(url=get_category_details_url, headers=headers)
            category_id = response.json().get("id", None)
            if not category_id:
                SESSION.post(url=categories_services_url, json=body, headers=headers)
                LOGGER.info("Created category %s", category["name"])
            LOGGER.info(response.json())
        LOGGER.info("Checking categories has been finished")
        return set(category["name"] for category in categories)


class ConvertToBadgerdoc(ImportConvertBase):
    def convert(self) -> None:
        categories = self.prepare_data(self.local_path)["categories"]
        pages = {"pages": []}  # type: ignore
        data = load_from_json(str(self.local_path))
        annotation = {"objs": [], "page_num": 0, "size": {}}
        num = 1
        for pos, obj in enumerate(data["annotations"]):
            if (
                pos + 1 >= len(data["annotations"])
                or data["annotations"][pos + 1]["image_id"] != obj["image_id"]
            ):
                image_id = obj["image_id"]
                annotation["page_num"] = 1
                pages["pages"].append(annotation)
                import_save_to_json(
                    os.path.join(Path(self.s3_data.bucket_s3).stem, str(image_id)),
                    str(obj["id"]),
                    annotation,
                    file_id=image_id,
                )
                annotation = {"objs": []}
                num = 1
            else:
                annotation_obj = {
                    "id": num,
                    "category": categories[obj["category_id"]]["name"],
                    "bbox": obj["bbox"],
                }
                annotation["size"] = {
                    "width": obj["width"],
                    "height": obj["height"],
                }
                annotation["objs"].append(annotation_obj)  # type: ignore
                num += 1

        LOGGER.info("Converting from coco to badgerdoc has been finished")
