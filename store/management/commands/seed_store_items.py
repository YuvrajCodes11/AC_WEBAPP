"""
Management command to seed store categories and items from the official item list.
Run: python manage.py seed_store_items
Safe to run multiple times — skips existing items by description+category.
"""

from django.core.management.base import BaseCommand
from store.models import StoreCategory, StoreItem


ITEMS = [
    # (category_name, description, unit, is_vrv)
    # COPPER PIPE
    ("Copper Pipe", "COPPER PIPE 6.4 mm/ 1/4\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 9.5 mm/ 3/8\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 12.7 mm/ 1/2\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 15.9 mm/ 5/8\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 19.1 mm/ 3/4\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 22.2 mm/ 7/8\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 28.6 mm/ 1-1/8\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 34.9 mm/ 1-3/8\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 41.3 mm/ 1-5/8\" VRV", "MTR", True),
    ("Copper Pipe", "COPPER PIPE 6.4 mm/ 1/4\" Non VRV", "MTR", False),
    ("Copper Pipe", "COPPER PIPE 9.5 mm/ 3/8\" Non VRV", "MTR", False),
    ("Copper Pipe", "COPPER PIPE 12.7 mm/ 1/2\" Non VRV", "MTR", False),
    ("Copper Pipe", "COPPER PIPE 15.9 mm/ 5/8\" Non VRV", "MTR", False),

    # SPLIT AC COPPER PIPE KIT
    ("Split AC Copper Pipe Kit", "Copper Pipe Kit 3/8\" 1/4\"", "MTR", False),
    ("Split AC Copper Pipe Kit", "Copper Pipe Kit 1/2\" 1/4\"", "MTR", False),

    # COPPER ACCESSORIES
    ("Copper Accessories", "COPPER ELBOW 3/4\"", "NOS", False),
    ("Copper Accessories", "COPPER ELBOW 7/8\"", "NOS", False),
    ("Copper Accessories", "COPPER ELBOW 1-1/8\"", "NOS", False),
    ("Copper Accessories", "COPPER ELBOW 1-3/8\"", "NOS", False),
    ("Copper Accessories", "COPPER ELBOW 1-5/8\"", "NOS", False),
    ("Copper Accessories", "COPPER SOCKET 3/4\"", "NOS", False),
    ("Copper Accessories", "COPPER SOCKET 7/8\"", "NOS", False),
    ("Copper Accessories", "COPPER SOCKET 1-1/8\"", "NOS", False),
    ("Copper Accessories", "COPPER SOCKET 1-3/8\"", "NOS", False),
    ("Copper Accessories", "COPPER SOCKET 1-5/8\"", "NOS", False),

    # COPPER PIPE INSULATION
    ("Copper Pipe Insulation", "COPPER INSULATION 6.4 mm Pipe VRV 13x6", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 9.5 mm Pipe VRV 13x10", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 12.7 mm Pipe VRV 13x13", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 15.9 mm Pipe VRV 13x16", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 19.1 mm Pipe VRV 13x19", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 22.2 mm Pipe VRV 19x22", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 28.6 mm Pipe VRV 19x28", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 34.9 mm Pipe VRV 19x35", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 41.3 mm Pipe VRV 19x42", "NOS", True),
    ("Copper Pipe Insulation", "COPPER INSULATION 6.4 mm Pipe Non VRV 6x6", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 9.5 mm Pipe Non VRV 6x10", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 12.7 mm Pipe Non VRV 6x13", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 15.9 mm Pipe Non VRV 6x16", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 6.4 mm Pipe Non VRV 9x6", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 9.5 mm Pipe Non VRV 9x10", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 12.7 mm Pipe Non VRV 9x13", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 15.9 mm Pipe Non VRV 9x16", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 19.1 mm Pipe Non VRV 9x19", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 22.2 mm Pipe Non VRV 9x22", "NOS", False),
    ("Copper Pipe Insulation", "COPPER INSULATION 28.6 mm Pipe Non VRV 9x28", "NOS", False),

    # PVC DRAIN PIPE
    ("PVC Drain Pipe", "PVC DRAIN PIPE 25 mm", "MTR", False),
    ("PVC Drain Pipe", "PVC DRAIN PIPE 40 mm", "MTR", False),
    ("PVC Drain Pipe", "PVC DRAIN PIPE 50 mm", "MTR", False),
    ("PVC Drain Pipe", "PVC DRAIN PIPE 63 mm", "MTR", False),
    ("PVC Drain Pipe", "PVC DRAIN PIPE 75 mm", "MTR", False),
    ("PVC Drain Pipe", "PVC PIPE 100 mm", "MTR", False),
    ("PVC Drain Pipe", "PVC PIPE 150 mm", "MTR", False),

    # DRAIN INSULATION
    ("Drain Insulation", "DRAIN INSULATION 25 mm 6x25", "NOS", False),
    ("Drain Insulation", "DRAIN INSULATION 32 mm 6x32", "NOS", False),
    ("Drain Insulation", "DRAIN INSULATION 40 mm 6x40", "NOS", False),

    # DRAIN ACCESSORIES
    ("Drain Accessories", "PVC ELBOW 25 mm", "NOS", False),
    ("Drain Accessories", "PVC ELBOW 32 mm", "NOS", False),
    ("Drain Accessories", "PVC ELBOW 40 mm", "NOS", False),
    ("Drain Accessories", "PVC SOCKET 25 mm", "NOS", False),
    ("Drain Accessories", "PVC SOCKET 32 mm", "NOS", False),
    ("Drain Accessories", "PVC SOCKET 40 mm", "NOS", False),
    ("Drain Accessories", "PVC TEE 25 mm", "NOS", False),
    ("Drain Accessories", "PVC TEE 32 mm", "NOS", False),
    ("Drain Accessories", "PVC TEE 40 mm", "NOS", False),
    ("Drain Accessories", "PVC REDUCER 32x25", "NOS", False),
    ("Drain Accessories", "PVC REDUCER 40x32", "NOS", False),
    ("Drain Accessories", "SOLVENT 100 ml", "NOS", False),
    ("Drain Accessories", "SOLVENT 250 ml", "NOS", False),
    ("Drain Accessories", "PIPE GI HOOK", "KG", False),

    # REFNET (Y JOINTS)
    ("Refnet Y Joints", "REFNET 22T", "NOS", True),
    ("Refnet Y Joints", "REFNET 33T", "NOS", True),
    ("Refnet Y Joints", "REFNET 72T", "NOS", True),
    ("Refnet Y Joints", "REFNET 73T", "NOS", True),
    ("Refnet Y Joints", "REFNET 73 TP6", "NOS", True),

    # PVC ELECTRICAL PIPE
    ("PVC Electrical Pipe", "ELECTRICAL PIPE 20 mm", "MTR", False),
    ("PVC Electrical Pipe", "ELECTRICAL PIPE 25 mm", "MTR", False),
    ("PVC Electrical Pipe", "L BEND 20 mm", "NOS", False),
    ("PVC Electrical Pipe", "L BEND 25 mm", "NOS", False),
    ("PVC Electrical Pipe", "JUNCTION BOX 20 mm", "NOS", False),
    ("PVC Electrical Pipe", "JUNCTION BOX 25 mm", "NOS", False),

    # COPPER WIRES
    ("Copper Wires", "COPPER SHIELDED WIRE 2 Core 0.75 mm", "MTR", False),
    ("Copper Wires", "COPPER SHIELDED WIRE 2 Core 1.0 mm", "MTR", False),
    ("Copper Wires", "COPPER SHIELDED WIRE 2 Core 1.5 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 2 Core 0.75 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 2 Core 1.0 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 3 Core 1.5 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 3 Core 2.5 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 4 Core 1.5 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 4 Core 2.5 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 4 Core 4.0 mm", "MTR", False),
    ("Copper Wires", "COPPER WIRE 6 Core 1.5 mm", "MTR", False),

    # GI PERFORATED TRAY
    ("GI Perforated Tray", "GI Cable Tray 100x50", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 150x50", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 200x50", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 250x50", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 300x50", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 450x50", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 100x75", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 150x75", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 200x75", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 250x75", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 300x75", "MTR", False),
    ("GI Perforated Tray", "GI Cable Tray 450x75", "MTR", False),

    # GI SHEETS
    ("GI Sheets", "GI SHEET 22 GAUGE 8x3", "NOS", False),
    ("GI Sheets", "GI SHEET 22 GAUGE 8x4", "NOS", False),
    ("GI Sheets", "GI SHEET 24 GAUGE 8x3", "NOS", False),
    ("GI Sheets", "GI SHEET 24 GAUGE 8x4", "NOS", False),
    ("GI Sheets", "GI SHEET 26 GAUGE 8x3", "NOS", False),
    ("GI Sheets", "GI SHEET 26 GAUGE 8x4", "NOS", False),

    # NITRILE SHEETS
    ("Nitrile Sheets", "NITRILE Sheet 6 mm", "SQMTR", False),
    ("Nitrile Sheets", "NITRILE Sheet 9 mm", "SQMTR", False),

    # DUCTING ACCESSORIES
    ("Ducting Accessories", "GI THREAD ROD 8 mm", "NOS", False),
    ("Ducting Accessories", "GI THREAD ROD 10 mm", "NOS", False),
    ("Ducting Accessories", "GI THREAD ROD 12 mm", "NOS", False),
    ("Ducting Accessories", "NUT 8 mm", "KG", False),
    ("Ducting Accessories", "WASHER 8 mm", "KG", False),
    ("Ducting Accessories", "NUT 10 mm", "KG", False),
    ("Ducting Accessories", "WASHER 10 mm", "KG", False),
    ("Ducting Accessories", "NUT 12 mm", "KG", False),
    ("Ducting Accessories", "WASHER 12 mm", "KG", False),
    ("Ducting Accessories", "DUCTING NUT BOLT", "KG", False),
    ("Ducting Accessories", "SR Solution", "LTR", False),
    ("Ducting Accessories", "FISHER FASTNER 8 mm", "NOS", False),
    ("Ducting Accessories", "FISHER FASTNER 10 mm", "NOS", False),
    ("Ducting Accessories", "BULLET FASTNER 8 mm", "NOS", False),
    ("Ducting Accessories", "BULLET FASTNER 10 mm", "NOS", False),
    ("Ducting Accessories", "CABLE TIE", "PKT", False),
    ("Ducting Accessories", "PACKING TAPE", "NOS", False),
    ("Ducting Accessories", "ELECTRICAL TAPE", "NOS", False),
    ("Ducting Accessories", "ECO TAPE", "NOS", False),
    ("Ducting Accessories", "CUTTING BLADE", "NOS", False),
    ("Ducting Accessories", "HEXA BLADE", "NOS", False),
    ("Ducting Accessories", "BRAZING ROD", "NOS", False),
    ("Ducting Accessories", "SHADDLE CLAMP", "NOS", False),
    ("Ducting Accessories", "PLASTIC GITTI", "PKT", False),
    ("Ducting Accessories", "WOODEN SCREW", "NOS", False),
    ("Ducting Accessories", "SELF SCREW", "NOS", False),
    ("Ducting Accessories", "BLACK SCREW", "NOS", False),
    ("Ducting Accessories", "GAS KIT", "ROLL", False),
    ("Ducting Accessories", "VIBRATION PAD", "NOS", False),
    ("Ducting Accessories", "FLOOR TYPE STAND", "NOS", False),
    ("Ducting Accessories", "WALL TYPE STAND", "NOS", False),
    ("Ducting Accessories", "M.S STAND", "NOS", False),
    ("Ducting Accessories", "HANGING STAND", "NOS", False),

    # BHF KITS
    ("BHF Kits", "BHF Kit 1006", "NOS", False),
    ("BHF Kits", "BHF Kit 1516", "NOS", False),
    ("BHF Kits", "BHF Kit 1356", "NOS", False),
    ("BHF Kits", "BHF Kit 1686", "NOS", False),

    # REMOTES & RECEIVER KITS
    ("Remotes and Receiver Kits", "CORDED REMOTE BRC2E61", "NOS", False),
    ("Remotes and Receiver Kits", "NAVIGATION REMOTE BRCIE63", "NOS", False),
    ("Remotes and Receiver Kits", "HANDSET BRC4M150W16", "NOS", False),
    ("Remotes and Receiver Kits", "RECEIVER KIT BRC7N618-6", "NOS", False),
    ("Remotes and Receiver Kits", "RECEIVER KIT BRC63AV", "NOS", False),
    ("Remotes and Receiver Kits", "RECEIVER KIT BRC4M61-6", "NOS", False),
    ("Remotes and Receiver Kits", "RECEIVER KIT BRC91A157", "NOS", False),
    ("Remotes and Receiver Kits", "RECEIVER KIT BRC7M632 F-6", "NOS", False),
    ("Remotes and Receiver Kits", "REMOTE BRC91A152", "NOS", False),
]


def seed_official_store_items():
    created_cats = 0
    created_items = 0
    skipped = 0

    for cat_name, description, unit, is_vrv in ITEMS:
        category, cat_created = StoreCategory.objects.get_or_create(
            category_name=cat_name
        )
        if cat_created:
            created_cats += 1

        item = StoreItem.objects.filter(
            category=category,
            item_description=description,
        ).first()

        if item:
            changed_fields = []
            if item.is_vrv != is_vrv:
                item.is_vrv = is_vrv
                changed_fields.append("is_vrv")
            previous_remarks = item.remarks
            item.set_non_vrv(not is_vrv)
            if item.remarks != previous_remarks:
                changed_fields.append("remarks")
            if changed_fields:
                item.save(update_fields=changed_fields)
            skipped += 1
            continue

        item = StoreItem(
            category=category,
            item_description=description,
            unit=unit,
            is_vrv=is_vrv,
            opening_stock=0,
            minimum_stock=0,
        )
        item.set_non_vrv(not is_vrv)
        item.save()
        created_items += 1

    return {
        "created_cats": created_cats,
        "created_items": created_items,
        "skipped": skipped,
    }


def official_catalog_is_missing():
    for cat_name, description, unit, is_vrv in ITEMS:
        if not StoreItem.objects.filter(
            category__category_name=cat_name,
            item_description=description,
        ).exists():
            return True
    return False


def ensure_official_store_catalog():
    if official_catalog_is_missing():
        return seed_official_store_items()
    return {
        "created_cats": 0,
        "created_items": 0,
        "skipped": len(ITEMS),
    }


class Command(BaseCommand):
    help = "Seed store categories and items from official item list"

    def handle(self, *args, **options):
        stats = seed_official_store_items()

        self.stdout.write(self.style.SUCCESS(
            f"Done — {stats['created_cats']} categories created, "
            f"{stats['created_items']} items created, "
            f"{stats['skipped']} skipped (already exist)."
        ))
