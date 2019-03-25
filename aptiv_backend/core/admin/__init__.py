from django.contrib import admin

from .pdf import PdfAdmin
from .excel import ExcelAdmin
from .aptiv_validate import AptivValidateAdmin

admin.site.site_header = 'VALIDATION BACKEND'
