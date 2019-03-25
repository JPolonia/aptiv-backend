from django.contrib import admin
from aptiv_backend.core.models import Excel


@admin.register(Excel)
class ExcelAdmin(admin.ModelAdmin):
    pass
