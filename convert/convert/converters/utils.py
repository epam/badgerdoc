from typing import List

from convert.converters.base_format.models.tokens import BadgerdocToken


def filter_printing_tokens(objs: List[BadgerdocToken]) -> List[BadgerdocToken]:
    needed_objs = []
    at_the_beginning_of_string = True
    non_printing_sequence = []
    for token_obj in objs:
        char = token_obj.text
        if not char.isspace():
            needed_objs.append(token_obj.copy())

        # form field previous
        if at_the_beginning_of_string:
            if char.isspace():
                non_printing_sequence.append(char)
                continue
            else:
                needed_objs[0].previous = (
                    "".join(non_printing_sequence)
                    if non_printing_sequence
                    else None
                )
                at_the_beginning_of_string = False

        # form field after
        if char.isspace():
            previous_text = needed_objs[-1].after
            needed_objs[-1].after = (
                char if not previous_text else previous_text + char
            )

    return needed_objs
