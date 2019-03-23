import fnmatch
import os
import re

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import File
from django.db import transaction

from contrib.geo.models import Concelho
from ..models import Licenca, LogoConcelho


@transaction.atomic
def load_imagens(path):
    ref_ci_regex = re.compile(
        r'L(?P<year>20[0-9]{2})(?P<serial>[0-9]{5})\.*'
    )

    for root, _, files in os.walk(path):
        if root != path:  # keep single level
            continue
        for name in files:
            if not (fnmatch.fnmatch(name, "*.jpg") or fnmatch.fnmatch(name, "*.jpeg")):
                continue

            fname = os.path.join(root, name)
            print(fname)

            # noinspection PyTypeChecker
            with open(fname, 'rb') as f:
                django_file = File(f)

            ref_ci = ref_ci_regex.search(name)
            if ref_ci:
                year = ref_ci.group('year')
                serial = ref_ci.group('serial')
                print(year, serial)
                licenca = Licenca.objects.filter(year=year).get(serial=serial)
                try:
                    projecto = licenca.projecto_arquitecto
                except ObjectDoesNotExist:
                    print('Projecto Arquitecto nao existe')
                    continue
                try:
                    projecto.imagens.create(imagem=django_file)
                except TypeError:
                    print('ImageError')


@transaction.atomic
def load_logos(path):
    ref_ci_regex = re.compile(
        r'L(?P<year>20[0-9]{2})(?P<serial>[0-9]{5})\.*'
    )

    for root, _, files in os.walk(path):
        if root != path:  # keep single level
            continue
        for name in files:
            if not (fnmatch.fnmatch(name, "*.jpg") or fnmatch.fnmatch(name, "*.jpeg")):
                continue

            fname = os.path.join(root, name)
            print(fname)

            # noinspection PyTypeChecker
            with open(fname, 'rb') as f:
                django_file = File(f)

            ref_ci = ref_ci_regex.search(name)
            if ref_ci:
                year = ref_ci.group('year')
                serial = ref_ci.group('serial')
                print(year, serial)

                try:
                    licenca = Licenca.objects.filter(year=year).get(serial=serial)
                except Licenca.DoesNotExist:
                    continue
                try:
                    arquitecto = licenca.projecto_arquitecto.arquitecto
                    if arquitecto.logo == '':
                        arquitecto.logo = django_file
                        arquitecto.save()
                except ObjectDoesNotExist:
                    print('DoesNotExist')
                except TypeError:
                    print('ImageError')


@transaction.atomic
def load_concelhos_logos(path):
    id_regex = re.compile(
        r'(?P<id>[0-9]{5,6})\.*'
    )

    for root, _, files in os.walk(path):
        if root != path:  # keep single level
            continue
        for name in files:
            if not fnmatch.fnmatch(name, "*.png"):
                continue

            fname = os.path.join(root, name)
            print(fname)

            # noinspection PyTypeChecker
            with open(fname, 'rb') as f:
                django_file = File(f)

            c = id_regex.search(name)
            if c:
                cid = c.group('id')
                print(cid)

                try:
                    concelho = Concelho.objects.get(id=cid)
                except Concelho.DoesNotExist:
                    continue

                lc = LogoConcelho(concelho=concelho, logo=django_file)
                lc.save()
