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
        self.host = self.instance.ip_address
        return super().get_url(path_params)

    def log_error(self, e):
        logger.info(f"{self.__class__.__name__} Error: {e}")
