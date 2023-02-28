from rest_framework.versioning import BaseVersioning
from rest_framework import exceptions


class HeaderVersioning(BaseVersioning):
    invalid_version_message = 'Invalid version in <Version> header.'

    def determine_version(self, request, *args, **kwargs):
        version = request.headers.get('Version', self.default_version)

        if not self.is_allowed_version(version):
            raise exceptions.NotAcceptable(self.invalid_version_message)

        try:
            version = float(version)
        except Exception:
            raise exceptions.NotAcceptable(self.invalid_version_message)

        return version
