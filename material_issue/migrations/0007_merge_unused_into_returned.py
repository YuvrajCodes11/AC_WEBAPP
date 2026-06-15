from django.db import migrations
from django.db.models import F, Sum


def merge_unused_into_returned(apps, schema_editor):
    MaterialIssueItem = apps.get_model("material_issue", "MaterialIssueItem")
    MaterialIssueItem.objects.update(
        returned_quantity=F("returned_quantity") + F("unused_quantity")
    )


def sync_boq_totals(apps, schema_editor):
    MaterialIssueItem = apps.get_model("material_issue", "MaterialIssueItem")
    ProjectBOQItem = apps.get_model("boq", "ProjectBOQItem")

    for boq_item in ProjectBOQItem.objects.all().iterator():
        totals = MaterialIssueItem.objects.filter(
            boq_item_id=boq_item.id
        ).aggregate(
            issued=Sum("issued_quantity"),
            consumed=Sum("consumed_quantity"),
            returned=Sum("returned_quantity"),
        )
        ProjectBOQItem.objects.filter(pk=boq_item.id).update(
            issued_quantity=totals["issued"] or 0,
            consumed_quantity=totals["consumed"] or 0,
            returned_quantity=totals["returned"] or 0,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("material_issue", "0006_materialissue_heading_and_more"),
    ]

    operations = [
        migrations.RunPython(merge_unused_into_returned, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="materialissueitem",
            name="unused_quantity",
        ),
        migrations.RunPython(sync_boq_totals, migrations.RunPython.noop),
    ]
