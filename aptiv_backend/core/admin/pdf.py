from django.contrib import admin
from aptiv_backend.core.models import Pdf


@admin.register(Pdf)
class PdfAdmin(admin.ModelAdmin):
    pass
