from rules import add_perm

from aleksis.core.util.predicates import has_global_perm, has_person

import_data_predicate = has_person & has_global_perm("csv_import.import_data")
add_perm("csv_import.import_data_rule", import_data_predicate)
