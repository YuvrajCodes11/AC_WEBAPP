from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_storeitem_alert_percentage_alter_storeitem_remarks'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeitem',
            name='serial_number',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                help_text='AC unit serial number (if applicable).',
            ),
        ),
    ]
