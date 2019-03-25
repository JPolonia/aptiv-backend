from django.contrib import admin
from aptiv_backend.core.models import Excel

from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget

@admin.register(Excel)
class ExcelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    readonly_fields = ['error_msg', 'rev_letter', 'compare_id']
