import logging

from apps.clubs.models import ClubBranch
from apps.pipeline.services import BaseService

logger = logging.getLogger("gizmo")


class BaseGizmoService(BaseService):
    headers = {
        "Content-Type": "application/json",
    }
    instance = ClubBranch

    def get_url(self, path_params) -> str:
        self.host = self.instance.api_host
        return super().get_url(path_params)

    def get_auth(self):
        return self.instance.api_user, self.instance.api_password

    def run_service(self):
        return self.fetch()

    def log_error(self, e):
        logger.info(f"{self.__class__.__name__} Error: {e}")
