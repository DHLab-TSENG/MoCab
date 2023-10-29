from base.fhir_search_obj import _FhirClassObject
from base.fhir_bulk_obj import _BulkDataClient
from base.table import _HooksConfigTable
from base.table import _FhirResourceRoute
from base.table import _FeatureTable
from base.table import _TrainingSetTable
from base.table import _TrainingStatusTable
from base.table import _TransformationTable

fhir_class_obj = _FhirClassObject()
cds_hooks_config_table = _HooksConfigTable()
fhir_resources_route = _FhirResourceRoute()
feature_table = _FeatureTable()
model_feature_table = _TransformationTable()
bulk_server = _BulkDataClient()

# Used for training pipline
training_feature_table = _FeatureTable("./config/continuous_training/features.csv")
training_model_feature_table = _TransformationTable("./config/continuous_training/transformation.csv")
training_sets_table = _TrainingSetTable()
training_status_table = _TrainingStatusTable()
