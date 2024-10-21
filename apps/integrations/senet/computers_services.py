from apps.clubs.models import ClubComputerGroup, ClubComputer
from apps.integrations.senet.base import BaseSenetService
from apps.integrations.soft_serializers import OuterComputerGroupsSaveSerializer, OuterComputersSaveSerializer


class SenetGetComputerZonesService(BaseSenetService):
    endpoint = "/api/v2/zone/?paginate=false&office_id={office_id}"
    method = "GET"
    save_serializer = OuterComputerGroupsSaveSerializer

    def run_request(self):
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


class SenetGetComputersWithSessionsService(BaseSenetService):
    endpoint = "/api/v2/map/table/?limit=999&office_id={office_id}"
    method = "GET"
    save_serializer = OuterComputersSaveSerializer

    def run_request(self):
        return self.fetch(path_params={"office_id": self.instance.outer_id})

    def save(self, response):
        if response and response.get('results') and isinstance(response['results'], list):
            resp_data = response['results']
            for outer_computer in resp_data:
                computer = ClubComputer.objects.filter(
                    club_branch_id=self.instance.id,
                    outer_id=outer_computer['workstation_id']
                ).first()
                computer_group = ClubComputerGroup.objects.filter(
                    club_branch_id=self.instance.id,
                    outer_id=outer_computer['dic_office_zone_id']
                ).first()
                if computer is None:
                    serializer = self.save_serializer(
                        data={
                            "outer_id": outer_computer['workstation_id'],
                            "club_branch": self.instance.id,
                            "number": outer_computer['num'],
                            "group": computer_group.id if computer_group else None,
                            "is_active_session": outer_computer['user_session_id'] is not None,
                            "is_locked": outer_computer['is_locked'] or outer_computer['is_updating'],
                            "is_broken": outer_computer['work_mode'] == 1,
                        }
                    )
                    try:
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)
                else:
                    computer.number = outer_computer['num']
                    computer.group = computer_group
                    computer.is_active_session = outer_computer['user_session_id'] is not None
                    computer.is_locked = outer_computer['is_locked'] or outer_computer['is_updating']
                    computer.is_broken = outer_computer['work_mode'] == 1
                    computer.save(update_fields=['number', 'group', 'is_active_session', 'is_locked', 'is_broken'])


class SenetWorkstationCommandService(BaseSenetService):
    endpoint = "/api/v2/workstation/command/"
    method = "POST"
    save_serializer = None
    command_type = None

    def run_request(self):
        command_type = self.command_type
        if command_type not in ("maintenance", "release"):
            self.log_error(f"Invalid command_type: {str(command_type)}")
        else:
            computers = [
                {
                    "workstation_id": c_outer_id,
                    "command_type": command_type
                } for c_outer_id in self.kwargs.get('computers')
            ]
            return self.fetch(json=computers)


class SenetLockComputersService(SenetWorkstationCommandService):
    command_type = "maintenance"


class SenetUnlockComputersService(SenetWorkstationCommandService):
    command_type = "release"


class SenetGetCashdeskIDService(BaseSenetService):
    endpoint = "/api/v2/cashdesk_office/?paginate=false"
    method = "GET"
    save_serializer = None

    def run_request(self):
        return self.fetch()

    # def finalize_response(self, response):
