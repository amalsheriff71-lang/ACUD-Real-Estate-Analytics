
from typing import Literal

DistrictId = Literal[
    "district_1",
    "district_2",
    "district_3",
    "district_4",
    "district_5",
    "government_district",
]

DISTRICTS = {
    "district_1": {
        "ar": "الحي السكني الأول",
        "en": "First Residential District",
    },
    "district_2": {
        "ar": "الحي السكني الثاني",
        "en": "Second Residential District",
    },
    "district_3": {
        "ar": "الحي السكني الثالث",
        "en": "Third Residential District",
    },
    "district_4": {
        "ar": "الحي السكني الرابع",
        "en": "Fourth Residential District",
    },
    "district_5": {
        "ar": "الحي السكني الخامس",
        "en": "Fifth Residential District",
    },
    "government_district": {
        "ar": "الحي الحكومي",
        "en": "Government District",
    },
}


def get_district_label(district_id: str, language: str = "ar") -> str:
    district = DISTRICTS.get(district_id)
    if district is None:
        return district_id
    return district.get(language, district["ar"])
