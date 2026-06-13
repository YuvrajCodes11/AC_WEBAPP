# Generated for requirement 14: keep complaint site type aligned to customer category.

from django.db import migrations


def sync_site_type(apps, schema_editor):
    CustomerComplaint = apps.get_model("complaints", "CustomerComplaint")

    for complaint in CustomerComplaint.objects.select_related("customer"):
        category = complaint.customer.customer_category
        if category == "WARRANTY":
            site_type = "WARRANTY"
        elif category == "AMC":
            site_type = "AMC"
        else:
            site_type = "GENERAL"

        if complaint.site_type != site_type:
            complaint.site_type = site_type
            complaint.save(update_fields=["site_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("complaints", "0002_alter_customercomplaint_id"),
    ]

    operations = [
        migrations.RunPython(sync_site_type, migrations.RunPython.noop),
    ]
