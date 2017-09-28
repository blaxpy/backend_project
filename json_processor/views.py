from django.shortcuts import render, redirect
from django.views import generic

from json_processor.models import InputData, TestInfo
from json_processor.forms import InputDataForm


class IndexView(generic.TemplateView):
    template_name = 'json_processor/index.html'


class UploadDataView(generic.FormView):
    template_name = 'json_processor/upload_data.html'
    form_class = InputDataForm

    def form_valid(self, form):
        input_data = form.save()
        print(input_data, repr(input_data.data_array))
        return redirect('index')
