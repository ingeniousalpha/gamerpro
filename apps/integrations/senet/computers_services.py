from apps.clubs.models import ClubComputerGroup
from apps.integrations.senet.base import BaseSenetService
from apps.integrations.soft_serializers import OuterComputerGroupsSaveSerializer


class SenetGetComputerZonesService(BaseSenetService):
    endpoint = "/api/v2/zone/?paginate=false&office_id={office_id}"
    method = "GET"
    save_serializer = OuterComputerGroupsSaveSerializer

    def run_service(self):
        return self.fetch(path_params={
            "office_id": self.instance.outer_id
        })

    def save(self, response):
        if isinstance(response, list) and len(response) > 0:
            for zone in response:
                if not ClubComputerGroup.objects.filter(
                    outer_id=zone['id'],
                    club_branch_id=self.instance.id
                ).exists():
                    try:
                        serializer = self.save_serializer(
                            data={
                                "outer_id": zone['id'],
                                "name": zone['name'],
                                "club_branch": self.instance.id,
                            }
                        )
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)
        else:
            self.log_error("Empty Response")
