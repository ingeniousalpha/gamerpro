import time
import traceback
import logging
from copy import deepcopy
from abc import ABC, abstractmethod
from typing import Optional, Type, Tuple, Union, Any

from requests import Session
from urllib.parse import urljoin
from requests.models import Response
from rest_framework.exceptions import ValidationError
from requests.exceptions import ConnectTimeout, ConnectionError, HTTPError, RequestException

from apps.integrations import ServiceStatuses
from apps.integrations.models import OuterServiceLog
from apps.integrations.exceptions import (
    ServiceUnavailable,
    ServiceNotFound,
    UnauthorizedError,
)

logger = logging.getLogger("api_services")


class BaseService(ABC):
    instance = None
    instance_class = None
    save_serializer: Optional[Type] = None

    log_headers: bool = False
    log_request: bool = False
    log_response: bool = False
    log_execution_time: bool = False

    headers: dict = None
    url: str = None
    host: str = None
    endpoint: str = None
    timeout: int = 45
    method: str = 'POST'
    auth: Optional[Tuple[str, str]] = None
    cert: Optional[Tuple[str, str]] = None
    _session: Optional[Session] = None
    host_verify: bool = True

    # History attrs
    status_code: int = None
    data: dict = None
    code: str = None
    status: ServiceStatuses
    last_request: Union[bytes, str, None] = ''
    last_response: Union[bytes, str, None] = ''
    runtime: float = 0

    def __init__(self, instance=None, **kwargs):
        self.instance = self.instance_class(instance) if self.instance_class else instance
        self.kwargs = kwargs
        self.status = ServiceStatuses.NO_REQUEST
        self.last_request, self.last_response = "", ""

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = Session()
            self._session.hooks["response"].append(self.history)
        return self._session

    def history(self, response: Response, *args, **kwargs) -> None:
        self.last_request = response.request.body
        self.last_response = response.text

    def get_url(self, path_params) -> str:
        if path_params:
            self.endpoint = self.endpoint.format(**path_params)
        url = urljoin(self.host, self.endpoint)
        return url

    def get_headers(self) -> dict:
        return self.headers

    def get_auth(self):
        return self.auth

    def fetch(self, query_params=None, path_params=None, data=None, json=None, files=None, **kwargs):
        _start = time.perf_counter()

        if self.url is None:
            self.url = self.get_url(path_params)

        if self.headers is None:
            self.headers = self.get_headers()

        if self.auth is None:
            self.auth = self.get_auth()

        if self.log_request:
            print("self.url: ", self.url)
            print()
        response_raw = self.session.request(
            method=self.method,
            url=self.url,
            auth=self.auth,
            headers=self.headers,
            params=query_params,
            data=data,
            json=json,
            files=files,
            timeout=self.timeout,
            verify=self.host_verify,
            **kwargs
        )
        self.status_code = response_raw.status_code

        self.runtime = time.perf_counter() - _start
        self.code = str(response_raw.status_code)

        logger.info('url: %s' % response_raw.request.url)
        if self.log_headers:
            logger.info('headers: %s' % response_raw.request.headers)  # TODO log properly
        if self.log_request:
            logger.info('request: %s' % response_raw.request.body)
        # if self.log_response:
            # logger.info('response: %s' % response_raw.content)

        if response_raw.status_code == 400:
            return self.handle_400(response_raw)

        if response_raw.status_code == 401:
            return self.handle_401(response_raw)

        if response_raw.status_code == 404:
            return self.handle_404(response_raw)

        if response_raw.status_code >= 500:
            return self.handle_500(response_raw)

        response =  self.get_response(response_raw)
        if self.log_response:
            print("response: ", response)

        return response

    def handle_400(self, response: Response):  # noqa
        return response.json()

    def handle_401(self, response: Response):
        raise UnauthorizedError

    def handle_404(self, response: Response):  # noqa
        raise ServiceNotFound

    def handle_500(self, response: Response):
        raise ServiceUnavailable

    def get_response(self, response: Response):  # noqa
        try:
            return response.json()
        except Exception as e:
            logger.info("JSON PARSE ERROR body %s, status_code %s" % (response.text, str(response.status_code)))
            raise e

    def get_instance(self):
        return self.instance

    def finalize_response(self, response):  # noqa
        return response

    @abstractmethod
    def run_service(self) -> Any:
        """
        This method should be overload
        """

    def skip_task(self):
        ...

    def run(self):
        start = time.perf_counter()

        response_data = None
        skip_task = self.skip_task()

        if skip_task:
            return skip_task

        try:
            response_data = self.run_service()
            self.data = deepcopy(response_data)
            self.save(response_data)

        except ServiceUnavailable:
            logger.error(f"Service is unavailable {self.__class__.__name__}")
            self.status = ServiceStatuses.SERVICE_UNAVAILABLE

        except UnauthorizedError:
            logger.error(f"Service is unauthorized {self.__class__.__name__}")
            self.status = ServiceStatuses.UNAUTHORIZED

        except (ConnectTimeout, ConnectionError, HTTPError, RequestException) as exc:
            raise exc

        except Exception as exc:
            logger.exception(exc)
            logger.error(f"Exception({self.__class__.__name__}): {exc.__class__} {exc}")
            logger.error(traceback.format_exc())
            self.status = ServiceStatuses.REQUEST_ERROR

        else:
            self.status = ServiceStatuses.WAS_REQUEST

        finally:
            self.log_save()

        finalized_response = self.finalize_response(response_data)
        if self.log_execution_time:
            exec_time = time.perf_counter() - start
            logger.info(f"Total execution time of {self.__class__.__name__} is {exec_time}")

        return finalized_response

    def log_save(self, instance=None):
        if not instance:
            instance = self.instance

        # print("log_save: ", instance)
        # print(instance.__dict__)
        if hasattr(instance, 'log_history'):
            # print('inside if')
            history = OuterServiceLog.objects.create(  # noqa
                content_object=instance,
                service=self.__class__.__name__,
                data=getattr(self, 'data', None),
                status=getattr(self, 'status', ServiceStatuses.NO_REQUEST),
                runtime=getattr(self, 'runtime', 0),
            )
            # print('history created')
            try:
                history.set_response(
                    url=getattr(self, 'url', None),
                    code=getattr(self, 'code', None),
                    method=getattr(self, 'method', None),
                    request=self.last_request,
                    response=self.last_response,
                )
                # print('set_response')
            except Exception as exc:
                logger.exception(exc)

    def prepare_to_save(self, response: dict) -> dict:  # noqa
        return response

    def save(self, response):
        if self.save_serializer and isinstance(response, dict):
            instance = self.get_instance()

            if instance and response:
                serializer = self.save_serializer(
                    instance=self.instance,
                    data=self.prepare_to_save(response)
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            elif response:
                serializer = self.save_serializer(
                    data=self.prepare_to_save(response)
                )
                try:
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                except ValidationError as e:
                    pass
                except Exception as e:
                    logger.exception(e)


class ServiceLoggingMixin:
    log_response = False
    log_request = False
    log_headers = False
