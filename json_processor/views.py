import json

from django.shortcuts import redirect
from django.views import generic
from django.contrib import messages

from .models import InputData, TestInfo, TestException
from .forms import InputDataForm, StartTestForm

from .tasks import test_func


class IndexView(generic.TemplateView):
    template_name = 'json_processor/index.html'


class UploadDataView(generic.FormView):
    template_name = 'json_processor/upload_data.html'
    form_class = InputDataForm

    def form_valid(self, form):
        form.save()

        messages.success(self.request, 'Data set was successfully uploaded.')

        return redirect('json_processor:upload_data')


class StartTestView(generic.FormView, generic.ListView):
    template_name = 'json_processor/start_test.html'
    form_class = StartTestForm

    def get_queryset(self):
        return InputData.objects.all()

    def form_valid(self, form):
        input_data = InputData.objects.all()
        last_test_info = TestInfo.objects.last()
        if last_test_info:
            test_request = last_test_info.test_request + 1
        else:
            test_request = 1

        for obj in input_data:
            json_request = repr(obj.data_array).replace("'", '"')
            result_object = test_func.delay(json_request=json_request, test_request=test_request,
                                            input_data_id=obj.id)
            json_response = result_object.get()
            result = json.loads(json_response)
            test_info = TestInfo.objects.create(test_request=test_request, input_data=obj, result=result)
            test_info.save()

        messages.success(self.request, 'We are testing the function on the previously listed data sets. '
                                       'Wait a moment and refresh this page.')
        return redirect('json_processor:show_test_info', test_request)


class ShowTestInfoView(generic.TemplateView):
    template_name = 'json_processor/show_test_info.html'

    def get_context_data(self, **kwargs):
        test_request = self.kwargs['test_request']
        test_info = TestInfo.objects.filter(test_request=test_request)
        test_exception = TestException.objects.filter(test_request=test_request)
        zipped_info_list = []
        if test_info:
            for t_i in test_info:
                zipped_info_list.append(zip(t_i.input_data.data_array, t_i.result))
        exception_list = []
        if test_exception:
            for t_e in test_exception:
                exception_list.append((t_e.input_data_id, t_e.input_data.data_array[t_e.array_item_index], t_e.exception_text))

        kwargs['test_request'] = test_request
        kwargs['zipped_info_list'] = zipped_info_list
        kwargs['exception_list'] = exception_list
        return super(ShowTestInfoView, self).get_context_data(**kwargs)
