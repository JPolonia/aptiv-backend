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

    list_display = ['id','output_has_errors', 'compare_id','rev_letter', 'excel_file',]
    list_display_links = ('id', 'output_has_errors', 'compare_id', 'rev_letter')

    readonly_fields = ['error_msg', 'rev_letter', 'compare_id', 'output_has_errors']

    fieldsets = (
        ('General Info', {
            'fields': ('excel_file', 'rev_letter', 'compare_id', 'output_has_errors')
        }),
        ('Output', {
            'fields': ('compare_id', 'compare_json')
        }),
        ('Errors', {
            'fields': (['error_msg'])
        }),
    )

    def output_has_errors(self,obj):
        if not obj.error_msg:
            return True
        return False
    output_has_errors.short_description = "No Errors"
    output_has_errors.boolean = True
