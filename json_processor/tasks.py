import json
import math

from json_processor.models import InputData, TestException

from celery import shared_task


@shared_task
def test_func(json_request, test_request, input_data_id):
    json_data = json.loads(json_request)
    result = []
    for array_item_index, data_dict in enumerate(json_data):
        result.append(process_json_dict(data_dict, test_request, input_data_id, array_item_index))
    json_response = repr(result).replace("'", '"')
    return json_response


def process_json_dict(data_dict, test_request, input_data_id, array_item_index):
    a = data_dict['a']
    b = data_dict['b']
    try:
        assert is_prime(a), "'a' is not prime number"
        assert is_prime(b), "'b' is not prime number"
    except AssertionError as e:
        input_data = InputData.objects.get(id=input_data_id)
        test_exception = TestException.objects.create(test_request=test_request, input_data=input_data,
                                                      array_item_index=array_item_index, exception_text=repr(e))
        test_exception.save()
        return {'result': 0}
    return {'result': a + b}


def is_prime(n):
    if n == 2:
        return True
    if n % 2 == 0 or n <= 1:
        return False

    sqr = int(math.sqrt(n)) + 1

    for divisor in range(3, sqr, 2):
        if n % divisor == 0:
            return False
    return True
