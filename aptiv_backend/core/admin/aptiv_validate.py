from django.contrib import admin
from aptiv_backend.core.models import AptivValidate

from django.utils.html import format_html
from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget


@admin.register(AptivValidate)
class AptivValidateAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    list_display = ['id','output_has_errors', 'output_has_warnings', 'pdf_model', 'pdf_file', 'excel_model', 'excel_file', ]
    list_display_links = ('id', 'output_has_errors', 'output_has_warnings',)

    readonly_fields = ['output',]

    def pdf_model(self, obj):
        return format_html("<a href='{url}'>{name}</a>", url=obj.pdf.get_admin_url(), name=obj.pdf)
    pdf_model.short_description = "PDF Process"

    def pdf_file(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.pdf.pdf_file.url)
    pdf_file.short_description = "PDF File"

    def excel_model(self, obj):
        return format_html("<a href='{url}'>{name}</a>", url=obj.excel.get_admin_url(), name=obj.excel)
    excel_model.short_description = "Excel Process"

    def excel_file(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.excel.excel_file.url)
    excel_file.short_description = "Excel File"

    def output_has_errors(self,obj):
        if str(obj.output).find('ERROR') == -1:
            return True
        return False
    output_has_errors.short_description = "Errors"
    output_has_errors.boolean = True

    def output_has_warnings(self,obj):
        if str(obj.output).find('WARNING') == -1:
            return True
        return False
    output_has_warnings.short_description = "Warnings"
    output_has_warnings.boolean = True
