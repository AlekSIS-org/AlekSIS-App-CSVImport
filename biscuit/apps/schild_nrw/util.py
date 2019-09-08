from collections import OrderedDict
from typing import Any, BinaryIO, Callable, Dict, Optional, Union

from django.http import HttpRequest
from django.utils.translation import ugettext as _

import pandas
import phonenumbers

from biscuit.core.models import Person
from biscuit.core.util import messages


SCHILD_STATE_ACTIVE = (True, 2)


def is_active(person_row: dict) -> bool:
    """ Find out whether an imported person is active by looking
    at different attributes.
    """

    if 'is_active' in person_row:
        return person_row['is_active'] in SCHILD_STATE_ACTIVE

    return True


def schild_import_csv_single(request: HttpRequest, csv: Union[BinaryIO, str], cols: Dict[str, Any], converters: Dict[str, Callable[[Optional[str]], Any]]) -> None:
    persons = pandas.read_csv(csv, sep=';', names=cols.keys(), dtype=cols, usecols=lambda k: not k.startswith('_'), keep_default_na=False,
                              converters=converters, parse_dates=['date_of_birth'], quotechar='"', encoding='utf-8-sig', true_values=['+', 'Ja'], false_values=['-', 'Nein'])

    # Clean up invalid date values
    persons.date_of_birth = persons.date_of_birth.astype(object)
    persons = persons.where(persons.notnull(), None)

    all_ok = True
    inactive_refs = []

    for person_row in persons.transpose().to_dict().values():
        # Fill the is_active field from other fields if necessary
        person_row['is_active'] = is_active(person_row)

        if person_row['is_active']:
            try:
                person, created = Person.objects.update_or_create(
                    import_ref=person_row['import_ref'], defaults=person_row)
            except ValueError as err:
                messages.error(request, _(
                    'Failed to import person %s' % ('%s, %s' % (person_row['last_name'], person_row['first_name']))) + ': %s' % err, fail_silently=True)
                all_ok = False

            # Ensure that newly set primary group is also in member_of
            if person.primary_group and person.primary_group not in person.member_of.all():
                person.member_of.add(person.primary_group)
                person.save()
        else:
            # Store import refs to deactivate later
            inactive_refs.append(person_row['import_ref'])

    # Deactivate all persons that existed but are now inactive
    if inactive_refs:
        affected = Person.objects.filter(
            import_ref__in=inactive_refs,
            is_active=True
        ).update(
            is_active=False
        )

        if affected:
            messages.warning(request, _('%d existing persons were deactivated.') % affected)

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
                                     ('postal_code', str), ('place', str), ('phone_number', str), ('is_active', int)])

    schild_import_csv_single(
        request, students_csv, students_csv_cols, csv_converters)
