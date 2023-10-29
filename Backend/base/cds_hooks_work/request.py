from dataclasses import dataclass
from typing import List


class RequestValidationException(Exception):
    pass


@dataclass
class FHIRAuthorization:
    # https://cds-hooks.org/specification/current/#fhir-resource-access
    access_token: str  # REQUIRED:	string	This is the OAuth 2.0 access token that provides access to the FHIR server.
    token_type: str  # expires_in	REQUIRED	Fixed value: Bearer
    expires_in = None  # REQUIRED	integer	The lifetime in seconds of the access token.
    scope: str  # REQUIRED	string	The scopes the access token grants the CDS Service.
    subject: str  # REQUIRED	string	The OAuth 2.0 client identifier of the CDS Service, as registered with the CDS Client's authorization server.


class Request(object):
    hook: str  # REQUIRED: The hook that triggered this CDS Service call. See Hooks.
    hookInstance: str  # REQUIRED	string	A UUID for this particular hook call (see more information below).
    fhirServer: str = ""  # OPTIONAL: an fhir server to access
    fhirAuthorization: FHIRAuthorization = None  # OPTIONAL: an fhirAuthorization
    prefetch: object  # OPTIONAL	object	The FHIR data that was prefetched by the CDS Client (see more information below).

    def hydrate(self, req):
        self.set_hooks(req)
        self.set_auth(req)
        self.set_prefetch(req)

    def set_hooks(self, req: dict):
        self.hook = req["hook"]
        self.hookInstance = req["hookInstance"]
        return self

    def set_auth(self, req: dict):
        if "fhirServer" in req:
            self.fhirServer = req["fhirServer"]
        if "fhirAuthorization" in req:  # if it's defined it can fail
            self.fhirAuthorization = FHIRAuthorization(**req["fhirAuthorization"])
        return self

    def set_prefetch(self, req: dict):
        if "prefetch" in req:
            self.prefetch = req["prefetch"]
        return self


@dataclass
class PatientViwContext(object):
    userId: str  # REQUIRED: The id of the current user
    patientId: str  # REQUIRED: The FHIR Patient.id of the current patient in context
    encounterId: str = ""  # OPTIONAL: The FHIR Encounter.id of the current encounter in context


class PatientViewRequest(Request):
    context: PatientViwContext

    def __init__(self, request_dict: dict):
        try:
            self.context = PatientViwContext(**request_dict["context"])
            self.hydrate(request_dict)
        except Exception as e:
            raise RequestValidationException from e


@dataclass
class OrderSelectContext(object):
    userId: str  # REQUIRED: The id of the current user
    patientId: str  # REQUIRED: The FHIR Patient.id of the current patient in context
    selections: List  # REQUIRED	No	array	The FHIR id of the newly selected order(s). The selections field references FHIR resources in the draftOrders Bundle. For example, MedicationRequest/103.
    draftOrders: object  # DSTU2 - FHIR Bundle of MedicationOrder, DiagnosticOrder, DeviceUseRequest, ReferralRequest, ProcedureRequest, NutritionOrder, VisionPrescription with draft status
    # STU3 - FHIR Bundle of MedicationRequest, ReferralRequest, ProcedureRequest, NutritionOrder, VisionPrescription with draft status
    # R4 - FHIR Bundle of MedicationRequest, NutritionOrder, ServiceRequest, VisionPrescription with draft status
    encounterId: str = ""  # OPTIONAL: The FHIR Encounter.id of the current encounter in context


class OrderSelectRequest(Request):
    context: OrderSelectContext

    def __init__(self, request_dict: dict):
        try:
            self.context = OrderSelectContext(**request_dict["context"])
            self.hydrate(request_dict)
        except Exception as e:
            raise RequestValidationException from e


@dataclass
class OrderSignContext(object):
    userId: str  # REQUIRED: The id of the current user.For this hook, the user is expected to be of type Practitioner or PractitionerRole. For example, PractitionerRole/123 or Practitioner/abc.
    patientId: str  # REQUIRED: The FHIR Patient.id of the current patient in context
    draftOrders: object  # DSTU2 - FHIR Bundle of MedicationOrder, DiagnosticOrder, DeviceUseRequest, ReferralRequest, ProcedureRequest, NutritionOrder, VisionPrescription with draft status
    # STU3 - FHIR Bundle of MedicationRequest, ReferralRequest, ProcedureRequest, NutritionOrder, VisionPrescription with draft status
    # R4 - FHIR Bundle of MedicationRequest, NutritionOrder, ServiceRequest, VisionPrescription with draft status
    encounterId: str = ""  # OPTIONAL: The FHIR Encounter.id of the current encounter in context


class OrderSignRequest(Request):
    context: OrderSignContext

    def __init__(self, request_dict: dict):
        try:
            self.context = OrderSignContext(**request_dict["context"])
            self.hydrate(request_dict)
        except Exception as e:
            raise RequestValidationException from e


@dataclass
class AppointmentBookContext(object):
    userId: str  # REQUIRED: The id of the current user
    patientId: str  # REQUIRED: The FHIR Patient.id of the current patient in context
    appointments: object  # REQUIRED	Yes	string	The FHIR Patient.id of Patient appointment(s) is/are for
    encounterId: str = ""  # OPTIONAL: The FHIR Encounter.id of the current encounter in context


class AppointmentBookRequest(Request):
    context: AppointmentBookContext

    def __init__(self, request_dict: dict):
        try:
            self.context = AppointmentBookContext(**request_dict["context"])
            self.hydrate(request_dict)
        except Exception as e:
            raise RequestValidationException from e


@dataclass
class EncounterStartContext(object):
    userId: str  # REQUIRED: The id of the current user
    patientId: str  # REQUIRED: The FHIR Patient.id of the current patient in context
    encounterId: str  # REQUIRED: The FHIR Encounter.id of the current encounter in context


class EncounterStartRequest(Request):
    context: EncounterStartContext

    def __init__(self, request_dict: dict):
        try:
            self.context = EncounterStartContext(**request_dict["context"])
            self.hydrate(request_dict)
        except Exception as e:
            raise RequestValidationException from e


@dataclass
class EncounterDischargeContext(object):
    userId: str  # REQUIRED: The id of the current user
    patientId: str  # REQUIRED: The FHIR Patient.id of the current patient in context
    encounterId: str  # REQUIRED: The FHIR Encounter.id of the current encounter in context


class EncounterDischargeRequest(Request):
    context: EncounterDischargeContext

    def __init__(self, request_dict: dict):
        try:
            self.context = EncounterDischargeContext(**request_dict["context"])
            self.hydrate(request_dict)
        except Exception as e:
            raise RequestValidationException from e
