"""
How the email names a machine: a category in the Czech 6th case ("na laseru") and its English form, never the
internal Fabman name. Mapped by Fabman resource id - names change, ids don't. A machine missing here gets FALLBACK.
"""
from typing import Tuple


CATEGORIES = {
    "3d_scanner": ("na 3D skeneru", "on the 3D scanner"),
    "3d_printer": ("na 3D tiskárně", "on a 3D printer"),
    "laser": ("na laseru", "on the laser cutter"),
    "cnc_mill": ("na CNC frézce", "on the CNC mill"),
    "cnc_lathe": ("na CNC soustruhu", "on the CNC lathe"),
    "vinyl_cutter": ("na řezacím plotru", "on the vinyl cutter"),
    "sewing_machine": ("na šicím stroji", "on the sewing machine"),
    "heat_press": ("na termolisu", "on the heat press"),
    "vacuum_former": ("na vakuové formovačce", "on the vacuum former"),
    "plastic_bender": ("na ohýbačce plastů", "on the plastic bender"),
    "saw": ("na pile", "on the saw"),
    "planer": ("na hoblovce", "on the planer"),
    "drill": ("na vrtačce", "on the drill press"),
    "mortiser": ("na dlabačce", "on the mortiser"),
}

FALLBACK = ("na jednom ze strojů", "on one of our machines")

MACHINES = {
    # 3D printers - Technopark and KUMST
    4554: "3d_printer", 1176: "3d_printer", 3880: "3d_printer", 86: "3d_printer", 458: "3d_printer",
    40: "3d_printer", 3881: "3d_printer", 1191: "3d_printer", 1206: "3d_printer", 6417: "3d_printer",
    6419: "3d_printer", 6418: "3d_printer", 6416: "3d_printer", 6276: "3d_printer", 6277: "3d_printer",
    4672: "3d_printer", 848: "3d_printer", 446: "3d_printer", 990: "3d_printer", 459: "3d_printer",
    4691: "3d_printer", 39: "3d_printer", 4416: "3d_printer", 2645: "3d_printer", 95: "3d_printer",
    924: "3d_printer",
    3707: "3d_scanner",
    3: "laser", 741: "laser", 3888: "laser",                                 # Speedy 300, 400, KUMST 360
    3358: "cnc_mill", 897: "cnc_mill", 4661: "cnc_mill", 4695: "cnc_mill",   # Jeřábek, Pocket NC, Two Trees x2
    4166: "cnc_lathe",                                                       # Numco
    43: "vinyl_cutter", 3894: "vinyl_cutter",                                # GS-24, KUMST GS-24
    291: "sewing_machine", 3895: "sewing_machine",                           # Innovis V5, KUMST Innovis v5
    61: "heat_press", 4558: "heat_press",                                    # Milano, KUMST Thermal Transfer Press
    3031: "vacuum_former",                                                   # Mayku Formbox
    962: "plastic_bender",                                                   # Formech
    1877: "saw", 204: "saw", 4525: "saw", 4683: "saw", 4682: "saw",          # Makita, Festool, ABG220, JET, Laguna
    4680: "planer", 4681: "planer",                                          # FELDER, JET
    961: "drill", 4685: "drill",                                             # stojanová, stolní
    4684: "mortiser",                                                        # ostrohranná dlabačka
}

# Doors, entrances, the key locker, Samosklad and test devices - never ask about these, even if listed in
# PROJECT_STORIES_RESOURCES by mistake.
NEVER_ASK = {
    2, 1794, 1630, 1781, 1843, 4474, 5293,   # Main Entrance, Main gate, doors, KUMST entrances
    4287,                                    # CNC key locker
    1395,                                    # Samosklad
    247, 4311, 4573, 4686, 5650,             # test devices
}


def machine_phrase(resource_id: int) -> Tuple[str, str]:
    """
    ("na laseru", "on the laser cutter") for a Fabman resource id.
    """
    category = MACHINES.get(resource_id)

    return CATEGORIES[category] if category else FALLBACK
