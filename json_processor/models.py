from django.db import models
from django.contrib.postgres.fields import JSONField


class InputData(models.Model):
    data_array = JSONField()

    def __str__(self):
        return 'array #%s' % self.id


class TestInfo(models.Model):
    test_request = models.IntegerField()
    input_data = models.ForeignKey(InputData)
    result = JSONField()

    def __str__(self):
        return 'info #%s' % self.id


class TestException(models.Model):
    test_request = models.IntegerField()
    input_data = models.ForeignKey(InputData)
    array_item_index = models.IntegerField()
    exception_text = models.CharField(max_length=100)

    def __str__(self):
        return 'exception #%s' % self.id
