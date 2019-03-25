from django.db import models
from .pdf import Pdf
from .excel import Excel
from django.conf import settings


def output_file_path(instance, filename):
    return settings.OUTPUT_PATH + filename

class AptivValidate(models.Model):
    pdf = models.ForeignKey(Pdf, blank= True, null= True, on_delete=models.CASCADE)
    excel = models.ForeignKey(Excel, blank=True, null=True, on_delete=models.CASCADE)

    output = models.FileField(upload_to=output_file_path)


    def save(self, *args, **kwargs):
        super(AptivValidate, self).save(*args, **kwargs)
