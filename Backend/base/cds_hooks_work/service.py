from typing import List
from .request import Request, PatientViewRequest
from .response import Response
from collections.abc import Callable

HookHandler = callable([[Request, Response]])
PatientViewHandler = callable([[PatientViewRequest, Response]])


class Service(object):
    # https://cds-hooks.org/specification/current/#discovery
    hook: str  # REQUIRED	string	The hook this service should be invoked on. See Hooks.
    id: str  # REQUIRED	string	The {id} portion of the URL to this service which is available at
    # {baseUrl}/cds-services/{id}
    description: str  # REQUIRED	string	The description of this service.
    title: str  # RECOMMENDED	string	The human-friendly name of this service.
    prefetch: object  # optional
    handler: HookHandler

    def __init__(self, hook, id, description, title="", prefetch=None, handler: HookHandler = None):
        self.hook = hook
        self.id = id
        self.description = description
        self.title = title
        if prefetch is not None:
            self.prefetch = prefetch
        else:
            self.prefetch = {}
        if handler is not None:
            self.handler = handler

    def to_dict(self):
        return {
            "hook": self.hook,
            "id": self.id,
            "description": self.description,
            "title": self.title,
            "prefetch": self.prefetch
        }

    def set_handler(self, handler: Callable):
        self.handler = handler

    def handle_input(self, request_dict: dict):
        response = Response(statusCode=200)  # set a response with a default status code

        if self.hook == 'patient-view':
            request = PatientViewRequest(request_dict)
            self.handler(request, response)
            return response
        else:
            raise NotImplemented
