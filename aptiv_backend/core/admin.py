# from django.contrib import admin
# from .models import ErrorFile
# from django.db import models
#
# class ErrorFileInline(admin.TabularInline):
#     model = ErrorFile
#     extra = 1
#     show_change_link = True
#
#     def get_readonly_fields(self, request, obj=None):
#         readonly_fields = super(ErrorFileInline, self).get_readonly_fields(request, obj)
#         if obj:  # editing an existing object
#             return ('file',) + readonly_fields
#         return readonly_fields
#
#
# class ImportProcessAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'upload_date', 'get_stage', 'celery_task', 'get_task_status', 'server_message', 'progress_bar')
#
#     list_filter = ('state__stage',)
#
#     inlines=()
#
#     def add_view(self, request, extra_content=None):
#         self.fieldsets = None
#         return super(ImportProcessAdmin, self).add_view(request)
#
#     def change_view(self, request, object_id, extra_content=None):
#         self.inlines = (ErrorFileInline,)
#         self.fieldsets = (
#             ('Report', {
#                 'fields': (('id',),
#                            'get_stage', 'get_duration',
#                            'get_inserts','get_updates' , 'get_duplicates', 'get_errors',
#                            )
#             }),
#             ('Logger', {
#                 'fields': ('get_logger', 'get_traceback',)
#             }),
#         )
#         return super(ImportProcessAdmin, self).change_view(request, object_id)
#
#     def get_readonly_fields(self, request, obj=None):
#         readonly_fields = super(ImportProcessAdmin, self).get_readonly_fields(request, obj)
#         if obj:  # editing an existing object
#             return ('id','file', 'state', 'celery_task', 'update_agentes',
#                     'get_stage', 'get_logger', 'get_traceback', 'get_inserts', 'get_updates', 'get_duplicates', 'get_errors', 'get_duration'
#                     ) + readonly_fields
#         return readonly_fields
#
#     class Media:
#         js = ('js/admin/import_process.js', 'js/admin/bootstrap.bundle.min.js')
#         css = {
#             'all': ('css/admin/import_process.css',)
#         }
