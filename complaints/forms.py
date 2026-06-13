from django import forms
from .models import CustomerComplaint


class CustomerComplaintForm(forms.ModelForm):

    class Meta:
        model = CustomerComplaint
        fields = [
            "customer",
            "site_type",
            "visit_date",
            "no_of_technicians",
            "complaint_title",
            "complaint_description",
            "work_done",
            "status",
            "remarks",
        ]

        widgets = {
            "customer": forms.Select(attrs={
                "class": "select2 w-full"
            }),

            "site_type": forms.Select(attrs={
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3"
            }),

            "visit_date": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3"
            }),

            "no_of_technicians": forms.NumberInput(attrs={
                "min": "1",
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3"
            }),

            "complaint_title": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3",
                "placeholder": "Enter complaint title"
            }),

            "complaint_description": forms.Textarea(attrs={
                "rows": 3,
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3",
                "placeholder": "Enter complaint details"
            }),

            "work_done": forms.Textarea(attrs={
                "rows": 3,
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3",
                "placeholder": "Enter work done"
            }),

            "status": forms.Select(attrs={
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3"
            }),

            "remarks": forms.Textarea(attrs={
                "rows": 3,
                "class": "w-full border border-slate-300 rounded-2xl px-4 py-3",
                "placeholder": "Enter remarks"
            }),
        }