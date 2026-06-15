from django.db import migrations, models


def set_initial_non_vrv(apps, schema_editor):
    """
    Preserve the old single-checkbox meaning for existing rows:
    items that were VRV stay VRV-only, everything else becomes Non-VRV.
    """
    StoreItem = apps.get_model("store", "StoreItem")
    StoreItem.objects.filter(is_vrv=True).update(is_non_vrv=False)
    StoreItem.objects.filter(is_vrv=False).update(is_non_vrv=True)


def reverse_non_vrv(apps, schema_editor):
    # Nothing meaningful to reverse; field is dropped on unapply.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0008_restore_vrv_classification"),
    ]

    operations = [
        migrations.AddField(
            model_name="storeitem",
            name="is_non_vrv",
            field=models.BooleanField(
                default=True,
                help_text="Check if this item is Non-VRV type.",
            ),
        ),
        migrations.RunPython(set_initial_non_vrv, reverse_non_vrv),
    ]
