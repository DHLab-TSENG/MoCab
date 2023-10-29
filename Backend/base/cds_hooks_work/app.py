from .service import Service
from .response import Response
from .server import init
from typing import List
from flask import Blueprint

class App(object):
    services: List[Service] = []
    server: Blueprint

    def __init__(self, services: List[Service] = None):
        if services is None:
            self.services = []
        else:
            self.services = services
        self.server = init(self)

    def register_service(self, service: Service):
        self.services.append(service)

    def discovery(self):
        return {"services": [s.to_dict() for s in self.services]}

    def handle_hook(self, id: str, input: dict) -> Response:
        try:
            if "hook" in input:
                hook = input["hook"]
                for service in self.services:
                    if hook == service.hook and id == service.id:
                        return service.handle_input(input)
                # message = f"service with id: {id} and hook {hook} not found"
            return Response(statusCode=400)
        except Exception as e:
            print(e)
            return Response(statusCode=500)

    def _handler_decorator(self, service_type, id: str, description: str, **kwargs):
        """decorator that creates a services and registers it"""

        def decorator(handler):
            kwargs["handler"] = handler
            self.register_service(Service(service_type, id, description, **kwargs))
            return handler

        return decorator

    def patient_view(self, *args, **kwargs):
        return self._handler_decorator("patient-view", *args, **kwargs)

    def order_select(self, *args, **kwargs):
        return self._handler_decorator("order-select", *args, **kwargs)

    def order_sign(self, *args, **kwargs):
        return self._handler_decorator("order-sign", *args, **kwargs)

    def appointment_book(self, *args, **kwargs):
        return self._handler_decorator("appointment-book", *args, **kwargs)

    def encounter_start(self, *args, **kwargs):
        return self._handler_decorator("encounter-start", *args, **kwargs)

    def encounter_discharge(self, *args, **kwargs):
        return self._handler_decorator("encounter-discharge", *args, **kwargs)
