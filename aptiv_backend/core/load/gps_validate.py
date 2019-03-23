from anuario_backoffice.anuario.models import Licenca, Pic
from .base import log


def gps_licencas(new_lics=None, process=None, task=None, state='VALIDATING GPS (LICS)'):
    count = len(new_lics)
    i = 0
    for licenca in new_lics:
        i += 1
        progress_data = {'current': i, 'total': count, 'pid': str(licenca.id)}
        log(process, task, state, progress_data, type='PROGRESS')
        licenca.validate_gps()
        licenca.save()

    if count:
        progress_data = {'current': count, 'total': count}
        log(process, task, state, progress_data, type='FPROGRESS')


def gps_pics(new_pics=None, process=None, task=None, state='VALIDATING GPS (PICS)'):
    count = len(new_pics)
    i = 0
    for pic in new_pics:
        i += 1
        progress_data = {'current': i, 'total': count, 'pid': str(pic.id)}
        log(process, task, state, progress_data, type='PROGRESS')
        pic.validate_gps()
        pic.save()

    if count:
        progress_data = {'current': count, 'total': count}
        log(process, task, state, progress_data, type='FPROGRESS')
