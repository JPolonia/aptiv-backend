from django.db import models
from django.contrib.postgres.fields import JSONField
from django.conf import settings

def import_file_path(instance, filename):
    return settings.UPLOAD_PATH + filename

class Excel(models.Model):

    excel_file = models.FileField(upload_to=import_file_path)

    rev_letter = models.CharField(max_length=10, null=True, blank=True)
    compare_id = models.IntegerField(null=True, blank=True)

    compare_json = JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):

        super(Excel, self).save(*args, **kwargs)
