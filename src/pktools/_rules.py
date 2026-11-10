"""Constantes partagées par les interfaces de conversion."""

REGEX_PK_EXT = r"(?P<add1>\d{1,3}|[DEFGH])(?P<comp>[BTQ]?)(?P<op>[+-])(?P<add2>\d{3,4})"
RER_C = {"D": "0", "E": "1", "F": "2", "G": "3", "H": "4"}
COMP_MAP = {"": 0, "B": 1, "T": 2, "Q": 3}
OP_MAP = {"+": 1, "-": -1}
