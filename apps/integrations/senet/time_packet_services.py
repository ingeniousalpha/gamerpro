from decimal import Decimal

from apps.integrations.senet.base import BaseSenetService
from apps.integrations.senet.serializers import SenetTimePacketCreateSerializer


class SenetGetTimePacketsV1Service(BaseSenetService):
    endpoint = "/api/v2/ticket/?office_id={office_id}"
    method = "GET"
    save_serializer = SenetTimePacketCreateSerializer

    def run_request(self):
        return self.fetch(path_params={"office_id": self.instance.outer_id})

    def save(self, response):
        for time_packet in response:
            try:
                computer_group = self.instance.computer_groups.filter(
                    outer_id=time_packet['zones'][0]
                ).first()
                if computer_group:
                    serializer = self.save_serializer(
                        data={
                            "outer_id": time_packet['id'],
                            "outer_name": time_packet['name'],
                            "display_name": time_packet['name'],
                            "price": time_packet['price'],
                            "minutes": time_packet['duration_period_length']*60,
                            "club_computer_group": computer_group.id,
                        }
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
            except Exception as e:
                self.log_error(e)


class SenetGetTimePacketsV2Service(BaseSenetService):
    endpoint = "/bonus_systems/additional_refill/?paginate=false"
    method = "GET"
    save_serializer = SenetTimePacketCreateSerializer

    def run_request(self):
        return self.fetch()

    def save(self, response):
        for time_packet in response:
            try:
                name = f"{int(float(time_packet['from_amount']))} + {int(float(time_packet['amount']))}"
                serializer = self.save_serializer(
                    data={
                        "outer_id": time_packet['id'],
                        "outer_name": name,
                        "display_name": name,
                        "price": Decimal(time_packet['from_amount']),
                        "club": self.instance.club_id
                    }
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except Exception as e:
                self.log_error(e)
