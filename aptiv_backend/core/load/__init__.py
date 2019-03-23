import os

# from anuario_backoffice.anuario.load.gps_validate import gps_licencas, gps_pics
# from anuario_backoffice.anuario.models import Licenca, Pic
from .base import BASE_DIR, log
from .arquitecto import load_arquitectos, load_arquitectos_licencas
from .agente import load_agentes, update_agentes
from .licenca import load_licencas, load_licenca_agente
from .pic import load_pics, load_pic_agente
from .images import load_imagens, load_logos, load_concelhos_logos


def load(subdir, process=None, task=None):
    log(process,task,type='STATE',state='INIT LOAD')
    # print(task.request.id)

    filepath = os.path.join(BASE_DIR, 'data', subdir, 'arquitectos.xlsx')
    if os.path.exists(filepath):
        log(process, task, type='STATE', state='LOADING ARQUITECTOS')
        load_arquitectos(filepath, process, task)

    filepath = os.path.join(BASE_DIR, 'data', subdir, 'promotores.xlsx')
    if os.path.exists(filepath):
        log(process, task, type='STATE', state='LOADING AGENTES')
        load_agentes(filepath, process, task)

        if process:
            if process.update_agentes:
                log(process, task, type='STATE', state='UPDATING EXISTING AGENTES')
                update_agentes(filepath, process, task, state='UPDATING EXISTING AGENTES')


    licencas = False
    filepath = os.path.join(BASE_DIR, 'data', subdir, 'licencas.xlsx')
    if os.path.exists(filepath):
        log(process, task, type='STATE', state='LOADING LICENCAS')
        new_lics = load_licencas(filepath, process, task)

        log(process, task, type='STATE', state='VALIDATING GPS (LICS)')
        gps_licencas(new_lics, process, task)
        licencas = True

    # filepath = os.path.join(BASE_DIR, 'data', subdir, 'lic_agente.xlsx')
    # if os.path.exists(filepath):
    #     print("Licencas/Agentes")
    #     load_licenca_agente(filepath)

    filepath = os.path.join(BASE_DIR, 'data', subdir, 'arq_obra.xlsx')
    if os.path.exists(filepath):
        log(process, task, type='STATE', state='LOADING ARQUITECTOS/LICS')
        load_arquitectos_licencas(filepath, process, task)

    pics = False
    filepath = os.path.join(BASE_DIR, 'data', subdir, 'pics.xlsx')
    if os.path.exists(filepath):
        log(process, task, type='STATE', state='LOADING PICS')
        new_pics = load_pics(filepath, process, task)

        log(process, task, type='STATE', state='VALIDATING GPS (PICS)')
        gps_pics(new_pics, process, task)
        pics = True

    # filepath = os.path.join(BASE_DIR, 'data', subdir, 'pic_agente.xlsx')
    # if os.path.exists(filepath):
    #     print("PICS/Agentes")
    #     load_pic_agente(filepath)

    log(process, task, type='STATE', state='CONSOLIDATE FLAGS')
    consolidate_flags(licencas, pics)


def consolidate_flags(licencas=False, pics=False):
    if licencas:
        Licenca.objects.update(empreiteiro=False, arquitecto=False)
        Licenca.objects.filter(agentes__licencaagente__tipo_id=6).distinct().update(empreiteiro=True)
        Licenca.objects.filter(projectos_arquitecto__isnull=False).distinct().update(arquitecto=True)
    if pics:
        Pic.objects.update(promotor=False)
        Pic.objects.filter(agentes__picagente__tipo_id__lte=2).distinct().update(promotor=True)
