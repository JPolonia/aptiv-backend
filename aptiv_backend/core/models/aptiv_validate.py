from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from aptiv_backend.core.logic import processValidation

from .pdf import Pdf
from .excel import Excel


def output_file_path(instance, filename):
    return settings.OUTPUT_PATH + filename

class AptivValidate(models.Model):
    pdf = models.ForeignKey(Pdf, blank= True, null= True, on_delete=models.CASCADE, verbose_name='PDF')
    excel = models.ForeignKey(Excel, blank=True, null=True, on_delete=models.CASCADE, verbose_name='EXCEL')

    output = models.TextField(_('OUTPUT'), null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def save(self,update=True, new=False, *args, **kwargs):
        if self.id is None:
            new = True

        super(AptivValidate, self).save(*args, **kwargs)

        if new or update:
            self.output = processValidation(self.pdf.compare_json, self.excel.compare_json)
            self.save(update=False)







