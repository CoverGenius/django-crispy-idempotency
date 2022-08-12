import functools
import json
from typing import Union

from django.core.cache import cache
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from django_crispy_idempotency.encoders import JSONEncoder

TIME_OUT = 60 * 60


def get_cached_response(idempotency_identifier):
    response_data = cache.get(idempotency_identifier)
    if response_data:
        return create_response(response_data)
    return response_data


def create_response(response_data):
    response_data = json.loads(response_data)
    response = Response(**response_data)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    response.render()
    return response


def process_response(idempotency_identifier, response):
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


def idempotency_identifier(request):
    return request.headers.get("x-idempotency-key", None)


def idempotent_view(retry_request=False):
    def outer_decorator(func):
        @functools.wraps(func)
        def _decorated(self, *args, **kwargs):
            try:
                request = args[0]

                _idempotency_identifier = idempotency_identifier(request)
                if (
                    not _idempotency_identifier
                    or not is_drf_object(request)
                    or request.method not in ("POST", "PUT")
                ):
                    return func(self, *args, **kwargs)

                response = get_cached_response(_idempotency_identifier)
                if not response:
                    response = func(self, *args, **kwargs)
                    if is_drf_object(response):
                        process_response(_idempotency_identifier, response)
                return response

            except Exception:
                if retry_request:
                    return func(self, *args, **kwargs)
                raise

        return _decorated

    return outer_decorator


def is_drf_object(instance: Union[Request, Response]):
    return isinstance(instance, (Request, Response))


class IdempotencyResponse:
    def __init__(self, _idempotency_identifier) -> None:
        self._identifier = _idempotency_identifier

    @property
    def cached_response(self):
        response_data = cache.get(self._identifier)
        if response_data:
            return self._recreate_response(response_data)
        return response_data

    def _recreate_response(self, data):
        data = json.loads(data)
        response = Response(**data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        response.render()
        return response

    def cache_response(self, idempotency_identifier, response):
        if not is_drf_object(response):
            return response

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
