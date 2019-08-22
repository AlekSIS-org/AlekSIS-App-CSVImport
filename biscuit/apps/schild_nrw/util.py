from collections import OrderedDict
from typing import Any, BinaryIO, Callable, Dict, Optional, Union

from django.http import HttpRequest
from django.utils.translation import ugettext as _

import pandas
import phonenumbers

from biscuit.core.models import Person
from biscuit.core.util import messages


def schild_import_csv_single(request: HttpRequest, csv: Union[BinaryIO, str], cols: Dict[str, Any], converters: Dict[str, Callable[[Optional[str]], Any]]) -> None:
    persons = pandas.read_csv(csv, sep=';', names=cols.keys(), dtype=cols, usecols=lambda k: not k.startswith('_'), keep_default_na=False,
                              converters=converters, parse_dates=['date_of_birth'], quotechar='"', encoding='utf-8-sig', true_values=['+', 'Ja'], false_values=['-', 'Nein'])

    # Clean up invalid date values
    persons.date_of_birth = persons.date_of_birth.astype(object)
    persons = persons.where(persons.notnull(), None)

    all_ok = True

    for person_row in persons.transpose().to_dict().values():
        if 'is_active' not in person_row or person_row['is_active']:
            try:
                person, created = Person.objects.update_or_create(
                    import_ref=person_row['import_ref'], defaults=person_row)
            except ValueError as err:
                messages.error(request, _(
                    'Failed to import person %s %s: %s') % (person_row['first_name'], person_row['last_name'], err), fail_silently=True)
                all_ok = False

    if all_ok:
        messages.success(request, _(
            'All persons were imported successfully.'))
    else:
        messages.warning(request, _(
            'Some persons failed to be imported.'))


def schild_import_csv(request: HttpRequest, teachers_csv: Union[BinaryIO, str], students_csv: Union[BinaryIO, str], guardians_csv: Union[BinaryIO, str]) -> None:
    csv_converters = {'phone_number': lambda v: phonenumbers.parse(v, 'DE') if v else '',
                      'mobile_number': lambda v: phonenumbers.parse(v, 'DE') if v else '',
                      'sex': lambda v: 'f' if v == 'w' else v}

    teachers_csv_cols = OrderedDict([('import_ref', str), ('email', str), ('_email_business', str),
                                     ('date_of_birth', str), ('sex',
                                                              str), ('short_name', str),
                                     ('last_name', str), ('first_name',
                                                          str), ('street', str),
                                     ('postal_code', str), ('place',
                                                            str), ('phone_number', str),
                                     ('mobile_number', str), ('is_active', 'bool')])

    schild_import_csv_single(
        request, teachers_csv, teachers_csv_cols, csv_converters)

    students_csv_cols = OrderedDict([('import_ref', str), ('_internal_id', int), ('primary_group_short_name', str),
                                     ('last_name', str), ('first_name',
                                                          str), ('additional_name', str),
                                     ('date_of_birth', str), ('email',
                                                              str), ('_email_business', str),
                                     ('sex', str), ('street',
                                                    str), ('housenumber', str),
                                     ('postal_code', str), ('place', str), ('phone_number', str)])

    schild_import_csv_single(
        request, students_csv, students_csv_cols, csv_converters)
