from typing import List

from src.converters.base_format.models.tokens import BadgerdocToken


def filter_printing_tokens(objs: List[BadgerdocToken]) -> List[BadgerdocToken]:
    needed_objs = []
    is_start_string = True
    non_printable_sequence = []
    for token_obj in objs:
        char = token_obj.text
        if char.isspace() and is_start_string:
            non_printable_sequence.append(char)
            continue
        if not char.isspace():
            is_start_string = False
            needed_objs.append(token_obj.copy())
            if non_printable_sequence:
                needed_objs[0].previous = "".join(non_printable_sequence)
            continue
        if char.isspace():
            previous_text = needed_objs[-1].after
            needed_objs[-1].after = (
                char if not previous_text else previous_text + char
            )

    return needed_objs
