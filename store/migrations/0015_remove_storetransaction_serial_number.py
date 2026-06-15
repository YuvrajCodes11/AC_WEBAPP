from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0014_storetransaction_serial_number"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="storetransaction",
            name="serial_number",
        ),
    ]
