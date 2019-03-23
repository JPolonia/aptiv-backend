import sys
import ntpath
from functools import partial

from django.db import transaction
from django.forms import ModelForm
from django.conf import settings

from .base import pd, get_cp7_row, coerce_str, coerce_klass, bz_guard, get_cae, log
from ..models import Agente


class AgenteForm(ModelForm):
    class Meta:
        model = Agente
        fields = '__all__'


@transaction.atomic
def load_agentes(filename, process=None, task=None, state='LOADING AGENTES'):
    filein, filename = bz_guard(filename)

    log(process, task, state, type='INFO', msg='Loading from ' + str(ntpath.basename(filename)))
    df = pd.read_excel(filein, sheet_name=0)
    log(process, task, state, type='OK', msg=' -> {:d} pics'.format(len(df)))

    df_in = df.copy()

    df['id'] = df['nif']

    log(process, task, state, type='INFO', msg='Normalizing CAE\n')
    df['cae'] = df['CAE'].apply(get_cae)

    log(process, task, state, type='INFO', msg='Normalizing CP\n')
    df_cp = df.apply(partial(get_cp7_row, cp_field='CP', localidade_field='Localidade'), axis=1)
    df = pd.merge(df, df_cp, on='id')

    count = len(df)
    agentes = []
    errors = []
    previous = 0
    i = 0
    for _, agente in df.iterrows():
        i += 1
        progress_data = {'current': i, 'total': count, 'errors': len(errors), 'prev': previous}
        log(process, task, state, progress_data, type='PROGRESS')
        try:
            Agente.objects.get(nif=agente['nif'])
            previous += 1
            continue
        except Agente.DoesNotExist:
            pass

        form = AgenteForm(dict(
            nif=agente['nif'],

            nome=coerce_str(agente['nome']),

            morada=coerce_str(agente['morada']),
            cp=coerce_klass(agente['cp']),
            cp_failed=agente['cp_failed'],

            telefones=coerce_str(agente['telefones']),
            email=coerce_str(agente['email']),
            website=coerce_str(agente['website']),

            cae=coerce_klass(agente['cae']),

            obs=coerce_str(agente['obs']),
        ))
        if form.is_valid():
            agentes.append(form.save(commit=False))
        else:
            agente['errors'] = form.errors.as_text()
            errors.append(agente)

    if count:
        progress_data = {'current': count, 'total': count, 'errors': len(errors), 'prev': previous}
        log(process, task, state, progress_data, type='FPROGRESS')

    new_agentes = Agente.objects.bulk_create(agentes)

    # if new_agentes:

    log(process, task, state, type='INFO', msg=str(len(new_agentes)) + ' agentes inserted\n')

    if len(errors) > 0:
        path = settings.ERROR_ROOT + str(process.id) + '_' + ntpath.basename(filename).replace('.xls', '.error.xls')

        # Generate Error File (Excel)
        df_error = pd.DataFrame(errors)
        df_error = df_error[pd.notnull(df_error['errors'])]
        df_error = pd.DataFrame(df_error, columns=('nif', 'errors'))
        df_out = pd.merge(df_in, df_error, on='nif')
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
    process.state.insertions += len(agentes)
    process.state.duplicates += previous


@transaction.atomic
def update_agentes(filename, process=None, task=None, state='UPDATING EXISTING AGENTES'):
    filein, filename = bz_guard(filename)

    log(process, task, state, type='INFO', msg='Loading from ' + str(ntpath.basename(filename)))
    df = pd.read_excel(filein, sheet_name=0)
    log(process, task, state, type='OK', msg=' -> {:d} pics'.format(len(df)))

    df_in = df.copy()

    df['id'] = df['nif']

    log(process, task, state, type='INFO', msg='Normalizing CAE\n')
    df['cae'] = df['CAE'].apply(get_cae)

    log(process, task, state, type='INFO', msg='Normalizing CP\n')
    df_cp = df.apply(partial(get_cp7_row, cp_field='CP', localidade_field='Localidade'), axis=1)
    df = pd.merge(df, df_cp, on='id')

    count = len(df)
    errors = []
    updated = 0
    not_found = 0
    i = 0
    for i, agente in df.iterrows():
        i += 1
        needs_update = False
        progress_data = {'current': i, 'total': count, 'errors': len(errors), 'pid': agente['nif'], 'updated': updated,
                         'not_found': not_found}
        log(process, task, state, progress_data, type='PROGRESS')
        try:
            p = Agente.objects.get(nif=agente['nif'])
        except Agente.DoesNotExist:
            not_found += 1
            continue

        # if coerce_str(agente['nome']).strip() != '' and coerce_str(agente['nome']).strip() != p.nome:
        #     needs_update = True
        #     p.nome = coerce_str(agente['nome']).strip()

        if coerce_str(agente['morada']).strip() != '' and coerce_str(agente['morada']).strip() != p.morada:
            needs_update = True
            p.morada = coerce_str(agente['morada']).strip()

        if coerce_klass(agente['cp']) and coerce_klass(agente['cp']) != p.cp_id:
            needs_update = True
            p.cp_id = coerce_klass(agente['cp'])

        if agente['cp_failed'] and agente['cp_failed'] != p.cp_failed:
            needs_update = True
            p.cp_failed = agente['cp_failed']

        if str(coerce_str(agente['telefones'])).strip() != '' and str(coerce_str(agente['telefones'])).strip() != p.telefones:
            needs_update = True
            p.telefones = str(coerce_str(agente['telefones'])).strip()

        if coerce_str(agente['email']).strip() != '' and coerce_str(agente['email']).strip() != p.email:
            needs_update = True
            p.email = coerce_str(agente['email']).strip()

        if coerce_str(agente['website']).strip() != '' and coerce_str(agente['website']).strip() != p.website:
            needs_update = True
            p.website = coerce_str(agente['website']).strip()

        if coerce_str(agente['obs']).strip() != '' and coerce_str(agente['obs']).strip() != p.obs:
            needs_update = True
            p.obs = coerce_str(agente['obs']).strip()

        if coerce_klass(agente['cae']) and coerce_klass(agente['cae']) != p.cae_id:
            needs_update = True
            p.cae_id = coerce_klass(agente['cae'])

        if needs_update:
            try:
                p.save()
                updated += 1
            except:
                errors.append(agente)

        # Old update function
        # cae_id = coerce_klass(agente['cae'])
        # if cae_id and p.cae_id != cae_id:
        #     p.cae_id = cae_id
        #     try:
        #         p.save()
        #         updated += 1
        #     except:
        #         errors.append(agente)

    if count:
        progress_data = {'current': count, 'total': count, 'errors': len(errors), 'updated': updated,
                         'not_found': not_found}
        log(process, task, state, progress_data, type='FPROGRESS')

    if len(errors) > 0:
        path = settings.ERROR_ROOT + str(process.id) + '_' + ntpath.basename(filename).replace('.xls', '.error.xls')

        # Generate Error File (Excel)
        df_error = pd.DataFrame(errors)
        df_error = df_error[pd.notnull(df_error['errors'])]
        df_error = pd.DataFrame(df_error, columns=('nif', 'errors'))
        df_out = pd.merge(df_in, df_error, on='nif')
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

    # Update updates
    process.state.updates += updated
