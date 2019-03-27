from django.db import models
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from aptiv_backend.core.logic import processExcel

import re

def import_file_path(instance, filename):
    return settings.UPLOAD_PATH + filename

def validate_file_extension(value):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.xls', '.xlsx']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Formato Inválido (formatos validos %s)' % ",".join(valid_extensions))

class Excel(models.Model):

    excel_file = models.FileField(upload_to=import_file_path, validators=[validate_file_extension])

    rev_letter = models.CharField(max_length=10, null=True, blank=True)
    compare_id = models.CharField(max_length=20, null=True, blank=True)

    compare_json = JSONField(null=True, blank=True)

    error_msg = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.compare_id:
            return self.compare_id + ' (ID:' + str(self.id) + ')'
        else:
            return str(self.id)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def save(self, update=True, new=False, *args, **kwargs):
        if self.id is None:
            new = True

        super(Excel, self).save(*args, **kwargs)

        if new or update:
            self.rev_letter, self.compare_id, self.compare_json, self.error_msg = processExcel(self.excel_file.path)
            self.save(update=False)
