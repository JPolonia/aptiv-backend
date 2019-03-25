from django.contrib import admin
from aptiv_backend.core.models import AptivValidate


@admin.register(AptivValidate)
class AptivValidateAdmin(admin.ModelAdmin):
    pass
