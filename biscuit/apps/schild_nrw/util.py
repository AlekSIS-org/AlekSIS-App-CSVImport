from biscuit.core.models import Person

from collections import OrderedDict

from django.contrib import messages
from django.utils.translation import gettext as _

import pandas
import phonenumbers


def schild_import_csv_single(request, csv, cols, converters):
    persons = pandas.read_csv(csv, sep=';', names=cols.keys(), dtype=cols, usecols=lambda k: not k.startswith('_'), keep_default_na=False,
                              converters=converters, parse_dates=['date_of_birth'], quotechar='"', encoding='utf-8-sig', true_values=['+', 'Ja'], false_values=['-', 'Nein'])

    all_ok = True

    for person_row in persons.transpose().to_dict().values():
        if person_row['is_active']:
            try:
                person, created = Person.objects.get_or_create(
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


def schild_import_csv(request, teachers_csv, students_csv, guardians_csv):
    csv_converters = {'phone_number': lambda v: phonenumbers.parse(v, 'DE') if v else '',
                      'mobile_number': lambda v: phonenumbers.parse(v, 'DE') if v else '',
                      'sex': lambda v: 'f' if v == 'w' else v}

    teachers_csv_cols = OrderedDict([('import_ref', str), ('email', str), ('_email_business', str),
                                     ('date_of_birth', str), ('sex',
                                                              str), ('_abbrev', str),
                                     ('last_name', str), ('first_name',
                                                          str), ('street', str),
                                     ('postal_code', str), ('place',
                                                            str), ('phone_number', str),
                                     ('mobile_number', str), ('is_active', 'bool')])
    teachers_csv_converters = {'phone_number': lambda v: phonenumbers.parse(v, 'DE') if v else '',
                               'mobile_number': lambda v: phonenumbers.parse(v, 'DE') if v else '',
                               'sex': lambda v: 'f' if v == 'w' else v}

    schild_import_csv_single(
        request, teachers_csv, teachers_csv_cols, csv_converters)

    students_csv_cols = OrderedDict([('import_ref', str), ('_internal_id', int), ('_class', str),
                                     ('last_name', str), ('first_name',
                                                          str), ('additional_name', str),
                                     ('date_of_birth', str), ('email',
                                                              str), ('_email_business', str),
                                     ('sex', str), ('street',
                                                    str), ('housenumber', str),
                                     ('postal_code', str), ('place', str), ('phone_number', str)])

    schild_import_csv_single(
        request, students_csv, students_csv_cols, csv_converters)
