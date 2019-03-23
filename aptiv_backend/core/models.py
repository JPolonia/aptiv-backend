# from django.db import models
# from django.utils.translation import ugettext as _
# from django.conf import settings
#
# from model_utils import Choices
# from model_utils.models import TimeStampedModel
# from .. import tasks
# from celery.result import AsyncResult
#
# import datetime
# import os
#
#
# def import_file_path(instance, filename):
#     return settings.UPLOAD_PATH + filename
#
#
# def validate_file_extension(value):
#     import os
#     from django.core.exceptions import ValidationError
#     ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
#     valid_extensions = ['.zip']
#     if not ext.lower() in valid_extensions:
#         raise ValidationError('Formato Inválido (formatos validos %s)' % ",".join(valid_extensions))
#
#
# class ImportProcessState(models.Model):
#     STAGES = Choices(
#         (0, 'loading', 'Loading'),
#         (1, 'failed', 'Failed'),
#         (2, 'finished', 'Finished'),
#         (3, 'init', 'Init'),
#         (4, 'removable', 'Removable'),
#         (5, 'finisherrors', 'Finished w/ Errors'),
#     )
#
#     stage = models.SmallIntegerField(choices=STAGES, default=STAGES.init, editable=False)
#
#     logger = models.TextField(_('Logger'), blank=True, default='')
#     traceback = models.TextField(_('Traceback'), blank=True, default='')
#
#     insertions = models.IntegerField(_('New'), default=0, editable=False)
#     duplicates = models.IntegerField(_('Duplicates'), default=0, editable=False)
#     errors = models.IntegerField(_('Erros'), default=0, editable=False)
#
#     updates = models.IntegerField(_('Updates'), default=0, editable=False)
#
#     duration = models.DurationField(_('Import Duration'), default=datetime.timedelta(seconds=0), editable=False)
#
#     dummy = models.TextField(default='', null=True, blank=True, editable=False)
#
#     def __str__(self):
#         return "%s: %s" % (str(self.id), self.get_stage_display())
#
#
# class ImportProcess(TimeStampedModel):
#     file = models.FileField(upload_to=import_file_path, validators=[validate_file_extension])
#     upload_date = models.DateField(_('Data de Upload'), auto_now_add=True)
#     state = models.OneToOneField(ImportProcessState, on_delete=models.CASCADE, null=True, editable=False)
#     celery_task = models.CharField(_('Celery Task ID'), max_length=100, blank=True, null=True, editable=False)
#
#     update_agentes = models.BooleanField(_('Update Existing Agentes'), default=False)
#
#     def __str__(self):
#         return "%s: %s" % (str(self.id), self.upload_date)
#
#     def progress_bar(self):
#         return 'OK'
#
#     progress_bar.short_description = 'Progress'  # Renames column head
#
#     def get_stage(self):
#         return self.state.get_stage_display()
#
#     get_stage.short_description = 'Stage'  # Renames column head
#     get_stage.admin_order_field = 'state__stage'  # Allows column order sorting
#
#     def get_logger(self):
#         return self.state.logger
#     get_logger.short_description = 'Logger'
#
#     def get_traceback(self):
#         return self.state.traceback
#     get_traceback.short_description = 'Traceback'
#
#     def get_inserts(self):
#         return self.state.insertions
#     get_inserts.short_description = 'Inserts'
#
#     def get_errors(self):
#         return self.state.errors
#     get_errors.short_description = 'Errors'
#
#     def get_duplicates(self):
#         return self.state.duplicates
#     get_duplicates.short_description = 'Duplicates'
#
#     def get_updates(self):
#         return self.state.updates
#     get_updates.short_description = 'Updates'
#
#     def get_duration(self):
#         return self.state.duration
#     get_duration.short_description = 'Time'
#
#     def server_message(self):
#         server_message = ''
#         if self.get_inserts() > 0:
#             server_message += str(self.get_inserts()) + ' insert(s) '
#         if self.get_updates() > 0 or self.update_agentes:
#             server_message += str(self.get_updates()) + ' updates(s) '
#         if self.get_duplicates() > 0:
#             server_message += str(self.get_duplicates()) + ' duplicate(s) '
#         if self.get_errors() > 0:
#             server_message += str(self.get_errors()) + ' error(s) '
#         return server_message
#
#     def obs(self):
#         return self.description
#
#
#     def get_task_status(self):
#         try:
#             status = AsyncResult(self.celery_task).state
#             if status == 'PENDING':
#                 if self.state.stage == ImportProcessState.STAGES.loading:
#                     self.state.stage = ImportProcessState.STAGES.failed
#                     self.state.save()
#                     return 'LOST'
#                 else:
#                     return 'UNKNOWN'
#             elif status == 'REVOKED' or status == 'FAILURE':
#                 if self.state.stage != ImportProcessState.STAGES.failed:
#                     self.state.stage = ImportProcessState.STAGES.failed
#                     self.state.save()
#                 return status
#             else:
#                 return status
#         except Exception as err:
#             return 'Task Inactive'
#
#     get_task_status.short_description = 'REDIS'  # Renames column head
#
#     def save(self, local=False, *args, **kwargs):
#         new = False
#         # local = True # Uncomment to run without celery
#
#         if self.id is None:
#             new = True
#             # Create new State obj
#             state = ImportProcessState()
#             state.save()
#             # Link State to ImportProcess
#             self.state = state
#
#         super(ImportProcess, self).save(*args, **kwargs)
#
#         if new:
#             if local:
#                 tasks.start_import(self.id)
#             else:
#                 tasks.start_import.apply_async((self.id,))
#
#     def delete(self, *args, **kwargs):
#         error_set = ErrorFile.objects.filter(import_process=self)
#         for error_file in error_set:
#             error_file.delete()
#
#         super(ImportProcess, self).delete()
#
#
# def import_error_path(instance, filename):
#     return settings.ERROR_PATH + filename
#
#
# class ErrorFile(models.Model):
#     file = models.FileField(upload_to=import_error_path)
#     import_process = models.ForeignKey(ImportProcess, on_delete=models.CASCADE, null=True)
#
#     def delete(self, *args, **kwargs):
#         process = self.import_process
#         path = self.file.path
#         super(ErrorFile, self).delete()
#         # Update Process
#         if not ErrorFile.objects.filter(import_process=process).exists():
#             # print('BINGO')
#             self.import_process.state.stage = ImportProcessState.STAGES.finished
#             self.import_process.state.errors = 0
#             self.import_process.state.save()
#         # Delete file
#         if os.path.exists(path):
#             print(path)
#             os.remove(path)
#         else:
#             print("The file does not exist")
