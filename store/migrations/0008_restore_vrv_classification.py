from django.db import migrations


def restore_vrv_classification(apps, schema_editor):
    StoreItem = apps.get_model("store", "StoreItem")

    StoreItem.objects.filter(
        remarks__iexact="VRV",
    ).update(is_vrv=True)

    StoreItem.objects.filter(
        remarks__iregex=r"^NON[\s-]*VRV$",
    ).update(is_vrv=False)


def reverse_vrv_classification(apps, schema_editor):
    StoreItem = apps.get_model("store", "StoreItem")
    StoreItem.objects.filter(remarks__iexact="VRV").update(is_vrv=False)


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0007_storetransaction_material_issue_item_and_more"),
    ]

    operations = [
        migrations.RunPython(
            restore_vrv_classification,
            reverse_vrv_classification,
        ),
    ]
