from celery import shared_task
from celery.task import task
# from django.core.exceptions import ObjectDoesNotExist
from time import sleep, time

# from django.conf import settings
#
# from .load import load
#
# import zipfile, datetime, os, shutil
#
# import traceback
# import sys

# def format_exception(e):
#     exception_list = traceback.format_stack()
#     exception_list = exception_list[:-2]
#     exception_list.extend(traceback.format_tb(sys.exc_info()[2]))
#     exception_list.extend(traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1]))
#
#     exception_str = "Traceback (most recent call last):\n"
#     exception_str += "".join(exception_list)
#     # Removing the last \n
#     exception_str = exception_str[:-1]
#
#     return exception_str


@task
def add(x, y):
    sleep(2)
    return x + y


# @task(bind=True, autoretry_for=(ObjectDoesNotExist,), retry_kwargs={'max_retries': 5}, retry_backoff=True)
# def start_import(task, process_id):
#     print(task.request.id)
#     print(process_id)
#
#     # Start timer for duration
#     start_time = time()
#
#     from .models import ImportProcess, ImportProcessState
#
#     # Get current ImportProcess
#     process = ImportProcess.objects.get(id=process_id)
#     process.celery_task = task.request.id
#     process.save()
#
#     # Unzip files to tmp folder
#     tmp_path = os.path.splitext(process.file.path)[0]
#     print(process.file.path)
#     print(tmp_path)
#     with zipfile.ZipFile(process.file.path, "r") as zip_ref:
#         zip_ref.extractall(tmp_path)
#
#     # Create dir for error files if not exist
#     if not os.path.exists(os.path.dirname(settings.ERROR_ROOT)):
#         os.makedirs(os.path.dirname(settings.ERROR_ROOT))
#
#     # print(os.path.splitext(process.file.name)[0])
#
#     # Stage updated to Loading - task id is sent to FrontEnd
#     process.state.stage = ImportProcessState.STAGES.loading
#     process.state.save()
#
#     try:
#         load(tmp_path, process, task)
#
#         if process.state.errors > 0:
#             process.state.stage = ImportProcessState.STAGES.finisherrors
#         else:
#             process.state.stage = ImportProcessState.STAGES.finished
#
#         process.state.duration = datetime.timedelta(seconds=(time() - start_time))
#
#         # Update Celery Status to Update FrontEnd
#         task.update_state(state='COMPLETED')
#
#     except Exception as err:
#         # Import Process Failed - Save to database
#         process.state.stage = ImportProcessState.STAGES.failed
#         process.state.duration = datetime.timedelta(seconds=(time() - start_time))
#         if process.state.dummy:
#             process.state.logger += process.state.dummy
#         process.state.logger += str(err) + '\n'
#         process.state.traceback += format_exception(err) + '\n'
#
#         task.update_state(state='FAILED')
#
#     finally:
#         process.state.save()
#
#     # Delete tmp folder
#     if os.path.exists(tmp_path):
#         print(tmp_path)
#         shutil.rmtree(tmp_path, ignore_errors=True)
#     else:
#         print("The folder does not exist")
#
#     # Remove zip file
#     path = process.file.path
#     if os.path.exists(path):
#         print(path)
#         os.remove(path)
#     else:
#         print("The zip file does not exist")
