from django import forms


class FavoriteForm(forms.Form):
    """The place snapshot posted by a "Save" button."""

    name = forms.CharField(max_length=200)
    state = forms.CharField(max_length=200, required=False)
    country = forms.CharField(max_length=2, required=False)
    lat = forms.FloatField(min_value=-90, max_value=90)
    lon = forms.FloatField(min_value=-180, max_value=180)
