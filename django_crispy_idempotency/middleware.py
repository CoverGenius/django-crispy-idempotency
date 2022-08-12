import json
from typing import Union

from django.core.cache import cache
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from django_crispy_idempotency.encoders import JSONEncoder

TIME_OUT = 60 * 60


class IdempotencyMiddleware:

    ALLOWED_METHODS = ("POST", "PUT")

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def idempotency_identifier(self, request):
        return request.headers.get("x-idempotency-key", None)

    def get_cached_response(self, idempotency_identifier):
        response_data = cache.get(idempotency_identifier)
        if response_data:
            return self.recreate_response(response_data)
        return response_data

    def recreate_response(self, response_data):
        response_data = json.loads(response_data)
        response = Response(**response_data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        response.render()
        return response

    def process_response(self, idempotency_identifier, response):
        if response and status.is_success(response.status_code):
            response_data = {
                "data": response.data,
                "status": response.status_code,
                "template_name": response.template_name,
                "headers": response.headers,
                "content_type": response.content_type,
            }
            cache.add(
                idempotency_identifier,
                json.dumps(response_data, cls=JSONEncoder),
                timeout=TIME_OUT,
            )

        return response

    def __call__(self, request):
        try:
            _idempotency_identifier = self.idempotency_identifier(request)
            if (
                not _idempotency_identifier
                or request.method not in self.ALLOWED_METHODS
            ):
                return self.get_response(request)

            if (
                not _idempotency_identifier
                or not is_drf_object(request)
                or request.method not in ("POST", "PUT")
            ):
                return self.get_response(request)
            response = self.get_cached_response(_idempotency_identifier)
            if not response:
                response = self.get_response(request)
                if is_drf_object(response):
                    self.process_response(_idempotency_identifier, response)

            return response
        except Exception:
            return self.get_response(request)


def is_drf_object(instance: Union[Request, Response]):
    return isinstance(instance, (Request, Response))
