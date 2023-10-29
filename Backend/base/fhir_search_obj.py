from __future__ import annotations
from fhirpy import SyncFHIRClient
from config import configObject as config


class _FhirClassObject:
    _default_client: SyncFHIRClient
    _client: SyncFHIRClient

    def __init__(self):
        self._default_client = SyncFHIRClient(
            url=config['fhir_server']['FHIR_SERVER_URL']
        )

    def update_client(self, **kwargs):
        """

        :param kwargs: configs of server, {
            url = fhir base url,
            authorization = "bearer ..." # used while server is protected.
        }
        :return: None
        """
        self._client = SyncFHIRClient(
            **kwargs
        )

    def client(self, default_client=False):
        if default_client:
            return self._default_client

        try:
            return self._default_client if self._client is None else self._client
        except AttributeError:
            return self._default_client


# fhir_class_obj = FhirClassObject()
