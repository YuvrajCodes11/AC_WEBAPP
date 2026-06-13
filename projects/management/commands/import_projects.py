from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from customers.models import Customer
from projects.models import CustomerProject


class Command(BaseCommand):
    help = "Import customer projects from an Excel workbook."

    def add_arguments(self, parser):
        default_path = Path(__file__).with_name("Book1.xlsx")
        parser.add_argument("path", nargs="?", default=str(default_path))

    def handle(self, *args, **options):
        try:
            import pandas as pd
        except ImportError as exc:
            raise CommandError(
                "This command requires pandas and an Excel reader such as openpyxl."
            ) from exc

        excel_path = Path(options["path"]).expanduser()
        if not excel_path.exists():
            raise CommandError(f"Excel file not found: {excel_path}")

        imported = 0
        for _, row in pd.read_excel(excel_path).iterrows():
            customer_name = str(row.get("CUSTOMER NAME", "")).strip()
            location = str(row.get("LOCATION", "")).strip()
            tonnage = str(row.get("TONAGE", "")).strip().upper()

            if not customer_name or customer_name.lower() == "nan":
                continue

            customer, _ = Customer.objects.get_or_create(
                customer_name=customer_name,
                defaults={"phone_number": "N/A"},
            )

            capacity_unit = "HP" if "HP" in tonnage else "TR"
            capacity_text = tonnage.replace(capacity_unit, "").strip()
            try:
                capacity_value = float(capacity_text or 0)
            except ValueError:
                capacity_value = 0

            CustomerProject.objects.create(
                customer=customer,
                site_name=location or f"{customer_name} Site",
                location=location or None,
                capacity_value=capacity_value,
                capacity_unit=capacity_unit,
            )
            imported += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported {imported} project(s) successfully."
        ))
