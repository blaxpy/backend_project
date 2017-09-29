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
            raise forms.ValidationError('Input does not match required format: input is not a valid JSON')
        if isinstance(json_data, list):
            for item in json_data:
                try:
                    if not (isinstance(item, dict) and len(item) == 2 and isinstance(item['a'], int) and isinstance(
                            item['b'], int)):
                        raise forms.ValidationError('Input does not match required format: '
                                                    'list items must be of (dict) type '
                                                    'with exactly two elements of (int) type')
                except KeyError as e:
                    raise forms.ValidationError(
                        'Input does not match required format: in dictionary %s key "%s" doesn\'t exist' % (
                            repr(item), e.args[0]))
        else:
            raise forms.ValidationError('Input does not match required format: input must be of (list) type')
        return json_data
