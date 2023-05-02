# custom exceptions to handle error codes in services


class ServiceUnavailable(Exception):
    ...


class ServiceNotFound(Exception):
    ...


class UnauthorizedError(Exception):
    ...
