import json
# from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from json_processor.models import InputData, TestInfo, TestException
from json_processor.tasks import get_json_request, test_func, save_json_response_and_exc


class InputDataFormTests(TestCase):
    def setUp(self):
        self.url = reverse('json_processor:upload_data')

    def test_correct_input(self):
        data = {'data_array': '[{"a": 2, "b": 3}, {"a": 4, "b": 5}]'}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertFormError(response, 'form', 'data_array', None)
        self.assertContains(response, text='Data set was successfully uploaded.')

    def test_not_json(self):
        data = {'data_array': '{"a": 2, "b": 3}, [1, 2]'}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertFormError(response, 'form', 'data_array',
                             'Input does not match required format: input is not a valid JSON')

    def test_not_list(self):
        data = {'data_array': '{"a": 2, "b": 3}'}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertFormError(response, 'form', 'data_array',
                             'Input does not match required format: input must be of (list) type')

    def test_float_value(self):
        data = {'data_array': '[{"a": 2, "b": 3.2}, {"a": 2, "b": 3, "c": 3}]'}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertFormError(response, 'form', 'data_array',
                             'Input does not match required format: '
                             'list items must be of (dict) type '
                             'with exactly two elements of (int) type')

    def test_list_items_are_not_dicts(self):
        data = {'data_array': '[[2, 3], [2, 3]]'}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertFormError(response, 'form', 'data_array',
                             'Input does not match required format: '
                             'list items must be of (dict) type '
                             'with exactly two elements of (int) type')

    def test_dict_of_incorrect_length(self):
        data = {'data_array': '[{"a": 2, "b": 3}, {"a": 2, "b": 3, "c": 5}]'}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertFormError(response, 'form', 'data_array',
                             'Input does not match required format: '
                             'list items must be of (dict) type '
                             'with exactly two elements of (int) type')

    def test_missing_key(self):
        data = {'data_array': '[{"a": 2, "b": 3}, {"c": 4, "b": 5}]'}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertFormError(response, 'form', 'data_array',
                             'Input does not match required format: '
                             'in dictionary {"c": 4, "b": 5} key "a" doesn\'t exist')


class ShowTestInfoViewTests(TestCase):
    def setUp(self):
        self.url = reverse('json_processor:show_test_info', args=(1,))

    def test_empty_test_info_and_no_msg(self):
        response = self.client.get(self.url)
        self.assertContains(response, text='Requested Test Info does not exist.')

    def test_request_without_exceptions(self):
        data_arrays = [[{"a": 2, "b": 3}, {"a": 3, "b": 5}], [{"a": 5, "b": 7}, {"a": 7, "b": 11}]]

        input_data_list = []
        results = []
        for data_array in data_arrays:
            input_data = InputData.objects.create(data_array=data_array)
            input_data.save()
            input_data_list.append(input_data)
            results.append([{"result": d["a"] + d["b"]} for d in data_array])

        for input_data, result in zip(input_data_list, results):
            test_info = TestInfo(test_request=1, input_data=input_data, result=result)
            test_info.save()

        response = self.client.get(self.url)
        self.assertContains(response, text='Overall status: <strong>True</strong>')

        for input_data, result in zip(input_data_list, results):
            for d, res in zip(input_data.data_array, result):
                self.assertContains(response,
                                    text="{&quot;a&quot;: %s, &quot;b&quot;: %s} - {&quot;result&quot;: %s}" % (
                                        d['a'], d['b'], res['result']))

        self.assertNotContains(response, text="During the test following exceptions occurred:")

    def test_request_with_exceptions(self):
        data_array_with_prime = [{"a": 2, "b": 3}, {"a": 4, "b": 5}]
        input_data_with_prime = InputData.objects.create(data_array=data_array_with_prime)
        input_data_with_prime.save()
        result_with_prime = [{"result": 5}, {"result": 0}]

        test_info = TestInfo(test_request=1, input_data=input_data_with_prime, result=result_with_prime)
        test_info.save()

        test_exception = TestException(test_info=test_info, array_item_index=1,
                                       exception_text='AssertionError("\'a\' is not prime number",)')
        test_exception.save()

        response = self.client.get(self.url)
        self.assertContains(response, text='Overall status: <strong>False</strong>')
        self.assertContains(response, text="During the test following exceptions occurred:")
        self.assertContains(response,
                            text="{&quot;a&quot;: 4, &quot;b&quot;: 5} - "
                                 "AssertionError(&quot;&#39;a&#39; is not prime number&quot;,)")


class GetJsonRequestTest(TestCase):
    def setUp(self):
        self.data_array = [{"a": 2, "b": 3}, {"a": 3, "b": 5}]
        self.input_data = InputData.objects.create(data_array=self.data_array)
        self.input_data.save()

    def test_json_request(self):
        self.assertEqual(get_json_request.apply(args=(InputData.objects.last().id,)).get(),
                         json.dumps(self.input_data.data_array))


class TestFuncTest(TestCase):
    def test_json_response_and_no_exceptions(self):
        data_array = [{"a": 2, "b": 3}, {"a": 3, "b": 5}]
        json_response = json.dumps([{"result": 5}, {"result": 8}])
        exceptions = []
        self.assertEqual(test_func.apply(args=(json.dumps(data_array),)).get(), (json_response, exceptions))

    def test_json_response_and_exceptions(self):
        data_array = [{"a": 2, "b": 3}, {"a": 4, "b": 5}]
        json_response = json.dumps([{"result": 5}, {"result": 0}])
        exceptions = [(1, 'AssertionError("\'a\' is not prime number",)')]
        self.assertEqual(test_func.apply(args=(json.dumps(data_array),)).get(), (json_response, exceptions))


class SaveJsonRequestAndExcTest(TestCase):
    def setUp(self):
        self.data_array = [{"a": 2, "b": 3}, {"a": 3, "b": 5}]
        # Define common input_data and json_response just to test object creation, values are not important
        self.input_data = InputData.objects.create(data_array=self.data_array)
        self.input_data.save()
        self.json_response = json.dumps([{"result": 5}, {"result": 8}])

    def test_test_info_without_exceptions(self):
        exceptions = []
        save_json_response_and_exc.apply(args=((self.json_response, exceptions), 1, InputData.objects.last().id))
        self.assertQuerysetEqual(TestInfo.objects.all(), ['<TestInfo: info #%s>' % TestInfo.objects.last().id])
        self.assertQuerysetEqual(TestInfo.objects.last().testexception_set.all(), [])

    def test_test_info_with_exceptions(self):
        exceptions = [(1, 'AssertionError("\'a\' is not prime number",)')]
        save_json_response_and_exc.apply(args=((self.json_response, exceptions), 2, InputData.objects.last().id))
        self.assertQuerysetEqual(TestInfo.objects.all(), ['<TestInfo: info #%s>' % TestInfo.objects.last().id])
        self.assertQuerysetEqual(TestInfo.objects.last().testexception_set.all(),
                                 ['<TestException: exception #%s>' % TestException.objects.last().id])
