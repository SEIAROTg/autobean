EVERYONE = 'everyone'
NOBODY = 'nobody'


def is_overall(viewpoint: str) -> bool:
    return viewpoint in (EVERYONE, NOBODY)
