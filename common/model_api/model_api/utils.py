import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

import pdfplumber

from .common import models as m
from .preprocessing import crop_page_images

logger = logging.getLogger(__name__)


def form_response(
    annotation: List[m.PageDOD],
    inp_page_category_bboxes: Dict[str, Dict[str, List[str]]],
) -> Dict[str, Dict[str, List[str]]]:
    """Form response object from annotations.
    Example:
        annotation={"pages":
            [{"page_num": 1,
             "size": {"width": 2100, "height": 2970},
             "objs":
                  [
                      {
                          "id": "aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                          "bbox": [500, 100, 1500, 1000], "category": "3"
                      },
                      {
                          "id": "30e4d539-8e90-49c7-b49c-883073e2b8c8",
                          "bbox": [100, 1600, 800, 2000], "category": "0"
                      }
                  ]
             },
             {"page_num": 2,
              "size": {"width": 2100, "height": 2970},
              "objs":
                  [
                      {
                          "id": "44d94e31-7079-470a-b8b5-74ce365353f7",
                          "bbox": [500, 500, 1500, 1300], "category": "3"
                      },
                      {
                           "id": "d86d467f-6ec1-404e-b4e6-ba8d78f93754",
                           "bbox": [500, 1300, 1500, 2600], "category": "3"
                      }
                  ]
                   }]}
        inp_page_category_bboxes={
            "0": {
                "1": ["30e4d539-8e90-49c7-b49c-883073e2b8c8"],
            },
            "3": {
                "1": ["aab83828-cd8b-41f7-a3c3-943f13e67c2c"],
                "2": [
                    "44d94e31-7079-470a-b8b5-74ce365353f7",
                    "d86d467f-6ec1-404e-b4e6-ba8d78f93754",
                ],
            },
        }
    """
    fresh_uuid_dict: Dict[str, Dict[str, str]] = {}
    for page in annotation:
        for obj in page.objs:
            fresh_uuid_dict[obj.idx] = {
                "page": str(page.page_num),
                "category": obj.category,
            }
    response_dict: Dict[str, Dict[str, List[str]]] = {}
    # todo: use defaultdict etc
    for (
        inp_category,
        inp_page_with_indexes,
    ) in inp_page_category_bboxes.items():
        for page_num, uuidxes in inp_page_with_indexes.items():
            for uuidx in uuidxes:
                if uuidx in fresh_uuid_dict:
                    fresh_category = fresh_uuid_dict[uuidx]["category"]
                    fresh_num = fresh_uuid_dict[uuidx]["page"]
                    if fresh_category not in response_dict:
                        response_dict[fresh_category] = {}
                    if fresh_num not in response_dict[fresh_category]:
                        response_dict[fresh_category][fresh_num] = []
                    response_dict[fresh_category][fresh_num].append(uuidx)
                    continue
                if inp_category not in response_dict:
                    response_dict[inp_category] = {}
                if page_num not in response_dict[inp_category]:
                    response_dict[inp_category][page_num] = []
                response_dict[inp_category][page_num].append(uuidx)
    return response_dict


def update_annotation_categories(
    inference: Any,
    model: Any,
    page: m.PageDOD,
    pdf: pdfplumber.PDF,
    categories: List[str],
    work_dir: Path,
    required_obj_ids: Optional[Tuple[str, ...]] = None,
) -> None:
    if page.page_num > len(pdf.pages):
        logger.error(
            "page %s in annotations doesn't exit in pdf", page.page_num
        )
        return
    bboxes_inference_result = {
        (page.page_num, Path(image).stem): inference_result
        for image, inference_result in inference(
            model,
            crop_page_images(
                pdf_page=pdf.pages[page.page_num - 1],
                dod_page=page,
                categories=categories,
                output_path=work_dir,
            ),
        )
    }
    # todo: separate as postprocessing
    logger.info("Updating an annotation")
    for obj in page.objs:
        if (page.page_num, obj.idx) in bboxes_inference_result:

            if required_obj_ids:
                if obj.idx not in required_obj_ids:
                    continue
            # obj.category = bboxes_inference_result[(page.page_num, obj.idx)]
            # Todo: check type of data
            if not obj.data:
                obj.data = {}

            inference_key = (page.page_num, obj.idx)
            if (data_field := "data") in bboxes_inference_result[
                inference_key
            ].keys():
                obj.data = {
                    **obj.data,
                    **bboxes_inference_result[inference_key][data_field],
                }
            if (category_field := "category") in bboxes_inference_result[
                inference_key
            ].keys():
                obj.category = bboxes_inference_result[inference_key][
                    category_field
                ]

            logger.info(
                "An annotation of a page %s with %s updated",
                obj.idx,
                obj.category,
            )


def get_needs_from_request_and_annotation(
    annotation: List[m.PageDOD], input_field: Dict[str, Dict[str, List[str]]]
) -> Tuple[Generator[m.PageDOD, None, None], Set[str]]:
    page_nums_in_the_request = {
        int(page_num)
        for page_obj_ids in input_field.values()
        for page_num in page_obj_ids.keys()
    }
    obj_ids_in_the_request = {
        obj_id
        for page_obj_ids in input_field.values()
        for lists_of_obj_ids in page_obj_ids.values()
        for obj_id in lists_of_obj_ids
    }
    logger.info(page_nums_in_the_request)
    needed_pages = (
        page
        for page in annotation
        if int(page.page_num) in set(page_nums_in_the_request)
    )
    return needed_pages, obj_ids_in_the_request
