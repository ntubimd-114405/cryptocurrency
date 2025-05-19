from django import forms
from .models import DataLocation

FEATURE_CHOICES = [
    ('close_price', 'Close Price'),
    ('S&P 500 Index', 'S&P 500 Index'),
    ('VIX Volatility Index', 'VIX Volatility Index'),
    ('WTI Crude Oil Futures', 'WTI Crude Oil Futures'),
    ('US Dollar Index', 'US Dollar Index'),
    ('Gold Futures', 'Gold Futures'),
    ('volume', 'Volume'),
    ('positive', 'Positive'),
    ('neutral', 'Neutral'),
    ('negative', 'Negative'),
    ('Average Block Size', 'Average Block Size'),
    ('Difficulty', 'Difficulty'),
    ('Hash Rate', 'Hash Rate'),
    ('Miners Revenue', 'Miners Revenue'),
    ('Number Of Unique Addresses Used', 'Unique Addresses'),
    ('open_price', 'Open Price'),
    ('high_price', 'High Price'),
    ('low_price', 'Low Price'),
]


class DataLocationForm(forms.ModelForm):
    features = forms.MultipleChoiceField(
        choices=FEATURE_CHOICES,
        widget=forms.CheckboxSelectMultiple,  # 我們會在前端覆蓋它的樣式
        required=False,
        label="選擇特徵"
    )

    class Meta:
        model = DataLocation
        fields = ["name", "features"]

    def clean_features(self):
        return ",".join(self.cleaned_data["features"])
