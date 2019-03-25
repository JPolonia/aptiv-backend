from django.contrib import admin
from aptiv_backend.core.models import Pdf

from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget

@admin.register(Pdf)
class PdfAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    list_display = ['id','output_has_errors', 'compare_id','rev_letter', 'pdf_file', 'num_pages',]
    list_display_links = ('id', 'output_has_errors', 'compare_id', 'rev_letter')

    readonly_fields = ['error_msg', 'num_pages', 'rev_letter', 'compare_id', 'output_has_errors']

    fieldsets = (
        ('General Info', {
            'fields': ('pdf_file', 'num_pages', 'rev_letter', 'compare_id', 'output_has_errors')
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
