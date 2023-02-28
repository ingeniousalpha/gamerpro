from django.db import models
import inspect
import sys


class MainManager(models.Manager):

    def get_queryset(self):
        queryset = super(MainManager, self).get_queryset()
        return queryset
