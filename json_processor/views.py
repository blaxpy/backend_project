from django.shortcuts import redirect
from django.views import generic
from django.contrib import messages

from celery import chain

from .models import InputData, TestInfo
from .forms import InputDataForm, StartTestForm

from .tasks import get_json_request, test_func, save_json_response_and_exc


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
        input_data_count = InputData.objects.count()
        last_test_info = TestInfo.objects.last()
        if last_test_info:
            test_request = last_test_info.test_request + 1
        else:
            test_request = 1

        for input_data_id in range(1, input_data_count + 1):
            chain(get_json_request.s(input_data_id)
                  | test_func.s()
                  | save_json_response_and_exc.s(test_request, input_data_id))()

        messages.success(self.request, 'We are testing the function on the previously listed data sets. '
                                       'Wait a moment and refresh this page.')
        return redirect('json_processor:show_test_info', test_request)


class ShowTestInfoView(generic.TemplateView):
    template_name = 'json_processor/show_test_info.html'

    def get_context_data(self, **kwargs):
        test_request = self.kwargs['test_request']
        if test_request == 'last':
            test_request = TestInfo.objects.last().test_request

        test_info = TestInfo.objects.filter(test_request=test_request)

        zipped_info_list = None
        exception_list = None

        if test_info:
            zipped_info_list = []
            exception_list = []
            for t_i in test_info:
                zipped_info_list.append(zip(t_i.input_data.data_array, t_i.result))

                test_exception = t_i.testexception_set.all()
                if test_exception:
                    exception_list.append(
                        (t_e.test_info.input_data.id, t_e.test_info.input_data.data_array[t_e.array_item_index],
                         t_e.exception_text) for t_e in test_exception)

        kwargs['test_request'] = test_request
        kwargs['zipped_info_list'] = zipped_info_list
        kwargs['exception_list'] = exception_list
        return super(ShowTestInfoView, self).get_context_data(**kwargs)
