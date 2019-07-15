from biscuit.core.models import Person

import codecs
import csv


def schild_import_csv(teachers_csv, students_csv, guardians_csv):
    teachers_reader = csv.DictReader(codecs.iterdecode(teachers_csv, 'utf-8'),
                                     fieldnames=('guid', 'email', 'email_business', 'date_of_birth',
                                                 'sex', 'abbrev', 'last_name', 'first_name', 'street', 'postal_code', 'place', 'phone_number', 'mobile_number', 'visible'))

    for teacher_row in teachers_reader:
        if teacher_row['visible']:
            person, created = Person.objects.get_or_create(
                guid=teacher_row['guid'], defaults=teacher_row)
