from aleksis.apps.csv_import.models import FieldType


def test_field_type_value_dict():
    data = FieldType.value_dict
    assert data["unique_reference"] == FieldType.UNIQUE_REFERENCE
    assert len(data) == len(FieldType.__members__)
