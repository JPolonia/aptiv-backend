import sys
import ntpath
from datetime import datetime
from functools import partial

from django.db import transaction
from django.forms import ModelForm
from django.conf import settings

from anuario_backoffice.anuario.models import Tipo
from anuario_backoffice.arquitecto.models import Arquitecto, Projecto, STATUS_PUBLISHED, STATUS_UNPUBLISHED
from .base import pd, get_cp7_row, coerce_str, coerce_klass, coerce_bool, coerce_int, bz_guard, log
from ..models import Licenca


class ArquitectoForm(ModelForm):
    class Meta:
        model = Arquitecto
        exclude = ['position', ]
        # fields = '__all__'


@transaction.atomic
def load_arquitectos(filename, process=None, task=None, state='LOADING ARQUITECTOS'):
    filein, filename = bz_guard(filename)

    log(process, task, state, type='INFO', msg='Loading from ' + str(ntpath.basename(filename)))
    df = pd.read_excel(filein, sheet_name=0)
    log(process, task, state, type='OK', msg=' -> {:d} pics'.format(len(df)))

    log(process, task, state, type='INFO', msg='Dropping duplicates\n')
    df.drop_duplicates(inplace=True)
    df_in = df.copy()

    log(process, task, state, type='INFO', msg='Normalizing cp\n')
    df_cp = df.apply(partial(get_cp7_row, cp_field='CP', localidade_field='Localidade'), axis=1)
    df = pd.merge(df, df_cp, on='id')

    count = len(df)
    arquitectos = []
    errors = []
    previous = 0
    i = 0
    for _, arquitecto in df.iterrows():
        i += 1
        progress_data = {'current': i, 'total': count, 'errors': len(errors), 'prev': previous,
                         'pid': str(arquitecto['id'])}
        log(process, task, state, progress_data, type='PROGRESS')
        try:
            dummy = Arquitecto.objects.get(pk=arquitecto['id'])
            previous += 1
            continue
        except Arquitecto.DoesNotExist:
            pass

        now = datetime.now()

        form = ArquitectoForm(dict(
            id=arquitecto['id'],
            ps=coerce_bool(arquitecto['ps']),
            nif=coerce_int(arquitecto['nif']),

            nome=arquitecto['nome'],
            atelier=coerce_str(arquitecto['atelier']),

            morada=coerce_str(arquitecto['morada']),
            cp=coerce_klass(arquitecto['cp']),
            cp_failed=arquitecto['cp_failed'],

            telefones=coerce_str(arquitecto['telefones']),
            email=coerce_str(arquitecto['email']),
            website=coerce_str(arquitecto['website']),

            observations=coerce_str(arquitecto['obs']),

            created=now,
            modified=now
        ))
        if form.is_valid():
            arquitectos.append(form.save(commit=False))
        else:
            arquitecto['errors'] = form.errors.as_text()
            errors.append(arquitecto)
            error_msg = 'Error found in {:s}: {:s}'.format(str(arquitecto['id']), form.errors.as_text())
            log(process, task, state, type='INFO', msg=error_msg)

    new_arq = Arquitecto.objects.bulk_create(arquitectos)

    #if new_arq:
    log(process, task, state, type='INFO', msg=str(len(new_arq))+' arquitectos inserted\n')

    # noinspection PyUnboundLocalVariable
    if count:
        progress_data = {'current': count, 'total': count, 'errors': len(errors), 'prev': previous}
        log(process, task, state, progress_data, type='FPROGRESS')

    if len(errors) > 0:
        path = settings.ERROR_ROOT + str(process.id) + '_' + ntpath.basename(filename).replace('.xls', '.error.xls')

        df_error = pd.DataFrame(errors)
        df_error = df_error[pd.notnull(df_error['errors'])]
        df_error = pd.DataFrame(df_error, columns=('id', 'errors'))
        df_out = pd.merge(df_in, df_error, on='id')
        df_out.to_excel(path, index=False)

        # Link Error File to ImportProcess
        from ..models import ErrorFile
        error_file = ErrorFile()
        error_file.file.name = settings.ERROR_PATH + ntpath.basename(path)
        error_file.import_process = process
        error_file.save()

        # Save Errors to ImportProcess
        process.state.errors += len(errors)
        process.state.save()

    # Update inserts and duplicates
    process.state.insertions += len(arquitectos)
    process.state.duplicates += previous


@transaction.atomic
def load_arquitectos_licencas(filename, process=None, task=None, state='LOADING ARQUITECTOS/LICS'):
    filein, filename = bz_guard(filename)

    df = pd.read_excel(filein, sheet_name=0)

    grouped = df.groupby(('year', 'serial'))
    count = len(grouped)

    # normalize tipo, remove escassa relevância
    tipos = dict(Tipo.objects.values_list('id', 'name'))
    tipos[3] = tipos[2]

    i = 0
    for _, ((year, serial), group) in enumerate(grouped):
        i += 1
        if i % 10 == 0:
            progress_data = {'current': i, 'total': count}
            log(process, task, state, progress_data, type='PROGRESS')
        try:
            licenca = Licenca.objects.get(year=year, serial=serial)
        except Licenca.DoesNotExist:
            print('Licenca not found', year, serial)
            continue

        projectos = []
        for _, arq_obra in group.iterrows():
            try:
                arquitecto = Arquitecto.objects.get(id=int(arq_obra['nr_ordem']))
            except Arquitecto.DoesNotExist:
                print('Arquitecto not found', arq_obra['nr_ordem'])
                continue

            if arquitecto.projectos.filter(licenca=licenca).count() > 0:
                # projecto already loaded
                continue

            if licenca.destino_id is None:
                nome = "%s - %s" % (licenca.concelho.name, tipos[licenca.tipo_id])
            else:
                nome = "%s - %s - %s" % (licenca.concelho.name, licenca.destino.name, tipos[licenca.tipo_id])

            if 'edicao_impressa_c_foto_arq' in arq_obra and arq_obra['edicao_impressa_c_foto_arq'] == 1:
                status = STATUS_PUBLISHED
            else:
                status = STATUS_UNPUBLISHED

            Projecto(
                arquitecto=arquitecto,
                licenca=licenca,
                nome=nome,
                concelho=licenca.concelho,
                destino=licenca.destino,
                status=status
            ).save()

    progress_data = {'current': count, 'total': count}
    log(process, task, state, progress_data, type='PROGRESS')
