import traceback

from django.conf import settings
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from constance import config

from .renderers import JSONRenderer
from .response_handler.dataclasses import CustomError, CustomResponse
from .services import save_error


class JSONRendererMixin:
    renderer_classes = [JSONRenderer]

    def dispatch(self, request, *args, **kwargs):

        if not config.EXCEPTION_HANDLING_STATUS:
            return super().dispatch(request, *args, **kwargs)

        else:
            try:
                response = super().dispatch(request, *args, **kwargs)
                print('response dispatched')
                return response

            except Exception as e:
                error = CustomError(None, 'internal_server_error', str(e)).__dict__
                error['traceback'] = traceback.format_exc()
                error['error_id'] = save_error(error['code'], error['message'], error['traceback'])

                if not settings.DEBUG:
                    error.pop('traceback')

                return JsonResponse(
                    CustomResponse(None, error).__dict__,
                    status=500, safe=True,
                    json_dumps_params={'ensure_ascii': False}
                )


class PublicAPIMixin:
    permission_classes = [AllowAny]


class PublicJSONRendererMixin(JSONRendererMixin, PublicAPIMixin):
    ...
