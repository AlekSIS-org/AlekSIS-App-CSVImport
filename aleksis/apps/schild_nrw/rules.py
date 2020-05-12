from rules import add_perm

from aleksis.core.util.predicates import has_global_perm, has_person

import_data_predicate = has_person & has_global_perm("schild_nrw.import_data")
add_perm("schild_nrw.import_data", import_data_predicate)
