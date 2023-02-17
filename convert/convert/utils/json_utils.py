import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from convert.logger import get_logger

LOGGER = get_logger(__file__)


def load_from_json(file_name: str) -> Any:
    """Load data from json file

    Args:
        file_name: json file's name
    Returns:
        Return file data
    Raises:
        FileNotFoundError: If there is no such file
        ValueError: If json file has an incorrect format
    """
    try:
        with open(Path(file_name)) as f_o:
            return json.load(f_o)
    except FileNotFoundError:
        LOGGER.error(f"[Errno 2] No such file or directory: {file_name}")
        raise FileNotFoundError(f"[Errno 2] No such file or directory: {file_name}")


def annotation_category_change(
    annotations: List[Dict[str, Any]],
    old_category_id: str,
    new_category_id: str,
) -> None:
    """
    Changed category_id for bboxes to right
    """
    for annotation in annotations:
        if annotation["category_id"] == old_category_id:
            annotation["category_id"] = new_category_id


def annotation_image_change(
    annotations: List[Dict[str, Any]], old_image_id: str, new_image_id: str
) -> None:
    """
    Changed image_id for bboxes to right
    """
    for annotation in annotations:
        if annotation["image_id"] == old_image_id:
            annotation["image_id"] = new_image_id


def merge_jobs_annotation(
    file_annotation: Dict[str, List[Dict[str, Any]]],
    merge_annotation: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Merge annotation two jobs
    Extend lists with annotations, images, categories
    Find the last id of the object(annotation, image, category) and continue to extend list from the next id
    If image_id or category_id has been changed, then check bboxes this job and change this field to right
    Args:
        file_annotation: coco annotation, which is in the file
        merge_annotation: coco annotation for merging
    """
    annotation_idx = 1
    image_idx = 1
    category_idx = 1
    last_annotation_id = file_annotation["annotations"][-1]["id"]
    last_image_id = file_annotation["images"][-1]["id"]
    last_category_id = file_annotation["categories"][-1]["id"]
    file_categories = [category["name"] for category in file_annotation["categories"]]
    for category_merge in merge_annotation["categories"]:
        if category_merge["name"] in file_categories:
            continue
        file_annotation["categories"].append(category_merge)
    for image in merge_annotation["images"]:
        image_old_merge_id = image["id"]
        image["id"] = last_image_id + image_idx
        image_idx += 1
        annotation_image_change(
            merge_annotation["annotations"],
            image_old_merge_id,
            image["id"],
        )
        file_annotation["images"].append(image)
    for annotation in merge_annotation["annotations"]:
        annotation["id"] = last_annotation_id + annotation_idx
        annotation_idx += 1
        file_annotation["annotations"].append(annotation)
    return file_annotation


def export_save_to_json(
    name: str,
    annotations: Any,
) -> None:
    """
    Save coco annotation to json if file hasn't been created.
    Else, merged annotation jobs to and write to file

    Args:
        name: file name
        annotations: annotations data dictionary
    """
    file_name = f"{name}.json"
    if not os.path.exists(file_name):
        with open(file_name, "w") as f_o:
            json.dump(annotations, f_o, default=str)
    else:
        with open(file_name) as f_obr:
            annotations_in_file = json.load(f_obr)
        with open(file_name, "w") as f_obw:
            annotation = merge_jobs_annotation(annotations_in_file, annotations)
            json.dump(annotation, f_obw, default=str)


def import_save_to_json(
    work_dir: str,
    name: str,
    annotations: Any,
    dataset_name: Optional[str] = None,
    output_path: Optional[str] = None,
    file_id: Optional[str] = None,
) -> None:
    """Save data to json

    Args:
        work_dir: path to an output directory
        name: file name
        annotations: annotations data dictionary
        dataset_name: dataset name
        output_path: path to an output directory
        file_id: image id

    Returns:
        Return None
    """
    if dataset_name and output_path and file_id:
        work_dir = os.path.join(output_path, dataset_name, work_dir)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir, exist_ok=True)
    annotations_path = os.path.join(work_dir, f"{name}.json")
    with open(annotations_path, "a") as f_o:
        json.dump(annotations, f_o, default=str)
