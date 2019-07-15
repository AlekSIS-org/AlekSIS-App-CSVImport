from biscuit.core.models import Person

from collections import OrderedDict

import pandas
import phonenumbers


def schild_import_csv(teachers_csv, students_csv, guardians_csv):
    teachers_csv_cols = OrderedDict([('import_ref', str), ('email', str), ('_email_business', str),
                                     ('date_of_birth', str), ('sex',
                                                              str), ('_abbrev', str),
                                     ('last_name', str), ('first_name',
                                                          str), ('street', str),
                                     ('postal_code', str), ('place',
                                                            str), ('phone_number', str),
                                     ('mobile_number', str), ('is_active', 'bool')])
    teachers_csv_converters = {'phone_number': lambda v: phonenumbers.parse(v, 'DE') if v else None,
                               'mobile_number': lambda v: phonenumbers.parse(v, 'DE') if v else None,
                               'sex': lambda v: 'f' if v == 'w' else v}

    teachers = pandas.read_csv(teachers_csv, sep=';', names=teachers_csv_cols.keys(), dtype=teachers_csv_cols, usecols=lambda k: not k.startswith('_'), keep_default_na=False, converters=teachers_csv_converters,
                               parse_dates=['date_of_birth'], quotechar='"', encoding='utf-8-sig', true_values=['+', 'Ja'], false_values=['-', 'Nein'])

    for teacher_row in teachers.transpose().to_dict().values():
        if teacher_row['is_active']:
            person, created = Person.objects.get_or_create(
                import_ref=teacher_row['import_ref'], defaults=teacher_row)
