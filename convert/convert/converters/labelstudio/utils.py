import copy
from typing import List

from .models.annotation import LabelStudioModel


def combine(parts: List[LabelStudioModel]) -> LabelStudioModel:
    combined_text = ""
    combined_annotations = []

    for part in parts:
        if part.__root__[0].annotations:
            for annotation in part.__root__[0].annotations[0].result:
                if annotation.value:
                    annotation.value.start += len(combined_text)
                    annotation.value.end += len(combined_text)
                combined_annotations.append(annotation)
        combined_text += part.__root__[0].data.text

    labelstudio = copy.deepcopy(parts[0])
    labelstudio.__root__[0].data.text = combined_text
    if labelstudio.__root__[0].annotations:
        labelstudio.__root__[0].annotations[0].result = combined_annotations
    return labelstudio
