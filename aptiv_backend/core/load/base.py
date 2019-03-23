import bz2
import os
import sys
from datetime import date

import pandas as pd
from joblib import Memory

from anuario_backoffice.anuario.models.agente import Agente
from anuario_backoffice.arquitecto.models import Arquitecto
from contrib.cae.models import CAE
from contrib.ctt.models import CP7
from contrib.geo.models import Freguesia, Freguesia2013
from ..models import Destino

memory = Memory(cachedir='/tmp/anuario', verbose=0)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def log(process=None, task=None, state='LOG ERROR',progress_data=None, msg='', type='INFO' ):
    def get_progress_msg(current, total, errors=-1, prev=-1, pid='', inserts=-1, updated=-1, not_found=-1):
        server_message = msg + ' {:.0f}% ({:d} of {:d})'.format((current * 1.0 / total) * 100, current, total)
        if updated > 0:
            server_message += ' ({:d} updated)'.format(updated)
        if inserts > 0:
            server_message += ' ({:d} inserts)'.format(inserts)
        if errors > 0:
            server_message += '({:d} errors found)'.format(errors)
        if prev > 0:
            server_message += ' ({:d} previous import)'.format(prev)
        if not_found > 0:
            server_message += ' ({:d} not found)'.format(not_found)
        if pid:
            server_message += ' {:s}'.format(str(pid))
        return server_message

    def get_progress_meta(current, total, errors=0, prev=-1, pid='', inserts=-1, updated=-1, not_found=-1):
        return {'server_message': msg, 'current': current, 'total': total, 'errors': errors}

    # Just in case - avoids divide by zero
    if progress_data:
        if progress_data['total'] == 0:
            progress_data['total'] = -1

    if type == 'STATE':
        # Log to terminal
        sys.stdout.write(state + '\n')
        # Log to Celery
        if task.request.id:
            task.update_state(state=state, meta=get_progress_meta(1, 1, 0))
        # Log to import process logger
        if process:
            process.state.logger += type + ': ' + state + '\n'
    elif type == 'INFO':
        # Log to terminal
        sys.stdout.write(msg)
        # Log to Celery
        if task.request.id:
            task.update_state(state=state, meta=get_progress_meta(1, 1, 0))
        # Log to import process logger
        if process:
            process.state.logger += '- ' + type + ': ' + msg
    elif type=='OK':
        # Log to terminal
        sys.stdout.write(msg + '\n')
        # Log to import process logger
        if process:
            process.state.logger += msg + '\n'
    elif type == 'PROGRESS':
        msg = get_progress_msg(**progress_data)
        # Log to Celery
        if task.request.id:
            task.update_state(state=state, meta=get_progress_meta(**progress_data))
        # Log to terminal
        if progress_data['current'] % 10 == 0:
            sys.stdout.write('\r' + msg + '\n')
            sys.stdout.flush()
        # Save to tmp field to be used in case of error
        if process:
            process.state.dummy = '- ' + type + ': ' + msg + '\n'

    elif type=='FPROGRESS':
        msg = get_progress_msg(**progress_data)

        # Log to import process logger
        if process:
            process.state.logger += '- ' + type + ': ' + msg + '\n'


def bz_guard(filename):
    if filename.endswith('bz2'):
        filein = bz2.BZ2File(filename, 'r')
        filename = filename.replace('.bz2', '')
    else:
        filein = filename
    return filein, filename


def coerce_int(value):
    if pd.isnull(value):
        return None
    return int(value)


def coerce_str(value):
    if pd.isnull(value):
        return ''
    return value


def coerce_bool(value):
    if pd.isnull(value):
        return False
    if value == 1:
        return True
    return False


def coerce_klass(value):
    if pd.isnull(value):
        return None
    try:
        return value.id
    except ValueError:
        pass
    if int(value) == 0:
        return None
    return int(value)


@memory.cache
def get_cp7(cp):
    cp7 = None
    try:
        cp4, cp3 = cp.split('-')
        cp7 = CP7.objects.get(id=int(cp4) * 1000 + int(cp3))
    except ValueError:
        pass
    except AttributeError:
        pass
    except CP7.DoesNotExist:
        pass
    return cp7


def get_cp7_row(row, cp_field, localidade_field=None):
    res = {
        'id': row['id'],
        'cp': None,
        'cp_failed': '%s' % (row[cp_field])
    }

    if localidade_field is not None and pd.notnull(row[localidade_field]):
        res['cp_failed'] += ' ' + str(row[localidade_field])

    cp = row[cp_field]
    if pd.isnull(cp):
        res['cp_failed'] = ''
        return pd.Series(res)

    cp = get_cp7(cp)
    if cp is not None:
        res['cp'] = cp
        res['cp_failed'] = ''

    return pd.Series(res)


@memory.cache
def get_choice_model(name, choicemodel=None):
    if pd.isnull(name) or choicemodel is None:
        return None
    try:
        return choicemodel.objects.get(name__iexact=name)
    except choicemodel.DoesNotExist:
        return None


@memory.cache
def get_choice_model_by_id(num_id, choicemodel=None):
    if pd.isnull(num_id) or choicemodel is None:
        return None
    try:
        return choicemodel.objects.get(id=num_id)
    except choicemodel.DoesNotExist:
        return None


@memory.cache
def get_destino(setor):
    if pd.isnull(setor):
        return None
    try:
        return Destino.objects.get(name__iexact=setor)
    except Destino.DoesNotExist:
        print("Destino (%s) does not exists" % setor)
        pass


@memory.cache
def get_freguesia(freguesia_id):
    if pd.isnull(freguesia_id):
        return None

    if not isinstance(freguesia_id, str):
        dicofre = "%06d" % freguesia_id

    try:
        freguesia = Freguesia.objects.get(dicofre=dicofre)
        if freguesia.fre2013 is not None:
            freguesia = freguesia.fre2013
        return Freguesia2013.objects.get(dicofre=freguesia.dicofre)
    except Freguesia.DoesNotExist:
        try:
            return Freguesia2013.objects.get(id=freguesia_id)
        except Freguesia2013.DoesNotExist:
            print('Freguesia not Found', freguesia_id)

    return None


@memory.cache
def get_cae(code):
    if pd.isnull(code):
        return None
    try:
        return CAE.objects.get(level=5, code=int(code))
    except CAE.DoesNotExist:
        print("code not found", code)
        return None


@memory.cache
def get_arquitecto(arquitecto_id):
    if pd.isnull(arquitecto_id):
        return None

    # noinspection PyTypeChecker
    if not isinstance(arquitecto_id, str):
        try:
            arquitecto_id = int(arquitecto_id)
        except ValueError:
            return None

    try:
        return Arquitecto.objects.get(id=arquitecto_id)
    except Arquitecto.DoesNotExist:
        return None


@memory.cache
def get_agente(nif):
    if pd.isnull(nif):
        return None

    # noinspection PyTypeChecker
    if isinstance(nif, str):
        try:
            nif = int(nif)
        except ValueError:
            return None

    try:
        return Agente.objects.get(nif=nif)
    except Agente.DoesNotExist:
        return None


@memory.cache
def normalize_date(year, month):
    if pd.notnull(year):
        try:
            year = int(year)
        except ValueError:
            return None

        if pd.notnull(month):
            try:
                month = int(month)
            except ValueError:
                return None
            return date(year, month, 1)
        else:
            return date(year, 12, 31)
    return None
