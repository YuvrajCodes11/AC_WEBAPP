from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_alter_customerproject_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customerproject",
            name="location",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
