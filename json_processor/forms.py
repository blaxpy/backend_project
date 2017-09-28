import json
from django import forms

from json_processor.models import InputData


class InputDataForm(forms.ModelForm):
    data_array = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': 'Input array similar to: [{"a": val1 (int)}, {"b": val2 (int)}, ...]'}), required=True)

    class Meta:
        model = InputData
        fields = ('data_array',)

    def clean_data_array(self):
        data_array = self.cleaned_data['data_array']
        try:
            data_array_json_string = data_array.replace("'", '"')
            json_data = json.loads(data_array_json_string)
        except json.JSONDecodeError:
            raise forms.ValidationError("Input does not match json format")
        return json_data
