import sys
import ntpath
import numpy as np

from functools import partial

from django.contrib.gis.geos import Point
from django.db import transaction
from django.forms import ModelForm
from django.conf import settings

from anuario_backoffice.anuario.models.agente import Agente
from anuario_backoffice.anuario.models.licenca import LicencaAgente
from .base import get_cp7_row, pd, get_choice_model, get_freguesia, coerce_str, \
    coerce_int, coerce_klass, normalize_date, bz_guard, get_destino, get_agente, log
from ..models import ClasseEnergetica, Fase, Licenca, Licenciamento, Tipo


class LicencaForm(ModelForm):
    class Meta:
        model = Licenca
        fields = '__all__'


@transaction.atomic
def load_licencas(filename, process=None, task=None, state='LOADING LICENCAS'):
    filein, filename = bz_guard(filename)

    log(process, task, state, type='INFO', msg='Loading from ' + str(ntpath.basename(filename)))
    df = pd.read_excel(filein, sheet_name=0)
    log(process, task, state, type='OK', msg=' -> {:d} pics'.format(len(df)))

    # Remove NaN from dataframe
    # df = df.replace(np.nan, '', regex=True)

    log(process, task, state, type='INFO', msg='Getting id from year & serial\n')
    df['id'] = df.apply(lambda x: int("%d%05d" % (x['year'], x['serial'])), axis=1)

    df_in = df.copy()

    errors = []

    log(process, task, state, type='INFO', msg='Dropping duplicates\n')
    df_dup = df_in[df_in.duplicated(subset=('year', 'serial'), keep=False)]
    for i, obra in df_dup.iterrows():
        obra['errors'] = "Duplicated Entry"
        errors.append(obra)
    df.drop_duplicates(subset=('year', 'serial'), keep=False, inplace=True)

    log(process, task, state, type='INFO', msg='Normalizing cp\n')
    df_cp = df.apply(partial(get_cp7_row, cp_field='cp', localidade_field='localidade'), axis=1)
    df.drop('cp', axis=1, inplace=True)
    df = pd.merge(df, df_cp, on='id')

    log(process, task, state, type='INFO', msg='Normalizing data alvara\n')
    df['alvara_data'] = df.apply(lambda x: normalize_date(x['alvara_ano'], x['alvara_mes']), axis=1)

    log(process, task, state, type='INFO', msg='Normalizing data processo_cm\n')
    df['processo_cm_data'] = df.apply(lambda x: normalize_date(x['processo_cm_ano'], x['processo_cm_mes']), axis=1)

    log(process, task, state, type='INFO', msg='Normalizing destino\n')
    df['destino'] = df.apply(lambda x: get_destino(x['setor']), axis=1)

    log(process, task, state, type='INFO', msg='Normalizing fase\n')
    df['fase'] = df['fase'].apply(partial(get_choice_model, choicemodel=Fase))

    log(process, task, state, type='INFO', msg='Normalizing licenciamento\n')
    df['licenciamento'] = df['licenciamento'].apply(partial(get_choice_model, choicemodel=Licenciamento))

    log(process, task, state, type='INFO', msg='Normalizing tipo\n')
    df['tipo'] = df['tipo'].apply(partial(get_choice_model, choicemodel=Tipo))

    log(process, task, state, type='INFO', msg='Normalizing classe energetica\n')
    df['classe_energetica'] = df['classe_energetica'].apply(partial(get_choice_model, choicemodel=ClasseEnergetica))

    log(process, task, state, type='INFO', msg='Normalizing freguesia\n')
    df['freguesia'] = df['freguesia_id'].apply(lambda x: get_freguesia(x))

    log(process, task, state, type='INFO', msg='Normalizing concelho\n')
    df['concelho'] = df['freguesia'].apply(lambda x: x.concelho_id)

    log(process, task, state, type='INFO', msg='Normalizing promotor/agente\n')
    df['promotor'] = df['promotor'].apply(get_agente)

    count = len(df)
    licencas = []
    previous = 0
    i = 0
    for _, obra in df.iterrows():
        i += 1
        progress_data = {'current': i, 'total': count, 'errors': len(errors), 'prev': previous}
        log(process, task, state, progress_data, type='PROGRESS')
        try:
            Licenca.objects.get(id=obra['id'])

            previous += 1
            continue
        except Licenca.DoesNotExist:
            pass

        try:
            lon, lat = obra['gps'].split(',')
            obra['gps'] = Point(float(lat), float(lon), srid=4326)
        except (ValueError, AttributeError) as err:
            obra['errors'] = "GPS Failed: {0}".format(err)
            errors.append(obra)
            continue

        form = LicencaForm(dict(
            id=obra['id'],
            year=obra['year'],
            serial=obra['serial'],

            designacao=coerce_str(obra['designacao']),

            morada=obra['morada'],

            cp=coerce_klass(obra['cp']),
            cp_failed=obra['cp_failed'],

            gps=obra['gps'],
            concelho=obra['concelho'],
            freguesia=coerce_klass(obra['freguesia']),

            licenciamento=coerce_klass(obra['licenciamento']),
            ano_previsto=coerce_int(obra['ano_previsto']),
            duracao=coerce_int(obra['duracao']),

            processo_cm=coerce_str(obra['processo_cm']),
            processo_cm_data=obra['processo_cm_data'],

            alvara=coerce_str(obra['alvara']),
            alvara_data=obra['alvara_data'],

            fase=coerce_klass(obra['fase']),
            tipo=coerce_klass(obra['tipo']),
            destino=coerce_klass(obra['destino']),
            destino_detalhe=coerce_str(obra['setor_detalhe']),

            classe_energetica=coerce_klass(obra['classe_energetica']),

            area_construcao=coerce_int(obra['area_construcao']),

            n_pisos_acima=coerce_int(obra['n_pisos_acima']),
            n_pisos_abaixo=coerce_int(obra['n_pisos_abaixo']),

            n_fogos_total=coerce_int(obra['n_fogos_total']),
            n_quartos_1=coerce_int(obra['n_quartos_1']),
            n_quartos_2=coerce_int(obra['n_quartos_2']),
            n_quartos_3=coerce_int(obra['n_quartos_3']),
            n_quartos_4_mais=coerce_int(obra['n_quartos_4_mais']),

            obs=coerce_str(obra['observacoes'])
        ))
        if form.is_valid():
            licencas.append(form.save(commit=False))
        else:
            obra['errors'] = form.errors.as_text()
            errors.append(obra)

    if count:
        progress_data = {'current': count, 'total': count, 'errors': len(errors), 'prev': previous}
        log(process, task, state, progress_data, type='FPROGRESS')

    new_lics = Licenca.objects.bulk_create(licencas)

    #if new_lics:
    log(process, task, state, type='INFO', msg=str(len(new_lics))+' licencas inserted\n')


    df2 = df[pd.notnull(df['promotor'])]
    count = len(df2)
    errors2 = 0
    previous2 = 0
    i = 0
    if count:
        state = 'LOADING LICS (Promotores)'
        log(process, task, state, type='STATE')
    for _, licenca in df2.iterrows():
        i += 1
        progress_data = {'current': i, 'total': count, 'errors': errors2, 'prev': previous2}
        log(process, task, state, progress_data, type='PROGRESS')
        try:
            licenca_ = Licenca.objects.get(id=licenca['id'])
        except Licenca.DoesNotExist:
            errors2 += 1
            continue

        promotor = licenca_.agentes.filter(nif=licenca['promotor'].nif)
        if promotor.exists():
            previous2 += 1
            continue

        if licenca['concelho'] == 110600:
            tipo_id = 1
        else:
            tipo_id = 2

        LicencaAgente(licenca_id=licenca_.id, agente_id=licenca['promotor'].nif, tipo_id=tipo_id).save()

    if count:
        progress_data = {'current': count, 'total': count, 'errors': errors2, 'prev': previous2}
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

    # Save inserts
    if len(licencas) > 0:
        process.state.insertions += len(licencas)
        process.state.save()

    # Save Duplicates
    if previous > 0:
        process.state.duplicates += previous
        process.state.save()

    return new_lics


@transaction.atomic()
def load_licenca_agente(filename):
    filein, filename = bz_guard(filename)

    df = pd.read_excel(filein, sheet_name=0)
    grouped = df.groupby('id_licenca')

    for i, (id_licenca, group) in enumerate(grouped):
        try:
            licenca = Licenca.objects.get(pk=id_licenca)
        except Licenca.DoesNotExist:
            print('Licenca not found', id_licenca)
            continue

        for _, agente in group.iterrows():
            try:
                agente = Agente.objects.get(pk=agente['id_agente'])
            except Agente.DoesNotExist:
                print('AGENTE NOT FOUND', agente['id_agente'])
                continue

            licenca_agente = LicencaAgente(
                licenca_id=licenca,
                agente_id=agente
            )
        licenca_agente.save()


