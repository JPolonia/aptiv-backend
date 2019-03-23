import sys
import ntpath
from functools import partial

from django.contrib.gis.geos import Point
from django.db import transaction
from django.forms import ModelForm
from django.conf import settings

from anuario_backoffice.anuario.models.agente import Agente
from anuario_backoffice.anuario.models.pic import Pic, PicAgente
from .base import get_cp7_row, pd, get_choice_model, get_freguesia, coerce_str, \
    coerce_int, coerce_klass, bz_guard, get_destino, get_arquitecto, normalize_date, get_choice_model_by_id, \
    get_agente, log
from ..models import ClasseEnergetica, Fase, Tipo


class PicForm(ModelForm):
    class Meta:
        model = Pic
        fields = '__all__'


@transaction.atomic
def load_pics(filename, process=None, task=None, state='LOADING PICS'):
    filein, filename = bz_guard(filename)

    log(process, task, state, type='INFO', msg='Loading from ' + str(ntpath.basename(filename)))
    df = pd.read_excel(filein, sheet_name=0)
    log(process, task, state, type='OK', msg=' -> {:d} pics'.format(len(df)))

    log(process, task, state, type='INFO', msg='Getting ref_ci from year & serial\n')
    df['ref_ci'] = df.apply(lambda x: int("%d%05d" % (x['year'], x['serial'])), axis=1)
    df['id'] = df['ref_ci']

    df_in = df.copy()

    errors = []

    log(process, task, state, type='INFO', msg='Dropping duplicates\n')
    df_dup = df_in[df_in.duplicated(subset=('year', 'serial'), keep=False)]
    for i, obra in df_dup.iterrows():
        obra['errors'] = "Duplicated Entry"
        errors.append(obra)
    df.drop_duplicates(subset=('year', 'serial'), keep=False, inplace=True)

    log(process, task, state, type='INFO', msg='Normalizing cp\n')
    df_cp = df.apply(partial(get_cp7_row, cp_field='cp'), axis=1)
    df.drop('cp', axis=1, inplace=True)
    df = pd.merge(df, df_cp, on='id')

    log(process, task, state, type='INFO', msg='Normalizing mês\n')
    df['mes'] = df.apply(lambda x: int("%02d" % x['mes']), axis=1)

    log(process, task, state, type='INFO', msg='Normalizing destino\n')
    df['destino'] = df.apply(lambda x: get_destino(x['destino']), axis=1)

    log(process, task, state, type='INFO', msg='Normalizing fase\n')
    df['fase'] = df['fase'].apply(partial(get_choice_model, choicemodel=Fase))

    log(process, task, state, type='INFO', msg='Normalizing tipo\n')
    df['tipo'] = df['tipo'].apply(partial(get_choice_model, choicemodel=Tipo))

    log(process, task, state, type='INFO', msg='Normalizing classe energetica\n')
    df['classe_energetica'] = df['classe_energetica'].apply(
        partial(get_choice_model_by_id, choicemodel=ClasseEnergetica))

    log(process, task, state, type='INFO', msg='Get arquitectos\n')
    df['arquitecto'] = df['arquitecto'].apply(get_arquitecto)

    log(process, task, state, type='INFO', msg='Get promotores\n')
    df['promotor'] = df['promotor'].apply(get_agente)

    log(process, task, state, type='INFO', msg='Normalizing freguesia\n')
    df['freguesia'] = df['freguesia'].apply(lambda x: get_freguesia(x))
    for i, obra in df[pd.isnull(df['freguesia'])].iterrows():
        log(process, task, state, type='INFO', msg='Erro na linha ' + i + ' - Freguesia Invalida (Ver Error File)\n')
        obra['errors'] = "Freguesia Inválida"
        errors.append(obra)
    df = df[pd.notnull(df['freguesia'])]

    log(process, task, state, type='INFO', msg='Normalizing concelhos\n')
    df['concelho'] = df['freguesia'].apply(lambda x: x.concelho_id)

    log(process, task, state, type='INFO', msg='Normalizing regiao\n')
    df['regiao'] = df['freguesia'].apply(lambda x: x.regiao_id)

    count = len(df) + len(errors)
    pics = []
    previous = 0
    i = 0
    for _, pic in df.iterrows():
        i += 1
        # Test Traceback
        # if i > 500:
        #     raise ValueError('A very specific bad thing happened.')
        progress_data = {'current': i, 'total': count, 'errors': len(errors), 'prev': previous, 'pid': str(pic['id'])}
        log(process, task, state, progress_data, type='PROGRESS')
        try:
            Pic.objects.get(id=pic['id'])
            previous += 1
            continue
        except Pic.DoesNotExist:
            pass

        try:
            lon, lat = pic['gps'].split(',')
            if lat.count('.') > 1:
                parts = lat.split('.')
                lat = parts[0] + '.' + ''.join(parts[1:])
            if lon.count('.') > 1:
                parts = lon.split('.')
                lon = parts[0] + '.' + ''.join(parts[1:])
            pic['gps'] = Point(float(lat), float(lon), srid=4326)
        except ValueError as err:
            pic['errors'] = "GPS Failed: {0}".format(err)
            errors.append(pic)
            continue

        form = PicForm(dict(
            id=pic['id'],
            year=pic['year'],
            serial=pic['serial'],
            mes=pic['mes'],
            data_emissao=normalize_date(pic['year'], pic['mes']),
            designacao=coerce_str(pic['designacao']),

            morada=pic['morada'],

            cp=coerce_klass(pic['cp']),
            cp_failed=pic['cp_failed'],

            gps=pic['gps'],
            regiao=pic['regiao'],
            concelho=pic['concelho'],
            freguesia=coerce_klass(pic['freguesia']),

            fase=coerce_klass(pic['fase']),
            tipo=coerce_klass(pic['tipo']),
            destino=coerce_klass(pic['destino']),
            destino_detalhe=coerce_str(pic['setor_detalhe']),
            classe_energetica=coerce_klass(pic['classe_energetica']),

            area_construcao=coerce_int(pic['area_construcao']),

            n_fogos_total=coerce_int(pic['n_fogos_total']),
            n_quartos_1=coerce_int(pic['n_quartos_1']),
            n_quartos_2=coerce_int(pic['n_quartos_2']),
            n_quartos_3=coerce_int(pic['n_quartos_3']),
            n_quartos_4_mais=coerce_int(pic['n_quartos_4_mais']),

            outras_tipologias=coerce_int(pic['outras_tipologias']),
            a_mais=coerce_int(pic['a_mais']),
            a=coerce_int(pic['a']),
            b=coerce_int(pic['b']),
            b_menos=coerce_int(pic['b_menos']),

            obs=coerce_str(pic['observacoes']),

            nivel=coerce_int(pic['nivel'])
        ))
        if form.is_valid():
            pics.append(form.save(commit=False))
        else:
            pic['errors'] = form.errors.as_text()
            print(form.errors.as_text())
            errors.append(pic)

    if count:
        progress_data = {'current': count, 'total': count, 'errors': len(errors), 'prev': previous}
        log(process, task, state, progress_data, type='FPROGRESS')

    new_pics = Pic.objects.bulk_create(pics)

    log(process, task, state, type='INFO', msg=str(len(new_pics))+' pics inserted\n')

    df2 = df[pd.notnull(df['arquitecto'])]
    count = len(df2)
    i = 0
    errors2 = 0
    previous2 = 0
    if count:
        state = 'LOADING PICS (Arquitectos)'
        log(process, task, state, type='STATE')
    for _, pic in df2.iterrows():
        i += 1
        progress_data = {'current': i, 'total': count, 'errors': errors2, 'prev': previous2, 'pid': str(pic['id'])}
        log(process, task, state, progress_data, type='PROGRESS')
        try:
            pic_ = Pic.objects.get(id=pic['id'])
        except Pic.DoesNotExist:
            errors2 += 1
            continue

        arquitectos = pic_.arquitecto.filter(id=pic['arquitecto'].id)
        if arquitectos.exists():
            previous2 += 1
            continue

        pic_.arquitecto.add(pic['arquitecto'])

    if count:
        progress_data = {'current': i, 'total': count, 'errors': errors2, 'prev': previous2}
        log(process, task, state, progress_data, type='FPROGRESS')


    df3 = df[pd.notnull(df['promotor'])]
    count = len(df3)
    errors2 = 0
    previous2 = 0
    i = 0
    if count:
        state = 'LOADING PICS (Promotores)'
        log(process, task, state, type='STATE')
    for _, pic in df3.iterrows():
        i += 1
        progress_data = {'current': i, 'total': count, 'errors': errors2, 'prev': previous2, 'pid': str(pic['id'])}
        log(process, task, state, progress_data, type='PROGRESS')

        try:
            pic_ = Pic.objects.get(id=pic['id'])
        except Pic.DoesNotExist:
            errors2 += 1
            continue

        promotor = pic_.agentes.filter(nif=pic['promotor'].nif)
        if promotor.exists():
            previous2 += 1
            continue

        if pic['concelho'] == 110600:
            tipo_id = 1
        else:
            tipo_id = 2

        PicAgente(pic_id=pic_.id, agente_id=pic['promotor'].nif, tipo_id=tipo_id).save()

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

    # Update inserts and duplicates
    process.state.insertions += len(pics)
    process.state.duplicates += previous

    return new_pics

@transaction.atomic
def update_pics(filename):
    filein, filename = bz_guard(filename)

    df = pd.read_excel(filein, sheet_name=0)
    df['id'] = df.apply(lambda x: int("%d%05d" % (x['year'], x['serial'])), axis=1)
    df_in = df.copy()

    df['destino'] = df.apply(lambda x: get_destino(x['setor']), axis=1)

    count = len(df)
    updated = 0
    not_found = []
    errors = []
    for i, obra in df.iterrows():
        if i % 10 == 0:
            sys.stdout.write("\rImport progress: %d%% (%d of %d) (%d updated) (%d errors found) (%d not found)" % (
                (i * 1.0 / count) * 100, i, count, updated, len(errors), len(not_found)))
            sys.stdout.flush()
        try:
            p = Pic.objects.get(id=obra['id'])
        except Pic.DoesNotExist:
            not_found += 1
            continue

        needs_update = False
        destino_id = coerce_klass(obra['destino'])
        if p.destino_id != destino_id:
            p.destino_id = destino_id
            needs_update = True
        if obra['setor_detalhe'] != '' and p.destino_detalhe != obra['setor_detalhe']:
            p.destino_detalhe = obra['setor_detalhe']
            needs_update = True

        if needs_update:
            try:
                p.save()
                updated += 1
            except:
                errors.append(obra)

    sys.stdout.write("\rImport progress: %d%% (%d of %d) (%d updated) (%d errors found) (%d not found)" % (
        100, count, count, updated, len(errors), len(not_found)))
    sys.stdout.flush()

    if len(errors) > 0:
        df_error = pd.DataFrame(errors)
        df_error = df_error[pd.notnull(df_error['errors'])]
        df_error = pd.DataFrame(df_error, columns=('id', 'errors'))
        df_out = pd.merge(df_in, df_error, on='id')
        df_out.to_excel(filename.replace('.xls', '.error.xls'), index=False)


@transaction.atomic()
def load_pic_agente(filename):
    filein, filename = bz_guard(filename)

    df = pd.read_excel(filein, sheet_name=0)
    grouped = df.groupby('id_licenca')

    for i, (id_pic, group) in enumerate(grouped):
        try:
            pic = Pic.objects.get(pk=id_pic)
        except Pic.DoesNotExist:
            print('PIC not found', id_pic)
            continue

        for _, agente in group.iterrows():
            try:
                agente = Agente.objects.get(pk=agente['id_agente'])
            except Agente.DoesNotExist:
                print('AGENTE NOT FOUND', agente['id_agente'])
                continue

            pic_agente = PicAgente(
                pic_id=pic,
                agente_id=agente
            )
        pic_agente.save()
