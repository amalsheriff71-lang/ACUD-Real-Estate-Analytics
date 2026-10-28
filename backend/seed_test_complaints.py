
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Complaint


random.seed(42)

CATEGORIES = {
    "lighting": [
        "A streetlight is not working near the residential buildings.",
        "Several streetlights are off along the main road.",
        "The lighting near the pedestrian crossing needs repair.",
    ],
    "roads": [
        "There is a pothole that needs repair.",
        "The pavement is damaged near the building entrance.",
        "The road surface is uneven and difficult to cross.",
    ],
    "waste": [
        "Waste has accumulated near the residential buildings.",
        "The waste collection point needs cleaning.",
        "Garbage has not been collected from the designated area.",
    ],
    "water": [
        "There appears to be a water leak near the pavement.",
        "Water is pooling beside the residential building.",
        "A leaking pipe needs inspection.",
    ],
    "parking": [
        "Vehicles are blocking the pedestrian walkway.",
        "Cars are parked in a restricted area.",
        "Parking is obstructing access to the building.",
    ],
    "noise": [
        "Construction noise continues late in the evening.",
        "Loud noise is disturbing residents.",
        "Noise from nearby maintenance work needs attention.",
    ],
    "other": [
        "A public facility needs maintenance.",
        "A damaged public sign needs replacement.",
        "An issue with a shared residential area needs inspection.",
    ],
}

DISTRICTS_AR = [
    "الحي السكني الأول",
    "الحي السكني الثاني",
    "الحي السكني الثالث",
    "الحي السكني الرابع",
    "الحي السكني الخامس",
    "الحي الحكومي",
]

DISTRICTS_EN = [
    "First Residential District",
    "Second Residential District",
    "Third Residential District",
    "Fourth Residential District",
    "Fifth Residential District",
    "Government District",
]

STATUSES = [
    "received",
    "in_progress",
    "resolved",
    "received",
    "received",
]

ONSETS = ["today", "week", "month", "unknown"]

ARABIC_NAMES = [
    "أحمد محمد",
    "محمود علي",
    "سارة أحمد",
    "منى إبراهيم",
    "عمر خالد",
    "نور مصطفى",
    "يوسف حسن",
    "مريم محمود",
]

ENGLISH_NAMES = [
    "Test Resident One",
    "Test Resident Two",
    "Test Resident Three",
    "Test Resident Four",
    "Test Resident Five",
]


def main():
    now = datetime.now(timezone.utc)
    created_count = 0

    with SessionLocal() as db:
        try:
            # Count existing records without changing them.
            existing_count = (
                db.scalar(
                    select(func.count()).select_from(Complaint)
                )
                or 0
            )

            print(f"Existing complaints: {existing_count}")

            for i in range(100):
                language = random.choice(["ar", "en"])
                category = random.choice(list(CATEGORIES.keys()))

                created_at = now - timedelta(
                    days=random.randint(0, 89),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )

                if language == "ar":
                    name = random.choice(ARABIC_NAMES)
                    district = random.choice(DISTRICTS_AR)
                else:
                    name = random.choice(ENGLISH_NAMES)
                    district = random.choice(DISTRICTS_EN)

                description = random.choice(CATEGORIES[category])

                # Clearly fictional test contact details.
                phone = f"TEST-{i + 1:04d}"

                complaint = Complaint(
                    language=language,
                    full_name=name,
                    phone=phone,
                    email=None,
                    category=category,
                    district=district,
                    address=(
                        f"Test Street {random.randint(1, 30)}, "
                        f"Building {random.randint(1, 50)}"
                    ),
                    description=description,
                    onset=random.choice(ONSETS),
                    consent=True,
                    attachment_name=None,
                    status=random.choice(STATUSES),
                    created_at=created_at,
                    updated_at=created_at,
                )

                db.add(complaint)
                created_count += 1

            # Insert all records in one transaction.
            db.commit()

            final_count = (
                db.scalar(
                    select(func.count()).select_from(Complaint)
                )
                or 0
            )

            print(f"Successfully inserted: {created_count}")
            print(f"Total complaints now: {final_count}")
            print("Existing complaints were not deleted.")

        except Exception:
            db.rollback()
            print("Insertion failed. Changes were rolled back.")
            raise


if __name__ == "__main__":
    main()
