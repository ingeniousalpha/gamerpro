from django.db import models
import inspect
import sys


class MainManager(models.Manager):

    def get_queryset(self):
        queryset = super(MainManager, self).get_queryset()

        ml_classes = [c[1] for c in inspect.getmembers(sys.modules['apps.translations.models'], inspect.isclass)]
        rel_fields = []

        for f in queryset.model._meta.get_fields():
            if f.is_relation and hasattr(f, 'to_fields') and 'id' in f.to_fields:
                if f.related_model in ml_classes:
                    rel_fields.append(f.name)

        queryset = queryset.select_related(*rel_fields)
        return queryset
