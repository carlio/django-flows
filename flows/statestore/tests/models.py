
from django.db import models


class TestModel(models.Model):
    fruit = models.CharField(max_length=20)
    count = models.IntegerField()