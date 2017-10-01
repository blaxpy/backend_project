import json

from .models import InputData, TestInfo, TestException
from .utils import is_prime

from celery import shared_task


@shared_task
def get_json_request(input_data_id):
    input_data = InputData.objects.get(id=input_data_id)
    json_request = json.dumps(input_data.data_array)
    return json_request


@shared_task
def test_func(json_request):
    json_data = json.loads(json_request)

    result = []
    test_exceptions = []
    for array_item_index, data_dict in enumerate(json_data):
        try:
            a = data_dict['a']
            b = data_dict['b']
            assert is_prime(a), "'a' is not prime number"
            assert is_prime(b), "'b' is not prime number"
            result.append({'result': a + b})
        except AssertionError as e:
            result.append({'result': 0})
            test_exceptions.append((array_item_index, repr(e)))

    json_response = json.dumps(result)
    return json_response, test_exceptions


@shared_task
def save_json_response_and_exc(test_func_return_tuple, test_request, input_data_id):
    json_response, test_exceptions = test_func_return_tuple
    result = json.loads(json_response)

    input_data = InputData.objects.get(id=input_data_id)
    test_info = TestInfo.objects.create(test_request=test_request, input_data=input_data, result=result)
    test_info.save()

    if test_exceptions:
        TestException.objects.bulk_create(
            [TestException(test_info=test_info, array_item_index=ind, exception_text=exc_text) for ind, exc_text in
             test_exceptions])
