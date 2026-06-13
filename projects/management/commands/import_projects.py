import os
import sys
import django
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

sys.path.append(BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "puriaccooling.settings"
)

django.setup()


from projects.models import CustomerProject


excel_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Book1.xlsx"
)


df = pd.read_excel(excel_path)


for index, row in df.iterrows():

    customer_name = str(row["CUSTOMER NAME"]).strip()
    location = str(row["LOCATION"]).strip()
    tonage = str(row["TONAGE"]).strip()

    if "HP" in tonage.upper():

        capacity_unit = "HP"
        capacity_value = tonage.upper().replace("HP", "").strip()

    else:

        capacity_unit = "TR"
        capacity_value = tonage.upper().replace("TR", "").strip()

    CustomerProject.objects.create(
        customer_name=customer_name,
        location=location,
        capacity_value=capacity_value,
        capacity_unit=capacity_unit,
        extra_note=""
    )


print("All projects imported successfully.")