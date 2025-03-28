from django import forms
from .models import DataLocation

class DataLocationForm(forms.ModelForm):
    class Meta:
        model = DataLocation
        fields = ["name"]  # 這裡選擇了需要的字段，視需求而定
