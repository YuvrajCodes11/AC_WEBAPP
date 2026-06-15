from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0013_remove_storeitem_is_non_vrv"),
    ]

    operations = [
        migrations.AddField(
            model_name="storetransaction",
            name="serial_number",
            field=models.CharField(
                blank=True,
                help_text="Serial number recorded for this stock movement.",
                max_length=100,
                null=True,
            ),
        ),
    ]
